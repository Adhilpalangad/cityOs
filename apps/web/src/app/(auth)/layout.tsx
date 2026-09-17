import Link from "next/link";

import { Logo } from "@/components/Logo";
import { Card } from "@/components/ui/Card";

export default function AuthLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center px-6 py-16">
      <Link href="/" className="mb-8">
        <Logo />
      </Link>
      <Card className="w-full">{children}</Card>
    </main>
  );
}
