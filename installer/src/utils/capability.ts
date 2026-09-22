import type { InstallCapability } from "../types/runtime";

/**
 * Turns a raw `InstallCapability` into what the main UI actually shows.
 * This is the one place deciding "Install" vs "Manual installation" vs
 * "Coming soon" vs hidden entirely — kept pure so it's covered by tests
 * without spinning up Tauri.
 */
export interface CapabilityPresentation {
  /** Whether this runtime should even appear as an install option. */
  offerable: boolean;
  /** Whether the checkbox can be checked / Install can be clicked. */
  installable: boolean;
  label: string;
}

export function presentCapability(capability: InstallCapability): CapabilityPresentation {
  switch (capability) {
    case "ready":
      return { offerable: true, installable: true, label: "Install" };
    case "manual":
      return { offerable: true, installable: false, label: "Manual installation" };
    case "unknown":
      return { offerable: true, installable: false, label: "Coming soon" };
    case "unsupported":
      return { offerable: false, installable: false, label: "Not compatible" };
  }
}

/** "Works with" badges only ever show runtimes with a real, working path. */
export function worksWithRuntimeIds(compatibility: Record<string, string>): string[] {
  return Object.entries(compatibility)
    .filter(([, status]) => status === "native" || status === "supported" || status === "adapted")
    .map(([runtimeId]) => runtimeId);
}
