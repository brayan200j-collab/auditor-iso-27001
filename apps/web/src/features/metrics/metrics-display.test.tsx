import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { dashboardCopy, metricsCopy } from "@/content/es";

import { DashboardCards } from "./DashboardCards";
import type { Metrics } from "./data";
import { MetricsView } from "./MetricsView";

const empty: Metrics = {
  anonymized: true,
  technical: {
    documents_attempted: 0,
    documents_processed_ok: 0,
    processed_ok_ratio: null,
    extraction_errors: 0,
    processing_failures: 0,
    average_analysis_seconds: null,
    llm_calls: 0,
    approximate_tokens: 0,
    findings_reviewed: 0,
    findings_modified: 0,
    authorization_denials: 0,
  },
  value: {
    responses: 0,
    average_manual_hours: null,
    average_system_hours: null,
    average_usefulness: null,
    average_ease_of_use: null,
    average_trust: null,
    actionable_yes: 0,
    average_willingness_to_use: null,
    pay_yes: 0,
    pay_maybe: 0,
    pay_no: 0,
  },
};

describe("MetricsView", () => {
  it("shows 'Sin datos aún' instead of inventing values", () => {
    render(<MetricsView metrics={empty} />);
    expect(screen.getAllByText(metricsCopy.noData).length).toBeGreaterThanOrEqual(9);
    expect(screen.getByText(metricsCopy.anonymized)).toBeInTheDocument();
  });

  it("formats recorded values in Spanish", () => {
    const { container } = render(
      <MetricsView
        metrics={{
          ...empty,
          anonymized: false,
          technical: {
            ...empty.technical,
            documents_attempted: 4,
            documents_processed_ok: 3,
            processed_ok_ratio: 0.75,
            average_analysis_seconds: 95,
            findings_reviewed: 30,
            findings_modified: 4,
          },
          value: {
            ...empty.value,
            responses: 2,
            average_manual_hours: 12.5,
            average_usefulness: 4.5,
            actionable_yes: 2,
            pay_maybe: 2,
          },
        }}
      />,
    );
    expect(container).toHaveTextContent("3 de 4 (75 %)");
    expect(container).toHaveTextContent("1 min 35 s");
    expect(container).toHaveTextContent("4 de 30");
    expect(container).toHaveTextContent("12,5 h");
    expect(container).toHaveTextContent("Sí: 0 · Tal vez: 2 · No: 0");
    expect(screen.queryByText(metricsCopy.anonymized)).not.toBeInTheDocument();
  });
});

describe("DashboardCards", () => {
  it("renders the five real counters with Spanish labels", () => {
    render(
      <DashboardCards
        counts={{
          active_evaluations: 2,
          pending_review: 1,
          approved: 3,
          documents_processed: 5,
          high_priority_findings: 7,
        }}
      />,
    );
    for (const label of Object.values(dashboardCopy.cards)) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
    expect(screen.getByText("7")).toBeInTheDocument();
  });
});
