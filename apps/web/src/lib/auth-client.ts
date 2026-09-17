"use client";

import type { TokenPair } from "@cityos/types";

// Dev-only session storage: tokens live in localStorage so this Module 02
// status app can demonstrate the auth flow without a backing session store.
// A production frontend should hold the refresh token in an httpOnly cookie
// set by a server route instead -- that hardening is future work, not part
// of this module.
const ACCESS_TOKEN_KEY = "cityos.access_token";
const REFRESH_TOKEN_KEY = "cityos.refresh_token";

function storage(): Storage | null {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

export function saveTokens(tokens: TokenPair): void {
  const store = storage();
  store?.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  store?.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
}

export function getAccessToken(): string | null {
  return storage()?.getItem(ACCESS_TOKEN_KEY) ?? null;
}

export function getRefreshToken(): string | null {
  return storage()?.getItem(REFRESH_TOKEN_KEY) ?? null;
}

export function clearTokens(): void {
  const store = storage();
  store?.removeItem(ACCESS_TOKEN_KEY);
  store?.removeItem(REFRESH_TOKEN_KEY);
}
