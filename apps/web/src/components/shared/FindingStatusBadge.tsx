import { Badge, type BadgeTone } from "@/components/ui/badge";
import { findingStatusLabels, reviewCopy, reviewStatusLabels } from "@/content/es";

type FindingStatus = keyof typeof findingStatusLabels;
type ReviewStatus = keyof typeof reviewStatusLabels;

const FINDING_TONES: Record<FindingStatus, BadgeTone> = {
  FOUND: "success",
  PARTIAL: "warning",
  NO_DOCUMENTARY_EVIDENCE: "danger",
};

const REVIEW_TONES: Record<ReviewStatus, BadgeTone> = {
  PENDING_REVIEW: "neutral",
  APPROVED: "success",
  EDITED_APPROVED: "info",
  DISCARDED: "neutral",
};

export function FindingStatusBadge({ status }: { status: FindingStatus | null | undefined }) {
  if (!status) return <Badge tone="danger">{reviewCopy.unclassified}</Badge>;
  return <Badge tone={FINDING_TONES[status]}>{findingStatusLabels[status]}</Badge>;
}

export function ReviewStatusBadge({ status }: { status: ReviewStatus }) {
  return <Badge tone={REVIEW_TONES[status]}>{reviewStatusLabels[status]}</Badge>;
}
