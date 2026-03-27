import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Base palette — editorial warmth
        bone: {
          DEFAULT: "#f5f0eb",
          50: "#fdfcfa",
          100: "#f5f0eb",
          200: "#ece3d9",
          300: "#ddd0c2",
          400: "#c9b8a0",
          500: "#b09f86",
        },
        ink: {
          DEFAULT: "#1a1a1a",
          50: "#f7f7f7",
          100: "#e8e8e8",
          200: "#c8c8c8",
          300: "#a0a0a0",
          400: "#6e6e6e",
          500: "#4a4a4a",
          600: "#333333",
          700: "#262626",
          800: "#1a1a1a",
          900: "#0d0d0d",
        },
        // Slate family for panels and surfaces
        slate: {
          50: "#f8f9fb",
          100: "#f1f3f7",
          200: "#e4e8f0",
          300: "#cdd4e0",
          400: "#a6b0c0",
          500: "#7c8898",
          600: "#5c6878",
          700: "#404d5e",
          800: "#2a3444",
          900: "#182030",
          950: "#0e1520",
        },
        // Signal colors — for confidence and status
        "signal-green": {
          DEFAULT: "#16a34a",
          light: "#dcfce7",
          muted: "#bbf7d0",
          dark: "#15803d",
        },
        "signal-amber": {
          DEFAULT: "#d97706",
          light: "#fef3c7",
          muted: "#fde68a",
          dark: "#b45309",
        },
        "signal-red": {
          DEFAULT: "#dc2626",
          light: "#fee2e2",
          muted: "#fecaca",
          dark: "#b91c1c",
        },
      },
      fontFamily: {
        heading: ["var(--font-inter)", "Inter", "system-ui", "sans-serif"],
        body: ["var(--font-inter)", "Inter", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "Instrument Serif", "Georgia", "serif"],
        mono: ["var(--font-mono)", "JetBrains Mono", "Menlo", "monospace"],
      },
      fontSize: {
        "2xs": ["0.625rem", { lineHeight: "0.875rem" }],
      },
      spacing: {
        "panel": "320px",
        "panel-sm": "260px",
        "panel-lg": "400px",
      },
      borderRadius: {
        "sm": "0.25rem",
        DEFAULT: "0.375rem",
        "md": "0.5rem",
        "lg": "0.75rem",
        "xl": "1rem",
      },
      boxShadow: {
        "panel": "0 0 0 1px rgba(26,26,26,0.06), 0 2px 8px rgba(26,26,26,0.04)",
        "card": "0 1px 3px rgba(26,26,26,0.08), 0 1px 2px rgba(26,26,26,0.04)",
        "elevated": "0 4px 16px rgba(26,26,26,0.12), 0 1px 4px rgba(26,26,26,0.06)",
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0", transform: "translateY(4px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "slide-in-left": {
          from: { opacity: "0", transform: "translateX(-8px)" },
          to: { opacity: "1", transform: "translateX(0)" },
        },
        "slide-in-right": {
          from: { opacity: "0", transform: "translateX(8px)" },
          to: { opacity: "1", transform: "translateX(0)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.2s ease-out",
        "slide-in-left": "slide-in-left 0.2s ease-out",
        "slide-in-right": "slide-in-right 0.2s ease-out",
      },
    },
  },
  plugins: [],
};

export default config;
