export interface RuntimePaths {
  user: string | null;
}

export interface RuntimeDetection {
  configDir: string | null;
  executable: string | null;
}

export interface RuntimeManifest {
  id: string;
  name: string;
  type: string;
  supportsAgentSkills: boolean | null;
  installStrategy: string;
  status: "verified" | "supported" | "unknown";
  paths: RuntimePaths | null;
  detection: RuntimeDetection | null;
  notes: string | null;
}

export interface RuntimeDetectionResult {
  runtime: RuntimeManifest;
  detected: boolean;
  automatable: boolean;
}

/**
 * What the app will actually do for one (skill, runtime) pair.
 * Mirrors `models::InstallCapability` in Rust exactly — never computed in TS.
 */
export type InstallCapability = "ready" | "unsupported" | "unknown" | "manual";

export type ConflictResolution = "keep-existing" | "replace" | "cancel";

export interface ConflictInfo {
  skillId: string;
  runtimeId: string;
}
