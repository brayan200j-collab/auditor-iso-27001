import { Badge, type BadgeTone } from "@/components/ui/badge";
import { evaluationStatusLabels, type EvaluationStatus } from "@/content/es";

const TONES: Record<EvaluationStatus, BadgeTone> = {
  DRAFT: "neutral",
  RECEIVED: "info",
  EXTRACTING: "info",
  ANALYZING: "info",
  PENDING_REVIEW: "warning",
  APPROVED: "success",
  REJECTED: "danger",
  FAILED: "danger",
};

export function EvaluationStatusBadge({ status }: { status: EvaluationStatus }) {
  return <Badge tone={TONES[status]}>{evaluationStatusLabels[status]}</Badge>;
}
