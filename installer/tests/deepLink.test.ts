import { describe, expect, it } from "vitest";
import { parseDeepLink } from "../src/app/useDeepLinks";

describe("parseDeepLink", () => {
  it("routes a skill install link", () => {
    expect(parseDeepLink("skillzforest://install/dev-seo")).toBe("/skills/dev-seo");
  });

  it("routes a pack install link", () => {
    expect(parseDeepLink("skillzforest://install-pack/saas-builder")).toBe("/packs/saas-builder");
  });

  it("ignores a different protocol", () => {
    expect(parseDeepLink("https://skillzforest.com/install/dev-seo")).toBeNull();
  });

  it("ignores an unrecognized action", () => {
    expect(parseDeepLink("skillzforest://uninstall/dev-seo")).toBeNull();
  });

  it("ignores a malformed URL", () => {
    expect(parseDeepLink("not-a-url")).toBeNull();
  });
});
