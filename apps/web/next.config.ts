import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  // Workspace packages ship TypeScript source directly (no build step of
  // their own), so Next.js has to transpile them itself.
  transpilePackages: ["@cityos/types", "@cityos/validation"],
  // Turbopack's own workspace-root inference is unreliable in this
  // monorepo layout (a well-documented class of bug -- see
  // https://github.com/vercel/next.js/issues/92540) and was silently
  // resolving something other than the repo root, so it couldn't see
  // ../../packages/* at all: "Module not found: Can't resolve
  // '@cityos/validation'" despite the symlink in node_modules being
  // completely correct (confirmed directly with require.resolve()).
  // Pointing it at the real monorepo root explicitly fixes it. Both
  // `npm run dev`/`build` here and this repo's Docker build run with cwd
  // already set to apps/web (npm workspace commands, and the Dockerfile's
  // `npm run build:web` from /workspace), so two levels up is the root
  // in both cases.
  turbopack: {
    root: path.resolve(process.cwd(), "..", ".."),
  },
};

export default nextConfig;

