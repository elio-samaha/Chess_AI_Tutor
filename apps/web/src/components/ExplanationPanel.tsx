import type { FC } from "react";

import type { MoveAnalysis } from "../types";

interface ExplanationPanelProps {
  move: MoveAnalysis | null;
}

const ExplanationPanel: FC<ExplanationPanelProps> = ({ move }) => {
  if (!move) {
    return <p className="empty-state">Select a move to see the explanation.</p>;
  }

  return (
    <div className="panel-block explanation-grid">
      <div>
        <p className="eyebrow">Summary</p>
        <h3>{move.explanation.summary}</h3>
      </div>
      <div>
        <p className="eyebrow">Why</p>
        <p>{move.explanation.why_good_or_bad}</p>
      </div>
      <div>
        <p className="eyebrow">Position Change</p>
        <p>{move.explanation.what_changed}</p>
      </div>
      <div>
        <p className="eyebrow">Best Alternative</p>
        <p>{move.explanation.best_alternative}</p>
      </div>
      <div>
        <p className="eyebrow">Practical Lesson</p>
        <p>{move.explanation.practical_lesson}</p>
      </div>
      <div>
        <p className="eyebrow">Motifs</p>
        <p>{move.motifs.join(", ")}</p>
      </div>
    </div>
  );
};

export default ExplanationPanel;
