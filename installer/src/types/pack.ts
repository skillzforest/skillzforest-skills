export interface PackManifest {
  id: string;
  name: string;
  publisher: string;
  version: string;
  description: string;
  skills: string[];
}

export interface CatalogPack {
  manifest: PackManifest;
}

export interface PackSkipReason {
  skillId: string;
  reason: string;
}

export interface PackInstallOutcome {
  packId: string;
  runtimeId: string;
  installed: string[];
  skipped: PackSkipReason[];
}
