import { describe, expect, it } from "vitest";

import * as es from "./es";

const FORBIDDEN = [
  /cumplimiento/i,
  /\bcertificad[oa]\b/i,
  /auditor[ií]a iso autom[aá]tica/i,
  /cumple iso/i,
  /no cumple iso/i,
  /compliance/i,
  /la ia es gratuita/i,
  /nunca son almacenados/i,
  /CyberAudit/i,
  /CIS Controls v8(?!\.1)/,
];

function collectStrings(value: unknown): string[] {
  if (typeof value === "string") return [value];
  if (typeof value === "function") return [String((value as (...a: number[]) => string)(1, 30))];
  if (value && typeof value === "object") return Object.values(value).flatMap(collectStrings);
  return [];
}

describe("Spanish copy catalogue", () => {
  const strings = collectStrings(es);

  it("never uses forbidden wording", () => {
    for (const text of strings) {
      for (const pattern of FORBIDDEN) {
        expect(text, `"${text}" matches ${pattern}`).not.toMatch(pattern);
      }
    }
  });

  it("never expresses coverage as a percentage", () => {
    for (const text of strings) expect(text).not.toMatch(/\d+\s?%/);
  });

  it("translates every internal enum", () => {
    expect(es.priorityLabels.CRITICAL).toBe("Crítica");
    expect(es.reviewStatusLabels.PENDING_REVIEW).toBe("Pendiente");
    expect(es.filterLabels.ALL).toBe("Todos");
    expect(es.coverage.withEvidence(18, 30)).toBe("18 de 30 criterios con evidencia documental");
  });
});
