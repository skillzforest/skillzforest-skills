//! `SkillSource` abstracts *where the catalog comes from*, so the installer
//! engine never cares whether a skill's manifest and distribution came from
//! this monorepo checked out on disk or from the future SkillzForest API.
//!
//! - `LocalSkillSource`: reads `skills/`, `packs/`, `runtimes/` directly from
//!   this repository. Fully functional — this is what the MVP uses.
//! - `RemoteSkillSource`: talks to the SkillzForest API. Not implemented —
//!   see the TODOs below for the shape it needs to fill in.
mod local;
mod remote;

pub use local::LocalSkillSource;
// Not wired into the app yet — see remote.rs's module docs for what's
// missing. Kept public and allowed dead code so the shape is real Rust that
// compiles and is ready to `use`, not just a design note.
#[allow(unused_imports)]
pub use remote::RemoteSkillSource;

use crate::models::{CatalogPack, CatalogSkill, RuntimeManifest};
use std::path::PathBuf;

#[derive(Debug, thiserror::Error)]
pub enum SkillSourceError {
    #[error("io error: {0}")]
    Io(#[from] std::io::Error),
    #[error("invalid manifest at {path}: {message}")]
    InvalidManifest { path: String, message: String },
    #[error("not found: {0}")]
    NotFound(String),
    // Only ever constructed by RemoteSkillSource, which isn't wired into
    // the app yet — see remote.rs.
    #[allow(dead_code)]
    #[error("not implemented yet: {0}")]
    NotImplemented(&'static str),
}

pub trait SkillSource: Send + Sync {
    /// Every skill this source currently knows about.
    fn list_skills(&self) -> Result<Vec<CatalogSkill>, SkillSourceError>;
    /// Every pack this source currently knows about.
    fn list_packs(&self) -> Result<Vec<CatalogPack>, SkillSourceError>;
    /// Every runtime manifest this source currently knows about.
    fn list_runtimes(&self) -> Result<Vec<RuntimeManifest>, SkillSourceError>;
    fn get_skill(&self, id: &str) -> Result<CatalogSkill, SkillSourceError> {
        self.list_skills()?
            .into_iter()
            .find(|s| s.manifest.id == id)
            .ok_or_else(|| SkillSourceError::NotFound(id.to_string()))
    }
    fn get_pack(&self, id: &str) -> Result<CatalogPack, SkillSourceError> {
        self.list_packs()?
            .into_iter()
            .find(|p| p.manifest.id == id)
            .ok_or_else(|| SkillSourceError::NotFound(id.to_string()))
    }
    /// Resolves the folder to install-from for one (skill, runtime) pair.
    ///
    /// End users of the packaged app never have Node.js, so this can't
    /// depend on `npm run build:skill` having been run first: for
    /// `LocalSkillSource` + a `filesystem`-strategy runtime, this returns
    /// the skill's own canonical `skills/<family>/<name>/` folder, and the
    /// generic filesystem adapter (`runtimes::filesystem_adapter`) applies
    /// the same exclusions `scripts/lib/adapters.js` uses (node_modules/,
    /// out/, .DS_Store) at copy time — i.e. the distribution is generated
    /// on the fly instead of being pre-materialized under `dist/`. For
    /// `RemoteSkillSource` this would be a downloaded, verified package —
    /// see remote.rs.
    fn resolve_distribution(
        &self,
        skill_id: &str,
        runtime_id: &str,
    ) -> Result<PathBuf, SkillSourceError>;
}
