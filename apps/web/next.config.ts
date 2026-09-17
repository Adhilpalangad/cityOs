import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  // Workspace packages ship TypeScript source directly (no build step of
  // their own), so Next.js has to transpile them itself.
  transpilePackages: ["@cityos/types", "@cityos/validation"],
};

export default nextConfig;

