import { z } from "zod";

// Every text, color, font and file comes from props (storyboard.json): one template,
// any brand, any idea. Files are relative to the short's assets/ folder, rendered with
// --public-dir, or absolute http(s) URLs.

export const brandSchema = z.object({
  name: z.string(),
  colors: z.object({
    bg: z.string(), // main background
    bg2: z.string(), // second gradient stop
    text: z.string(), // text on bg
    muted: z.string(), // secondary text on bg
    accent: z.string(), // highlight blocks, buttons, progress bar
    accentText: z.string(), // text written on the accent color
  }),
  fonts: z.object({
    display: z.string(), // CSS font-family of titles
    body: z.string(), // CSS font-family of everything else
  }),
  fontFiles: z
    .array(z.object({ family: z.string(), file: z.string(), weight: z.string().optional() }))
    .default([]),
  logo: z.string().optional(), // file (SVG or PNG) readable on bg
  handle: z.string().optional(), // @account or domain shown on the end card
  pattern: z.enum(["grid", "dots", "none"]).default("grid"), // faint texture of the background
});

export const mediaSchema = z.object({
  file: z.string(),
  kind: z.enum(["image", "video"]),
  frame: z.enum(["phone", "browser", "none"]).default("none"),
  zoom: z.enum(["in", "out", "none"]).default("in"),
  fit: z.enum(["cover", "contain"]).default("cover"),
  // width / height of the file (kit.json assets): frames a landscape clip without cropping it.
  aspect: z.number().positive().optional(),
  // Video only: seconds skipped at the start of the clip.
  trimBefore: z.number().min(0).default(0),
});

const base = { duration: z.number().min(0.6).max(15) }; // seconds

export const sceneSchema = z.discriminatedUnion("type", [
  // First scene: fully readable on frame 0 (it doubles as the automatic thumbnail).
  z.object({
    ...base,
    type: z.literal("hook"),
    text: z.string(),
    highlight: z.string().optional(),
    emoji: z.string().optional(),
    media: mediaSchema.optional(), // dimmed background
  }),
  z.object({
    ...base,
    type: z.literal("statement"),
    text: z.string(),
    highlight: z.string().optional(),
    strike: z.string().optional(), // words crossed out after a beat
    emoji: z.string().optional(),
  }),
  z.object({
    ...base,
    type: z.literal("media"),
    media: mediaSchema,
    caption: z.string().optional(),
    highlight: z.string().optional(),
  }),
  z.object({
    ...base,
    type: z.literal("list"),
    title: z.string().optional(),
    items: z.array(z.string()).min(2).max(4),
    marker: z.enum(["check", "number", "cross"]).default("check"),
  }),
  z.object({
    ...base,
    type: z.literal("stat"),
    value: z.number(),
    decimals: z.number().int().min(0).max(2).default(0),
    prefix: z.string().default(""),
    suffix: z.string().default(""),
    label: z.string(),
  }),
  z.object({
    ...base,
    type: z.literal("reveal"),
    tagline: z.string(),
  }),
  z.object({
    ...base,
    type: z.literal("cta"),
    text: z.string(),
    button: z.string(),
    url: z.string().optional(),
  }),
]);

export const coverSchema = z.object({
  title: z.string(), // 2–5 words, the hook's promise
  highlight: z.string().optional(), // one word of the title, on the accent block
  kicker: z.string().optional(), // small line above the title
  badge: z.string().optional(), // rotated sticker: "NOUVEAU", "EN 20 S"…
  visual: mediaSchema.optional(), // product screenshot, photo, or a video frame
});

export const shortSchema = z.object({
  language: z.string().default("fr"),
  brand: brandSchema,
  scenes: z.array(sceneSchema).min(2).max(12),
  music: z
    .object({
      file: z.string(),
      volume: z.number().min(0).max(1).default(0.55),
      trimBefore: z.number().min(0).default(0),
    })
    .optional(),
  voice: z.object({ file: z.string(), volume: z.number().min(0).max(2).default(1) }).optional(),
  progressBar: z.boolean().default(true),
  cover: coverSchema,
});

export type Brand = z.infer<typeof brandSchema>;
export type Media = z.infer<typeof mediaSchema>;
export type Scene = z.infer<typeof sceneSchema>;
export type ShortProps = z.infer<typeof shortSchema>;

export const FPS = 30;

export const FORMATS = {
  "9x16": { width: 1080, height: 1920 },
  "4x5": { width: 1080, height: 1350 },
  "1x1": { width: 1080, height: 1080 },
  "16x9": { width: 1280, height: 720 },
} as const;
export type FormatId = keyof typeof FORMATS;

// Areas covered by the platforms' interface (buttons, caption, account name), in px of
// a 1080×1920 frame. Text stays out of them; feed formats only keep a small margin.
export const SAFE: Record<FormatId, { top: number; bottom: number; left: number; right: number }> = {
  "9x16": { top: 240, bottom: 440, left: 72, right: 150 },
  "4x5": { top: 80, bottom: 110, left: 72, right: 72 },
  "1x1": { top: 70, bottom: 90, left: 72, right: 72 },
  "16x9": { top: 50, bottom: 50, left: 64, right: 64 },
};

export const sceneFrames = (scene: Scene) => Math.max(1, Math.round(scene.duration * FPS));
export const totalFrames = (scenes: Scene[]) => scenes.reduce((sum, s) => sum + sceneFrames(s), 0);
