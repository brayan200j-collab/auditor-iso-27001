import { Alert } from "@/components/ui/alert";
import { evaluations } from "@/content/es";

import type { Evaluation } from "./data";

/** Human-readable explanation for rejected or failed evaluations (never technical details). */
export function EvaluationNotices({ evaluation }: { evaluation: Evaluation }) {
  if (evaluation.status === "REJECTED" && evaluation.rejection_reason) {
    return (
      <Alert tone="warning" role="status">
        <p className="font-semibold">{evaluations.rejectionTitle}</p>
        <p className="mt-1">{evaluation.rejection_reason}</p>
        <p className="mt-1">{evaluations.rejectionHelp}</p>
      </Alert>
    );
  }
  if (evaluation.status === "FAILED") {
    const reason = evaluation.failure_reason ?? "ANALYSIS_ERROR";
    return (
      <Alert tone="danger">
        <p className="font-semibold">{evaluations.failureTitle}</p>
        <p className="mt-1">{evaluations.failureReasons[reason]}</p>
      </Alert>
    );
  }
  return null;
}
