"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import type { MeResponse } from "@cityos/types";

import { logout, me } from "@/lib/auth-api";
import { clearTokens, getAccessToken, getRefreshToken } from "@/lib/auth-client";
import { Logo } from "@/components/Logo";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

const STATUS_TONE = {
  ACTIVE: "success",
  PENDING_VERIFICATION: "brand",
  SUSPENDED: "danger",
  DEACTIVATED: "neutral",
} as const;

export default function AccountPage() {
  const router = useRouter();
  const [profile, setProfile] = useState<MeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const accessToken = getAccessToken();
    if (!accessToken) {
      router.replace("/login");
      return;
    }
    me(accessToken)
      .then(setProfile)
      .catch(() => setError("Your session has expired. Please sign in again."));
  }, [router]);

  async function onLogout() {
    const refreshToken = getRefreshToken();
    if (refreshToken) await logout(refreshToken).catch(() => undefined);
    clearTokens();
    router.push("/login");
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col items-center justify-center px-6 py-16">
      <Link href="/" className="mb-8">
        <Logo />
      </Link>
      <Card className="w-full">
        {error && (
          <div className="text-center">
            <p className="text-sm text-danger">{error}</p>
            <Link href="/login" className="mt-4 inline-block text-sm font-medium text-brand hover:underline">
              Sign in
            </Link>
          </div>
        )}

        {!error && !profile && (
          <div className="animate-pulse space-y-4">
            <div className="h-6 w-40 rounded bg-surface-muted" />
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="h-16 rounded-xl bg-surface-muted" />
              <div className="h-16 rounded-xl bg-surface-muted" />
              <div className="h-16 rounded-xl bg-surface-muted" />
              <div className="h-16 rounded-xl bg-surface-muted" />
            </div>
          </div>
        )}

        {profile && (
          <>
            <div className="flex items-center gap-4">
              <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-brand/12 text-lg font-semibold text-brand-strong">
                {initials(profile.full_name)}
              </div>
              <div className="min-w-0">
                <h1 className="truncate text-xl font-semibold tracking-tight text-ink">
                  {profile.full_name}
                </h1>
                <p className="truncate text-sm text-ink-muted">{profile.email}</p>
              </div>
            </div>

            <div className="mt-6 flex flex-wrap gap-2">
              <Badge tone="brand">{profile.role}</Badge>
              {profile.department && <Badge tone="neutral">{profile.department}</Badge>}
              <Badge tone={STATUS_TONE[profile.status]}>{profile.status.replaceAll("_", " ")}</Badge>
              {!profile.email_verified && <Badge tone="danger">Email not verified</Badge>}
            </div>

            <div className="mt-8">
              <h2 className="text-xs font-semibold uppercase tracking-wider text-ink-faint">
                Permissions
              </h2>
              <div className="mt-3 flex flex-wrap gap-2">
                {profile.permissions.length === 0 && (
                  <p className="text-sm text-ink-muted">No permissions granted.</p>
                )}
                {profile.permissions.map((permission) => (
                  <span
                    key={permission}
                    className="rounded-md border border-line bg-surface-muted px-2.5 py-1 font-mono text-xs text-ink-muted"
                  >
                    {permission}
                  </span>
                ))}
              </div>
            </div>

            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/city/command-center">
                <Button variant="primary">Open dashboard</Button>
              </Link>
              <Button variant="danger-outline" onClick={onLogout}>
                Sign out
              </Button>
            </div>
          </>
        )}
      </Card>
    </main>
  );
}

function initials(name: string): string {
  const parts = name.trim().split(/\s+/);
  return ((parts[0]?.[0] ?? "") + (parts[parts.length - 1]?.[0] ?? "")).toUpperCase();
}
