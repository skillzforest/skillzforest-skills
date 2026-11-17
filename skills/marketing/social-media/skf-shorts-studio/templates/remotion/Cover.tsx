import React, { useMemo } from "react";
import { AbsoluteFill } from "remotion";
import { Background, Logo, MediaView, RichText, alpha, fitText, useBrandFonts, useFormat } from "./kit";
import { Brand, ShortProps, shortSchema } from "./schema";

// The cover: 2–5 big words, one on the accent block, the product visual, the brand.
// On 9:16 the title stays inside the centre square (y 420–1500), the part every
// platform keeps when it crops the cover for a grid (Instagram 3:4 / 4:5, 1:1).

const Badge: React.FC<{ text?: string; brand: Brand; size: number }> = ({ text, brand, size }) =>
  text ? (
    <div
      style={{
        display: "inline-block",
        background: brand.colors.text,
        color: brand.colors.bg,
        fontFamily: brand.fonts.display,
        fontWeight: 900,
        fontSize: size,
        letterSpacing: size * 0.06,
        textTransform: "uppercase",
        padding: `${size * 0.35}px ${size * 0.7}px`,
        borderRadius: size * 0.4,
        transform: "rotate(-5deg)",
        boxShadow: `0 ${size * 0.25}px ${size * 0.8}px rgba(0,0,0,0.35)`,
      }}
    >
      {text}
    </div>
  ) : null;

export const Cover: React.FC<ShortProps> = (raw) => {
  const { brand, cover } = useMemo(() => shortSchema.parse(raw), [raw]);
  useBrandFonts(brand);
  const { format, width, height, safe } = useFormat();
  const boxW = width - safe.left - safe.right;
  const kickerSize = Math.round(width * (format === "16x9" ? 0.026 : 0.045));
  const badgeSize = Math.round(width * (format === "16x9" ? 0.026 : 0.042));
  // frame "full": the visual is the whole background (a game or film still), the title over a veil.
  const backdrop = cover.visual?.frame === "full" ? cover.visual : undefined;
  const visual = backdrop ? undefined : cover.visual;
  const Backdrop: React.FC<{ veil: string }> = ({ veil }) =>
    backdrop ? (
      <AbsoluteFill>
        <MediaView media={{ ...backdrop, zoom: "none" }} brand={brand} width={width} height={height} durationInFrames={1} still bare />
        <AbsoluteFill style={{ background: veil }} />
      </AbsoluteFill>
    ) : (
      <Background brand={brand} still />
    );

  if (format === "16x9") {
    const textW = visual ? width * 0.56 : boxW;
    const size = fitText(brand, cover.title, { box: textW, lines: 3, max: height * 0.22, highlight: cover.highlight, height: (height - safe.top - safe.bottom) * 0.68 });
    return (
      <AbsoluteFill style={{ backgroundColor: brand.colors.bg, overflow: "hidden" }}>
        <Backdrop veil={`linear-gradient(90deg, ${alpha(brand.colors.bg, 0.85)}, ${alpha(brand.colors.bg, 0.55)} 45%, transparent 75%)`} />
        {visual && (
          <div style={{ position: "absolute", right: width * 0.05, top: height * 0.12, transform: "rotate(6deg)" }}>
            <MediaView media={{ ...visual, zoom: "none" }} brand={brand} width={visual.frame === "phone" ? height * 0.5 : width * 0.34} height={visual.frame === "phone" ? height * 1.02 : height * 0.62} durationInFrames={1} still />
          </div>
        )}
        <div style={{ position: "absolute", left: safe.left, top: safe.top, bottom: safe.bottom, width: textW, display: "flex", flexDirection: "column", justifyContent: "center", gap: size * 0.3 }}>
          {cover.badge && (
            <div style={{ alignSelf: "flex-start" }}>
              <Badge text={cover.badge} brand={brand} size={badgeSize} />
            </div>
          )}
          <RichText text={cover.title} highlight={cover.highlight} brand={brand} size={size} align="left" />
          <Logo brand={brand} size={height * 0.07} />
        </div>
      </AbsoluteFill>
    );
  }

  // 9:16, 4:5, 1:1 — stacked: brand, kicker, title, visual.
  const titleZone = format === "9x16" ? { top: 400, height: visual ? 660 : 1100 } : { top: safe.top + height * 0.08, height: visual ? height * 0.45 : height * 0.72 };
  const extras = (cover.badge ? badgeSize * 2.2 : 0) + (cover.kicker ? kickerSize * 1.8 : 0);
  const size = fitText(brand, cover.title, { box: boxW, lines: visual ? 3 : 4, max: width * (visual ? 0.17 : 0.19), highlight: cover.highlight, height: titleZone.height - extras });
  const visualTop = titleZone.top + titleZone.height + height * 0.02;
  return (
    <AbsoluteFill style={{ backgroundColor: brand.colors.bg, overflow: "hidden" }}>
      <Backdrop veil={`linear-gradient(180deg, ${alpha(brand.colors.bg, 0.7)}, ${alpha(brand.colors.bg, 0.5)} 30%, ${alpha(brand.colors.bg, 0.5)} 70%, ${alpha(brand.colors.bg, 0.15)})`} />
      <div style={{ position: "absolute", top: format === "9x16" ? 290 : safe.top, left: 0, right: 0, display: "flex", justifyContent: "center" }}>
        <Logo brand={brand} size={width * 0.075} />
      </div>
      <div
        style={{
          position: "absolute",
          top: titleZone.top,
          height: titleZone.height,
          left: safe.left,
          right: safe.right,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: size * 0.28,
        }}
      >
        {cover.badge && <Badge text={cover.badge} brand={brand} size={badgeSize} />}
        {cover.kicker && (
          <div style={{ fontFamily: brand.fonts.body, fontWeight: 700, fontSize: kickerSize, color: brand.colors.muted, textTransform: "uppercase", letterSpacing: kickerSize * 0.12, textAlign: "center" }}>
            {cover.kicker}
          </div>
        )}
        <RichText text={cover.title} highlight={cover.highlight} brand={brand} size={size} />
      </div>
      {visual && (
        <div style={{ position: "absolute", top: visualTop, left: 0, right: 0, display: "flex", justifyContent: "center" }}>
          <div style={{ transform: "rotate(-4deg)", filter: `drop-shadow(0 30px 60px ${alpha("#000", 0.4)})` }}>
            <MediaView
              media={{ ...visual, zoom: "none" }}
              brand={brand}
              width={visual.frame === "phone" ? width * 0.56 : boxW}
              height={visual.frame === "phone" ? width * 0.56 * 2.05 : boxW * (visual.frame === "browser" ? 0.72 : 1)}
              durationInFrames={1}
              still
            />
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};
