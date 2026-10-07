import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { evaluationStatusLabels, type EvaluationStatus } from "@/content/es";

import { EvaluationStatusBadge } from "./EvaluationStatusBadge";
import { ProgressTimeline } from "./ProgressTimeline";

const RAW_ENUMS =
  /\b(DRAFT|RECEIVED|EXTRACTING|ANALYZING|PENDING|APPROVED|REJECTED|FAILED|DONE|CURRENT|CRITICAL|ALL)\b/;

describe("EvaluationStatusBadge", () => {
  it.each(Object.keys(evaluationStatusLabels) as EvaluationStatus[])(
    "shows %s in Spanish",
    (status) => {
      const { container } = render(<EvaluationStatusBadge status={status} />);
      expect(container).toHaveTextContent(evaluationStatusLabels[status]);
      expect(container.textContent).not.toMatch(RAW_ENUMS);
    },
  );
});

describe("ProgressTimeline", () => {
  it("renders the five steps with their state in Spanish", () => {
    const { container } = render(
      <ProgressTimeline
        steps={[
          { step: "RECEIVED", state: "DONE" },
          { step: "EXTRACTING", state: "DONE" },
          { step: "ANALYZING", state: "FAILED" },
          { step: "PENDING_REVIEW", state: "PENDING" },
          { step: "APPROVED", state: "PENDING" },
        ]}
      />,
    );
    const items = screen.getAllByRole("listitem");
    expect(items.map((item) => item.textContent)).toEqual([
      "1. Recibidocompletado",
      "2. Extraccióncompletado",
      "3. Análisiscon error",
      "4. Revisión humanapendiente",
      "5. Aprobadopendiente",
    ]);
    expect(container.textContent).not.toMatch(RAW_ENUMS);
  });

  it("marks the current step for assistive technologies", () => {
    render(<ProgressTimeline steps={[{ step: "ANALYZING", state: "CURRENT" }]} />);
    const current = screen
      .getAllByRole("listitem")
      .find((item) => item.getAttribute("aria-current"));
    expect(current).toHaveTextContent("Análisis");
  });
});
