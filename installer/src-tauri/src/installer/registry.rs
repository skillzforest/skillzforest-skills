//! The local record of what SkillzForest itself installed — the only
//! authority `installer::engine` trusts before it ever deletes anything.
use crate::filesystem::{self, FsError};
use crate::models::{InstalledSkillEntry, Registry};
use std::fs;

pub fn load() -> Result<Registry, FsError> {
    let path = filesystem::registry_path()?;
    if !path.is_file() {
        return Ok(Registry::default());
    }
    let raw = fs::read_to_string(&path).map_err(|e| FsError::Io {
        path: path.display().to_string(),
        source: e,
    })?;
    Ok(serde_json::from_str(&raw).unwrap_or_default())
}

pub fn save(registry: &Registry) -> Result<(), FsError> {
    let path = filesystem::registry_path()?;
    filesystem::ensure_dir(path.parent().expect("registry path always has a parent"))?;
    let raw = serde_json::to_string_pretty(registry).expect("Registry always serializes");
    fs::write(&path, raw).map_err(|e| FsError::Io {
        path: path.display().to_string(),
        source: e,
    })
}

pub fn is_ours(registry: &Registry, skill_id: &str, runtime_id: &str) -> bool {
    registry
        .skills
        .get(skill_id)
        .map(|by_runtime| by_runtime.contains_key(runtime_id))
        .unwrap_or(false)
}

pub fn record_install(
    registry: &mut Registry,
    skill_id: &str,
    runtime_id: &str,
    version: &str,
    source: &str,
) {
    let entry = InstalledSkillEntry {
        version: version.to_string(),
        install_date: now_epoch_millis(),
        source: source.to_string(),
    };
    registry
        .skills
        .entry(skill_id.to_string())
        .or_default()
        .insert(runtime_id.to_string(), entry);
}

pub fn remove_entry(registry: &mut Registry, skill_id: &str, runtime_id: &str) {
    if let Some(by_runtime) = registry.skills.get_mut(skill_id) {
        by_runtime.remove(runtime_id);
        if by_runtime.is_empty() {
            registry.skills.remove(skill_id);
        }
    }
}

fn now_epoch_millis() -> u64 {
    // Avoids pulling in `chrono` for one timestamp — the frontend can format
    // a plain epoch-millis number with `new Date(ms)`.
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_millis() as u64)
        .unwrap_or(0)
}
