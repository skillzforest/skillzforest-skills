pub mod adapter;
pub mod filesystem_adapter;
pub mod manual_adapter;

pub use adapter::{AdapterError, RuntimeAdapter};

use crate::models::RuntimeManifest;
use filesystem_adapter::FilesystemAdapter;
use manual_adapter::ManualAdapter;

/// Picks the right `RuntimeAdapter` impl for a runtime purely from its
/// declared `installStrategy` — this is the one place that decides
/// "filesystem gets automated, everything else doesn't (yet)". Adding a real
/// adapter for e.g. `upload` later means adding one match arm here, not
/// touching the engine or the frontend contract.
pub fn build_adapter(manifest: RuntimeManifest) -> Box<dyn RuntimeAdapter> {
    match manifest.install_strategy.as_str() {
        "filesystem" => Box::new(FilesystemAdapter::new(manifest)),
        _ => Box::new(ManualAdapter::new(manifest)),
    }
}

pub fn build_all_adapters(manifests: Vec<RuntimeManifest>) -> Vec<Box<dyn RuntimeAdapter>> {
    manifests.into_iter().map(build_adapter).collect()
}
