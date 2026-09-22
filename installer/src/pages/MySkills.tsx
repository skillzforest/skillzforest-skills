import { Link } from "react-router-dom";
import { useAppData } from "../store/AppContext";
import { computeInstalledPacks, computeInstalledSkills } from "../utils/myskills";
import { formatPackProgress } from "../utils/format";

export function MySkills() {
  const { skills, packs, registry, runtimes, loading } = useAppData();

  if (loading) return <p className="empty-state">Loading…</p>;

  const installedSkills = computeInstalledSkills(skills, registry);
  const installedPacks = computeInstalledPacks(packs, registry);
  const nameFor = (id: string) => runtimes.find((r) => r.runtime.id === id)?.runtime.name ?? id;

  return (
    <div>
      <h1 className="page-title">My Skills</h1>
      <p className="page-subtitle">What's installed, and where.</p>

      {installedPacks.length > 0 && (
        <div className="card-grid" style={{ marginBottom: 24 }}>
          {installedPacks.map((p) => (
            <Link key={p.packId} to={`/packs/${p.packId}`} className="card" style={{ textDecoration: "none", color: "inherit" }}>
              <p className="card-title">{p.name}</p>
              <p className="card-subtitle">{formatPackProgress(p.installedCount, p.totalCount)}</p>
            </Link>
          ))}
        </div>
      )}

      {installedSkills.length === 0 ? (
        <p className="empty-state">Nothing installed yet. Head to Home to install your first skill.</p>
      ) : (
        <div className="card-grid">
          {installedSkills.map((s) => (
            <Link key={s.skillId} to={`/skills/${s.skillId}`} className="card" style={{ textDecoration: "none", color: "inherit" }}>
              <p className="card-title">{s.name}</p>
              <p className="card-subtitle">Installed in:</p>
              <div className="badge-row">
                {s.runtimeIds.map((id) => (
                  <span key={id} className="badge detected">
                    {nameFor(id)}
                  </span>
                ))}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
