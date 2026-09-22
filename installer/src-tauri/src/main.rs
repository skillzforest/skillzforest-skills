// Prevents an extra console window on Windows in release builds.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod download;
mod filesystem;
mod installer;
mod models;
mod runtimes;
mod security;
mod skill_source;
mod state;

use skill_source::LocalSkillSource;
use state::AppState;
use tauri::Emitter;
use tauri_plugin_deep_link::DeepLinkExt;

fn main() {
    // MVP wiring: LocalSkillSource reads this repo's own skills/packs/runtimes
    // directly, since the app is being developed and run from a checkout of
    // skillzforest-skills. A packaged, standalone build for end users would construct
    // a `skill_source::RemoteSkillSource` here instead — see its module docs.
    let source = LocalSkillSource::discover()
        .expect("SkillzForest Installer (dev mode) must be run from within the skillzforest-skills repo checkout");
    let app_state = AppState::new(Box::new(source));

    tauri::Builder::default()
        .plugin(tauri_plugin_deep_link::init())
        .manage(app_state)
        .setup(|app| {
            // skillzforest://install/<skill-id> and
            // skillzforest://install-pack/<pack-id> arrive here (both a
            // cold start via the OS and a link opened while already
            // running). Forwarded to the frontend as a plain event so all
            // the navigation logic lives in one place (React Router), not
            // duplicated between Rust and TS.
            let handle = app.handle().clone();
            app.deep_link().on_open_url(move |event| {
                for url in event.urls() {
                    let _ = handle.emit("skillzforest://deep-link", url.to_string());
                }
            });
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::catalog::list_skills,
            commands::catalog::list_packs,
            commands::catalog::get_skill,
            commands::catalog::get_pack,
            commands::runtimes::detect_runtimes,
            commands::runtimes::get_skill_capabilities,
            commands::install::check_conflict,
            commands::install::install_skill,
            commands::install::update_skill,
            commands::install::uninstall_skill,
            commands::install::uninstall_everywhere,
            commands::install::install_pack,
            commands::registry::get_registry,
            commands::updates::check_updates,
        ])
        .run(tauri::generate_context!())
        .expect("error while running the SkillzForest Installer");
}
