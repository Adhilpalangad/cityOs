import Link from "next/link";

import { getApiHealth } from "@/lib/api";
import { env } from "@/lib/env";
import { Logo } from "@/components/Logo";
import { Card } from "@/components/ui/Card";
import { StatusDot } from "@/components/ui/Badge";

export default async function Home() {
  const health = await getApiHealth();
  const apiOnline = health?.status === "healthy";

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center px-6 py-20">
      <Logo className="mb-10" />
      <Card className="w-full text-center sm:p-12">
        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-brand">
          Urban Operating System
        </p>
        <h1 className="mt-3 text-4xl font-bold tracking-tight text-ink sm:text-5xl">
          Run the city on one platform
        </h1>
        <p className="mx-auto mt-4 max-w-md text-balance text-base text-ink-muted">
          City data, digital twin, and cross-department coordination in a single, software-defined
          operating layer.
        </p>

        <dl className="mt-10 grid gap-3 text-left sm:grid-cols-3">
          <Status label="Frontend" value="Online" online />
          <Status label="API Gateway" value={apiOnline ? "Online" : "Unavailable"} online={apiOnline} />
          <Status
            label="Environment"
            value={env.environment === "production" ? "Production" : "Development"}
            online
          />
        </dl>

        <div className="mt-10 flex flex-col justify-center gap-3 sm:flex-row">
          <Link
            href="/login"
            className="inline-flex h-11 items-center justify-center rounded-lg bg-brand px-6 text-sm font-medium text-brand-ink shadow-sm shadow-brand/20 transition-colors hover:bg-brand-strong"
          >
            Sign in
          </Link>
          <Link
            href="/register"
            className="inline-flex h-11 items-center justify-center rounded-lg border border-line px-6 text-sm font-medium text-ink transition-colors hover:border-brand hover:text-brand"
          >
            Create an account
          </Link>
        </div>
      </Card>
    </main>
  );
}

function Status({ label, value, online }: { label: string; value: string; online: boolean }) {
  return (
    <div className="rounded-xl border border-line bg-surface-muted/60 p-4">
      <dt className="text-xs font-medium text-ink-faint">{label}</dt>
      <dd className="mt-1.5 flex items-center gap-2 text-sm font-medium text-ink">
        <StatusDot online={online} />
        {value}
      </dd>
    </div>
  );
}
