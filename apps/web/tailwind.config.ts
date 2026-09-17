import type { Config } from "tailwindcss";

// Each color below aliases a CSS custom property defined in globals.css
// (--bg, --brand, ...), which is redefined per color-scheme there -- so
// e.g. `bg-brand` always resolves to the right value for light/dark
// automatically, without a `dark:` variant on every class.
const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)",
        surface: "var(--surface)",
        "surface-muted": "var(--surface-muted)",
        line: "var(--line)",
        ink: "var(--ink)",
        "ink-muted": "var(--ink-muted)",
        "ink-faint": "var(--ink-faint)",
        brand: "var(--brand)",
        "brand-strong": "var(--brand-strong)",
        "brand-ink": "var(--brand-ink)",
        success: "var(--success)",
        danger: "var(--danger)",
        "danger-strong": "var(--danger-strong)",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
