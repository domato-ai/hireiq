import { clsx } from "clsx";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  children: React.ReactNode;
}

/**
 * HireIQ Button — editorial and operational, not generic.
 *
 * Primary   — filled ink, for the one clear action per surface
 * Secondary — outlined, for supporting actions
 * Ghost     — no border, for toolbar actions and inline controls
 * Danger    — muted red, for destructive actions
 */
export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  disabled,
  className,
  children,
  ...props
}: ButtonProps) {
  const isDisabled = disabled || loading;

  return (
    <button
      disabled={isDisabled}
      className={clsx(
        // Base
        "inline-flex items-center justify-center gap-2 rounded font-medium transition-all duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 select-none whitespace-nowrap",

        // Disabled state
        isDisabled && "opacity-40 cursor-not-allowed pointer-events-none",

        // Sizes
        size === "sm" && "px-3 py-1.5 text-xs leading-none",
        size === "md" && "px-4 py-2 text-sm leading-none",
        size === "lg" && "px-5 py-2.5 text-sm leading-none",

        // Variants
        variant === "primary" && [
          "bg-ink text-bone-50",
          "hover:bg-ink-700",
          "active:bg-ink-900",
          "focus-visible:outline-ink",
        ],

        variant === "secondary" && [
          "bg-transparent text-ink border border-ink/20",
          "hover:bg-ink/6 hover:border-ink/30",
          "active:bg-ink/10",
          "focus-visible:outline-ink",
        ],

        variant === "ghost" && [
          "bg-transparent text-ink-400",
          "hover:bg-ink/6 hover:text-ink",
          "active:bg-ink/10",
          "focus-visible:outline-ink",
        ],

        variant === "danger" && [
          "bg-transparent text-signal-red border border-signal-red/20",
          "hover:bg-signal-red-light hover:border-signal-red/30",
          "active:bg-signal-red-muted",
          "focus-visible:outline-signal-red",
        ],

        className
      )}
      {...props}
    >
      {loading ? <SpinnerIcon /> : null}
      {children}
    </button>
  );
}

function SpinnerIcon() {
  return (
    <svg
      width="12"
      height="12"
      viewBox="0 0 12 12"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="animate-spin"
      aria-hidden="true"
    >
      <circle
        cx="6"
        cy="6"
        r="4.5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeOpacity="0.25"
      />
      <path
        d="M6 1.5A4.5 4.5 0 0110.5 6"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}
