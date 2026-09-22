//! Generic adapter for any runtime whose `runtime.json` declares
//! `installStrategy: "filesystem"` (Claude Code, Codex, Gemini today —
//! adding another one is just another runtime.json, no new Rust). The
//! target path always comes from `runtime.json`'s `paths.user`, never from
//! a constant in this file.
use super::adapter::{AdapterError, RuntimeAdapter};
use crate::filesystem::{self, executable_on_path};
use crate::models::{RuntimeManifest, SkillManifest};
use crate::security;
use std::path::PathBuf;

pub struct FilesystemAdapter {
    manifest: RuntimeManifest,
}

impl FilesystemAdapter {
    pub fn new(manifest: RuntimeManifest) -> Self {
        Self { manifest }
    }

    fn base_dir(&self) -> Result<PathBuf, AdapterError> {
        let raw = self
            .manifest
            .paths
            .as_ref()
            .and_then(|p| p.user.as_ref())
            .ok_or_else(|| AdapterError::ManualOnly(self.manifest.install_strategy.clone()))?;
        Ok(filesystem::expand_tilde(raw)?)
    }
}

impl RuntimeAdapter for FilesystemAdapter {
    fn manifest(&self) -> &RuntimeManifest {
        &self.manifest
    }

    fn detect(&self) -> bool {
        let detection = match &self.manifest.detection {
            Some(d) => d,
            None => return false,
        };
        let config_dir_present = detection
            .config_dir
            .as_ref()
            .and_then(|raw| filesystem::expand_tilde(raw).ok())
            .map(|p| p.is_dir())
            .unwrap_or(false);
        let executable_present = detection
            .executable
            .as_ref()
            .map(|name| executable_on_path(name))
            .unwrap_or(false);
        config_dir_present || executable_present
    }

    fn automated(&self) -> bool {
        self.manifest.install_strategy == "filesystem"
    }

    fn target_dir(&self, skill_id: &str) -> Result<PathBuf, AdapterError> {
        security::validate_id(skill_id)?;
        let base = self.base_dir()?;
        Ok(base.join(skill_id))
    }

    fn install(&self, skill: &SkillManifest, source_dir: &std::path::Path) -> Result<(), AdapterError> {
        security::validate_skill_manifest(skill)?;
        security::require_skill_md(source_dir)?;

        let target = self.target_dir(&skill.id)?;
        filesystem::remove_dir(&target)?; // caller has already confirmed overwrite is OK
        filesystem::copy_dir_safely(source_dir, &target)?;
        security::require_skill_md(&target)?; // verify the copy actually landed
        Ok(())
    }

    fn uninstall(&self, skill_id: &str) -> Result<(), AdapterError> {
        let target = self.target_dir(skill_id)?;
        filesystem::remove_dir(&target)?;
        Ok(())
    }

    fn get_installed_version(&self, skill_id: &str) -> Option<String> {
        let target = self.target_dir(skill_id).ok()?;
        let manifest_path = target.join("skill.json");
        let raw = std::fs::read_to_string(manifest_path).ok()?;
        let value: serde_json::Value = serde_json::from_str(&raw).ok()?;
        value
            .get("version")
            .and_then(|v| v.as_str())
            .map(String::from)
    }
}
