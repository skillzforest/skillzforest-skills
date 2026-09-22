import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { useAppData } from "../store/AppContext";
import { skillzforest } from "../services/tauri";
import type { CatalogPack } from "../types/pack";
import type { PackInstallOutcome } from "../types/pack";
import { RuntimeBadge } from "../components/RuntimeBadge";

export function PackDetails() {
  const { packId } = useParams<{ packId: string }>();
  const { skills, runtimes, refresh } = useAppData();
  const [pack, setPack] = useState<CatalogPack | null>(null);
  const [selectedRuntime, setSelectedRuntime] = useState<string | null>(null);
  const [installing, setInstalling] = useState(false);
  const [outcome, setOutcome] = useState<PackInstallOutcome | null>(null);

  useEffect(() => {
    if (!packId) return;
    void skillzforest.getPack(packId).then(setPack);
  }, [packId]);

  const compatibleRuntimeIds = useMemo(() => {
    if (!pack) return [];
    const ids = new Set<string>();
    for (const skillId of pack.manifest.skills) {
      const skill = skills.find((s) => s.manifest.id === skillId);
      if (!skill) continue;
      for (const [runtimeId, status] of Object.entries(skill.manifest.compatibility)) {
        if (status === "native" || status === "supported" || status === "adapted") ids.add(runtimeId);
      }
    }
    return Array.from(ids);
  }, [pack, skills]);

  if (!pack) return <p className="empty-state">Loading…</p>;

  const nameFor = (id: string) => runtimes.find((r) => r.runtime.id === id)?.runtime.name ?? id;

  async function handleInstall() {
    if (!packId || !selectedRuntime) return;
    setInstalling(true);
    try {
      const result = await skillzforest.installPack(packId, selectedRuntime);
      setOutcome(result);
      await refresh();
    } finally {
      setInstalling(false);
    }
  }

  return (
    <div style={{ maxWidth: 640 }}>
      <h1 className="page-title">{pack.manifest.name}</h1>
      <p className="page-subtitle">{pack.manifest.description}</p>

      <div className="card" style={{ marginBottom: 16 }}>
        <p className="card-title">{pack.manifest.skills.length} Skills</p>
        <p className="card-subtitle">Compatible with</p>
        <div className="badge-row">
          {compatibleRuntimeIds.map((id) => (
            <RuntimeBadge key={id} name={nameFor(id)} variant="default" />
          ))}
        </div>
      </div>

      {outcome ? (
        <div className="card">
          <p className="card-title">
            Installing {pack.manifest.name} — {nameFor(outcome.runtimeId)}
          </p>
          <p className="status-line status-ok">{outcome.installed.length} skills installed</p>
          {outcome.skipped.length > 0 && (
            <p className="status-line status-warn">{outcome.skipped.length} skill(s) skipped</p>
          )}
          {outcome.skipped.map((s) => (
            <div key={s.skillId} className="checklist-item">
              <span style={{ flex: 1 }}>{s.skillId}</span>
              <span className="card-subtitle" style={{ margin: 0 }}>
                {s.reason}
              </span>
            </div>
          ))}
        </div>
      ) : (
        <div className="card">
          <p className="card-title">Install this pack for</p>
          {compatibleRuntimeIds.map((id) => (
            <label key={id} className="checklist-item">
              <input
                type="radio"
                name="pack-runtime"
                checked={selectedRuntime === id}
                onChange={() => setSelectedRuntime(id)}
              />
              <span>{nameFor(id)}</span>
            </label>
          ))}
          <button
            className="btn"
            style={{ marginTop: 16 }}
            disabled={!selectedRuntime || installing}
            onClick={() => void handleInstall()}
          >
            {installing ? "Installing…" : "Install Pack"}
          </button>
        </div>
      )}
    </div>
  );
}
