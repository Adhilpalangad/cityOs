"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { ApiError, verifyEmail } from "@/lib/auth-api";

type Status = "verifying" | "verified" | "error";

function Spinner() {
  return (
    <svg className="mx-auto h-8 w-8 animate-spin text-brand" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle className="opacity-20" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
      <path className="opacity-90" fill="currentColor" d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z" />
    </svg>
  );
}

function VerifyEmailContent() {
  const token = useSearchParams().get("token");
  const [status, setStatus] = useState<Status>(token ? "verifying" : "error");
  const [error, setError] = useState<string | null>(
    token ? null : "This verification link is missing its token."
  );

  useEffect(() => {
    if (!token) return;
    verifyEmail(token)
      .then(() => setStatus("verified"))
      .catch((err) => {
        setStatus("error");
        setError(err instanceof ApiError ? err.message : "Verification failed.");
      });
  }, [token]);

  if (status === "verifying") {
    return (
      <div className="py-4 text-center">
        <Spinner />
        <p className="mt-4 text-sm text-ink-muted">Verifying your email...</p>
      </div>
    );
  }

  if (status === "verified") {
    return (
      <div className="text-center">
        <h1 className="text-2xl font-semibold tracking-tight text-ink">Email verified</h1>
        <p className="mt-2 text-sm text-ink-muted">Your account is now active.</p>
        <Link href="/login" className="mt-6 inline-block text-sm font-medium text-brand hover:underline">
          Sign in
        </Link>
      </div>
    );
  }

  return (
    <div className="text-center">
      <h1 className="text-2xl font-semibold tracking-tight text-ink">Verification failed</h1>
      <p className="mt-2 text-sm text-danger">{error}</p>
      <Link href="/login" className="mt-6 inline-block text-sm font-medium text-brand hover:underline">
        Back to sign in
      </Link>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<p className="text-center text-sm text-ink-muted">Loading...</p>}>
      <VerifyEmailContent />
    </Suspense>
  );
}
