import { useState } from "react";
import { useAppData } from "../store/AppContext";
import { RuntimeBadge } from "../components/RuntimeBadge";

export function Settings() {
  const { runtimes, refresh, loading } = useAppData();
  const [advancedOpen, setAdvancedOpen] = useState(false);

  return (
    <div style={{ maxWidth: 640 }}>
      <h1 className="page-title">Settings</h1>

      <div className="card" style={{ marginBottom: 16 }}>
        <p className="card-title">Detected runtimes</p>
        <div className="badge-row">
          {runtimes.map((r) => (
            <RuntimeBadge key={r.runtime.id} name={r.runtime.name} variant={r.detected ? "detected" : "not-detected"} />
          ))}
        </div>
        <button className="btn secondary" style={{ marginTop: 12 }} disabled={loading} onClick={() => void refresh()}>
          Rescan
        </button>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <p className="card-title">SkillzForest account</p>
        <p className="card-subtitle">Not connected yet — sign-in isn't built in this version.</p>
        <button className="btn secondary" disabled>
          Sign in (coming soon)
        </button>
      </div>

      <div className="card">
        <p className="card-title">Advanced</p>
        <button className="btn secondary" onClick={() => setAdvancedOpen((v) => !v)}>
          {advancedOpen ? "Hide install locations" : "Show install locations"}
        </button>
        {advancedOpen && (
          <div className="advanced-panel">
            {runtimes.map((r) => (
              <div key={r.runtime.id}>
                {r.runtime.name}: {r.runtime.paths?.user ?? "(no filesystem path — " + r.runtime.installStrategy + ")"}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
