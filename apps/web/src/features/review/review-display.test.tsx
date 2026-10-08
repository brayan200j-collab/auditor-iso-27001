import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { reviewCopy } from "@/content/es";

import { ConfidenceValue, formatConfidence } from "./ConfidenceValue";
import type { ReviewItem } from "./data";
import { EvidenceList } from "./EvidenceList";
import { ReviewQueueTable } from "./ReviewQueueTable";
import { ReviewSummaryCard } from "./ReviewSummaryCard";

const RAW_ENUMS =
  /\b(FOUND|PARTIAL|NO_DOCUMENTARY_EVIDENCE|PENDING_REVIEW|APPROVED|EDITED|DISCARDED|LOW|MEDIUM|HIGH|CRITICAL)\b/;

function item(overrides: Partial<ReviewItem["ai"]> = {}, code = "ISO-07"): ReviewItem {
  return {
    finding_id: `finding-${code}`,
    criterion: {
      code,
      name: "Gestión de accesos",
      evaluation_question: "¿Existe un procedimiento?",
      expected_evidence: "Procedimiento aprobado",
      iso_reference: null,
      cis_reference: null,
      nist_reference: null,
      reference_status: "draft",
    },
    ai: {
      status: "PARTIAL",
      confidence: 0.42,
      evidence: [],
      gap: "Falta revisión periódica",
      recommendation: "Definir revisión trimestral",
      preliminary_priority: "HIGH",
      estimated_effort: "MEDIUM",
      risk_level: "HIGH",
      llm_called: true,
      error_summary: null,
      needs_attention: true,
      provider: "fake",
      model: "fake-model",
      prompt_version: "v1",
      created_at: "2026-10-01T10:00:00Z",
      ...overrides,
    },
    review: { review_status: "PENDING_REVIEW", final: null, comment: null, reviewed_at: null },
  };
}

describe("ConfidenceValue", () => {
  it("shows a decimal value, never a percentage", () => {
    const { container } = render(<ConfidenceValue value={0.42} />);
    expect(container).toHaveTextContent("0,42");
    expect(container.textContent).not.toContain("%");
    expect(formatConfidence(0.9)).toBe("0,90");
  });

  it("explains when the model was not called", () => {
    const { container } = render(<ConfidenceValue value={null} />);
    expect(container).toHaveTextContent(reviewCopy.noModelCall);
    expect(container).toHaveTextContent(reviewCopy.noModelCallHelp);
  });
});

describe("EvidenceList", () => {
  it("shows document, page and quote, and flags unverified citations", () => {
    render(
      <EvidenceList
        evidence={[
          {
            document_name: "politica.pdf",
            page: 3,
            quote: "Se revisan los accesos.",
            citation_verified: true,
          },
          {
            document_name: "politica.pdf",
            page: 5,
            quote: "Texto inventado",
            citation_verified: false,
          },
        ]}
      />,
    );
    expect(screen.getByText(reviewCopy.page(3), { exact: false })).toBeInTheDocument();
    expect(screen.getByText("Se revisan los accesos.")).toBeInTheDocument();
    expect(screen.getAllByText(reviewCopy.unverified)).toHaveLength(1);
  });

  it("states when there are no citations", () => {
    render(<EvidenceList evidence={[]} />);
    expect(screen.getByText(reviewCopy.noCitations)).toBeInTheDocument();
  });
});

describe("ReviewSummaryCard", () => {
  it("summarises counts without percentages", () => {
    const { container } = render(
      <ReviewSummaryCard
        summary={{
          total: 30,
          found: 12,
          partial: 10,
          no_evidence: 8,
          errors: 0,
          reviewed: 3,
          pending: 27,
          needs_attention: 5,
        }}
      />,
    );
    expect(container).toHaveTextContent(reviewCopy.evaluated(30));
    expect(container).toHaveTextContent(reviewCopy.progress(3, 30));
    expect(container.textContent).not.toContain("%");
    expect(container.textContent).not.toMatch(/cumplimiento/i);
  });
});

describe("ReviewQueueTable", () => {
  it("renders labels in Spanish and links each finding", () => {
    const { container } = render(
      <ReviewQueueTable
        evaluationId="eval-1"
        items={[item(), item({ status: null, confidence: null, llm_called: false }, "ISO-08")]}
      />,
    );
    expect(container.textContent).not.toMatch(RAW_ENUMS);
    expect(container).toHaveTextContent(reviewCopy.needsAttention);
    const link = screen.getByRole("link", { name: reviewCopy.reviewLabel("ISO-07") });
    expect(link).toHaveAttribute("href", "/app/revision/eval-1/hallazgos/finding-ISO-07");
  });
});
