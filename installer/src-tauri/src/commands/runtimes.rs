use crate::models::{InstallCapability, RuntimeDetectionResult};
use crate::runtimes::build_all_adapters;
use crate::state::AppState;
use std::collections::HashMap;
use tauri::State;

/// Powers the Welcome/Settings "detected runtimes" screen — one pass over
/// every declared runtime, each probed via its own adapter's `detect()`.
#[tauri::command]
pub fn detect_runtimes(state: State<AppState>) -> Result<Vec<RuntimeDetectionResult>, String> {
    let manifests = state.source.list_runtimes().map_err(|e| e.to_string())?;
    let adapters = build_all_adapters(manifests);
    Ok(adapters
        .iter()
        .map(|a| RuntimeDetectionResult {
            runtime: a.manifest().clone(),
            detected: a.detect(),
            automatable: a.automated(),
        })
        .collect())
}

/// Per-runtime capability for one skill — what the Skill Details screen's
/// "Works with" / "Install for" checklist is built from.
#[tauri::command]
pub fn get_skill_capabilities(
    state: State<AppState>,
    skill_id: String,
) -> Result<HashMap<String, InstallCapability>, String> {
    let skill = state
        .source
        .get_skill(&skill_id)
        .map_err(|e| e.to_string())?
        .manifest;
    let manifests = state.source.list_runtimes().map_err(|e| e.to_string())?;
    let adapters = build_all_adapters(manifests);
    Ok(adapters
        .iter()
        .map(|a| (a.manifest().id.clone(), a.can_install(&skill)))
        .collect())
}
