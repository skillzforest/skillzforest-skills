use crate::models::Registry;
use crate::state::AppState;
use tauri::State;

#[tauri::command]
pub fn get_registry(state: State<AppState>) -> Result<Registry, String> {
    Ok(state.registry.lock().expect("registry mutex poisoned").clone())
}
