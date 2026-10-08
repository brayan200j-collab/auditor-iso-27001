import { z } from "zod";

import { surveyCopy } from "@/content/es";

const scale = z.enum(["1", "2", "3", "4", "5"], { message: surveyCopy.required });
const hours = z
  .string()
  .trim()
  .min(1, { message: surveyCopy.hoursInvalid })
  .transform((value) => Number(value.replace(",", ".")))
  .refine((value) => Number.isFinite(value) && value >= 0 && value <= 1000, {
    message: surveyCopy.hoursInvalid,
  });

export const surveySchema = z.object({
  usefulness: scale,
  ease_of_use: scale,
  trust_in_results: scale,
  actionable_recommendations: z.enum(["yes", "no"], { message: surveyCopy.required }),
  manual_time_hours: hours,
  system_time_hours: hours,
  willingness_to_use: scale,
  willingness_to_pay: z.enum(["YES", "MAYBE", "NO"], { message: surveyCopy.required }),
  comments: z.string().trim().max(2000),
});

export type SurveyInput = z.input<typeof surveySchema>;
export type SurveyValues = z.output<typeof surveySchema>;
