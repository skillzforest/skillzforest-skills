import React from "react";
import {
  AbsoluteFill,
  Easing,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Brand, ProductProps, SCENES } from "./schema";

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const Wordmark: React.FC<{ brand: Brand }> = ({ brand }) => (
  <div
    style={{
      position: "absolute",
      top: 56,
      left: 72,
      fontSize: 30,
      fontWeight: 700,
      color: brand.text,
      opacity: 0.85,
      letterSpacing: -0.5,
    }}
  >
    {brand.wordmark}
  </div>
);

const FadeUp: React.FC<{ delay?: number; children: React.ReactNode; style?: React.CSSProperties }> = ({
  delay = 0,
  children,
  style,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const progress = spring({ frame: frame - delay, fps, config: { damping: 200 } });
  return (
    <div
      style={{
        ...style,
        opacity: progress,
        translate: `0px ${interpolate(progress, [0, 1], [40, 0])}px`,
      }}
    >
      {children}
    </div>
  );
};

const TitleScene: React.FC<ProductProps> = ({ brand, name, headline, kind }) => (
  <AbsoluteFill style={{ justifyContent: "center", padding: "0 160px" }}>
    <FadeUp>
      <div style={{ fontSize: 34, fontWeight: 600, color: brand.accent, textTransform: "uppercase", letterSpacing: 4 }}>
        {kind === "pack" ? "Pack" : "Skill"}
      </div>
    </FadeUp>
    <FadeUp delay={6}>
      <div style={{ fontSize: 120, fontWeight: 800, color: brand.text, lineHeight: 1.05, marginTop: 16 }}>
        {name}
      </div>
    </FadeUp>
    <FadeUp delay={16}>
      <div style={{ fontSize: 46, fontWeight: 500, color: brand.muted, lineHeight: 1.3, marginTop: 36, maxWidth: 1500 }}>
        {headline}
      </div>
    </FadeUp>
  </AbsoluteFill>
);

const PromptScene: React.FC<ProductProps> = ({ brand, prompt, promptLabel, name }) => {
  const frame = useCurrentFrame();
  // Type the prompt over the first 70 % of the scene, then hold it.
  const typed = Math.round(
    interpolate(frame, [10, SCENES.prompt * 0.7], [0, prompt.length], clamp),
  );
  const cursorOn = Math.floor(frame / 15) % 2 === 0;
  const done = typed >= prompt.length;
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <FadeUp style={{ width: 1500 }}>
        <div style={{ fontSize: 30, fontWeight: 600, color: brand.muted, marginBottom: 20 }}>{promptLabel}</div>
        <div
          style={{
            background: brand.surface,
            borderRadius: 28,
            padding: "48px 56px",
            minHeight: 360,
            boxShadow: "0 40px 80px -30px rgba(0,0,0,0.55)",
            border: "1px solid rgba(255,255,255,0.12)",
          }}
        >
          <div style={{ display: "flex", gap: 12, marginBottom: 32 }}>
            {["#FF5F57", "#FEBC2E", "#28C840"].map((c) => (
              <div key={c} style={{ width: 18, height: 18, borderRadius: 9, background: c }} />
            ))}
          </div>
          <div style={{ fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace", fontSize: 36, lineHeight: 1.5, color: brand.text }}>
            <span style={{ color: brand.accent }}>&gt; </span>
            {prompt.slice(0, typed)}
            <span style={{ opacity: cursorOn && !done ? 1 : 0 }}>▍</span>
          </div>
          <div
            style={{
              marginTop: 36,
              display: "inline-block",
              padding: "10px 22px",
              borderRadius: 999,
              background: brand.accent,
              color: brand.surface,
              fontSize: 26,
              fontWeight: 700,
              opacity: interpolate(frame, [SCENES.prompt * 0.72, SCENES.prompt * 0.8], [0, 1], clamp),
            }}
          >
            ✓ {name}
          </div>
        </div>
      </FadeUp>
    </AbsoluteFill>
  );
};

const PointsScene: React.FC<ProductProps> = ({ brand, points, pointsTitle, kind }) => {
  const step = Math.max(8, Math.floor((SCENES.points - 30) / Math.max(points.length, 1)));
  return (
    <AbsoluteFill style={{ justifyContent: "center", padding: "0 200px" }}>
      <FadeUp>
        <div style={{ fontSize: 56, fontWeight: 800, color: brand.text, marginBottom: 48 }}>{pointsTitle}</div>
      </FadeUp>
      {points.map((point, i) => (
        <FadeUp key={point} delay={10 + i * step}>
          <div style={{ display: "flex", alignItems: "center", gap: 28, marginBottom: points.length > 4 ? 18 : 30 }}>
            <div
              style={{
                flex: "none",
                width: 64,
                height: 64,
                borderRadius: 32,
                background: brand.accent,
                color: brand.surface,
                fontSize: 30,
                fontWeight: 800,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              {kind === "pack" ? i + 1 : "✓"}
            </div>
            <div style={{ fontSize: points.length > 4 ? 36 : 44, fontWeight: 600, color: brand.text }}>{point}</div>
          </div>
        </FadeUp>
      ))}
    </AbsoluteFill>
  );
};

const OutroScene: React.FC<ProductProps> = ({ brand, name, cta }) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", textAlign: "center" }}>
      <FadeUp>
        <div style={{ fontSize: 110, fontWeight: 800, color: brand.text }}>{name}</div>
      </FadeUp>
      <FadeUp delay={10}>
        <div
          style={{
            marginTop: 40,
            padding: "20px 44px",
            borderRadius: 999,
            background: brand.accent,
            color: brand.surface,
            fontSize: 40,
            fontWeight: 700,
            scale: interpolate(frame, [30, 45, 60], [1, 1.05, 1], { ...clamp, easing: Easing.inOut(Easing.ease) }),
          }}
        >
          {cta}
        </div>
      </FadeUp>
    </AbsoluteFill>
  );
};

export const ProductHero: React.FC<ProductProps> = (props) => {
  const { fps } = useVideoConfig();
  const { brand } = props;
  let from = 0;
  const at = (length: number) => {
    const start = from;
    from += length;
    return start;
  };
  return (
    <AbsoluteFill style={{ background: brand.background, fontFamily: brand.fontFamily }}>
      <Wordmark brand={brand} />
      <Sequence from={at(SCENES.title)} durationInFrames={SCENES.title} premountFor={fps}>
        <TitleScene {...props} />
      </Sequence>
      <Sequence from={at(SCENES.prompt)} durationInFrames={SCENES.prompt} premountFor={fps}>
        <PromptScene {...props} />
      </Sequence>
      <Sequence from={at(SCENES.points)} durationInFrames={SCENES.points} premountFor={fps}>
        <PointsScene {...props} />
      </Sequence>
      <Sequence from={at(SCENES.outro)} durationInFrames={SCENES.outro} premountFor={fps}>
        <OutroScene {...props} />
      </Sequence>
    </AbsoluteFill>
  );
};
