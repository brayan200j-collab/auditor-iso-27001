import { evaluationStatusLabels, type EvaluationStatus } from "@/content/es";

export function statusParam(value: string | string[] | undefined): EvaluationStatus | undefined {
  const status = Array.isArray(value) ? value[0] : value;
  return status && status in evaluationStatusLabels ? (status as EvaluationStatus) : undefined;
}

export const EVALUATION_STATUSES = Object.keys(evaluationStatusLabels) as EvaluationStatus[];
