//! Network fetch + signature verification for `skill_source::RemoteSkillSource`.
//! Kept separate from `skill_source` so "where does the catalog come from"
//! (an API shape) stays decoupled from "how do we safely pull bytes off the
//! network" (HTTP client, checksums, retries) — the latter is generic enough
//! to reuse for skill packages, pack bundles, or future update checks alike.
//!
//! Not implemented. TODO before `RemoteSkillSource` can work:
//! 1. An HTTP client (e.g. `reqwest` with `rustls`) — deliberately not added
//!    as a dependency yet, since nothing calls this module today.
//! 2. Download to a temp file, not straight into the install target.
//! 3. Verify a signature/checksum from the manifest before the file is
//!    handed to `filesystem::copy_dir_safely` — this is the trust boundary
//!    that replaces "it's the maintainer's own repo".
//! 4. Surface progress to the frontend (Tauri events) for the install
//!    screen's progress bar.
//!
//! Not called from anywhere yet — allowed dead code rather than deleted, so
//! it stays real, compiling Rust to build against once the API exists.
#![allow(dead_code)]

#[derive(Debug, thiserror::Error)]
pub enum DownloadError {
    #[error("downloading from SkillzForest is not implemented yet")]
    NotImplemented,
}

pub struct VerifiedPackage {
    pub path: std::path::PathBuf,
}

/// Placeholder signature for the eventual download+verify step. Always
/// fails today — see the module docs for what's missing.
pub fn download_and_verify(_url: &str, _expected_checksum: &str) -> Result<VerifiedPackage, DownloadError> {
    Err(DownloadError::NotImplemented)
}
