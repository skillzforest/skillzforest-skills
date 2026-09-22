import { useEffect, useState } from "react";
import { skillzforest } from "../services/tauri";
import { useAppData } from "../store/AppContext";
import type { UpdateStatus } from "../types/registry";

export function Updates() {
  const { runtimes, refresh } = useAppData();
  const [statuses, setStatuses] = useState<UpdateStatus[] | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const load = () => void skillzforest.checkUpdates().then(setStatuses);
  useEffect(load, []);

  const nameFor = (id: string) => runtimes.find((r) => r.runtime.id === id)?.runtime.name ?? id;

  async function updateOne(status: UpdateStatus) {
    setBusy(`${status.skillId}:${status.runtimeId}`);
    try {
      await skillzforest.updateSkill(status.skillId, status.runtimeId);
      await refresh();
      load();
    } finally {
      setBusy(null);
    }
  }

  async function updateAll() {
    if (!statuses) return;
    for (const status of statuses.filter((s) => s.updateAvailable)) {
      await updateOne(status);
    }
  }

  if (!statuses) return <p className="empty-state">Checking for updates…</p>;

  const pending = statuses.filter((s) => s.updateAvailable);
  const upToDate = statuses.filter((s) => !s.updateAvailable);

  return (
    <div>
      <h1 className="page-title">Updates</h1>
      <p className="page-subtitle">
        {pending.length === 0 ? "Everything is up to date." : `${pending.length} update${pending.length === 1 ? "" : "s"} available.`}
      </p>

      {pending.length > 0 && (
        <button className="btn" style={{ marginBottom: 16 }} onClick={() => void updateAll()}>
          Update all
        </button>
      )}

      <div className="card">
        {statuses.length === 0 && <p className="empty-state">Nothing installed yet.</p>}
        {pending.map((s) => (
          <div key={`${s.skillId}:${s.runtimeId}`} className="checklist-item">
            <span style={{ flex: 1 }}>
              {s.skillId} — {nameFor(s.runtimeId)}
            </span>
            <span className="card-subtitle" style={{ margin: "0 10px" }}>
              {s.installedVersion} → {s.availableVersion}
            </span>
            <button className="btn secondary" disabled={busy === `${s.skillId}:${s.runtimeId}`} onClick={() => void updateOne(s)}>
              {busy === `${s.skillId}:${s.runtimeId}` ? "Updating…" : "Update"}
            </button>
          </div>
        ))}
        {upToDate.map((s) => (
          <div key={`${s.skillId}:${s.runtimeId}`} className="checklist-item">
            <span style={{ flex: 1 }} className="status-muted">
              {s.skillId} — {nameFor(s.runtimeId)}
            </span>
            <span className="status-line status-ok">Up to date</span>
          </div>
        ))}
      </div>
    </div>
  );
}
