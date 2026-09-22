use crate::models::{CatalogPack, CatalogSkill};
use crate::state::AppState;
use tauri::State;

#[tauri::command]
pub fn list_skills(state: State<AppState>) -> Result<Vec<CatalogSkill>, String> {
    state.source.list_skills().map_err(|e| e.to_string())
}

#[tauri::command]
pub fn list_packs(state: State<AppState>) -> Result<Vec<CatalogPack>, String> {
    state.source.list_packs().map_err(|e| e.to_string())
}

#[tauri::command]
pub fn get_skill(state: State<AppState>, id: String) -> Result<CatalogSkill, String> {
    state.source.get_skill(&id).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn get_pack(state: State<AppState>, id: String) -> Result<CatalogPack, String> {
    state.source.get_pack(&id).map_err(|e| e.to_string())
}
