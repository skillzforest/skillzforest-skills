import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAppData } from "../store/AppContext";
import { skillzforest } from "../services/tauri";
import type { CatalogSkill } from "../types/skill";
import type { ConflictResolution, InstallCapability } from "../types/runtime";
import type { InstallOutcome } from "../types/registry";
import { presentCapability, worksWithRuntimeIds } from "../utils/capability";
import { RuntimeBadge } from "../components/RuntimeBadge";
import { ConflictDialog } from "../components/ConflictDialog";

type ViewState =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "form" }
  | { kind: "conflict"; runtimeIds: string[] }
  | { kind: "installing" }
  | { kind: "done"; outcomes: InstallOutcome[] };

export function SkillDetails() {
  const { skillId } = useParams<{ skillId: string }>();
  const navigate = useNavigate();
  const { runtimes, registry, refresh } = useAppData();

  const [skill, setSkill] = useState<CatalogSkill | null>(null);
  const [capabilities, setCapabilities] = useState<Record<string, InstallCapability>>({});
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [view, setView] = useState<ViewState>({ kind: "loading" });

  useEffect(() => {
    if (!skillId) return;
    setView({ kind: "loading" });
    Promise.all([skillzforest.getSkill(skillId), skillzforest.getSkillCapabilities(skillId)])
      .then(([skillRes, capsRes]) => {
        setSkill(skillRes);
        setCapabilities(capsRes);
        const preselected = new Set(
          Object.entries(capsRes)
            .filter(([runtimeId, cap]) => cap === "ready" && runtimes.find((r) => r.runtime.id === runtimeId)?.detected)
            .map(([runtimeId]) => runtimeId),
        );
        setSelected(preselected);
        setView({ kind: "form" });
      })
      .catch((e) => setView({ kind: "error", message: String(e) }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [skillId]);

  const installedRuntimeIds = useMemo(
    () => (skillId ? Object.keys(registry.skills[skillId] ?? {}) : []),
    [registry, skillId],
  );

  if (view.kind === "loading") return <p className="empty-state">Loading…</p>;
  if (view.kind === "error") return <p className="empty-state">Couldn't load this skill: {view.message}</p>;
  if (!skill || !skillId) return null;

  const worksWith = worksWithRuntimeIds(skill.manifest.compatibility);
  const nameFor = (id: string) => runtimes.find((r) => r.runtime.id === id)?.runtime.name ?? id;
  const detectedFor = (id: string) => runtimes.find((r) => r.runtime.id === id)?.detected ?? false;
  const pathFor = (id: string) => runtimes.find((r) => r.runtime.id === id)?.runtime.paths?.user ?? null;

  async function startInstall() {
    const runtimeIds = Array.from(selected);
    const conflictChecks = await Promise.all(
      runtimeIds.map((id) => skillzforest.checkConflict(skillId!, id).then((c) => (c ? id : null))),
    );
    const conflicting = conflictChecks.filter((id): id is string => id !== null);
    if (conflicting.length > 0) {
      setView({ kind: "conflict", runtimeIds });
    } else {
      await runInstall(runtimeIds, undefined);
    }
  }

  async function runInstall(runtimeIds: string[], resolution: ConflictResolution | undefined) {
    setView({ kind: "installing" });
    const outcomes = await skillzforest.installSkill(skillId!, runtimeIds, resolution);
    await refresh();
    setView({ kind: "done", outcomes });
  }

  async function handleUninstall(runtimeId: string) {
    await skillzforest.uninstallSkill(skillId!, runtimeId);
    await refresh();
  }

  if (view.kind === "conflict") {
    return (
      <ConflictDialog
        skillName={skill.manifest.name}
        onResolve={(resolution) => {
          if (resolution === "cancel") {
            setView({ kind: "form" });
          } else {
            void runInstall(view.runtimeIds, resolution);
          }
        }}
      />
    );
  }

  if (view.kind === "done") {
    const succeeded = view.outcomes.filter((o) => o.installed);
    const failed = view.outcomes.filter((o) => !o.installed);
    return (
      <div className="centered-screen">
        <h1 style={{ margin: 0 }}>{skill.manifest.name} installed</h1>
        <div>
          {succeeded.map((o) => (
            <p key={o.runtimeId} className="status-line status-ok">
              ✓ {nameFor(o.runtimeId)}
            </p>
          ))}
          {failed.map((o) => (
            <p key={o.runtimeId} className="status-line status-warn">
              ✗ {nameFor(o.runtimeId)} — {o.reason}
            </p>
          ))}
        </div>
        {succeeded.length > 0 && (
          <p className="page-subtitle" style={{ maxWidth: 420 }}>
            You can now ask your AI assistant things like the example prompts on this skill's page.
          </p>
        )}
        <button className="btn" onClick={() => navigate("/my-skills")}>
          Done
        </button>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 640 }}>
      <h1 className="page-title">{skill.manifest.name}</h1>
      <p className="page-subtitle">{skill.manifest.description}</p>

      <div className="card" style={{ marginBottom: 16 }}>
        <p className="card-title">Works with</p>
        <div className="badge-row">
          {worksWith.map((id) => (
            <RuntimeBadge key={id} name={nameFor(id)} variant="default" />
          ))}
        </div>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <p className="card-title">Detected on this computer</p>
        <div className="badge-row">
          {worksWith.map((id) => (
            <RuntimeBadge key={id} name={nameFor(id)} variant={detectedFor(id) ? "detected" : "not-detected"} />
          ))}
        </div>
      </div>

      {installedRuntimeIds.length > 0 && (
        <div className="card" style={{ marginBottom: 16 }}>
          <p className="card-title">Already installed in</p>
          {installedRuntimeIds.map((id) => (
            <div key={id} className="checklist-item">
              <span className="status-line status-ok" style={{ flex: 1 }}>
                ✓ {nameFor(id)}
              </span>
              <button className="btn secondary" onClick={() => void handleUninstall(id)}>
                Remove
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="card">
        <p className="card-title">Install for</p>
        {worksWith
          .filter((id) => !installedRuntimeIds.includes(id))
          .map((id) => {
            const presentation = presentCapability(capabilities[id] ?? "unknown");
            if (!presentation.offerable) return null;
            return (
              <label key={id} className="checklist-item">
                <input
                  type="checkbox"
                  disabled={!presentation.installable}
                  checked={selected.has(id)}
                  onChange={(e) => {
                    const next = new Set(selected);
                    if (e.target.checked) next.add(id);
                    else next.delete(id);
                    setSelected(next);
                  }}
                />
                <span style={{ flex: 1 }}>{nameFor(id)}</span>
                {!presentation.installable && <span className="badge manual">{presentation.label}</span>}
              </label>
            );
          })}

        <button
          className="btn"
          style={{ marginTop: 16 }}
          disabled={selected.size === 0 || view.kind === "installing"}
          onClick={() => void startInstall()}
        >
          {view.kind === "installing" ? "Installing…" : "Install"}
        </button>

        <button className="btn secondary" style={{ marginTop: 16, marginLeft: 10 }} onClick={() => setAdvancedOpen((v) => !v)}>
          Advanced
        </button>

        {advancedOpen && (
          <div className="advanced-panel">
            <div>skill id: {skill.manifest.id}</div>
            <div>version: {skill.manifest.version}</div>
            <div>source: {skill.sourceDir}</div>
            {worksWith.map((id) => (
              <div key={id}>
                {id} install path: {pathFor(id) ?? "(manual — no filesystem path)"}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
