"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState, useMemo } from "react";
import { clsx } from "clsx";
import { getCandidatesByRole, type Candidate, type FactorScore } from "@/lib/mock-data";

interface CandidateTableProps {
  roleId: string;
  workspaceId: string;
  selectedCandidateId?: string;
  factors?: string[];
}

type SortKey = "rank" | "score" | string;
type SortDir = "asc" | "desc";

export function CandidateTable({
  roleId,
  workspaceId,
  selectedCandidateId,
  factors = [],
}: CandidateTableProps) {
  void workspaceId;

  const router = useRouter();
  const searchParams = useSearchParams();

  const [sortKey, setSortKey] = useState<SortKey>("score");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const allCandidates = getCandidatesByRole(roleId);

  const candidates = useMemo(() => {
    return [...allCandidates].sort((a, b) => {
      let av: number;
      let bv: number;

      if (sortKey === "score" || sortKey === "rank") {
        av = a.overallScore;
        bv = b.overallScore;
      } else {
        const afs = a.factorScores.find((f) => f.label === sortKey);
        const bfs = b.factorScores.find((f) => f.label === sortKey);
        av = afs?.score ?? -1;
        bv = bfs?.score ?? -1;
      }

      return sortDir === "desc" ? bv - av : av - bv;
    });
  }, [allCandidates, sortKey, sortDir]);

  // Show up to 5 factor columns (space constraint)
  const factorColumns = factors.slice(0, 5);

  function selectCandidate(candidateId: string) {
    const params = new URLSearchParams(searchParams.toString());
    if (params.get("candidateId") === candidateId) {
      params.delete("candidateId");
    } else {
      params.set("candidateId", candidateId);
    }
    router.push(`?${params.toString()}`, { scroll: false });
  }

  function handleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir((d) => (d === "desc" ? "asc" : "desc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

  const scored = candidates.filter((c) => c.status === "scored").length;

  return (
    <div className="flex flex-col h-full">
      {/* Table header */}
      <div className="flex-shrink-0 px-4 pt-4 pb-3 flex items-center justify-between border-b border-ink/8 bg-bone-50">
        <div>
          <h2 className="text-xs font-semibold uppercase tracking-widest text-ink-400">
            Candidates
          </h2>
          <p className="text-xs text-ink-400 mt-0.5">
            <span className="text-ink font-semibold font-mono">{scored}</span> evaluated ·{" "}
            <span className="text-ink font-semibold font-mono">{candidates.length}</span> total ·
            sorted by{" "}
            <span className="text-ink">{sortKey === "score" ? "fit score" : sortKey}</span>
          </p>
        </div>
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => handleSort("score")}
            className={clsx(
              "text-xs px-2 py-1 rounded border transition-colors",
              sortKey === "score"
                ? "border-ink/20 text-ink bg-bone-200"
                : "border-ink/10 text-ink-400 hover:text-ink hover:bg-ink/4"
            )}
          >
            Score {sortKey === "score" && (sortDir === "desc" ? "↓" : "↑")}
          </button>
        </div>
      </div>

      {/* Scrollable table */}
      <div className="flex-1 overflow-auto">
        <table className="data-table">
          <thead>
            <tr>
              <th className="w-7 pl-4 pr-2">#</th>
              <th className="min-w-[160px]">Candidate</th>
              <SortableTh
                label="Score"
                sortKey="score"
                currentKey={sortKey}
                dir={sortDir}
                onSort={handleSort}
                className="text-right pr-3 w-16"
              />
              {factorColumns.map((col) => (
                <SortableTh
                  key={col}
                  label={col}
                  sortKey={col}
                  currentKey={sortKey}
                  dir={sortDir}
                  onSort={handleSort}
                  className="text-right w-20"
                />
              ))}
              <th className="text-right pr-4 w-20">Confidence</th>
            </tr>
          </thead>
          <tbody>
            {candidates.map((candidate, idx) => (
              <CandidateRow
                key={candidate.id}
                candidate={candidate}
                rank={idx + 1}
                isSelected={selectedCandidateId === candidate.id}
                factorColumns={factorColumns}
                onClick={() => selectCandidate(candidate.id)}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function SortableTh({
  label,
  sortKey,
  currentKey,
  dir,
  onSort,
  className,
}: {
  label: string;
  sortKey: string;
  currentKey: string;
  dir: SortDir;
  onSort: (key: string) => void;
  className?: string;
}) {
  const active = currentKey === sortKey;
  return (
    <th className={className}>
      <button
        onClick={() => onSort(sortKey)}
        className={clsx(
          "flex items-center gap-0.5 ml-auto transition-colors hover:text-ink",
          active ? "text-ink" : "text-ink-400"
        )}
      >
        <span className="truncate max-w-[64px]">{label}</span>
        {active && (
          <span className="text-ink opacity-70">{dir === "desc" ? "↓" : "↑"}</span>
        )}
      </button>
    </th>
  );
}

function CandidateRow({
  candidate,
  rank,
  isSelected,
  factorColumns,
  onClick,
}: {
  candidate: Candidate;
  rank: number;
  isSelected: boolean;
  factorColumns: string[];
  onClick: () => void;
}) {
  return (
    <tr
      onClick={onClick}
      className={clsx(
        "cursor-pointer transition-colors",
        isSelected && "selected"
      )}
    >
      {/* Rank */}
      <td className="pl-4 pr-2 text-ink-400 text-2xs font-mono w-7">
        {rank}
      </td>

      {/* Name + title */}
      <td className="min-w-[160px]">
        <p className="text-sm font-medium text-ink leading-tight">
          {candidate.name}
        </p>
        <p className="text-2xs text-ink-400 mt-0.5">
          {candidate.currentTitle}
          {candidate.currentCompany ? `, ${candidate.currentCompany}` : ""}
        </p>
      </td>

      {/* Overall score with bar */}
      <td className="text-right pr-3 w-16">
        <div className="flex flex-col items-end gap-1">
          <ScoreChip score={candidate.overallScore} />
          <ScoreBar score={candidate.overallScore} />
        </div>
      </td>

      {/* Per-factor scores */}
      {factorColumns.map((col) => {
        const fs: FactorScore | undefined = candidate.factorScores.find(
          (f) => f.label === col
        );
        const score = fs?.score ?? null;
        return (
          <td key={col} className="text-right w-20">
            {score === null ? (
              <span className="text-ink-300 text-xs">—</span>
            ) : (
              <div className="flex flex-col items-end gap-1">
                <span
                  className={clsx(
                    "font-mono text-xs font-semibold",
                    score >= 75
                      ? "text-signal-green"
                      : score >= 50
                      ? "text-signal-amber"
                      : "text-signal-red"
                  )}
                >
                  {score}
                </span>
                <MiniBar score={score} />
              </div>
            )}
          </td>
        );
      })}

      {/* Confidence */}
      <td className="text-right pr-4 w-20">
        <ConfidenceDot confidence={candidate.confidence} />
      </td>
    </tr>
  );
}

function ScoreChip({ score }: { score: number }) {
  const color =
    score >= 75
      ? "text-signal-green-dark bg-signal-green-light"
      : score >= 50
      ? "text-signal-amber-dark bg-signal-amber-light"
      : "text-signal-red-dark bg-signal-red-light";

  return (
    <span
      className={clsx(
        "inline-flex items-center justify-center w-9 h-6 rounded text-xs font-bold font-mono",
        color
      )}
    >
      {score}
    </span>
  );
}

function ScoreBar({ score }: { score: number }) {
  const color =
    score >= 75
      ? "bg-signal-green"
      : score >= 50
      ? "bg-signal-amber"
      : "bg-signal-red";

  return (
    <div className="w-9 h-1 bg-bone-300 rounded-full overflow-hidden">
      <div
        className={clsx("h-full rounded-full", color)}
        style={{ width: `${score}%` }}
      />
    </div>
  );
}

function MiniBar({ score }: { score: number }) {
  const color =
    score >= 75
      ? "bg-signal-green/60"
      : score >= 50
      ? "bg-signal-amber/60"
      : "bg-signal-red/60";

  return (
    <div className="w-9 h-0.5 bg-bone-300 rounded-full overflow-hidden">
      <div
        className={clsx("h-full rounded-full", color)}
        style={{ width: `${score}%` }}
      />
    </div>
  );
}

function ConfidenceDot({
  confidence,
}: {
  confidence: "strong" | "weak" | "not-found";
}) {
  const config = {
    strong: { dot: "bg-signal-green", label: "Strong" },
    weak: { dot: "bg-signal-amber", label: "Weak" },
    "not-found": { dot: "bg-ink-300", label: "N/F" },
  }[confidence];

  return (
    <span className="inline-flex items-center gap-1 justify-end">
      <span className={clsx("w-1.5 h-1.5 rounded-full flex-shrink-0", config.dot)} />
      <span className="text-2xs text-ink-400">{config.label}</span>
    </span>
  );
}
