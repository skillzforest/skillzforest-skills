# SkillzForest Installer

A desktop app (Tauri + React + TypeScript) that lets a non-technical user install SkillzForest skills and packs into their local AI runtimes — no Node.js, npm, Git, or terminal required.

```text
Discover -> Buy -> Install -> Choose runtime -> Ready to use
```

## Principle

This app contains **no skill source**. It reads `skills/`, `packs/`, and `runtimes/` from the parent `skillzforest-skills` repo (in dev mode) and only ever *installs* — copies or generates a distribution and writes it to a runtime's own folder. It never duplicates a skill's files anywhere inside `installer/`.

```text
skills/      = canonical source        (../skills)
packs/       = commercial composition  (../packs)
runtimes/    = compatibility + paths   (../runtimes)
installer/   = UI + install engine     (this app)
dist/        = generated artifacts     (../dist, plus dist/installer/<os>/ for this app's own builds)
```

## Architecture

```text
installer/
├── src/                 # React + TypeScript UI
│   ├── app/             # App shell, router, deep-link handling
│   ├── components/      # Layout, cards, badges, dialogs
│   ├── pages/           # Welcome, Home, My Skills, Skill/Pack Details, Updates, Settings
│   ├── services/tauri.ts  # The ONLY place that calls `invoke(...)`
│   ├── store/           # React context: catalog + detected runtimes + registry
│   ├── types/           # Mirrors src-tauri/src/models.rs field-for-field
│   └── utils/           # Pure logic (capability presentation, My Skills projection) — unit tested
│
└── src-tauri/           # Rust backend
    ├── src/
    │   ├── commands/    # #[tauri::command] handlers — thin, call into installer::engine
    │   ├── installer/   # engine.rs (install/uninstall/update/conflict logic), registry.rs
    │   ├── runtimes/    # RuntimeAdapter trait + FilesystemAdapter + ManualAdapter
    │   ├── skill_source/  # SkillSource trait: LocalSkillSource (used today) + RemoteSkillSource (stub)
    │   ├── filesystem/  # path resolution, safe recursive copy, PATH lookup
    │   ├── security/    # id validation, path traversal prevention
    │   ├── download/    # stub for RemoteSkillSource's future HTTP fetch + verify
    │   └── models.rs    # every type that crosses the Tauri IPC boundary
    └── tauri.conf.json
```

