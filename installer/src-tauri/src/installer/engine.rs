//! The one place that decides *whether* to touch disk. Adapters know how to
//! install/uninstall for one runtime; this module decides, for a given
//! (skill, runtime) pair, whether that's safe (no un-registered conflict),
//! desired (compatibility says so), and then records the outcome in the
//! registry. Nothing here branches on a runtime id — it only calls through
//! `RuntimeAdapter`.
use super::registry;
use crate::models::{
    ConflictResolution, InstallCapability, InstallOutcome, PackInstallOutcome, PackManifest,
    PackSkipReason, Registry, SkillManifest,
};
use crate::runtimes::{AdapterError, RuntimeAdapter};
use std::path::Path;

#[derive(Debug, thiserror::Error)]
pub enum EngineError {
    #[error(transparent)]
    Adapter(#[from] AdapterError),
    #[error(transparent)]
    Fs(#[from] crate::filesystem::FsError),
    #[error("'{skill_id}' is already installed for {runtime_id}, but not by SkillzForest — ask the user to Keep/Replace/Cancel")]
    UnresolvedConflict { skill_id: String, runtime_id: String },
    #[error("installation cancelled")]
    Cancelled,
    #[error("compatibility is '{0:?}' for this runtime — not installable automatically")]
    NotInstallable(InstallCapability),
}

/// Existing-but-unregistered install found on disk. The frontend renders
/// this as the "already installed" dialog and calls back in with a
/// `ConflictResolution` once the user picks one.
#[derive(Debug, Clone, serde::Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ConflictInfo {
    pub skill_id: String,
    pub runtime_id: String,
}

/// Checks for a pre-existing, non-SkillzForest install before any write.
/// `None` means it's safe to proceed straight to `install_skill`.
pub fn detect_conflict(
    adapter: &dyn RuntimeAdapter,
    registry: &Registry,
    skill_id: &str,
) -> Result<Option<ConflictInfo>, EngineError> {
    let runtime_id = adapter.manifest().id.clone();
    if registry::is_ours(registry, skill_id, &runtime_id) {
        return Ok(None); // ours already — a plain reinstall/update, not a conflict
    }
    let target = adapter.target_dir(skill_id)?;
    if target.exists() {
        Ok(Some(ConflictInfo {
            skill_id: skill_id.to_string(),
            runtime_id,
        }))
    } else {
        Ok(None)
    }
}

/// Installs one skill into one runtime. `resolution` is required whenever
/// `detect_conflict` returned `Some(..)` for this pair; pass `None` when
/// there's no conflict (the common case).
pub fn install_skill(
    adapter: &dyn RuntimeAdapter,
    registry: &mut Registry,
    skill: &SkillManifest,
    source_dir: &Path,
    resolution: Option<ConflictResolution>,
    source_label: &str,
) -> Result<InstallOutcome, EngineError> {
    let capability = adapter.can_install(skill);
    if capability != InstallCapability::Ready {
        return Err(EngineError::NotInstallable(capability));
    }

    if let Some(conflict) = detect_conflict(adapter, registry, &skill.id)? {
        match resolution {
            Some(ConflictResolution::Replace) => {}
            Some(ConflictResolution::KeepExisting) | None => {
                return Err(EngineError::UnresolvedConflict {
                    skill_id: conflict.skill_id,
                    runtime_id: conflict.runtime_id,
                });
            }
            Some(ConflictResolution::Cancel) => return Err(EngineError::Cancelled),
        }
    }

    adapter.install(skill, source_dir)?;
    registry::record_install(
        registry,
        &skill.id,
        &adapter.manifest().id,
        &skill.version,
        source_label,
    );

    Ok(InstallOutcome {
        skill_id: skill.id.clone(),
        runtime_id: adapter.manifest().id.clone(),
        installed: true,
        version: skill.version.clone(),
        reason: None,
    })
}

/// Uninstalls one skill from one runtime — refuses unless the registry
/// confirms SkillzForest is the one that put it there.
pub fn uninstall_skill(
    adapter: &dyn RuntimeAdapter,
    registry: &mut Registry,
    skill_id: &str,
) -> Result<(), EngineError> {
    let runtime_id = adapter.manifest().id.clone();
    if !registry::is_ours(registry, skill_id, &runtime_id) {
        return Err(AdapterError::NotOurs(skill_id.to_string()).into());
    }
    adapter.uninstall(skill_id)?;
    registry::remove_entry(registry, skill_id, &runtime_id);
    Ok(())
}

/// Uninstalls one skill from every runtime the registry says it's in.
pub fn uninstall_everywhere(
    adapters: &[Box<dyn RuntimeAdapter>],
    registry: &mut Registry,
    skill_id: &str,
) -> Vec<(String, Result<(), EngineError>)> {
    let runtime_ids: Vec<String> = registry
        .skills
        .get(skill_id)
        .map(|by_runtime| by_runtime.keys().cloned().collect())
        .unwrap_or_default();

    runtime_ids
        .into_iter()
        .map(|runtime_id| {
            let result = adapters
                .iter()
                .find(|a| a.manifest().id == runtime_id)
                .ok_or_else(|| AdapterError::NotOurs(runtime_id.clone()).into())
                .and_then(|adapter| uninstall_skill(adapter.as_ref(), registry, skill_id));
            (runtime_id, result)
        })
        .collect()
}

/// Installs every pack skill that's `Ready` for this runtime; every other
/// skill is reported as skipped with the reason, never silently dropped.
pub fn install_pack(
    adapter: &dyn RuntimeAdapter,
    registry: &mut Registry,
    pack: &PackManifest,
    skills: &[(SkillManifest, std::path::PathBuf)],
    source_label: &str,
) -> PackInstallOutcome {
    let mut installed = Vec::new();
    let mut skipped = Vec::new();

    for skill_id in &pack.skills {
        let Some((skill, source_dir)) = skills.iter().find(|(s, _)| &s.id == skill_id) else {
            skipped.push(PackSkipReason {
                skill_id: skill_id.clone(),
                reason: "skill not found in catalog".to_string(),
            });
            continue;
        };

        let capability = adapter.can_install(skill);
        if capability != InstallCapability::Ready {
            skipped.push(PackSkipReason {
                skill_id: skill_id.clone(),
                reason: describe_capability(capability, skill, &adapter.manifest().id, &adapter.manifest().name),
            });
            continue;
        }

        // Pack installs never overwrite an unregistered conflict silently —
        // they skip it and let the user resolve it individually afterwards.
        match detect_conflict(adapter, registry, &skill.id) {
            Ok(Some(_)) => {
                skipped.push(PackSkipReason {
                    skill_id: skill_id.clone(),
                    reason: "already installed outside SkillzForest — resolve from My Skills"
                        .to_string(),
                });
                continue;
            }
            Ok(None) => {}
            Err(e) => {
                skipped.push(PackSkipReason {
                    skill_id: skill_id.clone(),
                    reason: e.to_string(),
                });
                continue;
            }
        }

        match install_skill(adapter, registry, skill, source_dir, None, source_label) {
            Ok(_) => installed.push(skill_id.clone()),
            Err(e) => skipped.push(PackSkipReason {
                skill_id: skill_id.clone(),
                reason: e.to_string(),
            }),
        }
    }

    PackInstallOutcome {
        pack_id: pack.id.clone(),
        runtime_id: adapter.manifest().id.clone(),
        installed,
        skipped,
    }
}

fn describe_capability(
    capability: InstallCapability,
    skill: &SkillManifest,
    current_runtime_id: &str,
    runtime_name: &str,
) -> String {
    match capability {
        InstallCapability::Unsupported => {
            // Best-effort: name the runtime this skill actually targets, so
            // the message reads like "ChatGPT-only distribution" rather than
            // just "unsupported".
            let other = skill
                .compatibility
                .iter()
                .find(|(id, status)| {
                    id.as_str() != current_runtime_id
                        && matches!(status.as_str(), "native" | "supported" | "adapted")
                })
                .map(|(id, _)| id.as_str());
            match other {
                Some(id) => format!("{id}-only distribution"),
                None => format!("not compatible with {runtime_name}"),
            }
        }
        InstallCapability::Unknown => format!("compatibility with {runtime_name} isn't confirmed yet"),
        InstallCapability::Manual => format!("{runtime_name} requires manual installation"),
        InstallCapability::Ready => unreachable!("Ready is filtered out before this is called"),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::models::{RuntimeDetection, RuntimeManifest, RuntimePaths};
    use crate::runtimes::filesystem_adapter::FilesystemAdapter;
    use std::collections::HashMap;
    use std::fs;
    use std::path::PathBuf;

    fn tmp_dir(name: &str) -> PathBuf {
        let dir = std::env::temp_dir().join(format!(
            "skillzforest-engine-test-{name}-{}",
            std::process::id()
        ));
        let _ = fs::remove_dir_all(&dir);
        fs::create_dir_all(&dir).unwrap();
        dir
    }

    /// A filesystem-strategy adapter pointed at a temp dir instead of a real
    /// runtime's home-relative path, so tests never touch the real ~/.claude
    /// or ~/.agents.
    fn fake_filesystem_adapter(id: &str, base: &Path) -> FilesystemAdapter {
        FilesystemAdapter::new(RuntimeManifest {
            id: id.to_string(),
            name: id.to_string(),
            kind: "filesystem".to_string(),
            supports_agent_skills: Some(true),
            install_strategy: "filesystem".to_string(),
            status: "verified".to_string(),
            paths: Some(RuntimePaths {
                user: Some(base.display().to_string()),
            }),
            detection: Some(RuntimeDetection {
                config_dir: None,
                executable: None,
            }),
            notes: None,
        })
    }

    fn fake_skill(id: &str, compatibility: &[(&str, &str)]) -> SkillManifest {
        SkillManifest {
            id: id.to_string(),
            name: id.to_string(),
            publisher: "Test".to_string(),
            version: "1.0.0".to_string(),
            category: "test".to_string(),
            description: "A test skill".to_string(),
            compatibility: compatibility
                .iter()
                .map(|(k, v)| (k.to_string(), v.to_string()))
                .collect::<HashMap<_, _>>(),
            permissions: None,
        }
    }

    fn write_skill_source(dir: &Path) {
        fs::create_dir_all(dir).unwrap();
        fs::write(dir.join("SKILL.md"), "# Test skill").unwrap();
    }

    #[test]
    fn installs_when_ready_and_no_conflict() {
        let base = tmp_dir("install-ready");
        let source = tmp_dir("install-ready-src");
        write_skill_source(&source);

        let adapter = fake_filesystem_adapter("fake-rt", &base);
        let skill = fake_skill("dev-seo", &[("fake-rt", "native")]);
        let mut registry = Registry::default();

        let outcome =
            install_skill(&adapter, &mut registry, &skill, &source, None, "test").unwrap();

        assert!(outcome.installed);
        assert!(base.join("dev-seo/SKILL.md").is_file());
        assert!(registry::is_ours(&registry, "dev-seo", "fake-rt"));

        let _ = fs::remove_dir_all(&base);
        let _ = fs::remove_dir_all(&source);
    }

    #[test]
    fn refuses_to_install_when_not_compatible() {
        let base = tmp_dir("install-unready");
        let source = tmp_dir("install-unready-src");
        write_skill_source(&source);

        let adapter = fake_filesystem_adapter("fake-rt", &base);
        let skill = fake_skill("dev-seo", &[("fake-rt", "unsupported")]);
        let mut registry = Registry::default();

        let err = install_skill(&adapter, &mut registry, &skill, &source, None, "test")
            .unwrap_err();
        assert!(matches!(err, EngineError::NotInstallable(InstallCapability::Unsupported)));
        assert!(!base.join("dev-seo").exists());

        let _ = fs::remove_dir_all(&base);
        let _ = fs::remove_dir_all(&source);
    }

    #[test]
    fn detects_conflict_with_unregistered_existing_install() {
        let base = tmp_dir("conflict-base");
        let source = tmp_dir("conflict-src");
        write_skill_source(&source);
        // Simulate a pre-existing install SkillzForest didn't create.
        fs::create_dir_all(base.join("dev-seo")).unwrap();
        fs::write(base.join("dev-seo/SKILL.md"), "hand-written").unwrap();

        let adapter = fake_filesystem_adapter("fake-rt", &base);
        let skill = fake_skill("dev-seo", &[("fake-rt", "native")]);
        let registry = Registry::default();

        let conflict = detect_conflict(&adapter, &registry, "dev-seo").unwrap();
        assert!(conflict.is_some());

        let mut registry = registry;
        let err = install_skill(&adapter, &mut registry, &skill, &source, None, "test")
            .unwrap_err();
        assert!(matches!(err, EngineError::UnresolvedConflict { .. }));
        assert_eq!(
            fs::read_to_string(base.join("dev-seo/SKILL.md")).unwrap(),
            "hand-written"
        );

        // Explicit Replace clears it.
        install_skill(
            &adapter,
            &mut registry,
            &skill,
            &source,
            Some(ConflictResolution::Replace),
            "test",
        )
        .unwrap();
        assert_eq!(
            fs::read_to_string(base.join("dev-seo/SKILL.md")).unwrap(),
            "# Test skill"
        );

        let _ = fs::remove_dir_all(&base);
        let _ = fs::remove_dir_all(&source);
    }

    #[test]
    fn uninstall_refuses_when_not_registered() {
        let base = tmp_dir("uninstall-not-ours");
        fs::create_dir_all(base.join("dev-seo")).unwrap();
        let adapter = fake_filesystem_adapter("fake-rt", &base);
        let mut registry = Registry::default();

        let err = uninstall_skill(&adapter, &mut registry, "dev-seo").unwrap_err();
        assert!(matches!(err, EngineError::Adapter(AdapterError::NotOurs(_))));
        assert!(base.join("dev-seo").exists());

        let _ = fs::remove_dir_all(&base);
    }

    #[test]
    fn pack_install_skips_incompatible_skill_with_reason() {
        let base = tmp_dir("pack-base");
        let source_a = tmp_dir("pack-src-a");
        let source_b = tmp_dir("pack-src-b");
        write_skill_source(&source_a);
        write_skill_source(&source_b);

        let adapter = fake_filesystem_adapter("claude-code", &base);
        let compatible_skill = fake_skill("presales-quote", &[("claude-code", "native")]);
        let incompatible_skill = fake_skill(
            "chatgpt-only-skill",
            &[("chatgpt", "native"), ("claude-code", "unsupported")],
        );
        let pack = PackManifest {
            id: "presales".to_string(),
            name: "Pre-Sales Pack".to_string(),
            publisher: "Test".to_string(),
            version: "0.1.0".to_string(),
            description: "test".to_string(),
            skills: vec!["presales-quote".to_string(), "chatgpt-only-skill".to_string()],
        };
        let mut registry = Registry::default();

        let outcome = install_pack(
            &adapter,
            &mut registry,
            &pack,
            &[
                (compatible_skill, source_a.clone()),
                (incompatible_skill, source_b.clone()),
            ],
            "test",
        );

        assert_eq!(outcome.installed, vec!["presales-quote".to_string()]);
        assert_eq!(outcome.skipped.len(), 1);
        assert_eq!(outcome.skipped[0].skill_id, "chatgpt-only-skill");
        assert_eq!(outcome.skipped[0].reason, "chatgpt-only distribution");

        let _ = fs::remove_dir_all(&base);
        let _ = fs::remove_dir_all(&source_a);
        let _ = fs::remove_dir_all(&source_b);
    }
}
