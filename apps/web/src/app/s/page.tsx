"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { NavLogo } from "@/components/ui/logo";
import InterviewPanel from "@/components/interview-panel";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://ca-hireiq-api-dev.delightfulsea-504dfc83.australiaeast.azurecontainerapps.io";

interface FactorDetail {
  score: number; label: string; weight: number; verdict: string;
  jd_required: string; candidate_has: string; reasoning: string;
  matched: string[]; missing: string[];
}

interface CandidateResult {
  id: string; name: string | null; current_title: string | null;
  current_company: string | null; location: string | null;
  years_experience: number | null; overall_score: number;
  recommendation: string; summary: string;
  factor_scores: Record<string, FactorDetail>;
  strengths: string[]; risks: string[]; missing_evidence: string[];
}

const VERDICT_COLOR: Record<string, string> = { strong: "#34d399", partial: "#fbbf24", weak: "#f87171", missing: "#666" };
function sc(s: number) { return s >= 75 ? "#34d399" : s >= 50 ? "#fbbf24" : "#f87171"; }
const REC: Record<string, { label: string; color: string; bg: string }> = {
  strong_yes: { label: "Strong Yes", color: "#34d399", bg: "rgba(52,211,153,0.10)" },
  yes: { label: "Yes", color: "#60a5fa", bg: "rgba(96,165,250,0.10)" },
  maybe: { label: "Maybe", color: "#fbbf24", bg: "rgba(251,191,36,0.10)" },
  no: { label: "No", color: "#f87171", bg: "rgba(248,113,113,0.10)" },
};

