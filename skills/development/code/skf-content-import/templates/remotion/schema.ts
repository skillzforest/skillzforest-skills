import { z } from "zod";

// Every text and color comes from props: one template, any brand, any product.
export const brandSchema = z.object({
  background: z.string(), // CSS background: a color or a gradient
  surface: z.string(), // cards, the terminal
  text: z.string(),
  muted: z.string(),
  accent: z.string(),
  fontFamily: z.string(),
  wordmark: z.string(), // site or brand name shown in the corner
});

export const productSchema = z.object({
  brand: brandSchema,
  kind: z.enum(["skill", "pack"]),
  name: z.string(),
  headline: z.string(),
  // Skill: up to 3 benefits. Pack: its skills, in order (shown as numbered steps).
  points: z.array(z.string()).max(8),
  // The example prompt typed in the terminal scene.
  prompt: z.string(),
  promptLabel: z.string(), // e.g. "Dans Claude Code" / "In Claude Code"
  pointsTitle: z.string(), // e.g. "Ce que vous obtenez" / "The skills, in order"
  cta: z.string(), // e.g. "Disponible sur SkillzForest"
  // 1–2 characters or an emoji: the emblem on the cover image.
  glyph: z.string().max(4),
});

export type Brand = z.infer<typeof brandSchema>;
export type ProductProps = z.infer<typeof productSchema>;

export const stillSchema = productSchema.extend({
  variant: z.enum(["cover", "poster", "outcome"]),
  // Outcome images: the block's own title.
  title: z.string(),
});

export type StillProps = z.infer<typeof stillSchema>;

export const FPS = 30;
export const SCENES = { title: 90, prompt: 150, points: 120, outro: 90 } as const;
export const HERO_DURATION =
  SCENES.title + SCENES.prompt + SCENES.points + SCENES.outro;
