import { Check, Circle, LoaderCircle, X } from "lucide-react";

import { evaluations, progressSteps } from "@/content/es";
import { cn } from "@/lib/utils";

export type StepState = "DONE" | "CURRENT" | "FAILED" | "PENDING";
export type TimelineStep = { step: string; state: StepState };

const ICONS = { DONE: Check, CURRENT: LoaderCircle, FAILED: X, PENDING: Circle } as const;

const STYLES: Record<StepState, string> = {
  DONE: "bg-success text-white border-success",
  CURRENT: "bg-info-soft text-info border-info",
  FAILED: "bg-danger text-white border-danger",
  PENDING: "bg-surface text-muted-foreground border-border",
};

/** Recibido → Extracción → Análisis → Revisión humana → Aprobado, with a state per step. */
export function ProgressTimeline({ steps }: { steps: TimelineStep[] }) {
  return (
    <ol aria-label={evaluations.progressTitle} className="grid gap-3 sm:grid-cols-5">
      {progressSteps.map((definition, index) => {
        const state = steps.find((item) => item.step === definition.key)?.state ?? "PENDING";
        const Icon = ICONS[state];
        return (
          <li
            key={definition.key}
            className="flex items-center gap-3 sm:flex-col sm:text-center"
            aria-current={state === "CURRENT" ? "step" : undefined}
          >
            <span
              className={cn(
                "flex size-9 shrink-0 items-center justify-center rounded-full border-2",
                STYLES[state],
              )}
              aria-hidden="true"
            >
              <Icon className={cn("size-4", state === "CURRENT" && "animate-spin")} />
            </span>
            <span className="text-sm">
              <span className="text-foreground font-medium">
                {index + 1}. {definition.label}
              </span>
              <span className="text-muted-foreground block text-xs">
                {evaluations.stepStates[state]}
              </span>
            </span>
          </li>
        );
      })}
    </ol>
  );
}
