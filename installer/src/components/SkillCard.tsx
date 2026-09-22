import { useNavigate } from "react-router-dom";
import type { CatalogSkill } from "../types/skill";
import { worksWithRuntimeIds } from "../utils/capability";
import { useAppData } from "../store/AppContext";
import { RuntimeBadge } from "./RuntimeBadge";

export function SkillCard({ skill }: { skill: CatalogSkill }) {
  const navigate = useNavigate();
  const { runtimes } = useAppData();
  const runtimeIds = worksWithRuntimeIds(skill.manifest.compatibility);
  const nameFor = (id: string) => runtimes.find((r) => r.runtime.id === id)?.runtime.name ?? id;

  return (
    <div
      className="card"
      role="button"
      tabIndex={0}
      onClick={() => navigate(`/skills/${skill.manifest.id}`)}
      style={{ cursor: "pointer" }}
    >
      <p className="card-title">{skill.manifest.name}</p>
      <p className="card-subtitle">{skill.manifest.description}</p>
      <div className="badge-row">
        {runtimeIds.map((id) => (
          <RuntimeBadge key={id} name={nameFor(id)} variant="default" />
        ))}
      </div>
    </div>
  );
}
