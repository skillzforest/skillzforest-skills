use crate::models::RuntimeManifest;
use crate::runtimes::build_adapter;
use crate::state::AppState;
use serde::Serialize;
use tauri::State;

#[derive(Debug, Clone, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct UpdateStatus {
    pub skill_id: String,
    pub runtime_id: String,
    pub installed_version: String,
    pub available_version: String,
    pub update_available: bool,
}

fn find_runtime_manifest(state: &AppState, runtime_id: &str) -> Result<RuntimeManifest, String> {
    state
        .source
        .list_runtimes()
        .map_err(|e| e.to_string())?
        .into_iter()
        .find(|r| r.id == runtime_id)
        .ok_or_else(|| format!("unknown runtime '{runtime_id}'"))
}

/// Compares each registered install's on-disk version against the catalog's
/// current `skill.json` version. No delta logic — an update just means
/// "reinstall cleanly", so all this needs to know is whether the versions
/// differ.
#[tauri::command]
pub fn check_updates(state: State<AppState>) -> Result<Vec<UpdateStatus>, String> {
    let registry = state.registry.lock().expect("registry mutex poisoned").clone();
    let mut out = Vec::new();

    for (skill_id, by_runtime) in &registry.skills {
        let Ok(catalog_skill) = state.source.get_skill(skill_id) else {
            continue; // skill removed from the catalog since it was installed
        };
        for runtime_id in by_runtime.keys() {
            let Ok(runtime) = find_runtime_manifest(&state, runtime_id) else {
                continue;
            };
            let adapter = build_adapter(runtime);
            let installed_version = adapter
                .get_installed_version(skill_id)
                .unwrap_or_else(|| by_runtime[runtime_id].version.clone());
            let available_version = catalog_skill.manifest.version.clone();
            out.push(UpdateStatus {
                skill_id: skill_id.clone(),
                runtime_id: runtime_id.clone(),
                update_available: installed_version != available_version,
                installed_version,
                available_version,
            });
        }
    }

    Ok(out)
}