No layer is more complex than it needs to be: there's no message queue, no plugin system beyond Tauri's own, no ORM for the registry (it's one JSON file).

## The install flow, in code

`SkillDetails` (frontend) → `install_skill` command → `installer::engine::install_skill`:

1. `RuntimeAdapter::can_install(skill)` — reads `skill.json`'s `compatibility[runtimeId]` and the runtime's `installStrategy`, returns `Ready | Manual | Unknown | Unsupported`. Only `Ready` proceeds.
2. `engine::detect_conflict` — is there already something at the target path that the registry doesn't know about? If so, the frontend shows the Keep/Replace/Cancel dialog and the call is retried with a `ConflictResolution`.
3. `RuntimeAdapter::install` — for a `filesystem` runtime, copies the skill folder (excluding `node_modules/`, `out/`, `.DS_Store`) into `paths.user/<skill-id>/`, guarded by `security::ensure_within` against path traversal, then verifies `SKILL.md` landed.
4. `installer::registry::record_install` — the only thing that makes SkillzForest "own" that install, and thus later allowed to uninstall or update it.

**Installing a skill never executes anything inside it.** Scripts that ship with a skill (e.g. `av-devis/scripts/fill_devis.js`) are copied like any other file — the runtime or the user runs them later, never this app.

## Runtimes: functional today vs. prepared

| Runtime | Status | Automated in this app? |
|---|---|---|
| Claude Code | verified, `filesystem` | **Yes** |
| Codex | supported, `filesystem` | **Yes** |
| Gemini (CLI) | supported, `filesystem` | **Yes** — same generic adapter, zero extra code |
| Claude.ai | verified, `upload` | No — `ManualAdapter` reports `Manual`; UI shows "Manual installation" |
| Mistral, Perplexity | supported, `manual-bundle` | No — same as above |
| ChatGPT, Cursor, OpenCode | unknown | No — UI shows "Coming soon" |

Any runtime with `installStrategy: "filesystem"` in `runtimes/<id>/runtime.json` is automatically installable with **zero new Rust** — `runtimes::build_adapter` picks `FilesystemAdapter` for any of them. Adding real automation for `upload`/`manual-bundle`/`plugin` means writing one more `RuntimeAdapter` impl and adding a match arm in `runtimes::build_adapter` — the engine, commands, and frontend never need to change.

## Development

```bash
npm install         # once, inside installer/
npm run dev          # Vite dev server only (fast UI iteration, no Tauri window)
npm run installer:dev  # full app: Tauri window + Vite dev server + Rust hot-reload
```

From the repo root:

```bash
npm run app:dev      # same as `npm run installer:dev`, run from installer/
```

`LocalSkillSource::discover()` locates the repo by walking up from this crate's own path, so **the installer must be run from inside a checkout of `skillzforest-skills`** — it will refuse to start otherwise (see `skill_source/local.rs`).

## Testing

```bash
npm test                                  # vitest — pure TS logic (capability rules, My Skills projection, deep-link parsing)
cd src-tauri && cargo test                # Rust — path traversal, id validation, install/conflict/pack engine logic
```

Rust tests use `std::env::temp_dir()` fixtures, never the real `~/.claude` or `~/.agents` — see `filesystem::tests` and `installer::engine::tests`.

## Building

```bash
npm run installer:build   # tauri build, then scripts/collect-bundle.mjs copies the OS bundle into ../dist/installer/<os>/
```

```text
dist/
├── skills/            # from `npm run build` at the repo root — untouched by this app
├── packs/
└── installer/
    ├── macos/         # .dmg (+ the .app itself)
    ├── windows/       # .exe (NSIS) / .msi
    └── linux/         # .AppImage
```

Building for Windows/Linux from this checkout requires running `tauri build` on that OS (or via CI matrix) — Tauri doesn't cross-compile installers.

**Icon**: `src-tauri/icons/icon.png` is a placeholder solid-color 128×128 PNG. Before a real release, run `npm run tauri icon <path-to-real-artwork.png>` to generate the full icon set Tauri's bundler expects.

## Adding a runtime

1. Add `runtimes/<id>/runtime.json` at the repo root (see `../runtimes/README.md`) — this alone makes it show up in `detect_runtimes` and in every skill's capability map.
2. If `installStrategy` is `"filesystem"`, nothing else to write — `FilesystemAdapter` already handles it via `paths.user` and `detection`.
3. If it needs a real transformation (`upload`, `manual-bundle`, `plugin`), add a new `impl RuntimeAdapter` in `src-tauri/src/runtimes/`, and add one match arm to `runtimes::build_adapter`.
4. Update `skill.json` compatibility values once actually verified — never guess `native`/`supported` here either.

## Adding a remote source

`src-tauri/src/skill_source/remote.rs` has the interface (`SkillSource`) and a documented TODO list: API endpoints for the catalog, signed-package download + verification, a local cache, and account/session handling. Swap it in by constructing `RemoteSkillSource` instead of `LocalSkillSource::discover()` in `main.rs` once it's implemented — nothing else in the app (commands, engine, frontend) depends on which source is active.

## The registry

`~/.skillzforest/registry.json` (via `dirs::data_dir()`, so it's `~/Library/Application Support/skillzforest/` on macOS, `%APPDATA%\skillzforest\` on Windows, `~/.local/share/skillzforest/` on Linux). Shape:

```json
{
  "skills": {
    "av-devis": {
      "claude-code": { "version": "0.1.0", "installDate": 1732000000000, "source": "local-repo" }
    }
  }
}
```

This is the **only** thing that makes an install "ours". Uninstall and update both refuse to touch a path that isn't in here — see `installer::registry::is_ours` and its use in `engine::uninstall_skill`.

## Security

- **No script execution, ever.** Installing copies files; it never runs them.
- **Path traversal**: every write goes through `security::ensure_within`, which rejects `..`, absolute components, and anything that normalizes outside the destination root. Covered by `filesystem::tests` and `security::tests`.
- **Id validation**: skill/pack/runtime ids are restricted to `[a-z0-9-]` before they're ever used to build a path (`security::validate_id`).
- **No silent overwrite**: `engine::detect_conflict` + the frontend's `ConflictDialog` mean an unregistered existing install is never touched without an explicit Replace.
- **Uninstall is scoped**: only removes a directory the registry says SkillzForest created.

## Deep links (`skillzforest://`)

Registered via `tauri-plugin-deep-link` (see `tauri.conf.json`'s `plugins.deep-link.desktop.schemes` and `main.rs`'s `on_open_url` handler, which forwards the URL to the frontend as a `skillzforest://deep-link` event; `src/app/useDeepLinks.ts` parses and navigates).

```text
skillzforest://install/dev-seo          -> opens Skill Details for dev-seo
skillzforest://install-pack/saas-builder -> opens Pack Details for saas-builder
```

**Not independently verified in this environment** (no display server to click-test an actual OS handoff). What's configured:
- macOS/Linux: the `deep-link` plugin's desktop config registers the `skillzforest` scheme at build time via the bundler.
- Windows: the same plugin registers a registry entry on install (NSIS/MSI).

Before shipping, actually click a `skillzforest://` link on each target OS after installing a built package and confirm the app opens on the right screen — this class of OS integration can't be confirmed by compiling alone.

## Known limitations (MVP)

- Only `filesystem`-strategy runtimes are automated (see the table above).
- `RemoteSkillSource` doesn't exist yet — this build only ever talks to a local `skillzforest-skills` checkout.
- No SkillzForest account / auth (Settings shows a disabled placeholder).
- Update = clean reinstall, no delta/diffing.
- Icon is a placeholder; deep-link OS registration is configured but not click-tested.
