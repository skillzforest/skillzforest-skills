use crate::installer::registry;
use crate::models::Registry;
use crate::skill_source::SkillSource;
use std::sync::Mutex;

/// Shared app state managed by Tauri. `source` is swappable in principle
/// (Local today, Remote once it exists) but never re-decided per call — one
/// process, one source, matching how the app is actually built and shipped.
pub struct AppState {
    pub source: Box<dyn SkillSource>,
    pub registry: Mutex<Registry>,
}

impl AppState {
    pub fn new(source: Box<dyn SkillSource>) -> Self {
        let registry = registry::load().unwrap_or_default();
        Self {
            source,
            registry: Mutex::new(registry),
        }
    }

    pub fn persist_registry(&self) -> Result<(), String> {
        let reg = self.registry.lock().expect("registry mutex poisoned");
        registry::save(&reg).map_err(|e| e.to_string())
    }
}
