"use client";

import { clsx } from "clsx";
import {
  getCandidateById,
  getEvidenceForCandidate,
  type EvidenceItem,
  type Candidate,
} from "@/lib/mock-data";

interface EvidencePanelProps {
  roleId: string;
  workspaceId: string;
  candidateId?: string;
}

export function EvidencePanel({
  roleId,
  workspaceId,
  candidateId,
}: EvidencePanelProps) {
  void roleId;
  void workspaceId;

  if (!candidateId) {
    return <EvidenceEmptyState />;
  }

  const candidate = getCandidateById(candidateId);
  if (!candidate) return <EvidenceEmptyState />;

  const evidence = getEvidenceForCandidate(candidateId);

  return (
    <div className="flex flex-col h-full animate-slide-in-right">
      {/* Panel header */}
      <CandidateHeader candidate={candidate} />

      {/* Evidence body */}
      <div className="flex-1 overflow-y-auto">
        {/* Score overview */}
        <ScoreOverview candidate={candidate} />

        {/* Strengths / risks */}
        <StrengthsRisks candidate={candidate} />

        {/* Per-factor evidence */}
        {evidence.length > 0 ? (
          <FactorEvidence evidence={evidence} />
        ) : (
          <InlineFactorScores candidate={candidate} />
        )}
      </div>

      {/* Footer */}
      <div className="flex-shrink-0 border-t border-ink/8 px-4 py-3 flex gap-2">
        <button className="text-xs text-ink-400 hover:text-ink transition-colors px-3 py-1.5 rounded border border-ink/10 hover:bg-ink/4 flex-1">
          Compare
        </button>
        <button className="text-xs text-ink-400 hover:text-ink transition-colors px-3 py-1.5 rounded border border-ink/10 hover:bg-ink/4 flex-1">
          Export brief
        </button>
        <button className="text-xs text-ink-400 hover:text-ink transition-colors px-3 py-1.5 rounded border border-ink/10 hover:bg-ink/4 flex-1">
          Flag
        </button>
      </div>
    </div>
  );
}

/* ─── Candidate header ──────────────────────────────────────────────────────── */

function CandidateHeader({ candidate }: { candidate: Candidate }) {
  return (
    <div className="flex-shrink-0 px-4 pt-4 pb-3 border-b border-ink/8">
      <p className="text-2xs font-semibold uppercase tracking-widest text-ink-400">
        Evidence
      </p>
      <div className="flex items-start justify-between gap-2 mt-1">
        <div>
          <p className="text-sm font-semibold text-ink">{candidate.name}</p>
          <p className="text-xs text-ink-400 mt-0.5">
            {candidate.currentTitle}
            {candidate.currentCompany ? `, ${candidate.currentCompany}` : ""}
          </p>
          <p className="text-2xs text-ink-400 mt-0.5">
            {candidate.location} · {candidate.yearsExp}y exp
          </p>
        </div>
        <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
          <OverallScoreRing score={candidate.overallScore} />
          <ConfidenceBadge confidence={candidate.confidence} />
        </div>
      </div>
    </div>
  );
}

function OverallScoreRing({ score }: { score: number }) {
  const color =
    score >= 75
      ? "text-signal-green-dark bg-signal-green-light border-signal-green/30"
      : score >= 50
      ? "text-signal-amber-dark bg-signal-amber-light border-signal-amber/30"
      : "text-signal-red-dark bg-signal-red-light border-signal-red/30";

  return (
    <div
      className={clsx(
        "w-12 h-12 rounded-full border-2 flex flex-col items-center justify-center",
        color
      )}
    >
      <span className="text-sm font-bold font-mono leading-none">{score}</span>
      <span className="text-2xs opacity-70 leading-none mt-0.5">/ 100</span>
    </div>
  );
}

/* ─── Score overview ────────────────────────────────────────────────────────── */

function ScoreOverview({ candidate }: { candidate: Candidate }) {
  return (
    <div className="px-4 py-4 border-b border-ink/8 space-y-3">
      <h3 className="text-label">Factor scores</h3>
      <div className="space-y-2.5">
        {candidate.factorScores.map((fs) => (
          <FactorScoreRow key={fs.factorId} factorScore={fs} />
        ))}
      </div>
    </div>
  );
}

