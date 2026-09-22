import { useNavigate } from "react-router-dom";
import { useAppData } from "../store/AppContext";
import { RuntimeBadge } from "../components/RuntimeBadge";

export function Welcome() {
  const navigate = useNavigate();
  const { runtimes, loading, refresh } = useAppData();

  return (
    <div className="centered-screen">
      <h1 style={{ margin: 0 }}>Welcome to SkillzForest</h1>
      <p className="page-subtitle" style={{ margin: 0 }}>We found:</p>

      {loading ? (
        <p>Scanning this computer…</p>
      ) : (
        <div className="badge-row" style={{ justifyContent: "center" }}>
          {runtimes.map((r) => (
            <RuntimeBadge
              key={r.runtime.id}
              name={r.runtime.name}
              variant={r.detected ? "detected" : "not-detected"}
            />
          ))}
        </div>
      )}

      <div style={{ display: "flex", gap: 10 }}>
        <button className="btn secondary" onClick={() => void refresh()} disabled={loading}>
          Rescan
        </button>
        <button className="btn" onClick={() => navigate("/home")} disabled={loading}>
          Continue
        </button>
      </div>
    </div>
  );
}
