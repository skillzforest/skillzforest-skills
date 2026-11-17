import React, { useEffect, useState } from "react";
import {
  AbsoluteFill,
  Img,
  OffthreadVideo,
  continueRender,
  delayRender,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Brand, FormatId, FPS, Media, SAFE } from "./schema";

export const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

export const src = (file: string) => (/^(https?:|data:)/.test(file) ? file : staticFile(file));

// Brand fonts shipped as files (woff2, ttf…): loaded before the first frame. Returns
// true once they are in, so the component re-renders and measures text with them.
export const useBrandFonts = (brand: Brand) => {
  const [handle] = useState(() => (brand.fontFiles.length ? delayRender("brand fonts") : null));
  const [ready, setReady] = useState(handle === null);
  useEffect(() => {
    if (handle === null) return;
    Promise.all(
      brand.fontFiles.map((f) =>
        new FontFace(f.family, `url(${src(f.file)})`, { weight: f.weight ?? "400" })
          .load()
          .then((face) => document.fonts.add(face)),
      ),
    )
      .catch((err) => console.warn("font not loaded", err))
      .finally(() => {
        setReady(true);
        continueRender(handle);
      });
  }, [brand, handle]);
  return ready;
};

export const useFormat = (): { format: FormatId; width: number; height: number; safe: (typeof SAFE)[FormatId] } => {
  const { width, height } = useVideoConfig();
  const ratio = width / height;
  const format: FormatId = ratio < 0.7 ? "9x16" : ratio < 0.9 ? "4x5" : ratio < 1.2 ? "1x1" : "16x9";
  return { format, width, height, safe: SAFE[format] };
};

// Text styles shared by RichText and fitText (they must agree for the measure to hold).
export const TYPE = {
  display: { weight: 800, tracking: -0.025 },
  body: { weight: 600, tracking: 0 },
  gap: 0.26, // space between words, in em
  pad: 0.32, // horizontal padding of the highlight block, in em
  lineHeight: 1.12,
  rowGap: 0.12,
} as const;

let canvas: CanvasRenderingContext2D | null = null;
const context = () => {
  if (!canvas && typeof document !== "undefined") canvas = document.createElement("canvas").getContext("2d");
  return canvas;
};

export type Fit = {
  box: number; // width available, px
  lines: number; // most lines allowed
  max: number; // largest size wanted, px
  min?: number;
  height?: number; // height available, px
  highlight?: string;
  strike?: string;
  font?: "display" | "body";
  weight?: number;
};

// Largest font size (px) at which `text`, wrapped word by word like RichText, fits the
// box: measured in the browser with the brand's real font (loaded by useBrandFonts).
export const fitText = (brand: Brand, text: string, o: Fit) => {
  const kind = o.font ?? "display";
  const family = kind === "display" ? brand.fonts.display : brand.fonts.body;
  const weight = o.weight ?? TYPE[kind].weight;
  const units = toUnits(splitMarked(text, o.highlight, o.strike));
  const min = o.min ?? 34;
  const ctx = context();
  const box = o.box * 0.97;
  const fits = (size: number) => {
    if (!ctx) return size <= (0.85 * box * o.lines) / (0.56 * Math.max(text.length, 1));
    ctx.font = `${weight} ${size}px ${family}`;
    (ctx as unknown as { letterSpacing: string }).letterSpacing = `${TYPE[kind].tracking * size}px`;
    let lines = 1;
    let line = 0;
    for (const u of units) {
      const w = ctx.measureText(u.w).width + (u.kind === "highlight" ? TYPE.pad * size : 0);
      if (w > box) return false;
      const next = line === 0 ? w : line + TYPE.gap * size + w;
      if (next > box) {
        lines += 1;
        line = w;
      } else line = next;
    }
    if (lines > o.lines) return false;
    return !o.height || lines * size * TYPE.lineHeight + (lines - 1) * size * TYPE.rowGap <= o.height;
  };
  if (!fits(min)) return min;
  let lo = min;
  let hi = o.max;
  if (fits(hi)) return Math.floor(hi);
  while (hi - lo > 1) {
    const mid = (lo + hi) / 2;
    if (fits(mid)) lo = mid;
    else hi = mid;
  }
  return Math.floor(lo);
};

// Any CSS color with an opacity, without parsing it.
export const alpha = (color: string, a: number) =>
  `color-mix(in srgb, ${color} ${Math.round(a * 100)}%, transparent)`;

export const pop = (frame: number, delay = 0, damping = 12) =>
  spring({ frame: frame - delay, fps: FPS, config: { damping, stiffness: 180, mass: 0.6 } });