function FactorScoreRow({
  factorScore,
}: {
  factorScore: {
    factorId: string;
    label: string;
    score: number | null;
    confidence: "strong" | "weak" | "not-found";
    weight: number;
  };
}) {
  const score = factorScore.score;

  const barColor =
    score === null
      ? "bg-ink-200"
      : score >= 75
      ? "bg-signal-green"
      : score >= 50
      ? "bg-signal-amber"
      : "bg-signal-red";

  const textColor =
    score === null
      ? "text-ink-300"
      : score >= 75
      ? "text-signal-green"
      : score >= 50
      ? "text-signal-amber"
      : "text-signal-red";

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 flex-1 min-w-0">
          <span className="text-xs text-ink truncate">{factorScore.label}</span>
          {/* Weight dots */}
          <div className="flex gap-0.5 flex-shrink-0">
            {[1, 2, 3].map((w) => (
              <div
                key={w}
                className={clsx(
                  "w-1 h-1 rounded-full",
                  w <= factorScore.weight ? "bg-ink-400" : "bg-ink-200"
                )}
              />
            ))}
          </div>
        </div>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <ConfidenceDot confidence={factorScore.confidence} />
          <span className={clsx("text-xs font-semibold font-mono w-6 text-right", textColor)}>
            {score ?? "—"}
          </span>
        </div>
      </div>
      {/* Score bar */}
      <div className="h-1 bg-bone-300 rounded-full overflow-hidden">
        <div
          className={clsx("h-full rounded-full transition-all", barColor)}
          style={{ width: score !== null ? `${score}%` : "0%" }}
        />
      </div>
    </div>
  );
}

/* ─── Strengths & Risks ─────────────────────────────────────────────────────── */

