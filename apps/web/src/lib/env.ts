const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const env = {
  apiUrl: apiUrl.replace(/\/$/, ""),
  environment: process.env.NODE_ENV ?? "development",
} as const;

