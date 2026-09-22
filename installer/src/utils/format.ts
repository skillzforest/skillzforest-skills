/** Human-friendly runtime display names, for the rare case a manifest's own
 * `name` isn't loaded yet (e.g. a skeleton state before first fetch). */
export function formatInstallDate(epochMillis: number): string {
  if (!epochMillis) return "Unknown date";
  return new Date(epochMillis).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

/** "12 / 15 skills installed" for a pack card. */
export function formatPackProgress(installed: number, total: number): string {
  return `${installed} / ${total} skill${total === 1 ? "" : "s"} installed`;
}
