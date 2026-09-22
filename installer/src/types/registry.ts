export interface InstalledSkillEntry {
  version: string;
  /** Unix epoch milliseconds — format with `new Date(installDate)`. */
  installDate: number;
  source: string;
}

export interface Registry {
  /** skillId -> runtimeId -> installed entry */
  skills: Record<string, Record<string, InstalledSkillEntry>>;
}

export interface InstallOutcome {
  skillId: string;
  runtimeId: string;
  installed: boolean;
  version: string;
  reason: string | null;
}

export interface UninstallOutcome {
  runtimeId: string;
  success: boolean;
  error: string | null;
}

export interface UpdateStatus {
  skillId: string;
  runtimeId: string;
  installedVersion: string;
  availableVersion: string;
  updateAvailable: boolean;
}
