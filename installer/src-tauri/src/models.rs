//! Every struct here crosses the Tauri IPC boundary to TypeScript, so they
//! all serialize as camelCase — the one consistent JSON contract the
//! frontend types in `installer/src/types/` mirror field-for-field.
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Mirrors schemas/skill.schema.json. Extra fields in skill.json are ignored.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SkillManifest {
    pub id: String,
    pub name: String,
    pub publisher: String,
    pub version: String,
    pub category: String,
    pub description: String,
    #[serde(default)]
    pub compatibility: HashMap<String, String>,
    /// Present on some skills (skill.json doesn't require it); read only for
    /// the Permissions screen. Never used to decide whether to run anything —
    /// the installer never executes a skill's scripts.
    #[serde(default)]
    pub permissions: Option<SkillPermissions>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SkillPermissions {
    #[serde(default)]
    pub read_project_files: bool,
    #[serde(default)]
    pub edit_project_files: bool,
    #[serde(default)]
    pub network_access: bool,
    #[serde(default)]
    pub shell_commands: bool,
}

/// A skill as the catalog exposes it to the frontend: manifest plus where its
/// source folder lives on disk (never shown raw in the main UI).
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CatalogSkill {
    pub manifest: SkillManifest,
    pub family: String,
    pub source_dir: String,
}

/// Mirrors schemas/pack.schema.json.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PackManifest {
    pub id: String,
    pub name: String,
    pub publisher: String,
    pub version: String,
    pub description: String,
    #[serde(default)]
    pub skills: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CatalogPack {
    pub manifest: PackManifest,
}

/// Mirrors schemas/runtime.schema.json.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeManifest {
    pub id: String,
    pub name: String,
    #[serde(rename = "type")]
    pub kind: String,
    pub supports_agent_skills: Option<bool>,
    pub install_strategy: String,
    pub status: String,
    #[serde(default)]
    pub paths: Option<RuntimePaths>,
    #[serde(default)]
    pub detection: Option<RuntimeDetection>,
    #[serde(default)]
    pub notes: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimePaths {
    pub user: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeDetection {
    pub config_dir: Option<String>,
    pub executable: Option<String>,
}

/// Result of probing one runtime on this machine.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeDetectionResult {
    pub runtime: RuntimeManifest,
    pub detected: bool,
    /// Whether the installer can actually automate install/uninstall for
    /// this runtime, independent of whether it was detected on this machine.
    pub automatable: bool,
}

/// What the installer will actually do for one (skill, runtime) pair before
/// the user clicks Install — computed from skill.json compatibility +
/// runtime.json installStrategy, never guessed.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub enum InstallCapability {
    /// Verified/known-good and automatable now.
    Ready,
    /// Declared unsupported for this runtime — never offered.
    Unsupported,
    /// Compatibility or install mechanism isn't confirmed yet.
    Unknown,
    /// A real mechanism exists but isn't automated (e.g. copy-paste bundle).
    Manual,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct InstalledSkillEntry {
    pub version: String,
    /// Unix epoch milliseconds — the frontend formats it with `new Date(ms)`.
    pub install_date: u64,
    pub source: String,
}

/// ~/.skillzforest/registry.json — the local record of what SkillzForest
/// itself installed, so uninstall/update never touches anything else.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Registry {
    #[serde(default)]
    pub skills: HashMap<String, HashMap<String, InstalledSkillEntry>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct InstallOutcome {
    pub skill_id: String,
    pub runtime_id: String,
    pub installed: bool,
    pub version: String,
    pub reason: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PackInstallOutcome {
    pub pack_id: String,
    pub runtime_id: String,
    pub installed: Vec<String>,
    pub skipped: Vec<PackSkipReason>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PackSkipReason {
    pub skill_id: String,
    pub reason: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct UninstallOutcome {
    pub runtime_id: String,
    pub success: bool,
    pub error: Option<String>,
}

/// What to do when a same-named skill exists but wasn't installed by
/// SkillzForest — the app must always ask, never overwrite silently.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub enum ConflictResolution {
    KeepExisting,
    Replace,
    Cancel,
}
