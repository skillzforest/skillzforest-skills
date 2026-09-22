//! Covers every `installStrategy` this app doesn't automate yet: `upload`
//! (e.g. Claude.ai), `manual-bundle` (e.g. Mistral, Perplexity), `plugin`
//! (e.g. ChatGPT), and bare `manual` (unconfirmed runtimes). It never
//! pretends to install anything — `detect()` still works so the Welcome
//! screen can show what's present, but the UI shows "Manual installation"
//! or "Coming soon" for these, matching the runtime's declared status.
use super::adapter::{AdapterError, RuntimeAdapter};
use crate::filesystem::executable_on_path;
use crate::models::{RuntimeManifest, SkillManifest};
use std::path::PathBuf;

pub struct ManualAdapter {
    manifest: RuntimeManifest,
}

impl ManualAdapter {
    pub fn new(manifest: RuntimeManifest) -> Self {
        Self { manifest }
    }
}

impl RuntimeAdapter for ManualAdapter {
    fn manifest(&self) -> &RuntimeManifest {
        &self.manifest
    }

    fn detect(&self) -> bool {
        self.manifest
            .detection
            .as_ref()
            .and_then(|d| d.executable.as_ref())
            .map(|name| executable_on_path(name))
            .unwrap_or(false)
    }

    fn automated(&self) -> bool {
        false
    }

    fn target_dir(&self, _skill_id: &str) -> Result<PathBuf, AdapterError> {
        Err(AdapterError::ManualOnly(self.manifest.install_strategy.clone()))
    }

    fn install(&self, _skill: &SkillManifest, _source_dir: &std::path::Path) -> Result<(), AdapterError> {
        Err(AdapterError::ManualOnly(self.manifest.install_strategy.clone()))
    }

    fn uninstall(&self, _skill_id: &str) -> Result<(), AdapterError> {
        Err(AdapterError::ManualOnly(self.manifest.install_strategy.clone()))
    }

    fn get_installed_version(&self, _skill_id: &str) -> Option<String> {
        None
    }
}
