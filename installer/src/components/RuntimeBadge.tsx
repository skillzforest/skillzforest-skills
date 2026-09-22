interface RuntimeBadgeProps {
  name: string;
  variant: "detected" | "not-detected" | "manual" | "default";
}

/** A small pill for a runtime name — the only place "detected" state shows
 * up visually, kept deliberately free of any technical wording. */
export function RuntimeBadge({ name, variant }: RuntimeBadgeProps) {
  const symbol = variant === "detected" ? "✓" : variant === "not-detected" ? "○" : null;
  const className = `badge${variant !== "default" ? ` ${variant}` : ""}`;
  return (
    <span className={className}>
      {symbol ? `${symbol} ` : ""}
      {name}
    </span>
  );
}
