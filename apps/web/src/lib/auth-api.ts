import type { ApiErrorBody, MeResponse, MessageResponse, RegisterResponse, TokenPair } from "@cityos/types";

import { env } from "./env";

export class ApiError extends Error {
  code: string;
  requestId: string;

  constructor(body: ApiErrorBody) {
    super(body.error.message);
    this.code = body.error.code;
    this.requestId = body.error.request_id;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${env.apiUrl}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    signal: AbortSignal.timeout(10_000),
  });
  const body = await response.json();
  if (!response.ok) throw new ApiError(body as ApiErrorBody);
  return body as T;
}

export function register(input: { email: string; password: string; full_name: string }) {
  return request<RegisterResponse>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function login(input: { email: string; password: string }) {
  return request<TokenPair>("/api/v1/auth/login", { method: "POST", body: JSON.stringify(input) });
}

export function verifyEmail(token: string) {
  return request<MessageResponse>("/api/v1/auth/verify-email", {
    method: "POST",
    body: JSON.stringify({ token }),
  });
}

export function requestPasswordReset(email: string) {
  return request<MessageResponse>("/api/v1/auth/request-password-reset", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export function resetPassword(input: { token: string; new_password: string }) {
  return request<MessageResponse>("/api/v1/auth/reset-password", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function logout(refresh_token: string) {
  return request<MessageResponse>("/api/v1/auth/logout", {
    method: "POST",
    body: JSON.stringify({ refresh_token }),
  });
}

export function me(accessToken: string) {
  return request<MeResponse>("/api/v1/auth/me", {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
}
