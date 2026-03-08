import type { FC, FormEvent } from "react";

import type { QuestionAnswer } from "../types";

interface QaPanelProps {
  question: string;
  candidateMove: string;
  answer: QuestionAnswer | null;
  loading: boolean;
  onQuestionChange: (value: string) => void;
  onCandidateMoveChange: (value: string) => void;
  onSubmit: () => Promise<void>;
}

const QaPanel: FC<QaPanelProps> = ({
  question,
  candidateMove,
  answer,
  loading,
  onQuestionChange,
  onCandidateMoveChange,
  onSubmit,
}) => {
  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await onSubmit();
  };

  return (
    <div className="panel-block qa-panel">
      <form onSubmit={handleSubmit}>
        <label>
          Ask about this game or position
          <textarea value={question} onChange={(event) => onQuestionChange(event.target.value)} />
        </label>
        <label>
          Counterfactual move (optional SAN)
          <input value={candidateMove} onChange={(event) => onCandidateMoveChange(event.target.value)} />
        </label>
        <button type="submit" className="primary-button" disabled={loading || !question.trim()}>
          {loading ? "Thinking..." : "Ask the coach"}
        </button>
      </form>
      {answer ? (
        <div className="qa-answer">
          <p>{answer.answer}</p>
          {answer.suggested_lines.length > 0 ? (
            <p className="qa-line">Engine line: {answer.suggested_lines.join(" ")}</p>
          ) : null}
        </div>
      ) : (
        <p className="empty-state">Questions stay grounded in the selected move and current game.</p>
      )}
    </div>
  );
};

export default QaPanel;
