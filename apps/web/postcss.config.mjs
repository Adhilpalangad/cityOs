// Tailwind v3 (pure JS content scanning), not v4: v4's PostCSS plugin
// depends on a native Rust binary (@tailwindcss/oxide) to walk the
// filesystem and find class names, and on this machine that binary's file
// I/O silently returns nothing -- content-based processing works fine, but
// reading a file by path or listing a directory does not, which is the
// signature of security software blocking an unsigned native addon's
// syscalls. Since that isn't something a project can fix for every future
// developer's machine, Tailwind v3 avoids the native dependency entirely:
// content scanning goes through plain Node `fs`, which is unaffected.
const config = { plugins: { tailwindcss: {}, autoprefixer: {} } };

export default config;
