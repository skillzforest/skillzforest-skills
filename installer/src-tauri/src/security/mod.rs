//! Defensive checks run before anything touches disk. This module never
//! executes anything from a skill — it only validates ids, manifests, and
//! paths. "Installing a skill" means copying files; it never means running
//! the scripts that ship inside one.
use crate::models::SkillManifest;
use std::path::{Component, Path};

#[derive(Debug, thiserror::Error)]
pub enum SecurityError {
    #[error("invalid id '{0}': ids must be lowercase letters, digits and hyphens only")]
    InvalidId(String),
    #[error("manifest is missing required field '{0}'")]
    MissingField(String),
    #[error("path '{0}' escapes its intended destination")]
    PathTraversal(String),
    #[error("skill source is missing SKILL.md at {0}")]
    MissingSkillMd(String),
}

/// Ids (skill ids, pack ids, runtime ids) are used to build filesystem paths,
/// so they're restricted to a safe character set — never taken from user
/// input as a raw path.
pub fn validate_id(id: &str) -> Result<(), SecurityError> {
    let valid = !id.is_empty()
        && id
            .chars()
            .all(|c| c.is_ascii_lowercase() || c.is_ascii_digit() || c == '-')
        && !id.starts_with('-')
        && !id.ends_with('-')
        && !id.contains("--");
    if valid {
        Ok(())
    } else {
        Err(SecurityError::InvalidId(id.to_string()))
    }
}

pub fn validate_skill_manifest(manifest: &SkillManifest) -> Result<(), SecurityError> {
    validate_id(&manifest.id)?;
    if manifest.name.trim().is_empty() {
        return Err(SecurityError::MissingField("name".into()));
    }
    if manifest.version.trim().is_empty() {
        return Err(SecurityError::MissingField("version".into()));
    }
    Ok(())
}

pub fn require_skill_md(skill_dir: &Path) -> Result<(), SecurityError> {
    let skill_md = skill_dir.join("SKILL.md");
    if skill_md.is_file() {
        Ok(())
    } else {
        Err(SecurityError::MissingSkillMd(skill_dir.display().to_string()))
    }
}

/// Refuses any path containing `..`, an absolute component, or (on Windows) a
/// prefix/root component once joined onto `base` — used before copying any
/// file so a maliciously crafted archive/manifest can never write outside its
/// intended destination directory.
pub fn ensure_within(base: &Path, candidate: &Path) -> Result<(), SecurityError> {
    for component in candidate.components() {
        match component {
            Component::ParentDir | Component::RootDir | Component::Prefix(_) => {
                return Err(SecurityError::PathTraversal(candidate.display().to_string()));
            }
            _ => {}
        }
    }
    let joined = base.join(candidate);
    let normalized = normalize(&joined);
    let base_normalized = normalize(base);
    if normalized.starts_with(&base_normalized) {
        Ok(())
    } else {
        Err(SecurityError::PathTraversal(candidate.display().to_string()))
    }
}

/// Lexical normalization (no filesystem access, so it works on paths that
/// don't exist yet) — resolves `.`/`..` components without following
/// symlinks.
fn normalize(path: &Path) -> std::path::PathBuf {
    let mut out = std::path::PathBuf::new();
    for component in path.components() {
        match component {
            Component::ParentDir => {
                out.pop();
            }
            Component::CurDir => {}
            other => out.push(other.as_os_str()),
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn accepts_normal_ids() {
        assert!(validate_id("av-devis").is_ok());
        assert!(validate_id("dev-seo").is_ok());
    }

    #[test]
    fn rejects_traversal_and_weird_ids() {
        assert!(validate_id("../etc").is_err());
        assert!(validate_id("Av-Devis").is_err());
        assert!(validate_id("av_devis").is_err());
        assert!(validate_id("").is_err());
        assert!(validate_id("-av-devis").is_err());
    }

    #[test]
    fn ensure_within_blocks_parent_dir_escape() {
        let base = Path::new("/home/user/.claude/skills");
        assert!(ensure_within(base, Path::new("av-devis")).is_ok());
        assert!(ensure_within(base, Path::new("../../etc/passwd")).is_err());
        assert!(ensure_within(base, Path::new("/etc/passwd")).is_err());
    }
}
