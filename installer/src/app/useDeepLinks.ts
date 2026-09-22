import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { listen } from "@tauri-apps/api/event";

/**
 * Listens for the `skillzforest://deep-link` event `main.rs` emits whenever
 * the OS hands this app a `skillzforest://` URL (cold start or already
 * running). Parses the two supported forms and navigates straight to the
 * matching detail screen — this is what lets "Install" on SkillzForest.com
 * open the app directly on the right page instead of just launching it.
 */
export function useDeepLinks() {
  const navigate = useNavigate();

  useEffect(() => {
    const unlisten = listen<string>("skillzforest://deep-link", (event) => {
      const target = parseDeepLink(event.payload);
      if (target) navigate(target);
    });
    return () => {
      void unlisten.then((fn) => fn());
    };
  }, [navigate]);
}

export function parseDeepLink(url: string): string | null {
  let parsed: URL;
  try {
    parsed = new URL(url);
  } catch {
    return null;
  }
  if (parsed.protocol !== "skillzforest:") return null;

  // Tauri/OS URL parsing can put "install" in either .hostname or the first
  // path segment depending on platform — handle both.
  const segments = [parsed.hostname, ...parsed.pathname.split("/")].filter(Boolean);
  const [action, id] = segments;
  if (action === "install" && id) return `/skills/${id}`;
  if (action === "install-pack" && id) return `/packs/${id}`;
  return null;
}
