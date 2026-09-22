import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { skillzforest } from "../services/tauri";
import type { CatalogSkill } from "../types/skill";
import type { CatalogPack } from "../types/pack";
import type { Registry } from "../types/registry";
import type { RuntimeDetectionResult } from "../types/runtime";

interface AppData {
  skills: CatalogSkill[];
  packs: CatalogPack[];
  runtimes: RuntimeDetectionResult[];
  registry: Registry;
  loading: boolean;
  error: string | null;
  /** Re-fetches everything — used by "Rescan" and after any install/uninstall. */
  refresh: () => Promise<void>;
}

const AppDataContext = createContext<AppData | null>(null);

export function AppDataProvider({ children }: { children: ReactNode }) {
  const [skills, setSkills] = useState<CatalogSkill[]>([]);
  const [packs, setPacks] = useState<CatalogPack[]>([]);
  const [runtimes, setRuntimes] = useState<RuntimeDetectionResult[]>([]);
  const [registry, setRegistry] = useState<Registry>({ skills: {} });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [skillsRes, packsRes, runtimesRes, registryRes] = await Promise.all([
        skillzforest.listSkills(),
        skillzforest.listPacks(),
        skillzforest.detectRuntimes(),
        skillzforest.getRegistry(),
      ]);
      setSkills(skillsRes);
      setPacks(packsRes);
      setRuntimes(runtimesRes);
      setRegistry(registryRes);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const value = useMemo<AppData>(
    () => ({ skills, packs, runtimes, registry, loading, error, refresh }),
    [skills, packs, runtimes, registry, loading, error, refresh],
  );

  return <AppDataContext.Provider value={value}>{children}</AppDataContext.Provider>;
}

export function useAppData(): AppData {
  const ctx = useContext(AppDataContext);
  if (!ctx) throw new Error("useAppData must be used within AppDataProvider");
  return ctx;
}
