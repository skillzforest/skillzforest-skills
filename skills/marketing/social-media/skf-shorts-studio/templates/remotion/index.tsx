// Standalone entry point: rendered without touching the host project's own Root —
// npx remotion render <this folder>/index.tsx Short9x16 out.mp4 --props=storyboard.props.json --public-dir=<short>/assets
import React from "react";
import { CalculateMetadataFunction, Composition, Still, registerRoot } from "remotion";
import { Cover } from "./Cover";
import { Short } from "./Short";
import { FORMATS, FPS, ShortProps, shortSchema, totalFrames } from "./schema";

const sample: ShortProps = {
  language: "fr",
  brand: {
    name: "Acme",
    colors: { bg: "#0E1525", bg2: "#1D2B53", text: "#FFFFFF", muted: "#B8C1DA", accent: "#FFD23F", accentText: "#0E1525" },
    fonts: { display: "Inter, system-ui, sans-serif", body: "Inter, system-ui, sans-serif" },
    fontFiles: [],
    handle: "acme.app",
  },
  scenes: [
    { type: "hook", duration: 2, text: "Tes devis te prennent 3 heures ?", highlight: "3 heures", emoji: "😩" },
    { type: "statement", duration: 2.5, text: "Copier, coller, recalculer… à la main", strike: "à la main" },
    { type: "reveal", duration: 2, tagline: "Acme écrit le devis à ta place" },
    { type: "list", duration: 3.5, title: "En 30 secondes", items: ["Tu décris le projet", "Acme chiffre", "Tu envoies"], marker: "number" },
    { type: "stat", duration: 2.5, value: 3, suffix: " h", label: "rendues chaque semaine", decimals: 0, prefix: "" },
    { type: "cta", duration: 3, text: "Essaie-le sur ton prochain devis", button: "acme.app" },
  ],
  progressBar: true,
  cover: { title: "Tes devis en 30 secondes", highlight: "30 secondes", badge: "Nouveau", kicker: "Acme" },
};

const withDuration: CalculateMetadataFunction<ShortProps> = ({ props }) => ({
  durationInFrames: totalFrames(props.scenes),
});

const shorts = (["9x16", "4x5", "1x1"] as const).map((f) => (
  <Composition
    key={f}
    id={`Short${f}`}
    component={Short}
    schema={shortSchema}
    fps={FPS}
    durationInFrames={totalFrames(sample.scenes)}
    calculateMetadata={withDuration}
    width={FORMATS[f].width}
    height={FORMATS[f].height}
    defaultProps={sample}
  />
));

const covers = (["9x16", "4x5", "1x1", "16x9"] as const).map((f) => (
  <Still
    key={f}
    id={f === "16x9" ? "Thumb16x9" : `Cover${f}`}
    component={Cover}
    schema={shortSchema}
    width={FORMATS[f].width}
    height={FORMATS[f].height}
    defaultProps={sample}
  />
));

const Root: React.FC = () => (
  <>
    {shorts}
    {covers}
  </>
);

registerRoot(Root);
