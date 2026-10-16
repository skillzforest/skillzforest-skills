import React from "react";
import { AbsoluteFill } from "remotion";
import { StillProps } from "./schema";

// Static images for a product page, rendered with `remotion still`:
// - cover   (1:1)  the card / listing image: an emblem, legible at 36 px, safe inside a circle
// - poster  (16:9) the video's cover, shown before it plays
// - outcome (2:1)  a "what you can do" block's picture
export const ProductStill: React.FC<StillProps> = ({ brand, variant, glyph, name, headline, title, prompt }) => {
  if (variant === "cover") {
    return (
      <AbsoluteFill style={{ background: brand.background, justifyContent: "center", alignItems: "center" }}>
        {/* Subject inside the central 80 %: the site crops the cover into a circle. */}
        <div
          style={{
            width: "62%",
            height: "62%",
            borderRadius: "50%",
            background: brand.surface,
            border: `12px solid ${brand.accent}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontFamily: brand.fontFamily,
            fontWeight: 800,
            fontSize: /\p{Extended_Pictographic}/u.test(glyph) ? 340 : glyph.length > 1 ? 200 : 260,
            color: brand.accent,
            letterSpacing: -6,
          }}
        >
          {glyph}
        </div>
      </AbsoluteFill>
    );
  }

  const isPoster = variant === "poster";
  return (
    <AbsoluteFill
      style={{
        background: brand.background,
        fontFamily: brand.fontFamily,
        padding: isPoster ? "120px 140px" : "90px 110px",
        flexDirection: "row",
        alignItems: "center",
        gap: 80,
      }}
    >
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 30, fontWeight: 700, color: brand.accent, textTransform: "uppercase", letterSpacing: 4 }}>
          {isPoster ? brand.wordmark : name}
        </div>
        <div style={{ fontSize: isPoster ? 96 : 84, fontWeight: 800, color: brand.text, lineHeight: 1.05, marginTop: 20 }}>
          {isPoster ? name : title}
        </div>
        {isPoster && (
          <div style={{ fontSize: 40, fontWeight: 500, color: brand.muted, lineHeight: 1.3, marginTop: 32 }}>{headline}</div>
        )}
        {isPoster && (
          <div
            style={{
              marginTop: 48,
              background: brand.surface,
              borderRadius: 20,
              padding: "26px 32px",
              fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
              fontSize: 28,
              color: brand.text,
              maxHeight: 160,
              overflow: "hidden",
            }}
          >
            <span style={{ color: brand.accent }}>&gt; </span>
            {prompt.length > 140 ? `${prompt.slice(0, 137)}…` : prompt}
          </div>
        )}
      </div>
      <div
        style={{
          flex: "none",
          width: isPoster ? 420 : 380,
          height: isPoster ? 420 : 380,
          borderRadius: "50%",
          background: brand.surface,
          border: `10px solid ${brand.accent}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 170,
          fontWeight: 800,
          color: brand.accent,
        }}
      >
        {glyph}
      </div>
    </AbsoluteFill>
  );
};
