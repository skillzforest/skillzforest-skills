// Mirrors installer/src-tauri/src/models.rs field-for-field. Keep these two
// in sync by hand — there are few enough types that generating them isn't
// worth the build-time complexity yet.

export interface SkillPermissions {
  readProjectFiles: boolean;
  editProjectFiles: boolean;
  networkAccess: boolean;
  shellCommands: boolean;
}

/** Runtime id -> compatibility status, straight from skill.json. */
export type CompatibilityMap = Record<string, string>;

export interface SkillManifest {
  id: string;
  name: string;
  publisher: string;
  version: string;
  category: string;
  description: string;
  compatibility: CompatibilityMap;
  permissions: SkillPermissions | null;
}

export interface CatalogSkill {
  manifest: SkillManifest;
  family: string;
  sourceDir: string;
}
