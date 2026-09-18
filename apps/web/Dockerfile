FROM node:22-alpine AS deps
WORKDIR /workspace
COPY package.json package-lock.json* ./
COPY apps/web/package.json apps/web/package.json
# apps/web depends on @cityos/types and @cityos/validation as npm workspace
# packages (root package.json's "packages/*" entry). npm needs every
# workspace member's package.json present to link them, not just the one
# being installed -- without this, `npm install` silently skips linking
# @cityos/validation/@cityos/types into node_modules and the later `next
# build` fails with "Module not found: Can't resolve '@cityos/validation'".
COPY packages/ ./packages/
RUN npm install --workspace=@cityos/web --include-workspace-root

FROM node:22-alpine AS builder
WORKDIR /workspace
COPY --from=deps /workspace/node_modules ./node_modules
COPY . .
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
# --webpack, not Turbopack (the project default): Turbopack has a known,
# currently-unfixed bug where it silently ignores next.config.ts's
# turbopack.root and misdetects the workspace root in exactly this
# npm-workspace-from-the-repo-root invocation shape, so `next build` fails
# with "Module not found: Can't resolve '@cityos/validation'" even though
# the module is genuinely there and correctly linked (confirmed directly --
# require.resolve() finds it fine; only Turbopack's bundler can't).
# See https://github.com/vercel/next.js/issues/92540. `next dev`/`build`
# outside Docker aren't affected -- only this exact invocation is -- so
# only this build step is pinned to webpack, not local development.
RUN npm run build:web -- --webpack

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
USER node
COPY --from=builder --chown=node:node /workspace/apps/web/.next/standalone ./
COPY --from=builder --chown=node:node /workspace/apps/web/.next/static ./apps/web/.next/static
EXPOSE 3000
CMD ["node", "apps/web/server.js"]

