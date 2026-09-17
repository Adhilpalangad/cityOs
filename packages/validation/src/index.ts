import { z } from "zod";

// Mirrors the password rule enforced server-side in
// services/identity/app/schemas/common.py (validate_password_strength).
// The backend is the source of truth and re-validates independently --
// this only gives the user a fast, friendly error before the round trip.
export const passwordSchema = z
  .string()
  .min(8, "Password must be at least 8 characters long.")
  .regex(/[A-Za-z]/, "Password must contain at least one letter.")
  .regex(/\d/, "Password must contain at least one digit.");

export const emailSchema = z.string().email("Enter a valid email address.");

export const registerSchema = z.object({
  email: emailSchema,
  password: passwordSchema,
  full_name: z.string().trim().min(1, "Enter your full name."),
});
export type RegisterInput = z.infer<typeof registerSchema>;

export const loginSchema = z.object({
  email: emailSchema,
  password: z.string().min(1, "Enter your password."),
});
export type LoginInput = z.infer<typeof loginSchema>;

export const requestPasswordResetSchema = z.object({ email: emailSchema });
export type RequestPasswordResetInput = z.infer<typeof requestPasswordResetSchema>;

export const resetPasswordSchema = z.object({
  token: z.string().min(1),
  new_password: passwordSchema,
});
export type ResetPasswordInput = z.infer<typeof resetPasswordSchema>;
