import type { FC } from "react";

import type { CoachingLayers } from "../types";

interface CoachingPanelProps {
  coaching: CoachingLayers | null;
  loading: boolean;
}

const CoachingPanel: FC<CoachingPanelProps> = ({ coaching, loading }) => {
  if (loading) {
    return (
      <div className="panel-block">
        <p className="empty-state">Generating layered coaching...</p>
      </div>
    );
  }

  if (!coaching) {
    return (
      <div className="panel-block">
        <p className="empty-state">Select a game and move to generate high/mid/move-level coaching.</p>
      </div>
    );
  }

  return (
    <div className="panel-block">
      <div className="section-header">
        <h2>Layered coaching</h2>
        <span>Ply {coaching.ply ?? "-"}</span>
      </div>
      <p className="eyebrow">High level (whole game)</p>
      <p>{coaching.high_level}</p>
      <p className="eyebrow">Mid level (critical moves)</p>
      <p>{coaching.mid_level}</p>
      <p className="eyebrow">Move-level explanation</p>
      <p>{coaching.move_level}</p>
      {coaching.engine_line.length > 0 ? <p className="qa-line">Engine line: {coaching.engine_line.join(" ")}</p> : null}
      <p className="empty-state">{coaching.grounding_note}</p>
    </div>
  );
};

export default CoachingPanel;
