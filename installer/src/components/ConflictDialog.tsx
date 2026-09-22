import type { ConflictResolution } from "../types/runtime";

interface ConflictDialogProps {
  skillName: string;
  onResolve: (resolution: ConflictResolution) => void;
}

/** "Technical SEO is already installed. The existing version was not
 * installed by SkillzForest." — shown before ever overwriting anything the
 * app doesn't already own, per the no-silent-overwrite rule. */
export function ConflictDialog({ skillName, onResolve }: ConflictDialogProps) {
  return (
    <div className="modal-overlay">
      <div className="modal">
        <p className="card-title">{skillName} is already installed.</p>
        <p className="card-subtitle">The existing version was not installed by SkillzForest.</p>
        <div style={{ display: "flex", gap: 10, marginTop: 16 }}>
          <button className="btn secondary" onClick={() => onResolve("keep-existing")}>
            Keep existing
          </button>
          <button className="btn danger" onClick={() => onResolve("replace")}>
            Replace
          </button>
          <button className="btn secondary" onClick={() => onResolve("cancel")}>
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