// Animated brand background: gradient, two slow accent glows, a faint grid or dots.
export const Background: React.FC<{ brand: Brand; still?: boolean }> = ({ brand, still }) => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();
  const t = still ? 40 : frame;
  const x1 = 20 + 12 * Math.sin(t / 50);
  const y1 = 18 + 8 * Math.cos(t / 65);
  const x2 = 80 + 10 * Math.cos(t / 55);
  const y2 = 82 + 8 * Math.sin(t / 45);
  const c = brand.colors;
  const cell = Math.round(width / 12);
  const line = alpha(c.text, 0.05);
  const kind = brand.pattern ?? "grid";
  const pattern =
    kind === "grid"
      ? `linear-gradient(${line} 2px, transparent 2px), linear-gradient(90deg, ${line} 2px, transparent 2px)`
      : kind === "dots"
        ? `radial-gradient(${alpha(c.text, 0.09)} 2.5px, transparent 3px)`
        : "none";
  return (
    <>
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at ${x1}% ${y1}%, ${alpha(c.accent, 0.28)} 0%, transparent 42%),
            radial-gradient(circle at ${x2}% ${y2}%, ${alpha(c.accent, 0.2)} 0%, transparent 38%),
            linear-gradient(160deg, ${c.bg} 0%, ${c.bg2} 100%)`,
        }}
      />
      {pattern !== "none" && (
        <AbsoluteFill
          style={{
            backgroundImage: pattern,
            backgroundSize: `${cell}px ${cell}px`,
            backgroundPosition: `0px ${-(t * 0.6) % cell}px`,
            maskImage: "radial-gradient(ellipse at 50% 45%, black 20%, transparent 75%)",
          }}
        />
      )}
    </>
  );
};

// Text where one word or phrase sits on an accent block, and another can be struck.
export const RichText: React.FC<{
  text: string;
  brand: Brand;
  size: number;
  highlight?: string;
  strike?: string;
  strikeProgress?: number;
  appear?: number; // 0..1, words pop in one after the other; 1 = all visible
  align?: "left" | "center";
  color?: string;
  font?: "display" | "body";
}> = ({ text, brand, size, highlight, strike, strikeProgress = 0, appear = 1, align = "center", color, font = "display" }) => {
  const words = toUnits(splitMarked(text, highlight, strike));
  return (
    <div
      style={{
        fontFamily: font === "display" ? brand.fonts.display : brand.fonts.body,
        fontWeight: TYPE[font].weight,
        fontSize: size,
        lineHeight: TYPE.lineHeight,
        letterSpacing: TYPE[font].tracking * size,
        color: color ?? brand.colors.text,
        textAlign: align,
        display: "flex",
        flexWrap: "wrap",
        justifyContent: align === "center" ? "center" : "flex-start",
        columnGap: size * TYPE.gap,
        rowGap: size * TYPE.rowGap,
        textShadow: "0 4px 24px rgba(0,0,0,0.25)",
      }}
    >
      {words.map(({ w, kind }, i) => {
        const shown = Math.max(0, Math.min(1, appear * words.length - i));
        const style: React.CSSProperties = {
          display: "inline-block",
          whiteSpace: "nowrap",
          opacity: shown,
          transform: `translateY(${(1 - shown) * size * 0.35}px) scale(${0.85 + 0.15 * shown})`,
          position: "relative",
        };
        if (kind === "highlight") {
          Object.assign(style, {
            background: brand.colors.accent,
            color: brand.colors.accentText,
            padding: `0 ${(size * TYPE.pad) / 2}px`,
            borderRadius: size * 0.14,
            transform: `${style.transform} rotate(-2deg)`,
            textShadow: "none",
          });
        }
        return (
          <span key={i} style={style}>
            {w}
            {kind === "strike" && (
              <span
                style={{
                  position: "absolute",
                  left: -size * 0.05,
                  top: "52%",
                  height: size * 0.12,
                  width: `${strikeProgress * 110}%`,
                  background: brand.colors.accent,
                  borderRadius: size,
                  transform: "rotate(-4deg)",
                }}
              />
            )}
          </span>
        );
      })}
    </div>
  );
};

type Part = { text: string; kind: "plain" | "highlight" | "strike" };

// Words that animate and wrap as one: plain text word by word, a highlighted or struck
// phrase whole, and punctuation (« ? », « ! », « : ») glued to the word before it.
const toUnits = (parts: Part[]) => {
  const units: { w: string; kind: Part["kind"] }[] = [];
  for (const p of parts) {
    // A no-break space (U+00A0) keeps words on one line: « 6 juin 1944 ».
    const pieces = p.kind === "plain" ? p.text.split(/[^\S\u00A0]+/).filter(Boolean) : [p.text.trim()];
    pieces.forEach((w, i) => {
      // Punctuation stays with the word before it: after a space in the text (French « ? », « : ») with a
      // no-break space, right after a marked phrase (« bombe. ») with none.
      const tight = i === 0 && p.kind === "plain" && !/^\s/.test(p.text);
      if (/^[?!:;.,…»)]+$/.test(w) && units.length) units[units.length - 1].w += (tight ? "" : "\u00A0") + w;
      else units.push({ w, kind: p.kind });
    });
  }
  return units;
};

const splitMarked = (text: string, highlight?: string, strike?: string): Part[] => {
  let parts: Part[] = [{ text, kind: "plain" }];
  for (const [needle, kind] of [
    [highlight, "highlight"],
    [strike, "strike"],
  ] as const) {
    if (!needle) continue;
    parts = parts.flatMap((p) => {
      if (p.kind !== "plain") return [p];
      const at = p.text.toLowerCase().indexOf(needle.toLowerCase());
      if (at < 0) return [p];
      return [
        { text: p.text.slice(0, at), kind: "plain" as const },
        { text: p.text.slice(at, at + needle.length), kind },
        { text: p.text.slice(at + needle.length), kind: "plain" as const },
      ].filter((x) => x.text.trim());
    });
  }
  return parts;
};

// A screenshot or clip, optionally inside a phone or browser frame, with a slow zoom.
export const MediaView: React.FC<{
  media: Media;
  brand: Brand;
  width: number;
  height: number;
  durationInFrames: number;
  still?: boolean;
  bare?: boolean; // no border, no shadow, no rounded corners (full-bleed clip)
}> = ({ media, brand, width, height, durationInFrames, still, bare }) => {
  const frame = useCurrentFrame();
  const progress = still ? 0.5 : interpolate(frame, [0, durationInFrames], [0, 1], clamp);
  const scale = media.zoom === "in" ? 1 + 0.12 * progress : media.zoom === "out" ? 1.12 - 0.12 * progress : 1;
  const focus = `${media.focusX * 100}% ${media.focusY * 100}%`;
  const fill: React.CSSProperties = { width: "100%", height: "100%", objectFit: media.fit, objectPosition: focus, transform: `scale(${scale})`, transformOrigin: focus };
  const inner =
    media.kind === "video" ? (
      <OffthreadVideo
        src={src(media.file)}
        muted
        trimBefore={Math.round(media.trimBefore * FPS)}
        style={fill}
      />
    ) : (
      <Img
        src={src(media.file)}
        style={fill}
      />
    );

  if (media.frame === "phone") {
    const bezel = Math.round(width * 0.035);
    return (
      <div
        style={{
          width,
          height,
          borderRadius: width * 0.13,
          padding: bezel,
          background: "#0B0B0F",
          boxShadow: `0 ${width * 0.08}px ${width * 0.2}px rgba(0,0,0,0.45), 0 0 0 ${bezel * 0.25}px #2A2A33`,
          position: "relative",
        }}
      >
        <div style={{ width: "100%", height: "100%", borderRadius: width * 0.1, overflow: "hidden", background: "#000" }}>
          {inner}
        </div>
        <div
          style={{
            position: "absolute",
            top: bezel + width * 0.03,
            left: "50%",
            width: width * 0.28,
            height: width * 0.075,
            marginLeft: -width * 0.14,
            borderRadius: width,
            background: "#0B0B0F",
          }}
        />
      </div>
    );
  }
  if (media.frame === "browser") {
    const bar = Math.round(width * 0.075);
    return (
      <div
        style={{
          width,
          height,
          borderRadius: width * 0.035,
          overflow: "hidden",
          background: "#fff",
          boxShadow: `0 ${width * 0.05}px ${width * 0.14}px rgba(0,0,0,0.45)`,
        }}
      >
        <div style={{ height: bar, background: "#ECECF1", display: "flex", alignItems: "center", gap: bar * 0.22, paddingLeft: bar * 0.4 }}>
          {["#FF5F57", "#FEBC2E", "#28C840"].map((c) => (
            <div key={c} style={{ width: bar * 0.28, height: bar * 0.28, borderRadius: bar, background: c }} />
          ))}
          <div style={{ flex: 1, height: bar * 0.5, margin: `0 ${bar * 0.5}px`, borderRadius: bar, background: "#fff" }} />
        </div>
        <div style={{ width: "100%", height: height - bar, overflow: "hidden" }}>{inner}</div>
      </div>
    );
  }
  if (bare || media.frame === "full") return <div style={{ width, height, overflow: "hidden" }}>{inner}</div>;
  return (
    <div
      style={{
        width,
        height,
        borderRadius: width * 0.05,
        overflow: "hidden",
        boxShadow: `0 ${width * 0.05}px ${width * 0.14}px rgba(0,0,0,0.4)`,
        outline: `${Math.max(4, width * 0.008)}px solid ${brand.colors.accent}`,
      }}
    >
      {inner}
    </div>
  );
};

export const Logo: React.FC<{ brand: Brand; size: number }> = ({ brand, size }) =>
  brand.logo ? (
    <Img src={src(brand.logo)} style={{ height: size, maxWidth: size * 5, objectFit: "contain" }} />
  ) : (
    <div
      style={{
        fontFamily: brand.fonts.display,
        fontWeight: 800,
        fontSize: size * 0.8,
        color: brand.colors.text,
        letterSpacing: -size * 0.02,
      }}
    >
      {brand.name}
    </div>
  );

export const Fill: React.FC<{ children: React.ReactNode; style?: React.CSSProperties }> = ({ children, style }) => (
  <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", ...style }}>{children}</AbsoluteFill>
);
