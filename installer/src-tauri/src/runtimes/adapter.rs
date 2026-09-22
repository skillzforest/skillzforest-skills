use crate::filesystem::FsError;
use crate::models::{InstallCapability, RuntimeManifest, SkillManifest};
use crate::security::SecurityError;
use std::path::Path;

#[derive(Debug, thiserror::Error)]
pub enum AdapterError {
    #[error(transparent)]
    Fs(#[from] FsError),
    #[error(transparent)]
    Security(#[from] SecurityError),
    #[error("this runtime has no automated install mechanism yet (installStrategy: '{0}') — see its runtimes/<id>/README.md")]
    ManualOnly(String),
    #[error("'{0}' is not installed by SkillzForest here — refusing to touch it")]
    NotOurs(String),
}

/// One implementation per runtime. The engine (`installer::engine`) never
/// branches on a runtime id directly — it only calls through this trait, so
/// adding a runtime never means touching the engine.
pub trait RuntimeAdapter {
    fn manifest(&self) -> &RuntimeManifest;

    /// Best-effort, non-invasive presence check (config dir / known
    /// executable on PATH) — never a deep filesystem scan.
    fn detect(&self) -> bool;

    /// What would happen if the user tried to install `skill` here, purely
    /// from declared manifests — no filesystem access.
    fn can_install(&self, skill: &SkillManifest) -> InstallCapability {
        let status = skill
            .compatibility
            .get(&self.manifest().id)
            .map(String::as_str)
            .unwrap_or("unknown");
        match status {
            "unsupported" => InstallCapability::Unsupported,
            "unknown" => InstallCapability::Unknown,
            "native" | "supported" | "adapted" => {
                if self.automated() {
                    InstallCapability::Ready
                } else {
                    InstallCapability::Manual
                }
            }
            _ => InstallCapability::Unknown,
        }
    }

    /// Whether this adapter can actually perform `install`/`uninstall`
    /// itself, as opposed to only reporting status.
    fn automated(&self) -> bool;

    /// Where a skill would land on disk, without installing anything.
    /// The engine uses this to detect a pre-existing, non-SkillzForest
    /// install before ever calling `install` — see `installer::engine`.
    fn target_dir(&self, skill_id: &str) -> Result<std::path::PathBuf, AdapterError>;

    fn install(&self, skill: &SkillManifest, source_dir: &Path) -> Result<(), AdapterError>;

    /// Trusts the caller: `installer::engine` only calls this after
    /// confirming (via the registry) that this path is actually a
    /// SkillzForest-managed install.
    fn uninstall(&self, skill_id: &str) -> Result<(), AdapterError>;

    /// Default update = clean reinstall. Good enough for the MVP; a runtime
    /// that needs smarter merging can override this.
    fn update(&self, skill: &SkillManifest, source_dir: &Path) -> Result<(), AdapterError> {
        self.uninstall(&skill.id)?;
        self.install(skill, source_dir)
    }

    /// Reads the version actually on disk (source of truth), not the
    /// registry, so drift is always visible.
    fn get_installed_version(&self, skill_id: &str) -> Option<String>;
}
