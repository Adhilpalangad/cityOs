import { env } from "./env";

export type Health = { status: string; service: string };

export async function getApiHealth(): Promise<Health | null> {
  try {
    const response = await fetch(`${env.apiUrl}/health`, {
      cache: "no-store",
      signal: AbortSignal.timeout(3000),
    });
    if (!response.ok) return null;
    return (await response.json()) as Health;
  } catch {
    return null;
  }
}

