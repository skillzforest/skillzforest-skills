use super::{SkillSource, SkillSourceError};
use crate::models::{CatalogPack, CatalogSkill, PackManifest, RuntimeManifest, SkillManifest};
use std::fs;
use std::path::{Path, PathBuf};

/// Reads `skills/`, `packs/`, `runtimes/` straight from this monorepo. This
/// is a dev/maintainer-mode source: it locates the repo by walking up from
/// this crate's own manifest directory, which only exists when the
/// installer is built from a checkout of this repository. A packaged,
/// standalone app for end users would ship with `RemoteSkillSource`
/// instead — see `remote.rs`.
pub struct LocalSkillSource {
    repo_root: PathBuf,
}

impl LocalSkillSource {
    pub fn discover() -> Result<Self, SkillSourceError> {
        // installer/src-tauri -> installer -> <repo root>
        let manifest_dir = Path::new(env!("CARGO_MANIFEST_DIR"));
        let repo_root = manifest_dir
            .parent()
            .and_then(|p| p.parent())
            .ok_or_else(|| SkillSourceError::NotFound("repository root".into()))?
            .to_path_buf();

        if !repo_root.join("skills").is_dir() {
            return Err(SkillSourceError::NotFound(format!(
                "skills/ not found under {} — LocalSkillSource must be built from within the skillzforest-skills repo checkout",
                repo_root.display()
            )));
        }
        Ok(Self { repo_root })
    }

    fn skills_root(&self) -> PathBuf {
        self.repo_root.join("skills")
    }
    fn packs_root(&self) -> PathBuf {
        self.repo_root.join("packs")
    }
    fn runtimes_root(&self) -> PathBuf {
        self.repo_root.join("runtimes")
    }

    fn read_json<T: serde::de::DeserializeOwned>(path: &Path) -> Result<T, SkillSourceError> {
        let raw = fs::read_to_string(path)?;
        serde_json::from_str(&raw).map_err(|e| SkillSourceError::InvalidManifest {
            path: path.display().to_string(),
            message: e.to_string(),
        })
    }
}

impl SkillSource for LocalSkillSource {
    fn list_skills(&self) -> Result<Vec<CatalogSkill>, SkillSourceError> {
        let mut out = Vec::new();
        let skills_root = self.skills_root();
        for family_entry in fs::read_dir(&skills_root)? {
            let family_entry = family_entry?;
            if !family_entry.file_type()?.is_dir() {
                continue;
            }
            let family = family_entry.file_name().to_string_lossy().to_string();
            if family == "lib" {
                continue;
            }
            for skill_entry in fs::read_dir(family_entry.path())? {
                let skill_entry = skill_entry?;
                if !skill_entry.file_type()?.is_dir() {
                    continue;
                }
                let skill_dir = skill_entry.path();
                let manifest_path = skill_dir.join("skill.json");
                if !manifest_path.is_file() {
                    continue;
                }
                let manifest: SkillManifest = Self::read_json(&manifest_path)?;
                out.push(CatalogSkill {
                    manifest,
                    family: family.clone(),
                    source_dir: skill_dir.display().to_string(),
                });
            }
        }
        Ok(out)
    }

    fn list_packs(&self) -> Result<Vec<CatalogPack>, SkillSourceError> {
        let mut out = Vec::new();
        let packs_root = self.packs_root();
        if !packs_root.is_dir() {
            return Ok(out);
        }
        for entry in fs::read_dir(&packs_root)? {
            let entry = entry?;
            if !entry.file_type()?.is_dir() {
                continue;
            }
            let manifest_path = entry.path().join("pack.json");
            if !manifest_path.is_file() {
                continue;
            }
            let manifest: PackManifest = Self::read_json(&manifest_path)?;
            out.push(CatalogPack { manifest });
        }
        Ok(out)
    }

    fn list_runtimes(&self) -> Result<Vec<RuntimeManifest>, SkillSourceError> {
        let mut out = Vec::new();
        let runtimes_root = self.runtimes_root();
        for entry in fs::read_dir(&runtimes_root)? {
            let entry = entry?;
            if !entry.file_type()?.is_dir() {
                continue;
            }
            let manifest_path = entry.path().join("runtime.json");
            if !manifest_path.is_file() {
                continue;
            }
            out.push(Self::read_json(&manifest_path)?);
        }
        Ok(out)
    }

    fn resolve_distribution(
        &self,
        skill_id: &str,
        _runtime_id: &str,
    ) -> Result<PathBuf, SkillSourceError> {
        let skill = self.get_skill(skill_id)?;
        Ok(PathBuf::from(skill.source_dir))
    }
}
