use crate::installer::{engine, ConflictInfo};
use crate::models::{ConflictResolution, InstallOutcome, PackInstallOutcome, RuntimeManifest, UninstallOutcome};
use crate::runtimes::build_adapter;
use crate::state::AppState;
use tauri::State;

/// Distributions built from this repo's own checkout, via `LocalSkillSource`
/// — recorded as the registry's `source` field so it's visible (in Advanced)
/// where an install actually came from.
const LOCAL_SOURCE_LABEL: &str = "local-repo";

fn find_runtime_manifest(state: &AppState, runtime_id: &str) -> Result<RuntimeManifest, String> {
    state
        .source
        .list_runtimes()
        .map_err(|e| e.to_string())?
        .into_iter()
        .find(|r| r.id == runtime_id)
        .ok_or_else(|| format!("unknown runtime '{runtime_id}'"))
}

#[tauri::command]
pub fn check_conflict(
    state: State<AppState>,
    skill_id: String,
    runtime_id: String,
) -> Result<Option<ConflictInfo>, String> {
    let runtime = find_runtime_manifest(&state, &runtime_id)?;
    let adapter = build_adapter(runtime);
    let registry = state.registry.lock().expect("registry mutex poisoned");
    engine::detect_conflict(adapter.as_ref(), &registry, &skill_id).map_err(|e| e.to_string())
}

/// Installs one skill into every listed runtime. Each runtime is
/// independent: a conflict or failure on one never blocks the others —
/// callers get one `InstallOutcome` per runtime and render a checklist.
#[tauri::command]
pub fn install_skill(
    state: State<AppState>,
    skill_id: String,
    runtime_ids: Vec<String>,
    resolution: Option<ConflictResolution>,
) -> Result<Vec<InstallOutcome>, String> {
    let skill = state
        .source
        .get_skill(&skill_id)
        .map_err(|e| e.to_string())?
        .manifest;

    let mut results = Vec::new();
    for runtime_id in runtime_ids {
        let attempt = (|| -> Result<InstallOutcome, String> {
            let runtime = find_runtime_manifest(&state, &runtime_id)?;
            let adapter = build_adapter(runtime);
            let source_dir = state
                .source
                .resolve_distribution(&skill_id, &runtime_id)
                .map_err(|e| e.to_string())?;
            let mut registry = state.registry.lock().expect("registry mutex poisoned");
            engine::install_skill(
                adapter.as_ref(),
                &mut registry,
                &skill,
                &source_dir,
                resolution,
                LOCAL_SOURCE_LABEL,
            )
            .map_err(|e| e.to_string())
        })();

        results.push(match attempt {
            Ok(outcome) => outcome,
            Err(reason) => InstallOutcome {
                skill_id: skill_id.clone(),
                runtime_id,
                installed: false,
                version: skill.version.clone(),
                reason: Some(reason),
            },
        });
    }

    state.persist_registry()?;
    Ok(results)
}

#[tauri::command]
pub fn update_skill(
    state: State<AppState>,
    skill_id: String,
    runtime_id: String,
) -> Result<InstallOutcome, String> {
    let skill = state
        .source
        .get_skill(&skill_id)
        .map_err(|e| e.to_string())?
        .manifest;
    let runtime = find_runtime_manifest(&state, &runtime_id)?;
    let adapter = build_adapter(runtime);
    let source_dir = state
        .source
        .resolve_distribution(&skill_id, &runtime_id)
        .map_err(|e| e.to_string())?;

    let mut registry = state.registry.lock().expect("registry mutex poisoned");
    let result = adapter
        .update(&skill, &source_dir)
        .map_err(|e| e.to_string());
    if result.is_ok() {
        crate::installer::registry::record_install(
            &mut registry,
            &skill_id,
            &runtime_id,
            &skill.version,
            LOCAL_SOURCE_LABEL,
        );
    }
    drop(registry);
    state.persist_registry()?;

    result.map(|_| InstallOutcome {
        skill_id,
        runtime_id,
        installed: true,
        version: skill.version.clone(),
        reason: None,
    })
}

#[tauri::command]
pub fn uninstall_skill(
    state: State<AppState>,
    skill_id: String,
    runtime_id: String,
) -> Result<(), String> {
    let runtime = find_runtime_manifest(&state, &runtime_id)?;
    let adapter = build_adapter(runtime);
    let mut registry = state.registry.lock().expect("registry mutex poisoned");
    engine::uninstall_skill(adapter.as_ref(), &mut registry, &skill_id).map_err(|e| e.to_string())?;
    drop(registry);
    state.persist_registry()
}

#[tauri::command]
pub fn uninstall_everywhere(
    state: State<AppState>,
    skill_id: String,
) -> Result<Vec<UninstallOutcome>, String> {
    let manifests = state.source.list_runtimes().map_err(|e| e.to_string())?;
    let adapters = crate::runtimes::build_all_adapters(manifests);
    let mut registry = state.registry.lock().expect("registry mutex poisoned");
    let raw = engine::uninstall_everywhere(&adapters, &mut registry, &skill_id);
    drop(registry);
    state.persist_registry()?;

    Ok(raw
        .into_iter()
        .map(|(runtime_id, result)| match result {
            Ok(()) => UninstallOutcome {
                runtime_id,
                success: true,
                error: None,
            },
            Err(e) => UninstallOutcome {
                runtime_id,
                success: false,
                error: Some(e.to_string()),
            },
        })
        .collect())
}

#[tauri::command]
pub fn install_pack(
    state: State<AppState>,
    pack_id: String,
    runtime_id: String,
) -> Result<PackInstallOutcome, String> {
    let pack = state.source.get_pack(&pack_id).map_err(|e| e.to_string())?.manifest;
    let runtime = find_runtime_manifest(&state, &runtime_id)?;
    let adapter = build_adapter(runtime);

    let mut skills = Vec::new();
    for skill_id in &pack.skills {
        let skill = state.source.get_skill(skill_id).map_err(|e| e.to_string())?.manifest;
        let source_dir = state
            .source
            .resolve_distribution(skill_id, &runtime_id)
            .map_err(|e| e.to_string())?;
        skills.push((skill, source_dir));
    }

    let mut registry = state.registry.lock().expect("registry mutex poisoned");
    let outcome = engine::install_pack(adapter.as_ref(), &mut registry, &pack, &skills, LOCAL_SOURCE_LABEL);
    drop(registry);
    state.persist_registry()?;
    Ok(outcome)
}
