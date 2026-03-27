"use client";

import Link from "next/link";

/**
 * Domato AI icon — two overlapping squares with purple->magenta gradient.
 * Used as the HireIQ brand mark across all pages.
 */
export function DomatoIcon({ size = 20, className = "" }: { size?: number; className?: string }) {
  const id = `domato-grad-${size}`;
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      className={className}
      aria-hidden="true"
    >
      <defs>
        <linearGradient gradientTransform="rotate(25)" id={id} x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#1E0B36" stopOpacity="1" />
          <stop offset="100%" stopColor="#CA3782" stopOpacity="1" />
        </linearGradient>
      </defs>
      <path
        d="M9.382 8.675h13.943v13.943L32 31.293V0H.707zM22.618 23.325H8.675V9.382L0 .707V32h31.293z"
        fill={`url(#${id})`}
      />
    </svg>
  );
}

/** White version for dark backgrounds */
export function DomatoIconWhite({ size = 20, className = "" }: { size?: number; className?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      className={className}
      aria-hidden="true"
    >
      <path
        d="M9.382 8.675h13.943v13.943L32 31.293V0H.707zM22.618 23.325H8.675V9.382L0 .707V32h31.293z"
        fill="white"
        fillOpacity="0.85"
      />
    </svg>
  );
}

/** Full nav logo: icon + HireIQ text — adapts to theme via CSS variables */
export function NavLogo({ variant = "dark" }: { variant?: "dark" | "light" }) {
  return (
    <Link href="/" className="flex items-center gap-2.5 group">
      <div
        className="w-8 h-8 rounded-lg flex items-center justify-center overflow-hidden"
        style={{
          background: 'var(--nav-btn-bg)',
          border: '1px solid var(--nav-btn-border)',
          boxShadow: '0 0 16px rgba(202,55,130,0.15)',
        }}
      >
        {/* Gradient icon for light mode */}
        <span className="logo-icon-light" style={{ display: 'none' }}>
          <DomatoIcon size={18} />
        </span>
        {/* White icon for dark mode */}
        <span className="logo-icon-dark">
          <DomatoIconWhite size={18} />
        </span>
      </div>
      <span
        className="text-[15px] font-semibold"
        style={{ color: 'var(--text-heading)' }}
      >
        HireIQ
      </span>
    </Link>
  );
}
