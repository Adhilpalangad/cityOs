"use client";

import Link from "next/link";
import { useState } from "react";
import { registerSchema } from "@cityos/validation";

import { ApiError, register } from "@/lib/auth-api";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

export default function RegisterPage() {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [registered, setRegistered] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    const parsed = registerSchema.safeParse({ email, password, full_name: fullName });
    if (!parsed.success) {
      setError(parsed.error.issues[0]?.message ?? "Check the form and try again.");
      return;
    }
    setSubmitting(true);
    try {
      await register(parsed.data);
      setRegistered(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Try again.");
    } finally {
      setSubmitting(false);
    }
  }

  if (registered) {
    return (
      <div className="text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-success/12">
          <svg className="h-6 w-6 text-success" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path
              d="M5 13l4 4L19 7"
              stroke="currentColor"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
        <h1 className="text-2xl font-semibold tracking-tight text-ink">Check your email</h1>
        <p className="mt-2 text-sm text-ink-muted">
          We&rsquo;ve sent a verification link to <strong className="text-ink">{email}</strong>. In
          this development environment no real email is sent &mdash; the link is written to the
          identity service&rsquo;s logs instead.
        </p>
        <Link href="/login" className="mt-6 inline-block text-sm font-medium text-brand hover:underline">
          Back to sign in
        </Link>
      </div>
    );
  }

  return (
    <>
      <h1 className="text-2xl font-semibold tracking-tight text-ink">Create an account</h1>
      <p className="mt-1.5 text-sm text-ink-muted">Join CityOS as a citizen.</p>

      <form onSubmit={onSubmit} noValidate className="mt-7 space-y-4">
        <Input
          label="Full name"
          type="text"
          autoComplete="name"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
        />
        <Input
          label="Email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <Input
          label="Password"
          type="password"
          autoComplete="new-password"
          hint="At least 8 characters, with one letter and one digit."
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        {error && (
          <p role="alert" className="rounded-lg bg-danger/10 px-3.5 py-2.5 text-sm text-danger">
            {error}
          </p>
        )}

        <Button type="submit" size="lg" loading={submitting} className="w-full">
          {submitting ? "Creating account..." : "Create account"}
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-ink-muted">
        Already have an account?{" "}
        <Link href="/login" className="font-medium text-brand hover:underline">
          Sign in
        </Link>
      </p>
    </>
  );
}
