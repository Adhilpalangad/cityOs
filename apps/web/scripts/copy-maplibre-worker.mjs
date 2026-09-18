// MapLibre GL JS (v3+) resolves its Web Worker's URL from `import.meta.url`
// at runtime, expecting it to already be an absolute http(s) URL -- see
// node_modules/maplibre-gl/dist/maplibre-gl.mjs's getWorkerUrl(): if the
// module's own URL doesn't match /^https?:/, it silently returns "" instead
// of throwing. Next.js's dev/build bundlers (both webpack and Turbopack)
// don't resolve import.meta.url that way for a package pulled in through
// node_modules, so the worker URL comes back empty and the worker never
// loads. Raster tile layers don't need the worker (they're just images),
// but every GeoJSON-backed layer does (it's what turns vector data into
// renderable tiles) -- so without this, roads/hospitals/vehicles/incidents
// silently never draw, while the base map looks fine.
//
// Fix: serve maplibre-gl's own worker bundle as a static file from /public
// and point maplibregl.setWorkerUrl() at it explicitly (see CityMap.tsx) --
// no CDN dependency, no version-mismatch risk, works in dev and prod.
//
// Runs as a "predev"/"prebuild" step (see package.json) rather than being a
// one-off copied file, so it can't silently go stale on a maplibre-gl
// version bump -- npm install always re-triggers it.
import { copyFileSync, existsSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const srcDir = join(here, "..", "..", "..", "node_modules", "maplibre-gl", "dist");
const destDir = join(here, "..", "public");

mkdirSync(destDir, { recursive: true });

for (const file of ["maplibre-gl-worker.mjs", "maplibre-gl-worker.mjs.map"]) {
  const src = join(srcDir, file);
  if (!existsSync(src)) {
    console.warn(`[copy-maplibre-worker] ${src} not found -- skipping (maplibre-gl not installed yet?)`);
    continue;
  }
  copyFileSync(src, join(destDir, file));
}

console.log("[copy-maplibre-worker] synced maplibre-gl-worker.mjs into public/");