function StrengthsRisks({ candidate }: { candidate: Candidate }) {
  return (
    <div className="px-4 py-4 border-b border-ink/8 space-y-4">
      {/* Strengths */}
      <div className="space-y-2">
        <h3 className="text-label text-signal-green-dark">Strengths</h3>
        <ul className="space-y-1.5">
          {candidate.strengths.map((s, i) => (
            <li key={i} className="flex items-start gap-2">
              <span className="text-signal-green mt-0.5 flex-shrink-0 text-xs">+</span>
              <p className="text-xs text-ink-500 leading-snug">{s}</p>
            </li>
          ))}
        </ul>
      </div>

      {/* Risks */}
      {candidate.risks.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-label text-signal-amber-dark">Risks</h3>
          <ul className="space-y-1.5">
            {candidate.risks.map((r, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-signal-amber mt-0.5 flex-shrink-0 text-xs">!</span>
                <p className="text-xs text-ink-500 leading-snug">{r}</p>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Missing evidence */}
      {candidate.missingEvidence.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-label text-ink-400">Missing evidence</h3>
          <ul className="space-y-1">
            {candidate.missingEvidence.map((m, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-ink-300 mt-0.5 flex-shrink-0 text-xs">?</span>
                <p className="text-xs text-ink-400 leading-snug">{m}</p>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

/* ─── Factor evidence (with quotes) ────────────────────────────────────────── */

function FactorEvidence({ evidence }: { evidence: EvidenceItem[] }) {
  return (
    <div className="px-4 py-4 space-y-5">
      <h3 className="text-label">Source citations</h3>
      {evidence.map((item) => (
        <EvidenceCard key={item.factorId} item={item} />
      ))}
    </div>
  );
}

function EvidenceCard({ item }: { item: EvidenceItem }) {
  const hasScore = item.score !== null;

  return (
    <div className="space-y-2">
      {/* Criterion header */}
      <div className="flex items-start justify-between gap-2">
        <p className="text-xs font-semibold text-ink leading-snug flex-1">
          {item.factorLabel}
        </p>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          {hasScore && (
            <span
              className={clsx(
                "text-xs font-bold font-mono",
                item.score! >= 75
                  ? "text-signal-green"
                  : item.score! >= 50
                  ? "text-signal-amber"
                  : "text-signal-red"
              )}
            >
              {item.score}
            </span>
          )}
          <ConfidenceBadge confidence={item.confidence} />
        </div>
      </div>

      {/* Quote */}
      {item.quote && (
        <div className="bg-bone-200 border-l-2 border-ink-400 pl-3 pr-2 py-2 rounded-r">
          <p className="text-2xs text-ink-600 leading-relaxed italic">
            {item.quote}
          </p>
          {item.sourceSection && (
            <p className="text-2xs text-ink-400 mt-1.5 font-mono">
              {item.sourceSection}
            </p>
          )}
        </div>
      )}

      {/* Reasoning */}
      <p className="text-xs text-ink-400 leading-relaxed">{item.reasoning}</p>
    </div>
  );
}

/* ─── Inline factor scores (no evidence data available) ─────────────────────── */

function InlineFactorScores({ candidate }: { candidate: Candidate }) {
  return (
    <div className="px-4 py-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-label">Scoring details</h3>
        <span className="text-2xs text-ink-400">No source citations available</span>
      </div>
      <p className="text-xs text-ink-400 leading-relaxed">
        Detailed per-criterion quotes and reasoning will appear here after the resume has been fully processed.
      </p>
      <div className="space-y-2">
        {candidate.factorScores.map((fs) => (
          <div key={fs.factorId} className="flex items-center justify-between gap-2 py-1">
            <span className="text-xs text-ink">{fs.label}</span>
            <div className="flex items-center gap-2">
              <ConfidenceDot confidence={fs.confidence} />
              <span
                className={clsx(
                  "text-xs font-semibold font-mono",
                  fs.score === null
                    ? "text-ink-300"
                    : fs.score >= 75
                    ? "text-signal-green"
                    : fs.score >= 50
                    ? "text-signal-amber"
                    : "text-signal-red"
                )}
              >
                {fs.score ?? "—"}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ─── Empty state ───────────────────────────────────────────────────────────── */

function EvidenceEmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full px-6 text-center space-y-3">
      <div className="w-10 h-10 rounded-lg bg-bone-200 flex items-center justify-center">
        <EvidenceIcon />
      </div>
      <div>
        <p className="text-sm font-semibold text-ink">Select a candidate</p>
        <p className="text-xs text-ink-400 mt-1 leading-relaxed">
          Click any row to see per-criterion evidence, source quotes, and AI reasoning.
        </p>
      </div>
      <div className="pt-2 border-t border-ink/8 w-full space-y-1">
        <p className="text-2xs text-ink-400 text-left">Evidence includes:</p>
        <ul className="space-y-1 text-left">
          {["Factor scores with bars", "Direct resume quotes", "AI reasoning", "Confidence ratings"].map(
            (item) => (
              <li key={item} className="flex items-center gap-1.5">
                <span className="text-signal-green text-2xs">✓</span>
                <span className="text-2xs text-ink-400">{item}</span>
              </li>
            )
          )}
        </ul>
      </div>
    </div>
  );
}

/* ─── Shared components ─────────────────────────────────────────────────────── */

function ConfidenceBadge({
  confidence,
}: {
  confidence: "strong" | "weak" | "not-found";
}) {
  const config = {
    strong: { label: "Strong", bg: "bg-signal-green-light", text: "text-signal-green-dark", dot: "bg-signal-green" },
    weak: { label: "Weak", bg: "bg-signal-amber-light", text: "text-signal-amber-dark", dot: "bg-signal-amber" },
    "not-found": { label: "N/F", bg: "bg-ink-100", text: "text-ink-400", dot: "bg-ink-300" },
  }[confidence];

  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-2xs font-semibold",
        config.bg,
        config.text
      )}
    >
      <span className={clsx("w-1 h-1 rounded-full", config.dot)} />
      {config.label}
    </span>
  );
}

function ConfidenceDot({
  confidence,
}: {
  confidence: "strong" | "weak" | "not-found";
}) {
  const dot = {
    strong: "bg-signal-green",
    weak: "bg-signal-amber",
    "not-found": "bg-ink-300",
  }[confidence];

  return <span className={clsx("inline-block w-1.5 h-1.5 rounded-full flex-shrink-0", dot)} />;
}

function EvidenceIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 18 18"
      fill="none"
      className="text-ink-300"
      aria-hidden="true"
    >
      <path
        d="M3 4.5h12M3 7.5h9M3 10.5h6M3 13.5h8"
        stroke="currentColor"
        strokeWidth="1.3"
        strokeLinecap="round"
      />
    </svg>
  );
}
