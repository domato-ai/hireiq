"use client";

import { useTheme } from "@/lib/theme";

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
      className="w-8 h-8 flex items-center justify-center rounded-lg transition-all duration-200"
      style={{
        background: 'var(--nav-btn-bg)',
        border: '1px solid var(--nav-btn-border)',
      }}
    >
      {theme === "dark" ? (
        /* Sun icon — shown in dark mode, click to go light */
        <svg width="15" height="15" viewBox="0 0 15 15" fill="none" style={{ color: 'var(--text-muted)' }}>
          <circle cx="7.5" cy="7.5" r="3" stroke="currentColor" strokeWidth="1.2" />
          <path d="M7.5 1.5v1.5M7.5 12v1.5M1.5 7.5H3M12 7.5h1.5M3.25 3.25l1.06 1.06M10.69 10.69l1.06 1.06M3.25 11.75l1.06-1.06M10.69 4.31l1.06-1.06" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
        </svg>
      ) : (
        /* Moon icon — shown in light mode, click to go dark */
        <svg width="15" height="15" viewBox="0 0 15 15" fill="none" style={{ color: 'var(--text-muted)' }}>
          <path d="M12.5 8.5a5.5 5.5 0 0 1-6.5-6.5 5.5 5.5 0 1 0 6.5 6.5Z" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round" />
        </svg>
      )}
    </button>
  );
}
