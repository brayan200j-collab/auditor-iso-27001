import { z } from "zod";

import { auth } from "@/content/es";

const email = z
  .string()
  .trim()
  .min(1, auth.validation.required)
  .max(320)
  .pipe(z.email(auth.validation.email));

export const loginSchema = z.object({
  email,
  password: z.string().min(1, auth.validation.required).max(200),
});

export const recoverySchema = z.object({ email });

export const PASSWORD_RULE = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{12,200}$/;

export const resetSchema = z
  .object({
    password: z.string().regex(PASSWORD_RULE, auth.validation.passwordWeak),
    confirm: z.string().min(1, auth.validation.required),
  })
  .refine((values) => values.password === values.confirm, {
    message: auth.reset.mismatch,
    path: ["confirm"],
  });

export type LoginInput = z.infer<typeof loginSchema>;
export type RecoveryInput = z.infer<typeof recoverySchema>;
export type ResetInput = z.infer<typeof resetSchema>;
