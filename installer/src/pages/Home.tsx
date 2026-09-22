import { useAppData } from "../store/AppContext";
import { SkillCard } from "../components/SkillCard";
import { PackCard } from "../components/PackCard";

export function Home() {
  const { skills, packs, loading, error } = useAppData();

  if (loading) return <p className="empty-state">Loading skills…</p>;
  if (error) return <p className="empty-state">Something went wrong: {error}</p>;

  return (
    <div>
      <h1 className="page-title">Install a Skill</h1>
      <p className="page-subtitle">
        Browse the skills and packs available today. Click one to see what it does and where it can go.
      </p>

      {packs.length > 0 && (
        <>
          <h2 style={{ fontSize: 16, marginTop: 24 }}>Packs</h2>
          <div className="card-grid">
            {packs.map((pack) => (
              <PackCard key={pack.manifest.id} pack={pack} />
            ))}
          </div>
        </>
      )}

      <h2 style={{ fontSize: 16, marginTop: 24 }}>Skills</h2>
      {skills.length === 0 ? (
        <p className="empty-state">No skills found.</p>
      ) : (
        <div className="card-grid">
          {skills.map((skill) => (
            <SkillCard key={skill.manifest.id} skill={skill} />
          ))}
        </div>
      )}
    </div>
  );
}