function ShortlistContent() {
  const searchParams = useSearchParams();
  const id = searchParams.get("id") || "";
  const [data, setData] = useState<{ analysis: { candidates: CandidateResult[]; jd_requirements?: Record<string, unknown> } } | null>(null);
  const [error, setError] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    if (!id) { setError("No shortlist ID provided"); return; }
    fetch(`${API_URL}/api/v1/shortlists/${id}`)
      .then((r) => { if (!r.ok) throw new Error("Not found"); return r.json(); })
      .then(setData)
      .catch((e) => setError(e.message));
  }, [id]);

  if (error) return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-4" style={{ background: "var(--page-bg)" }}>
      <p className="text-[16px]" style={{ color: "var(--text-muted)" }}>This shortlist link has expired or doesn&apos;t exist.</p>
      <Link href="/" className="text-[14px] font-semibold px-5 py-2.5 rounded-xl"
        style={{ background: "linear-gradient(135deg, #7c5cff 0%, #6346e0 100%)", color: "#fff" }}>
        Try HireIQ Free
      </Link>
    </div>
  );

  if (!data) return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: "var(--page-bg)" }}>
      <p style={{ color: "var(--text-muted)" }}>Loading shortlist...</p>
    </div>
  );

  const candidates = data.analysis.candidates || [];

  return (
    <div className="min-h-screen" style={{ background: "var(--page-bg)" }}>
      <nav className="flex items-center justify-between px-6 py-4 max-w-3xl mx-auto">
        <NavLogo variant="dark" />
        <Link href="/" className="text-[13px] font-semibold px-4 py-2 rounded-lg"
          style={{ background: "linear-gradient(135deg, #7c5cff 0%, #6346e0 100%)", color: "#fff" }}>
          Try HireIQ Free
        </Link>
      </nav>
      <div className="max-w-3xl mx-auto px-6 pb-16">
        <div className="mb-6">
          <h1 className="text-xl font-semibold mb-1" style={{ color: "var(--text-heading)" }}>Shared Shortlist</h1>
          <p className="text-[13px]" style={{ color: "var(--text-muted)" }}>{candidates.length} candidates ranked by evidence strength</p>
        </div>
        <div className="space-y-3">
          {candidates.map((c, i) => {
            const rec = REC[c.recommendation] || REC.maybe;
            const expanded = expandedId === c.id;
            return (
              <div key={c.id} className="rounded-xl overflow-hidden" style={{ background: "var(--card-bg)", border: "1px solid var(--card-border)" }}>
                <div className="flex items-start gap-3 px-4 pt-3.5 pb-2 cursor-pointer" onClick={() => setExpandedId(expanded ? null : c.id)}>
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 text-[13px] font-bold"
                    style={{ background: sc(c.overall_score) + "18", color: sc(c.overall_score) }}>#{i + 1}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-[14px] font-semibold truncate" style={{ color: "var(--text-heading)" }}>{c.name || "Unknown"}</span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full uppercase" style={{ background: rec.bg, color: rec.color }}>{rec.label}</span>
                    </div>
                    <p className="text-[12px] truncate" style={{ color: "var(--text-muted)" }}>
                      {c.current_title}{c.current_company ? ` at ${c.current_company}` : ""}{c.location ? ` | ${c.location}` : ""}{c.years_experience ? ` | ${c.years_experience}yr` : ""}
                    </p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <span className="text-[20px] font-bold" style={{ color: sc(c.overall_score) }}>{c.overall_score}</span>
                    <span className="text-[11px]" style={{ color: "var(--text-faint)" }}>%</span>
                  </div>
                </div>
                {expanded && (
                  <div className="px-4 pb-4">
                    <p className="text-[12px] leading-relaxed mb-3" style={{ color: "var(--text-muted)" }}>{c.summary}</p>
                    <div className="space-y-1.5 mb-3">
                      {Object.entries(c.factor_scores).map(([key, f]) => (
                        <div key={key} className="flex items-center gap-2">
                          <span className="text-[11px] w-[120px] truncate" style={{ color: "var(--text-faint)" }}>{f.label}</span>
                          <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ background: "var(--input-bg)" }}>
                            <div className="h-full rounded-full" style={{ width: `${f.score}%`, background: VERDICT_COLOR[f.verdict] || "#666" }} />
                          </div>
                          <span className="text-[11px] w-8 text-right font-medium" style={{ color: VERDICT_COLOR[f.verdict] }}>{f.score}</span>
                        </div>
                      ))}
                    </div>
                    {c.strengths.length > 0 && (
                      <div className="mb-2">
                        <p className="text-[10px] font-semibold uppercase mb-1" style={{ color: "#34d399" }}>Strengths</p>
                        {c.strengths.map((s, j) => <p key={j} className="text-[11px]" style={{ color: "var(--text-muted)" }}>+ {s}</p>)}
                      </div>
                    )}
                    {c.risks.length > 0 && (
                      <div>
                        <p className="text-[10px] font-semibold uppercase mb-1" style={{ color: "#f87171" }}>Risks</p>
                        {c.risks.map((r, j) => <p key={j} className="text-[11px]" style={{ color: "var(--text-muted)" }}>- {r}</p>)}
                      </div>
                    )}
                    <InterviewPanel
                      candidate={{
                        name: c.name,
                        current_title: c.current_title,
                        current_company: c.current_company,
                        years_experience: c.years_experience,
                        strengths: c.strengths,
                        risks: c.risks,
                        missing_evidence: c.missing_evidence,
                      }}
                      jdRequirements={data.analysis.jd_requirements || {}}
                    />
                  </div>
                )}
              </div>
            );
          })}
        </div>
        <div className="mt-8 p-6 rounded-2xl text-center" style={{ background: "var(--card-bg)", border: "1px solid var(--card-border)" }}>
          <p className="text-[16px] font-semibold mb-2" style={{ color: "var(--text-heading)" }}>Want to rank your own candidates?</p>
          <p className="text-[13px] mb-4" style={{ color: "var(--text-muted)" }}>Paste a job description, upload resumes, get a ranked shortlist in 30 seconds.</p>
          <Link href="/" className="inline-block px-6 py-3 rounded-xl text-[14px] font-semibold"
            style={{ background: "linear-gradient(135deg, #7c5cff 0%, #6346e0 100%)", color: "#fff", boxShadow: "0 0 20px rgba(124,92,255,0.3)" }}>
            Try HireIQ Free
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function SharedShortlistPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center" style={{ background: "var(--page-bg)" }}><p style={{ color: "var(--text-muted)" }}>Loading...</p></div>}>
      <ShortlistContent />
    </Suspense>
  );
}
