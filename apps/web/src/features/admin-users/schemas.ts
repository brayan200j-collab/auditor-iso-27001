import { z } from "zod";

import { adminUsers } from "@/content/es";

export const ROLES = ["ADMIN", "REVIEWER", "SME", "MENTOR"] as const;

export const createUserSchema = z
  .object({
    email: z.string().trim().pipe(z.email(adminUsers.validation.email)),
    fullName: z
      .string()
      .trim()
      .min(2, adminUsers.validation.fullName)
      .max(200, adminUsers.validation.fullName),
    role: z.enum(ROLES),
    companyId: z.string(),
  })
  .refine((values) => values.role !== "SME" || values.companyId !== "", {
    message: adminUsers.validation.company,
    path: ["companyId"],
  });

export const updateUserSchema = z.object({
  fullName: z
    .string()
    .trim()
    .min(2, adminUsers.validation.fullName)
    .max(200, adminUsers.validation.fullName),
  companyId: z.string(),
});

export type CreateUserValues = z.infer<typeof createUserSchema>;
export type UpdateUserValues = z.infer<typeof updateUserSchema>;
