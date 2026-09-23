//! Path resolution and safe file operations. Nothing here reads skill.json
//! or runtime.json content — that's `runtimes::manifest` — this module only
//! moves bytes around safely.
use crate::security::{self, SecurityError};
use std::fs;
use std::path::{Path, PathBuf};

#[derive(Debug, thiserror::Error)]
pub enum FsError {
    #[error(transparent)]
    Security(#[from] SecurityError),
    #[error("io error at {path}: {source}")]
    Io {
        path: String,
        #[source]
        source: std::io::Error,
    },
    #[error("could not determine the user's home directory")]
    NoHomeDir,
}

fn io(path: &Path, source: std::io::Error) -> FsError {
    FsError::Io {
        path: path.display().to_string(),
        source,
    }
}

pub fn home_dir() -> Result<PathBuf, FsError> {
    dirs::home_dir().ok_or(FsError::NoHomeDir)
}

/// Expands a leading `~` (as used in runtime.json `paths.user`) against the
/// real OS home directory. This is the ONLY place that interprets `~` —
/// runtime.json paths are otherwise used verbatim.
pub fn expand_tilde(raw: &str) -> Result<PathBuf, FsError> {
    if let Some(rest) = raw.strip_prefix("~/") {
        Ok(home_dir()?.join(rest))
    } else if raw == "~" {
        home_dir()
    } else {
        Ok(PathBuf::from(raw))
    }
}

/// The SkillzForest app-data root (registry, exported manual-install
/// bundles). Uses the OS-appropriate convention via `dirs`, falling back to
/// `~/.skillzforest` if the platform data dir can't be resolved.
pub fn app_data_dir() -> Result<PathBuf, FsError> {
    let base = dirs::data_dir().unwrap_or(home_dir()?);
    Ok(base.join("skillzforest"))
}

pub fn registry_path() -> Result<PathBuf, FsError> {
    Ok(app_data_dir()?.join("registry.json"))
}

/// Recursively copies `src` into `dest`, refusing to write anything outside
/// `dest` (defense in depth on top of the fact that `src` only ever comes
/// from this repo's own `dist/skills/<name>/<runtime>/`, never from
/// unsanitized user input).
pub fn copy_dir_safely(src: &Path, dest: &Path) -> Result<Vec<PathBuf>, FsError> {
    let mut copied = Vec::new();
    fs::create_dir_all(dest).map_err(|e| io(dest, e))?;
    copy_dir_inner(src, dest, dest, &mut copied)?;
    Ok(copied)
}

fn copy_dir_inner(
    src: &Path,
    dest_root: &Path,
    dest: &Path,
    copied: &mut Vec<PathBuf>,
) -> Result<(), FsError> {
    for entry in fs::read_dir(src).map_err(|e| io(src, e))? {
        let entry = entry.map_err(|e| io(src, e))?;
        let file_name = entry.file_name();
        let rel = Path::new(&file_name);
        // `file_name()` is always a single atomic component with no
        // separators, so this can never actually fail for a local copy —
        // it's here so this same function stays safe to reuse for a future
        // source (e.g. RemoteSkillSource extracting a downloaded archive)
        // where the "file name" could be attacker-influenced.
        security::ensure_within(dest_root, rel)?;

        let src_path = entry.path();
        let dest_path = dest.join(&file_name);
        let file_type = entry.file_type().map_err(|e| io(&src_path, e))?;

        if file_type.is_dir() {
            fs::create_dir_all(&dest_path).map_err(|e| io(&dest_path, e))?;
            copy_dir_inner(&src_path, dest_root, &dest_path, copied)?;
        } else if file_type.is_file() {
            fs::copy(&src_path, &dest_path).map_err(|e| io(&dest_path, e))?;
            copied.push(dest_path);
        }
        // Symlinks inside a skill distribution are skipped deliberately —
        // nothing in this repo's build output produces one.
    }
    Ok(())
}

/// Removes a directory this installer itself created — only ever called
/// with a path resolved from the registry (a known SkillzForest install),
/// never with an arbitrary user-supplied path.
pub fn remove_dir(path: &Path) -> Result<(), FsError> {
    if path.exists() {
        fs::remove_dir_all(path).map_err(|e| io(path, e))?;
    }
    Ok(())
}

pub fn ensure_dir(path: &Path) -> Result<(), FsError> {
    fs::create_dir_all(path).map_err(|e| io(path, e))
}

/// A permissive PATH lookup used only for best-effort runtime *detection*
/// (never for deciding whether to run anything). Returns true if a binary
/// with this name is found on PATH.
pub fn executable_on_path(name: &str) -> bool {
    let Some(path_var) = std::env::var_os("PATH") else {
        return false;
    };
    std::env::split_paths(&path_var).any(|dir| {
        let candidate = dir.join(name);
        candidate.is_file()
            || (cfg!(windows) && candidate.with_extension("exe").is_file())
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    fn tmp_dir(name: &str) -> PathBuf {
        let dir = std::env::temp_dir().join(format!("skillzforest-test-{name}-{}", std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        fs::create_dir_all(&dir).unwrap();
        dir
    }

    #[test]
    fn expands_tilde_against_home() {
        let expanded = expand_tilde("~/.claude/skills").unwrap();
        assert!(expanded.starts_with(home_dir().unwrap()));
        assert!(expanded.ends_with(".claude/skills"));
    }

    #[test]
    fn leaves_absolute_paths_untouched() {
        let expanded = expand_tilde("/opt/skills").unwrap();
        assert_eq!(expanded, PathBuf::from("/opt/skills"));
    }

    #[test]
    fn copy_dir_safely_copies_nested_structure() {
        let src = tmp_dir("src");
        let dest_root = tmp_dir("dest");
        fs::write(src.join("SKILL.md"), "hello").unwrap();
        fs::create_dir_all(src.join("scripts")).unwrap();
        fs::write(src.join("scripts/run.js"), "// noop").unwrap();

        let dest = dest_root.join("presales-quote");
        let copied = copy_dir_safely(&src, &dest).unwrap();

        assert!(dest.join("SKILL.md").is_file());
        assert!(dest.join("scripts/run.js").is_file());
        assert_eq!(copied.len(), 2);

        let _ = fs::remove_dir_all(&src);
        let _ = fs::remove_dir_all(&dest_root);
    }
}
