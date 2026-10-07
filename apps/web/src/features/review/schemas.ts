import { z } from "zod";

const level = z.enum(["LOW", "MEDIUM", "HIGH"]);

export const editSchema = z.object({
  status: z.enum(["FOUND", "PARTIAL", "NO_DOCUMENTARY_EVIDENCE"]),
  gap: z.string().trim().min(1).max(2000),
  recommendation: z.string().trim().min(1).max(2000),
  priority: z.enum(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
  risk_level: level,
  effort: level,
  comment: z.string().trim().max(2000),
});

export type EditValues = z.infer<typeof editSchema>;
