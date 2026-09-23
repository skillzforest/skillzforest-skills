import { describe, expect, it } from "vitest";
import { computeInstalledPacks, computeInstalledSkills } from "../src/utils/myskills";
import type { CatalogSkill } from "../src/types/skill";
import type { CatalogPack } from "../src/types/pack";
import type { Registry } from "../src/types/registry";

function fakeSkill(id: string, name: string): CatalogSkill {
  return {
    manifest: {
      id,
      name,
      publisher: "Test",
      version: "1.0.0",
      category: "test",
      description: "",
      compatibility: {},
      permissions: null,
    },
    family: "test",
    sourceDir: `/skills/test/${id}`,
  };
}

function fakePack(id: string, name: string, skills: string[]): CatalogPack {
  return { manifest: { id, name, publisher: "Test", version: "1.0.0", description: "", skills } };
}

describe("computeInstalledSkills", () => {
  it("lists only skills present in the registry, sorted by name", () => {
    const skills = [fakeSkill("presales-quote", "Devis"), fakeSkill("presales-domain-name", "Nom de domaine")];
    const registry: Registry = {
      skills: {
        "presales-domain-name": { "claude-code": { version: "1.0.0", installDate: 1, source: "test" } },
        "presales-quote": {
          "claude-code": { version: "1.0.0", installDate: 1, source: "test" },
          codex: { version: "1.0.0", installDate: 1, source: "test" },
        },
      },
    };

    const result = computeInstalledSkills(skills, registry);

    expect(result).toEqual([
      { skillId: "presales-quote", name: "Devis", runtimeIds: ["claude-code", "codex"] },
      { skillId: "presales-domain-name", name: "Nom de domaine", runtimeIds: ["claude-code"] },
    ]);
  });

  it("falls back to the raw id when a registered skill left the catalog", () => {
    const registry: Registry = {
      skills: { "removed-skill": { "claude-code": { version: "1.0.0", installDate: 1, source: "test" } } },
    };
    const result = computeInstalledSkills([], registry);
    expect(result).toEqual([{ skillId: "removed-skill", name: "removed-skill", runtimeIds: ["claude-code"] }]);
  });

  it("omits an entry whose every runtime install was removed", () => {
    const registry: Registry = { skills: { "presales-quote": {} } };
    expect(computeInstalledSkills([fakeSkill("presales-quote", "Devis")], registry)).toEqual([]);
  });
});

describe("computeInstalledPacks", () => {
  it("counts how many of a pack's skills are installed anywhere", () => {
    const packs = [fakePack("presales", "Pre-Sales Pack", ["presales-quote", "presales-functional-scoping", "presales-maintenance-quote"])];
    const registry: Registry = {
      skills: {
        "presales-quote": { "claude-code": { version: "1.0.0", installDate: 1, source: "test" } },
        "presales-functional-scoping": { codex: { version: "1.0.0", installDate: 1, source: "test" } },
      },
    };

    expect(computeInstalledPacks(packs, registry)).toEqual([
      { packId: "presales", name: "Pre-Sales Pack", installedCount: 2, totalCount: 3 },
    ]);
  });

  it("excludes packs with nothing installed", () => {
    const packs = [fakePack("saas-builder", "SaaS Builder Pack", ["dev-seo"])];
    expect(computeInstalledPacks(packs, { skills: {} })).toEqual([]);
  });
});
