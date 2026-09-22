// Thin, typed wrappers around every Tauri command in
// installer/src-tauri/src/main.rs's invoke_handler. Nothing else in the
// frontend should call `invoke` directly — this is the one place that knows
// the command names and argument shapes, so a rename on the Rust side only
// needs updating here.
import { invoke } from "@tauri-apps/api/core";
import type { CatalogSkill } from "../types/skill";
import type { CatalogPack } from "../types/pack";
import type { PackInstallOutcome } from "../types/pack";
import type {
  ConflictInfo,
  ConflictResolution,
  InstallCapability,
  RuntimeDetectionResult,
} from "../types/runtime";
import type {
  InstallOutcome,
  Registry,
  UninstallOutcome,
  UpdateStatus,
} from "../types/registry";

export const skillzforest = {
  listSkills: () => invoke<CatalogSkill[]>("list_skills"),
  listPacks: () => invoke<CatalogPack[]>("list_packs"),
  getSkill: (id: string) => invoke<CatalogSkill>("get_skill", { id }),
  getPack: (id: string) => invoke<CatalogPack>("get_pack", { id }),

  detectRuntimes: () => invoke<RuntimeDetectionResult[]>("detect_runtimes"),
  getSkillCapabilities: (skillId: string) =>
    invoke<Record<string, InstallCapability>>("get_skill_capabilities", { skillId }),

  checkConflict: (skillId: string, runtimeId: string) =>
    invoke<ConflictInfo | null>("check_conflict", { skillId, runtimeId }),

  installSkill: (
    skillId: string,
    runtimeIds: string[],
    resolution?: ConflictResolution,
  ) => invoke<InstallOutcome[]>("install_skill", { skillId, runtimeIds, resolution: resolution ?? null }),

  updateSkill: (skillId: string, runtimeId: string) =>
    invoke<InstallOutcome>("update_skill", { skillId, runtimeId }),

  uninstallSkill: (skillId: string, runtimeId: string) =>
    invoke<void>("uninstall_skill", { skillId, runtimeId }),

  uninstallEverywhere: (skillId: string) =>
    invoke<UninstallOutcome[]>("uninstall_everywhere", { skillId }),

  installPack: (packId: string, runtimeId: string) =>
    invoke<PackInstallOutcome>("install_pack", { packId, runtimeId }),

  getRegistry: () => invoke<Registry>("get_registry"),
  checkUpdates: () => invoke<UpdateStatus[]>("check_updates"),
};
