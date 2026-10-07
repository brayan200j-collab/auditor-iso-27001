import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { resultsCopy } from "@/content/es";

import { CoverageCard } from "./CoverageCard";
import type { ResultFinding, Results } from "./data";
import { ImprovementPlan } from "./ImprovementPlan";

const RAW_ENUMS = /\b(FOUND|PARTIAL|NO_DOCUMENTARY_EVIDENCE|LOW|MEDIUM|HIGH|CRITICAL)\b/;

function finding(code: string, overrides: Partial<ResultFinding> = {}): ResultFinding {
  return {
    finding_id: `id-${code}`,
    criterion: {
      code,
      name: "Gestión de activos",
      evaluation_question: "¿Existe inventario?",
      expected_evidence: "Inventario",
      iso_reference: null,
      cis_reference: null,
      nist_reference: null,
      reference_status: "draft",
    },
    review_status: "APPROVED",
    status: "PARTIAL",
    gap: "Brecha",
    recommendation: `Recomendación ${code}`,
    priority: "CRITICAL",
    effort: "LOW",
    risk_level: "HIGH",
    evidence: [],
    reviewer_comment: null,
    ...overrides,
  };
}

const results: Results = {
  evaluation_id: "eval-1",
  title: "Evaluación",
  approved_at: "2026-10-07T10:00:00Z",
  coverage: { total: 30, found: 18, partial: 7, no_evidence: 4, discarded: 1 },
  findings: [finding("ISO-07"), finding("ISO-02", { priority: "LOW" })],
  gap_ids: ["id-ISO-07", "id-ISO-02"],
  plan: [
    { phase: 1, finding_ids: ["id-ISO-07"] },
    { phase: 3, finding_ids: ["id-ISO-02"] },
  ],
};

describe("CoverageCard", () => {
  it("shows counts out of the total and never a percentage", () => {
    const { container } = render(<CoverageCard coverage={results.coverage} />);
    expect(container).toHaveTextContent("18 de 30 criterios con evidencia documental");
    expect(container).toHaveTextContent("7 de 30 con evidencia parcial");
    expect(container).toHaveTextContent("4 de 30 sin evidencia documental");
    expect(container).toHaveTextContent(resultsCopy.coverageDiscarded(1, 30));
    expect(container.textContent).not.toContain("%");
    expect(container.textContent).not.toMatch(/cumplimiento|compliance/i);
  });
});

describe("ImprovementPlan", () => {
  it("lists gaps by phase with Spanish labels and detail links", () => {
    const { container } = render(<ImprovementPlan evaluationId="eval-1" results={results} />);
    expect(screen.getByRole("heading", { name: resultsCopy.phases[1] })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: resultsCopy.phases[3] })).toBeInTheDocument();
    expect(container.textContent).not.toMatch(RAW_ENUMS);
    expect(screen.getByRole("link", { name: resultsCopy.detailLabel("ISO-07") })).toHaveAttribute(
      "href",
      "/app/evaluaciones/eval-1/resultados/id-ISO-07",
    );
  });

  it("states when there are no gaps", () => {
    render(<ImprovementPlan evaluationId="eval-1" results={{ ...results, plan: [] }} />);
    expect(screen.getByText(resultsCopy.noGaps)).toBeInTheDocument();
  });
});
