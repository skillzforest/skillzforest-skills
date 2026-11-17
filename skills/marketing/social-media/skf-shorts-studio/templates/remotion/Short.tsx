import React, { useMemo } from "react";
import { AbsoluteFill, Audio, Easing, Sequence, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { Background, Fill, Logo, MediaView, RichText, alpha, clamp, fitText, pop, src, useBrandFonts, useFormat } from "./kit";
import { Brand, Scene, ShortProps, sceneFrames, shortSchema, totalFrames } from "./schema";

type SceneProps<T extends Scene["type"]> = { scene: Extract<Scene, { type: T }>; brand: Brand; frames: number };

// Content box: the frame minus the areas the platforms' interface covers.
const useBox = () => {
  const { width, height, safe, format } = useFormat();
  return { width, height, safe, format, boxW: width - safe.left - safe.right, boxH: height - safe.top - safe.bottom };
};

const Box: React.FC<{ children: React.ReactNode; gap?: number; justify?: "center" | "flex-start" }> = ({ children, gap = 0, justify = "center" }) => {
  const { safe } = useBox();
  return (
    <AbsoluteFill
      style={{
        padding: `${safe.top}px ${safe.right}px ${safe.bottom}px ${safe.left}px`,
        display: "flex",
        flexDirection: "column",
        justifyContent: justify,
        alignItems: "center",
        gap,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};

const Emoji: React.FC<{ emoji?: string; size: number; delay?: number; still?: boolean }> = ({ emoji, size, delay = 0, still }) => {
  const frame = useCurrentFrame();
  if (!emoji) return null;
  const s = still ? 1 : pop(frame, delay, 9);
  const wobble = Math.sin(frame / 6) * 6;
  return <div style={{ fontSize: size, lineHeight: 1, transform: `scale(${s}) rotate(${wobble}deg)` }}>{emoji}</div>;
};

const Hook: React.FC<SceneProps<"hook">> = ({ scene, brand, frames }) => {
  const frame = useCurrentFrame();
  const { width, height, boxW, boxH } = useBox();
  // Readable on frame 0: the platforms take their automatic thumbnail there.
  const breathe = interpolate(frame, [0, frames], [1, 1.05], clamp);
  const size = fitText(brand, scene.text, { box: boxW / 1.05, lines: 5, max: width * 0.16, highlight: scene.highlight, height: boxH * (scene.emoji ? 0.62 : 0.8) });
  return (
    <>
      {scene.media && scene.media.frame === "full" ? (
        // Footage that sells by itself (a game, a flight): kept bright, a veil only behind the words.
        <AbsoluteFill>
          <MediaView media={scene.media} brand={brand} width={width} height={height} durationInFrames={frames} bare />
          <AbsoluteFill style={{ background: `linear-gradient(180deg, ${alpha(brand.colors.bg, 0.15)}, ${alpha(brand.colors.bg, 0.6)} 35%, ${alpha(brand.colors.bg, 0.6)} 65%, ${alpha(brand.colors.bg, 0.2)})` }} />
        </AbsoluteFill>
      ) : scene.media ? (
        <AbsoluteFill style={{ opacity: 0.45 }}>
          <MediaView media={{ ...scene.media, frame: "none" }} brand={brand} width={width} height={height} durationInFrames={frames} />
          <AbsoluteFill style={{ background: `linear-gradient(180deg, ${alpha(brand.colors.bg, 0.7)}, ${alpha(brand.colors.bg, 0.4)} 50%, ${alpha(brand.colors.bg, 0.85)})` }} />
        </AbsoluteFill>
      ) : null}
      <Box gap={size * 0.4}>
        <Emoji emoji={scene.emoji} size={size * 1.2} still />
        <div style={{ transform: `scale(${breathe})` }}>
          <RichText text={scene.text} highlight={scene.highlight} brand={brand} size={size} />
        </div>
      </Box>
    </>
  );
};

const Statement: React.FC<SceneProps<"statement">> = ({ scene, brand, frames }) => {
  const frame = useCurrentFrame();
  const { width, boxW, boxH } = useBox();
  const size = fitText(brand, scene.text, { box: boxW, lines: 5, max: width * 0.14, highlight: scene.highlight, strike: scene.strike, height: boxH * (scene.emoji ? 0.62 : 0.8) });
  const appear = interpolate(frame, [0, Math.min(16, frames * 0.35)], [0.15, 1], clamp);
  const strike = interpolate(frame, [frames * 0.45, frames * 0.62], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
  return (
    <Box gap={size * 0.4}>
      <Emoji emoji={scene.emoji} size={size * 1.1} />
      <RichText text={scene.text} highlight={scene.highlight} strike={scene.strike} strikeProgress={strike} appear={appear} brand={brand} size={size} />
    </Box>
  );
};

const MediaScene: React.FC<SceneProps<"media">> = ({ scene, brand, frames }) => {
  const frame = useCurrentFrame();
  const { width, height, safe, boxW, format } = useBox();
  const caption = scene.caption ?? "";
  const capSize = caption ? fitText(brand, caption, { box: boxW, lines: 2, max: width * 0.1, highlight: scene.highlight }) : 0;
  const capH = caption ? capSize * 2.5 : 0;
  // Visuals may run over the bottom interface area (text never does).
  const availH = height - safe.top - capH - (format === "9x16" ? 150 : safe.bottom);
  const m = scene.media;
  let w: number;
  let h: number;
  if (m.frame === "phone") {
    h = Math.min(availH, (boxW * 0.78) * 2.05);
    w = h / 2.05;
  } else if (m.frame === "browser") {
    w = boxW;
    h = Math.min(availH, w * 0.72);
  } else {
    w = boxW;
    h = Math.min(availH, m.aspect ? w / m.aspect : w * 1.3);
    if (m.aspect && h === availH) w = h * m.aspect;
  }
  if (m.frame === "full") return <FullMedia scene={scene} brand={brand} frames={frames} capSize={capSize} />;
  const bleed = m.frame === "none" && (m.aspect ?? 0) > 1.05;
  if (bleed) {
    w = width;
    h = width / (m.aspect as number);
  }
  const enter = pop(frame, 2, 14);
  return (
    <AbsoluteFill style={{ paddingTop: safe.top, alignItems: "center" }}>
      {bleed && (
        <AbsoluteFill style={{ filter: "blur(40px) brightness(0.45) saturate(1.2)", transform: "scale(1.2)" }}>
          <MediaView media={{ ...m, fit: "cover", zoom: "none" }} brand={brand} width={width} height={height} durationInFrames={frames} bare />
        </AbsoluteFill>
      )}
      {caption && (
        <div style={{ height: capH, width: boxW, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <RichText text={caption} highlight={scene.highlight} brand={brand} size={capSize} appear={interpolate(frame, [0, 12], [0.2, 1], clamp)} />
        </div>
      )}
      <div
        style={{
          marginTop: bleed ? Math.max(0, (availH - h) / 2) : 0,
          transform: `translateY(${(1 - enter) * height * 0.25}px) rotate(${(1 - enter) * 6}deg)`,
          opacity: interpolate(enter, [0, 0.3], [0, 1], clamp),
        }}
      >
        <MediaView media={m} brand={brand} width={w} height={h} durationInFrames={frames} bare={bleed} />
      </div>
    </AbsoluteFill>
  );
};

// The footage on the whole screen, the caption over a veil at the top (above the platforms' buttons).
const FullMedia: React.FC<SceneProps<"media"> & { capSize: number }> = ({ scene, brand, frames, capSize }) => {
  const frame = useCurrentFrame();
  const { width, height, safe, boxW } = useBox();
  const caption = scene.caption ?? "";
  return (
    <AbsoluteFill>
      <MediaView media={scene.media} brand={brand} width={width} height={height} durationInFrames={frames} bare />
      {caption && (
        <>
          <AbsoluteFill style={{ background: `linear-gradient(180deg, ${alpha(brand.colors.bg, 0.75)}, ${alpha(brand.colors.bg, 0.35)} 28%, transparent 42%)` }} />
          <div style={{ position: "absolute", top: safe.top, left: safe.left, width: boxW, display: "flex", justifyContent: "center", textAlign: "center" }}>
            <RichText text={caption} highlight={scene.highlight} brand={brand} size={capSize} appear={interpolate(frame, [0, 10], [0.2, 1], clamp)} />
          </div>
        </>
      )}
    </AbsoluteFill>
  );
};

const ListScene: React.FC<SceneProps<"list">> = ({ scene, brand, frames }) => {
  const frame = useCurrentFrame();
  const { width, boxW } = useBox();
  const longest = scene.items.reduce((a, b) => (b.length > a.length ? b : a), "");
  const itemSize = fitText(brand, longest, { box: boxW * 0.72, lines: 2, max: width * 0.075, font: "body", weight: 700 });
  const titleSize = scene.title ? fitText(brand, scene.title, { box: boxW, lines: 2, max: width * 0.115 }) : 0;
  const step = Math.max(6, Math.floor((frames * 0.55) / scene.items.length));
  const markers = { check: "✓", cross: "✕" } as const;
  return (
    <Box gap={itemSize * 0.55}>
      {scene.title && <RichText text={scene.title} brand={brand} size={titleSize} />}
      <div style={{ display: "flex", flexDirection: "column", gap: itemSize * 0.45, width: boxW, marginTop: titleSize * 0.2 }}>
        {scene.items.map((item, i) => {
          const p = pop(frame, 6 + i * step, 13);
          return (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "center",
                gap: itemSize * 0.5,
                opacity: interpolate(p, [0, 0.4], [0, 1], clamp),
                transform: `translateX(${(1 - p) * -width * 0.3}px)`,
                background: alpha(brand.colors.text, 0.08),
                border: `2px solid ${alpha(brand.colors.text, 0.14)}`,
                borderRadius: itemSize * 0.5,
                padding: `${itemSize * 0.35}px ${itemSize * 0.5}px`,
              }}
            >
              <div
                style={{
                  flex: "none",
                  width: itemSize * 1.25,
                  height: itemSize * 1.25,
                  borderRadius: itemSize,
                  background: brand.colors.accent,
                  color: brand.colors.accentText,
                  fontFamily: brand.fonts.display,
                  fontWeight: 800,
                  fontSize: itemSize * 0.75,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                {scene.marker === "number" ? i + 1 : markers[scene.marker]}
              </div>
              <div style={{ fontFamily: brand.fonts.body, fontWeight: 700, fontSize: itemSize, lineHeight: 1.15, color: brand.colors.text }}>
                {item}
              </div>
            </div>
          );
        })}
      </div>
    </Box>
  );
};

const StatScene: React.FC<SceneProps<"stat"> & { language: string }> = ({ scene, brand, frames, language }) => {
  const frame = useCurrentFrame();
  const { width, boxW } = useBox();
  const value = interpolate(frame, [4, frames * 0.6], [0, scene.value], { ...clamp, easing: Easing.out(Easing.exp) });
  const shown = `${scene.prefix}${value.toLocaleString(language, { minimumFractionDigits: scene.decimals, maximumFractionDigits: scene.decimals })}${scene.suffix}`;
  const final = `${scene.prefix}${scene.value.toLocaleString(language)}${scene.suffix}`;
  const size = fitText(brand, final, { box: boxW, lines: 1, max: width * 0.34, weight: 900 });
  const labelSize = fitText(brand, scene.label, { box: boxW, lines: 3, max: width * 0.085, font: "body" });
  const land = pop(frame, frames * 0.6, 8);
  return (
    <Box gap={labelSize * 0.6}>
      <div
        style={{
          fontFamily: brand.fonts.display,
          fontWeight: 900,
          fontSize: size,
          lineHeight: 1,
          color: brand.colors.accent,
          letterSpacing: -size * 0.04,
          fontVariantNumeric: "tabular-nums",
          transform: `scale(${1 + 0.08 * Math.sin(land * Math.PI)})`,
        }}
      >
        {shown}
      </div>
      <RichText text={scene.label} brand={brand} size={labelSize} font="body" appear={interpolate(frame, [6, 20], [0, 1], clamp)} />
    </Box>
  );
};

const Reveal: React.FC<SceneProps<"reveal">> = ({ scene, brand }) => {
  const frame = useCurrentFrame();
  const { width, boxW } = useBox();
  const p = pop(frame, 0, 10);
  const ring = interpolate(frame, [0, 22], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
  const size = fitText(brand, scene.tagline, { box: boxW, lines: 3, max: width * 0.1, font: "body" });
  return (
    <>
      <Fill>
        <div
          style={{
            width: width * 1.4 * ring,
            height: width * 1.4 * ring,
            borderRadius: width,
            border: `${width * 0.02}px solid ${brand.colors.accent}`,
            opacity: 1 - ring,
          }}
        />
      </Fill>
      <Box gap={size * 0.7}>
        <div style={{ transform: `scale(${p})` }}>
          <Logo brand={brand} size={width * 0.16} />
        </div>
        <RichText text={scene.tagline} brand={brand} size={size} font="body" appear={interpolate(frame, [10, 24], [0, 1], clamp)} />
      </Box>
    </>
  );
};

const Cta: React.FC<SceneProps<"cta">> = ({ scene, brand }) => {
  const frame = useCurrentFrame();
  const { width, boxW } = useBox();
  const size = fitText(brand, scene.text, { box: boxW, lines: 4, max: width * 0.125 });
  const btnSize = fitText(brand, scene.button, { box: boxW * 0.7, lines: 1, max: width * 0.075 });
  const pulse = 1 + 0.04 * Math.sin(frame / 4);
  const p = pop(frame, 8, 10);
  return (
    <Box gap={size * 0.55}>
      <RichText text={scene.text} brand={brand} size={size} appear={interpolate(frame, [0, 12], [0.2, 1], clamp)} />
      <div
        style={{
          transform: `scale(${p * pulse})`,
          background: brand.colors.accent,
          color: brand.colors.accentText,
          fontFamily: brand.fonts.display,
          fontWeight: 800,
          fontSize: btnSize,
          padding: `${btnSize * 0.5}px ${btnSize * 1.1}px`,
          borderRadius: btnSize * 2,
          boxShadow: `0 ${btnSize * 0.3}px ${btnSize}px ${alpha(brand.colors.accent, 0.45)}`,
        }}
      >
        {scene.button}
      </div>
      {(scene.url || brand.handle) && (scene.url ?? brand.handle) !== scene.button && (
        <div style={{ fontFamily: brand.fonts.body, fontWeight: 600, fontSize: btnSize * 0.75, color: brand.colors.muted, opacity: interpolate(frame, [14, 24], [0, 1], clamp) }}>
          {scene.url ?? brand.handle}
        </div>
      )}
      <div style={{ marginTop: size * 0.2, opacity: 0.9 }}>
        <Logo brand={brand} size={width * 0.075} />
      </div>
    </Box>
  );
};

// Every scene but the first enters with a short punch-in (hard cuts keep the pace).
const Enter: React.FC<{ children: React.ReactNode; first: boolean }> = ({ children, first }) => {
  const frame = useCurrentFrame();
  if (first) return <AbsoluteFill>{children}</AbsoluteFill>;
  const t = interpolate(frame, [0, 6], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
  return (
    <AbsoluteFill style={{ opacity: t, transform: `scale(${1.08 - 0.08 * t})`, filter: `blur(${(1 - t) * 10}px)` }}>
      {children}
    </AbsoluteFill>
  );
};

const SceneView: React.FC<{ scene: Scene; brand: Brand; frames: number; language: string }> = ({ scene, brand, frames, language }) => {
  switch (scene.type) {
    case "hook":
      return <Hook scene={scene} brand={brand} frames={frames} />;
    case "statement":
      return <Statement scene={scene} brand={brand} frames={frames} />;
    case "media":
      return <MediaScene scene={scene} brand={brand} frames={frames} />;
    case "list":
      return <ListScene scene={scene} brand={brand} frames={frames} />;
    case "stat":
      return <StatScene scene={scene} brand={brand} frames={frames} language={language} />;
    case "reveal":
      return <Reveal scene={scene} brand={brand} frames={frames} />;
    case "cta":
      return <Cta scene={scene} brand={brand} frames={frames} />;
  }
};

const ProgressBar: React.FC<{ brand: Brand; total: number }> = ({ brand, total }) => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();
  return (
    <div style={{ position: "absolute", top: 0, left: 0, height: Math.round(width * 0.009), width: `${((frame + 1) / total) * 100}%`, background: brand.colors.accent }} />
  );
};

export const Short: React.FC<ShortProps> = (raw) => {
  // Remotion checks props against the schema but passes them as given: apply the defaults.
  const props = useMemo(() => shortSchema.parse(raw), [raw]);
  const { brand, scenes, music, voice, sounds, progressBar, language } = props;
  useBrandFonts(brand);
  const total = totalFrames(scenes);
  let from = 0;
  const sequences = scenes.map((scene, i) => {
    const frames = sceneFrames(scene);
    const seq = (
      <Sequence key={i} from={from} durationInFrames={frames} name={`${i + 1}. ${scene.type}`}>
        <Enter first={i === 0}>
          <SceneView scene={scene} brand={brand} frames={frames} language={language} />
        </Enter>
      </Sequence>
    );
    from += frames;
    return seq;
  });
  const fade = (f: number) => interpolate(f, [0, 8, total - 24, total], [0, 1, 1, 0], clamp);
  return (
    <AbsoluteFill style={{ backgroundColor: brand.colors.bg, overflow: "hidden" }}>
      <Background brand={brand} />
      {sequences}
      {progressBar && <ProgressBar brand={brand} total={total} />}
      {music && (
        <Audio
          src={src(music.file)}
          trimBefore={Math.round(music.trimBefore * 30)}
          volume={(f) => fade(f) * music.volume * (voice ? 0.32 : 1)}
        />
      )}
      {voice && <Audio src={src(voice.file)} volume={voice.volume} />}
      {sounds.map((s, i) => (
        <Sequence key={`sfx${i}`} from={Math.round(s.at * 30)} durationInFrames={s.duration ? Math.round(s.duration * 30) : undefined} name={`sound ${s.file}`}>
          <Audio src={src(s.file)} trimBefore={Math.round(s.trimBefore * 30)} volume={s.volume} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
