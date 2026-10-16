// Standalone entry point: render these compositions without touching the host
// project's own Root — `npx remotion render <this folder>/index.ts ProductHero …`.
import React from "react";
import { Composition, Still, registerRoot } from "remotion";
import { ProductHero } from "./ProductHero";
import { ProductStill } from "./ProductStill";
import { FPS, HERO_DURATION, ProductProps, StillProps, productSchema, stillSchema } from "./schema";

const defaults: ProductProps = {
  brand: {
    background: "linear-gradient(160deg, #13262F 0%, #1E464E 60%, #236A62 100%)",
    surface: "#192E3A",
    text: "#FFFFFF",
    muted: "#BCCACC",
    accent: "#43C891",
    fontFamily: "Inter, system-ui, -apple-system, sans-serif",
    wordmark: "Brand",
  },
  kind: "skill",
  name: "Product name",
  headline: "One sentence: what it does for you.",
  points: ["First benefit", "Second benefit", "Third benefit"],
  prompt: "Use my-skill on the files in docs/ and write a summary.",
  promptLabel: "In Claude Code",
  pointsTitle: "What you get",
  cta: "Available now",
  glyph: "P",
};

const stillDefaults: StillProps = { ...defaults, variant: "cover", title: "" };

const Root: React.FC = () =>
  React.createElement(
    React.Fragment,
    null,
    React.createElement(Composition, {
      id: "ProductHero",
      component: ProductHero,
      schema: productSchema,
      durationInFrames: HERO_DURATION,
      fps: FPS,
      width: 1920,
      height: 1080,
      defaultProps: defaults,
    }),
    React.createElement(Still, {
      id: "ProductCover",
      component: ProductStill,
      schema: stillSchema,
      width: 1024,
      height: 1024,
      defaultProps: { ...stillDefaults, variant: "cover" as const },
    }),
    React.createElement(Still, {
      id: "ProductPoster",
      component: ProductStill,
      schema: stillSchema,
      width: 1920,
      height: 1080,
      defaultProps: { ...stillDefaults, variant: "poster" as const },
    }),
    React.createElement(Still, {
      id: "ProductOutcome",
      component: ProductStill,
      schema: stillSchema,
      width: 1600,
      height: 800,
      defaultProps: { ...stillDefaults, variant: "outcome" as const },
    }),
  );

registerRoot(Root);
