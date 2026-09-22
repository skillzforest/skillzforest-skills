import type { CatalogSkill } from "../types/skill";
import type { CatalogPack } from "../types/pack";
import type { Registry } from "../types/registry";

export interface InstalledSkillSummary {
  skillId: string;
  name: string;
  runtimeIds: string[];
}

export interface InstalledPackSummary {
  packId: string;
  name: string;
  installedCount: number;
  totalCount: number;
}

/** Pure projection of (catalog, registry) -> what "My Skills" renders. Kept
 * out of the component so it's testable without mounting React or Tauri. */
export function computeInstalledSkills(
  skills: CatalogSkill[],
  registry: Registry,
): InstalledSkillSummary[] {
  const byId = new Map(skills.map((s) => [s.manifest.id, s]));
  return Object.entries(registry.skills)
    .map(([skillId, byRuntime]) => {
      const catalogEntry = byId.get(skillId);
      return {
        skillId,
        name: catalogEntry?.manifest.name ?? skillId,
        runtimeIds: Object.keys(byRuntime),
      };
    })
    .filter((s) => s.runtimeIds.length > 0)
    .sort((a, b) => a.name.localeCompare(b.name));
}

/** For each pack, how many of its skills are installed in ANY runtime. */
export function computeInstalledPacks(
  packs: CatalogPack[],
  registry: Registry,
): InstalledPackSummary[] {
  return packs
    .map((pack) => {
      const installedCount = pack.manifest.skills.filter(
        (skillId) => Object.keys(registry.skills[skillId] ?? {}).length > 0,
      ).length;
      return {
        packId: pack.manifest.id,
        name: pack.manifest.name,
        installedCount,
        totalCount: pack.manifest.skills.length,
      };
    })
    .filter((p) => p.installedCount > 0);
}
