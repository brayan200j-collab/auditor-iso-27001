import { z } from "zod";

const levels = z.enum(["LOW", "MEDIUM", "HIGH"]);

export const itemSchema = z.object({
  name: z.string().trim().min(1).max(160),
  description: z.string().trim().min(10).max(2000),
  evaluation_question: z.string().trim().min(10).max(2000),
  expected_evidence: z.string().trim().min(10).max(2000),
  iso_reference: z.string().trim().max(80),
  cis_reference: z.string().trim().max(80),
  nist_reference: z.string().trim().max(80),
  reference_status: z.enum(["draft", "confirmed"]),
  keywords: z.string().trim().min(2),
  priority: z.enum(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
  risk_level: levels,
  effort: levels,
  active: z.boolean(),
});

export type ItemValues = z.infer<typeof itemSchema>;
