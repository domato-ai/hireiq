import { clsx } from "clsx";

type Confidence = "strong" | "weak" | "not-found";

interface ConfidenceBadgeProps {
  confidence: Confidence;
  showLabel?: boolean;
  className?: string;
}

const CONFIDENCE_CONFIG: Record<
  Confidence,
  { label: string; dotClass: string; textClass: string; bgClass: string }
> = {
  strong: {
    label: "Strong",
    dotClass: "bg-signal-green",
    textClass: "text-signal-green-dark",
    bgClass: "bg-signal-green-light",
  },
  weak: {
    label: "Weak",
    dotClass: "bg-signal-amber",
    textClass: "text-signal-amber-dark",
    bgClass: "bg-signal-amber-light",
  },
  "not-found": {
    label: "Not found",
    dotClass: "bg-ink-300",
    textClass: "text-ink-400",
    bgClass: "bg-ink-100",
  },
};

/**
 * Confidence badge — signals evidence strength for a scored criterion.
 *
 * strong     — clear, direct evidence found in the CV
 * weak       — indirect or inferred evidence; confidence is lower
 * not-found  — criterion not addressed in the document
 */
export function ConfidenceBadge({
  confidence,
  showLabel = true,
  className,
}: ConfidenceBadgeProps) {
  const config = CONFIDENCE_CONFIG[confidence];

  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-2xs font-semibold",
        config.bgClass,
        config.textClass,
        className
      )}
      title={`Evidence confidence: ${config.label}`}
    >
      <span
        className={clsx("w-1.5 h-1.5 rounded-full flex-shrink-0", config.dotClass)}
        aria-hidden="true"
      />
      {showLabel && config.label}
    </span>
  );
}

/* ─── Generic status badge ──────────────────────────────────────────────────── */

type StatusVariant =
  | "default"
  | "active"
  | "processing"
  | "done"
  | "error"
  | "draft";

interface StatusBadgeProps {
  label: string;
  variant?: StatusVariant;
  className?: string;
}

const STATUS_STYLES: Record<StatusVariant, string> = {
  default: "bg-ink-100 text-ink-500",
  active: "bg-signal-green-light text-signal-green-dark",
  processing: "bg-signal-amber-light text-signal-amber-dark",
  done: "bg-signal-green-light text-signal-green-dark",
  error: "bg-signal-red-light text-signal-red-dark",
  draft: "bg-bone-200 text-ink-400",
};

export function StatusBadge({
  label,
  variant = "default",
  className,
}: StatusBadgeProps) {
  return (
    <span
      className={clsx(
        "inline-flex items-center px-2 py-0.5 rounded-full text-2xs font-semibold",
        STATUS_STYLES[variant],
        className
      )}
    >
      {label}
    </span>
  );
}

/* ─── Score badge ───────────────────────────────────────────────────────────── */

interface ScoreBadgeProps {
  score: number;
  className?: string;
}

/**
 * Renders a numeric score (0–100) with semantic color coding.
 * 75+  → green (meets bar)
 * 50–74 → amber (borderline)
 * <50  → red (below bar)
 */
export function ScoreBadge({ score, className }: ScoreBadgeProps) {
  const [colorClass, bgClass] =
    score >= 75
      ? ["text-signal-green-dark", "bg-signal-green-light"]
      : score >= 50
      ? ["text-signal-amber-dark", "bg-signal-amber-light"]
      : ["text-signal-red-dark", "bg-signal-red-light"];

  return (
    <span
      className={clsx(
        "inline-flex items-center justify-center w-9 h-6 rounded text-xs font-semibold font-mono",
        colorClass,
        bgClass,
        className
      )}
    >
      {score}
    </span>
  );
}
