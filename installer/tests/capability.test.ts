import { describe, expect, it } from "vitest";
import { presentCapability, worksWithRuntimeIds } from "../src/utils/capability";

describe("presentCapability", () => {
  it("offers and enables install when ready", () => {
    expect(presentCapability("ready")).toEqual({
      offerable: true,
      installable: true,
      label: "Install",
    });
  });

  it("offers but disables install for manual runtimes", () => {
    const result = presentCapability("manual");
    expect(result.offerable).toBe(true);
    expect(result.installable).toBe(false);
    expect(result.label).toBe("Manual installation");
  });

  it("shows coming soon for unknown compatibility", () => {
    expect(presentCapability("unknown").label).toBe("Coming soon");
  });

  it("hides unsupported runtimes entirely", () => {
    expect(presentCapability("unsupported").offerable).toBe(false);
  });
});

describe("worksWithRuntimeIds", () => {
  it("includes native, supported and adapted runtimes", () => {
    const ids = worksWithRuntimeIds({
      "claude-code": "native",
      codex: "supported",
      cursor: "adapted",
      chatgpt: "unknown",
      opencode: "unsupported",
    });
    expect(ids.sort()).toEqual(["claude-code", "codex", "cursor"]);
  });

  it("returns an empty list when nothing is compatible", () => {
    expect(worksWithRuntimeIds({ chatgpt: "unknown" })).toEqual([]);
  });
});
