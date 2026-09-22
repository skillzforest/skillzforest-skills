// Not wired into `main.rs` yet (see module docs) — allowed dead code rather
// than deleted, so the interface stays real, compiling Rust to build against
// once the API exists.
#![allow(dead_code)]
use super::{SkillSource, SkillSourceError};
use crate::models::{CatalogPack, CatalogSkill, RuntimeManifest};
use std::path::PathBuf;

/// Talks to the SkillzForest API instead of a local checkout. This is what a
/// packaged, standalone build ships with — the end user never sees this
/// repository at all.
///
/// Not implemented. Wiring it up needs, in order:
///
/// 1. TODO: `GET {api_base}/skills` / `GET {api_base}/packs` / a runtimes
///    manifest endpoint — same shapes as `skill.json` / `pack.json` /
///    `runtime.json`, so `CatalogSkill` etc. don't need to change.
/// 2. TODO: authenticated download of a signed package for
///    `resolve_distribution` (see the "Discover -> Buy -> Install" flow in
///    the root README) — likely a signed, versioned zip per
///    (skill, runtime) pair, mirroring `dist/skills/<skill>/<runtime>/`.
/// 3. TODO: signature verification before the downloaded package is ever
///    passed to `runtimes::filesystem_adapter` — this is the security
///    boundary that replaces "it's the maintainer's own repo" trust.
/// 4. TODO: a local cache dir (`app_data_dir()/cache/`) so re-installing or
///    updating doesn't always re-download.
/// 5. TODO: auth/session handling for a SkillzForest account — see
///    `installer/README.md`'s Settings section.
///
/// Until then, every method returns `SkillSourceError::NotImplemented` and
/// the frontend simply doesn't offer a "browse SkillzForest" entry point —
/// only `LocalSkillSource` is wired into the app today.
pub struct RemoteSkillSource {
    #[allow(dead_code)]
    api_base: String,
}

impl RemoteSkillSource {
    pub fn new(api_base: impl Into<String>) -> Self {
        Self {
            api_base: api_base.into(),
        }
    }
}

impl SkillSource for RemoteSkillSource {
    fn list_skills(&self) -> Result<Vec<CatalogSkill>, SkillSourceError> {
        Err(SkillSourceError::NotImplemented(
            "RemoteSkillSource::list_skills — SkillzForest API not built yet",
        ))
    }

    fn list_packs(&self) -> Result<Vec<CatalogPack>, SkillSourceError> {
        Err(SkillSourceError::NotImplemented(
            "RemoteSkillSource::list_packs — SkillzForest API not built yet",
        ))
    }

    fn list_runtimes(&self) -> Result<Vec<RuntimeManifest>, SkillSourceError> {
        Err(SkillSourceError::NotImplemented(
            "RemoteSkillSource::list_runtimes — SkillzForest API not built yet",
        ))
    }

    fn resolve_distribution(
        &self,
        _skill_id: &str,
        _runtime_id: &str,
    ) -> Result<PathBuf, SkillSourceError> {
        Err(SkillSourceError::NotImplemented(
            "RemoteSkillSource::resolve_distribution — signed package download not built yet",
        ))
    }
}
