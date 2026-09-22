import { useNavigate } from "react-router-dom";
import type { CatalogPack } from "../types/pack";

export function PackCard({ pack }: { pack: CatalogPack }) {
  const navigate = useNavigate();
  return (
    <div
      className="card"
      role="button"
      tabIndex={0}
      onClick={() => navigate(`/packs/${pack.manifest.id}`)}
      style={{ cursor: "pointer" }}
    >
      <p className="card-title">{pack.manifest.name}</p>
      <p className="card-subtitle">{pack.manifest.description}</p>
      <div className="badge-row">
        <span className="badge">{pack.manifest.skills.length} Skills</span>
      </div>
    </div>
  );
}
