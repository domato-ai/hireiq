"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import Link from "next/link";
import { NavLogo } from "@/components/ui/logo";
import { ThemeToggle } from "@/components/ui/theme-toggle";

/* ─── API ────────────────────────────────────────────────────────────────── */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://ca-hireiq-api-dev.delightfulsea-504dfc83.australiaeast.azurecontainerapps.io";

/* ─── Types ─────────────────────────────────────────────────────────────── */

type Step = "idle" | "analyzing" | "results";

interface FactorDetail {
  score: number;
  label: string;
  weight: number;
  verdict: "strong" | "partial" | "weak" | "missing";
  jd_required: string;
  candidate_has: string;
  reasoning: string;
  matched: string[];
  missing: string[];
}

interface CandidateResult {
  id: string;
  name: string | null;
  current_title: string | null;
  current_company: string | null;
  location: string | null;
  years_experience: number | null;
  overall_score: number;
  recommendation: string; // "strong_yes" | "yes" | "maybe" | "no"
  summary: string;
  factor_scores: Record<string, FactorDetail>;
  strengths: string[];
  risks: string[];
  missing_evidence: string[];
}

interface AnalysisResult {
  analysis_id: string;
  jd_requirements: Record<string, unknown>;
  candidates: CandidateResult[];
  total_processed: number;
  total_skipped: number;
}

/* ─── Verdict helpers ────────────────────────────────────────────────────── */

const VERDICT_COLOR: Record<string, string> = {
  strong: "#34d399",
  partial: "#fbbf24",
  weak: "#f87171",
  missing: "var(--text-faint)",
};

const VERDICT_BG: Record<string, string> = {
  strong: "rgba(52,211,153,0.10)",
  partial: "rgba(251,191,36,0.10)",
  weak: "rgba(248,113,113,0.10)",
  missing: "var(--input-bg)",
};

const VERDICT_LABEL: Record<string, string> = {
  strong: "Strong",
  partial: "Partial",
  weak: "Weak",
  missing: "Missing",
};

const RECOMMENDATION_META: Record<string, { label: string; color: string; bg: string; border: string }> = {
  strong_yes: { label: "Strong Yes", color: "#34d399", bg: "rgba(52,211,153,0.10)", border: "rgba(52,211,153,0.25)" },
  yes: { label: "Yes", color: "#60a5fa", bg: "rgba(96,165,250,0.10)", border: "rgba(96,165,250,0.25)" },
  maybe: { label: "Maybe", color: "#fbbf24", bg: "rgba(251,191,36,0.10)", border: "rgba(251,191,36,0.25)" },
  no: { label: "No", color: "#f87171", bg: "rgba(248,113,113,0.10)", border: "rgba(248,113,113,0.25)" },
};

function scoreColor(score: number) {
  return score >= 75 ? "#34d399" : score >= 50 ? "#fbbf24" : "#f87171";
}

/* ─── Main page ─────────────────────────────────────────────────────────── */

export default function HomePage() {
  const [jdText, setJdText] = useState("");
  const [jdFile, setJdFile] = useState<File | null>(null);
  const [jdMode, setJdMode] = useState<"paste" | "upload">("paste");
  const [files, setFiles] = useState<File[]>([]);
  const [dragging, setDragging] = useState(false);
  const [step, setStep] = useState<Step>("idle");
  const [error, setError] = useState("");
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [progressStep, setProgressStep] = useState(0);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [compareMode, setCompareMode] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const jdFileInputRef = useRef<HTMLInputElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);
  const [user, setUser] = useState<{ email: string; name: string; plan: string } | null>(null);
  const [usage, setUsage] = useState<{ used: number; limit: number; remaining: number; plan: string } | null>(null);
  const [limitModal, setLimitModal] = useState<{ plan: string; used: number; limit: number; hint: string } | null>(null);

  useEffect(() => {
    try {
      const stored = localStorage.getItem("hireiq-user");
      if (stored) setUser(JSON.parse(stored));
    } catch {}
  }, []);

  const fetchUsage = async () => {
    try {
      const headers: Record<string, string> = {};
      const token = typeof window !== "undefined" ? localStorage.getItem("hireiq-token") : null;
      if (token) headers["Authorization"] = `Bearer ${token}`;
      const res = await fetch(`${API_URL}/api/v1/analyze/usage`, { headers });
      if (res.ok) setUsage(await res.json());
    } catch {}
  };

  useEffect(() => {
    fetchUsage();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const handleSignOut = () => {
    localStorage.removeItem("hireiq-token");
    localStorage.removeItem("hireiq-user");
    setUser(null);
  };

  // Progress pipeline steps — timed to match real API processing
  const progressSteps = [
    { label: "Reading job description", detail: "Extracting role requirements, must-have skills, and seniority level", icon: "📋", pct: 8 },
    { label: "Parsing resumes", detail: `Opening ${files.length} document${files.length !== 1 ? "s" : ""} and extracting text content`, icon: "📄", pct: 20 },
    { label: "Identifying candidates", detail: "Extracting names, experience, skills, and education from each resume", icon: "🔍", pct: 40 },
    { label: "Matching skills to requirements", detail: "Comparing each candidate's skills against your must-have and nice-to-have criteria", icon: "🎯", pct: 55 },
    { label: "Evaluating experience levels", detail: "Checking years of experience, seniority fit, and relevant industry background", icon: "📊", pct: 70 },
    { label: "Scoring and ranking", detail: "Running weighted scoring across all factors for each candidate", icon: "⚖️", pct: 85 },
    { label: "Generating shortlist", detail: "Identifying strengths, risks, and evidence gaps for your top matches", icon: "✨", pct: 95 },
  ];

  useEffect(() => {
    if (step !== "analyzing") {
      setProgressStep(0);
      return;
    }
    const interval = Math.max(1500, (files.length * 1200));
    const timer = setInterval(() => {
      setProgressStep((prev) => {
        if (prev >= progressSteps.length - 1) return prev;
        return prev + 1;
      });
    }, interval);
    return () => clearInterval(timer);
  }, [step, files.length, progressSteps.length]);

  const hasJD = jdMode === "paste" ? jdText.trim().length > 20 : jdFile !== null;
  const hasFiles = files.length > 0;
  const canStart = hasJD && hasFiles;

  const sortedCandidates = analysisResult
    ? [...analysisResult.candidates].sort((a, b) => b.overall_score - a.overall_score)
    : [];
  const topCandidate = sortedCandidates[0] ?? null;

  const handleFiles = useCallback((newFiles: FileList | File[]) => {
    const valid = Array.from(newFiles).filter((f) =>
      ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"].includes(f.type)
    );
    setFiles((prev) => {
      const existing = new Set(prev.map((f) => f.name + f.size));
      const deduped = valid.filter((f) => !existing.has(f.name + f.size));
      return [...prev, ...deduped];
    });
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      if (e.dataTransfer.files.length) handleFiles(e.dataTransfer.files);
    },
    [handleFiles]
  );

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleStart = async () => {
    setStep("analyzing");
    setError("");
    setExpandedId(null);
    setSelectedIds(new Set());
    setCompareMode(false);

    try {
      let jdContent = jdText;
      if (jdMode === "upload" && jdFile) {
        jdContent = await jdFile.text();
      }

      const formData = new FormData();
      formData.append("jd_text", jdContent);

      for (const file of files) {
        formData.append("files", file);
      }

      const headers: Record<string, string> = {};
      const token = typeof window !== "undefined" ? localStorage.getItem("hireiq-token") : null;
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const response = await fetch(`${API_URL}/api/v1/analyze`, {
        method: "POST",
        headers,
        body: formData,
      });

      if (response.status === 429) {
        const data = await response.json();
        setLimitModal({
          plan: data.detail.plan,
          used: data.detail.used,
          limit: data.detail.limit,
          hint: data.detail.upgrade_hint,
        });
        setStep("idle");
        return;
      }

      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: "Analysis failed" }));
        throw new Error(err.detail || `Error ${response.status}`);
      }

      const data = await response.json();
      if (data.usage) {
        setUsage(data.usage);
      }
      setAnalysisResult(data);
      setStep("results");
      fetchUsage();
      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 100);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
      setStep("idle");
    }
  };

  const handleReset = () => {
    setStep("idle");
    setAnalysisResult(null);
    setJdText("");
    setJdFile(null);
    setFiles([]);
    setError("");
    setExpandedId(null);
    setSelectedIds(new Set());
    setCompareMode(false);
  };

  const toggleExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  const toggleSelect = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const selectedCandidates = sortedCandidates.filter((c) => selectedIds.has(c.id));

  return (
    <div className="min-h-screen relative" style={{ background: "var(--page-bg)" }}>
      {/* Radial glow behind hero */}
      <div
        className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] pointer-events-none"
        style={{
          background: "radial-gradient(ellipse 50% 70% at 50% 0%, var(--glow-color) 0%, transparent 70%)",
        }}
      />

      {/* Dot grid */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage: "radial-gradient(var(--dot-grid-color) 1px, transparent 1px)",
          backgroundSize: "24px 24px",
        }}
      />

      {/* ── Nav ── */}
      <nav className="relative z-20 flex items-center justify-between px-6 md:px-10 py-5 max-w-5xl mx-auto">
        <NavLogo variant="dark" />
        <div className="flex items-center gap-4">
          {user ? (
            <>
              <span className="text-[13px] transition-colors" style={{ color: "var(--text-muted)" }}>
                {user.email}
              </span>
              <ThemeToggle />
              <button
                onClick={handleSignOut}
                className="text-[13px] font-medium px-4 py-2 rounded-lg transition-all duration-200"
                style={{
                  color: "var(--text-heading)",
                  background: "var(--nav-btn-bg)",
                  border: "1px solid var(--nav-btn-border)",
                }}
              >
                Sign out
              </button>
            </>
          ) : (
            <>
              <Link href="/signup" className="text-[13px] transition-colors" style={{ color: "var(--text-muted)" }}>
                Create workspace
              </Link>
              <ThemeToggle />
              <Link
                href="/login"
                className="text-[13px] font-medium px-4 py-2 rounded-lg transition-all duration-200"
                style={{
                  color: "var(--text-heading)",
                  background: "var(--nav-btn-bg)",
                  border: "1px solid var(--nav-btn-border)",
                }}
              >
                Sign in
              </Link>
            </>
          )}
        </div>
      </nav>

      {/* ── Hero ── */}
      <div className="relative z-10 flex flex-col items-center pt-16 md:pt-24 pb-20 px-6">
        {/* Badge */}
        <div
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full mb-8 home-stagger-1"
          style={{
            background: "rgba(124,92,255,0.08)",
            border: "1px solid rgba(124,92,255,0.15)",
          }}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-[#7c5cff] metric-pulse" />
          <span className="text-[12px] font-medium" style={{ color: "rgba(124,92,255,0.9)" }}>
            Evidence-first hiring decisions
          </span>
        </div>

        {/* Heading */}
        <h1
          className="text-center font-display text-5xl md:text-6xl lg:text-7xl tracking-[-0.03em] leading-[1.05] max-w-3xl home-stagger-2"
          style={{ color: "var(--text-heading)" }}
        >
          {step === "analyzing" ? (
            "Analyzing candidates"
          ) : step === "results" ? (
            <>
              Here&rsquo;s your <span className="italic" style={{ color: "#a78bfa" }}>shortlist</span>
            </>
          ) : (
            <>
              Find the <span className="italic" style={{ color: "#a78bfa" }}>right</span> hire
            </>
          )}
        </h1>

        <p
          className="text-center text-base md:text-lg mt-5 max-w-xl leading-relaxed home-stagger-2"
          style={{ color: "var(--text-muted)" }}
        >
          {step === "results"
            ? "Ranked by evidence strength. Click a card to see full analysis."
            : "Paste a job description, upload resumes, and get an evidence-backed shortlist in seconds."}
        </p>

        {/* ── Error banner ── */}
        {error && (
          <div
            className="w-full max-w-[640px] mb-4 px-4 py-3 rounded-xl text-sm"
            style={{ background: "var(--error-bg)", border: "1px solid var(--error-border)", color: "var(--error-text)" }}
          >
            {error}
          </div>
        )}

        {/* ── Main card ── */}
        <div
          className="w-full max-w-[640px] mt-12 rounded-2xl p-5 home-stagger-3"
          style={{
            background: "var(--card-bg)",
            border: "1px solid var(--card-border)",
            boxShadow: "var(--card-shadow), 0 0 80px rgba(124,92,255,0.04)",
          }}
        >
          {step === "analyzing" ? (
            <div className="py-6 px-1">
              {/* Progress bar */}
              <div className="mb-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[12px] font-medium" style={{ color: "var(--text-body)" }}>
                    Analyzing {files.length} resume{files.length !== 1 ? "s" : ""}
                  </span>
                  <span className="text-[11px] font-mono" style={{ color: "var(--text-faint)" }}>
                    {progressSteps[progressStep]?.pct ?? 0}%
                  </span>
                </div>
                <div className="w-full h-1.5 rounded-full overflow-hidden" style={{ background: "var(--input-bg)" }}>
                  <div
                    className="h-full rounded-full transition-all duration-1000 ease-out"
                    style={{
                      width: `${progressSteps[progressStep]?.pct ?? 0}%`,
                      background: "linear-gradient(90deg, #7c5cff 0%, #a78bfa 100%)",
                      boxShadow: "0 0 8px rgba(124,92,255,0.4)",
                    }}
                  />
                </div>
              </div>

              {/* Step list */}
              <div className="space-y-1">
                {progressSteps.map((s, i) => {
                  const isDone = i < progressStep;
                  const isActive = i === progressStep;
                  const isPending = i > progressStep;

                  return (
                    <div
                      key={i}
                      className="flex items-start gap-3 py-2 px-3 rounded-lg transition-all duration-300"
                      style={{
                        background: isActive ? "var(--input-bg)" : "transparent",
                        opacity: isPending ? 0.35 : 1,
                      }}
                    >
                      {/* Status indicator */}
                      <div className="flex-shrink-0 mt-0.5">
                        {isDone ? (
                          <div className="w-5 h-5 rounded-full flex items-center justify-center" style={{ background: "rgba(52,211,153,0.15)" }}>
                            <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                              <path d="M2 5.5L4 7.5L8 3" stroke="#34d399" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                          </div>
                        ) : isActive ? (
                          <div className="w-5 h-5 rounded-full flex items-center justify-center analyzing-spinner" style={{ background: "rgba(124,92,255,0.1)" }}>
                            <div className="w-2 h-2 rounded-full" style={{ background: "#7c5cff" }} />
                          </div>
                        ) : (
                          <div className="w-5 h-5 rounded-full" style={{ background: "var(--input-bg)", border: "1px solid var(--card-border)" }} />
                        )}
                      </div>

                      {/* Step content */}
                      <div className="flex-1 min-w-0">
                        <p className="text-[12px] font-medium" style={{ color: isDone ? "var(--ready-color)" : isActive ? "var(--text-body)" : "var(--text-faint)" }}>
                          {s.label}
                        </p>
                        {isActive && (
                          <p className="text-[11px] mt-0.5 progress-detail-enter" style={{ color: "var(--text-muted)" }}>
                            {s.detail}
                          </p>
                        )}
                      </div>

                      {/* Emoji icon */}
                      <span className="text-[13px] flex-shrink-0 mt-0.5" style={{ opacity: isPending ? 0.3 : 0.7 }}>
                        {s.icon}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : step === "results" ? (
            /* ── Results summary card ── */
            <div className="py-4 px-1">
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#34d399] metric-pulse" />
                  <span className="text-[13px] font-medium" style={{ color: "var(--text-body)" }}>
                    {sortedCandidates.length} candidates analyzed
                  </span>
                  <span style={{ color: "var(--text-faint)" }}>·</span>
                  <span className="text-[13px]" style={{ color: "var(--text-muted)" }}>
                    Top match:{" "}
                    <span className="font-semibold" style={{ color: "var(--text-heading)" }}>
                      {topCandidate?.name ?? "Unknown"}
                    </span>{" "}
                    <span style={{ color: "#a78bfa" }}>({topCandidate?.overall_score ?? 0}/100)</span>
                  </span>
                </div>
                <button
                  onClick={handleReset}
                  className="text-[11px] px-2.5 py-1 rounded-lg transition-all duration-200"
                  style={{
                    color: "var(--text-muted)",
                    border: "1px solid var(--card-border)",
                    background: "var(--input-bg)",
                  }}
                >
                  New analysis
                </button>
              </div>
            </div>
          ) : (
            <>
              {/* ── JD Section ── */}
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2.5">
                  <label className="text-[12px] font-medium uppercase tracking-wider" style={{ color: "var(--text-muted)" }}>
                    Job Description
                  </label>
                  {/* Toggle */}
                  <div className="flex items-center gap-0.5 p-0.5 rounded-md" style={{ background: "var(--input-bg)" }}>
                    {(["paste", "upload"] as const).map((mode) => (
                      <button
                        key={mode}
                        onClick={() => setJdMode(mode)}
                        className="px-2.5 py-1 rounded text-[11px] font-medium transition-all duration-200"
                        style={
                          jdMode === mode
                            ? {
                                background: "var(--badge-active-bg)",
                                color: "var(--badge-active-text)",
                              }
                            : {
                                color: "var(--badge-inactive-text)",
                              }
                        }
                      >
                        {mode === "paste" ? "Paste" : "Upload"}
                      </button>
                    ))}
                  </div>
                </div>

                {jdMode === "paste" ? (
                  <div className="relative">
                    <textarea
                      value={jdText}
                      onChange={(e) => setJdText(e.target.value)}
                      placeholder="We're looking for a Senior Product Manager with 5+ years of B2B SaaS experience..."
                      rows={4}
                      className="w-full rounded-xl px-4 py-3.5 text-[13px] leading-relaxed placeholder:italic resize-none focus:outline-none transition-all duration-200"
                      style={{
                        background: "var(--input-bg)",
                        border: "1px solid var(--input-border)",
                        color: "var(--text-body)",
                      }}
                      onFocus={(e) => {
                        e.currentTarget.style.borderColor = "var(--input-focus-border)";
                        e.currentTarget.style.boxShadow = "0 0 0 3px var(--input-focus-ring)";
                      }}
                      onBlur={(e) => {
                        e.currentTarget.style.borderColor = "var(--input-border)";
                        e.currentTarget.style.boxShadow = "none";
                      }}
                    />
                    {hasJD && <ReadyBadge />}
                  </div>
                ) : (
                  <div className="relative">
                    <div
                      onClick={() => jdFileInputRef.current?.click()}
                      className="rounded-xl cursor-pointer transition-all duration-200"
                      style={{
                        border: jdFile ? "1px solid var(--card-border)" : "1.5px dashed var(--input-border)",
                        background: jdFile ? "var(--input-bg)" : "transparent",
                      }}
                    >
                      <input
                        ref={jdFileInputRef}
                        type="file"
                        accept=".pdf,.doc,.docx,.txt"
                        className="hidden"
                        onChange={(e) => {
                          if (e.target.files?.[0]) setJdFile(e.target.files[0]);
                          e.target.value = "";
                        }}
                      />
                      {jdFile ? (
                        <FileRow
                          name={jdFile.name}
                          size={jdFile.size}
                          onRemove={(e) => {
                            e.stopPropagation();
                            setJdFile(null);
                          }}
                          accent="purple"
                        />
                      ) : (
                        <DropPlaceholder icon={<JDIcon />} label="Upload job description" hint="PDF, DOCX, or TXT" />
                      )}
                    </div>
                    {hasJD && <ReadyBadge />}
                  </div>
                )}
              </div>

              {/* ── Divider ── */}
              <div className="h-px my-1" style={{ background: "var(--divider)" }} />

              {/* ── Resumes Section ── */}
              <div className="mt-4 mb-5">
                <label className="text-[12px] font-medium uppercase tracking-wider mb-2.5 block" style={{ color: "var(--text-muted)" }}>
                  Resumes
                </label>
                <div
                  onDragOver={(e) => {
                    e.preventDefault();
                    setDragging(true);
                  }}
                  onDragLeave={() => setDragging(false)}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  className="rounded-xl cursor-pointer transition-all duration-200"
                  style={{
                    border: dragging
                      ? "1.5px solid rgba(52,211,153,0.4)"
                      : files.length > 0
                      ? "1px solid var(--card-border)"
                      : "1.5px dashed var(--input-border)",
                    background: dragging ? "rgba(52,211,153,0.04)" : files.length > 0 ? "var(--input-bg)" : "transparent",
                  }}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept=".pdf,.doc,.docx"
                    className="hidden"
                    onChange={(e) => {
                      if (e.target.files) handleFiles(e.target.files);
                      e.target.value = "";
                    }}
                  />
                  {files.length === 0 ? (
                    <DropPlaceholder icon={<ResumeIcon />} label="Drop resume files here" hint="PDF or DOCX · up to 50 files" />
                  ) : (
                    <div className="p-3">
                      <div className="flex items-center justify-between mb-2 px-1">
                        <span className="text-[11px] font-medium" style={{ color: "var(--text-muted)" }}>
                          {files.length} file{files.length !== 1 ? "s" : ""}
                        </span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            fileInputRef.current?.click();
                          }}
                          className="text-[11px] font-medium transition-colors"
                          style={{ color: "var(--text-faint)" }}
                        >
                          + Add more
                        </button>
                      </div>
                      <div className="space-y-0.5 max-h-[140px] overflow-y-auto">
                        {files.map((file, i) => (
                          <FileRow
                            key={file.name + file.size}
                            name={file.name}
                            size={file.size}
                            onRemove={(e) => {
                              e.stopPropagation();
                              removeFile(i);
                            }}
                            accent="green"
                          />
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* ── CTA Button ── */}
              {(() => {
                const atLimit = usage !== null && usage.remaining === 0;
                const isPro = usage?.plan === "pro";
                const isDisabled = !canStart || atLimit;

                let buttonLabel: string;
                if (!hasFiles) {
                  buttonLabel = "Add resume files above";
                } else if (!hasJD) {
                  buttonLabel = "Paste a job description to start";
                } else if (atLimit) {
                  buttonLabel = "Limit reached — upgrade to continue";
                } else if (canStart && usage !== null && !isPro) {
                  buttonLabel = `Analyze ${files.length} candidate${files.length !== 1 ? "s" : ""} → (${usage.remaining} remaining)`;
                } else {
                  buttonLabel = `Analyze ${files.length} candidate${files.length !== 1 ? "s" : ""} →`;
                }

                return (
                  <button
                    onClick={handleStart}
                    disabled={isDisabled}
                    className="w-full py-3 rounded-xl text-sm font-semibold transition-all duration-300 active:scale-[0.98]"
                    style={
                      !isDisabled
                        ? {
                            background: "linear-gradient(135deg, #7c5cff 0%, #6346e0 100%)",
                            color: "#fff",
                            boxShadow: "0 0 24px rgba(124,92,255,0.3), 0 2px 8px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.15)",
                          }
                        : {
                            background: "var(--btn-disabled-bg)",
                            color: "var(--btn-disabled-text)",
                            cursor: "not-allowed",
                          }
                    }
                  >
                    {buttonLabel}
                  </button>
                );
              })()}

              {/* ── Usage counter ── */}
              {usage !== null && (
                <p
                  className="text-center text-[11px] mt-3"
                  style={{
                    color:
                      usage.remaining === 0
                        ? "#f87171"
                        : usage.remaining <= 2
                        ? "#fbbf24"
                        : "var(--text-faint)",
                  }}
                >
                  {usage.plan === "pro"
                    ? "Unlimited analyses"
                    : usage.plan === "anonymous"
                    ? `${usage.remaining}/${usage.limit} free analyses remaining`
                    : `${usage.used}/${usage.limit} analyses used this month`}
                </p>
              )}
              {usage === null && (
                <p className="text-center text-[11px] mt-3" style={{ color: "var(--text-faint)" }}>
                  Free to try · No account needed
                </p>
              )}
            </>
          )}
        </div>

        {/* ── Pricing + features (idle only) ── */}
        {step === "idle" && (
          <div className="w-full max-w-[640px] mt-12 home-stagger-4">
            {/* Feature pills */}
            <div className="flex flex-wrap items-center justify-center gap-2 mb-10">
              {["Evidence-backed scores", "No hallucinations", "Private & secure", "Works in seconds"].map((text) => (
                <span
                  key={text}
                  className="text-[11px] font-medium px-3 py-1.5 rounded-full"
                  style={{
                    color: "var(--text-muted)",
                    border: "1px solid var(--card-border)",
                    background: "var(--input-bg)",
                  }}
                >
                  {text}
                </span>
              ))}
            </div>

            {/* Pricing section */}
            <div className="grid grid-cols-2 gap-3">
              {/* Free tier */}
              <div
                className="rounded-xl p-5"
                style={{
                  background: "var(--card-bg)",
                  border: "1px solid var(--card-border)",
                }}
              >
                <p className="text-[11px] font-semibold uppercase tracking-wider mb-1" style={{ color: "var(--text-muted)" }}>Free</p>
                <p className="font-display text-2xl mb-3" style={{ color: "var(--text-heading)" }}>$0</p>
                <div className="space-y-2">
                  {[
                    "3 analyses without account",
                    "10/month with free account",
                    "Up to 10 resumes each",
                    "Full scoring & evidence",
                    "Compare candidates",
                  ].map((f) => (
                    <div key={f} className="flex items-start gap-2">
                      <span className="text-[10px] mt-0.5" style={{ color: "#34d399" }}>✓</span>
                      <span className="text-[12px]" style={{ color: "var(--text-muted)" }}>{f}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Pro tier */}
              <div
                className="rounded-xl p-5 relative overflow-hidden"
                style={{
                  background: "var(--card-bg)",
                  border: "1px solid rgba(124,92,255,0.2)",
                  boxShadow: "0 0 30px rgba(124,92,255,0.06)",
                }}
              >
                <div
                  className="absolute top-3 right-3 text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full"
                  style={{ background: "rgba(124,92,255,0.1)", color: "#a78bfa", border: "1px solid rgba(124,92,255,0.2)" }}
                >
                  Popular
                </div>
                <p className="text-[11px] font-semibold uppercase tracking-wider mb-1" style={{ color: "#a78bfa" }}>Pro</p>
                <div className="flex items-baseline gap-1 mb-3">
                  <span className="font-display text-2xl" style={{ color: "var(--text-heading)" }}>$19</span>
                  <span className="text-[12px]" style={{ color: "var(--text-faint)" }}>/month</span>
                </div>
                <div className="space-y-2">
                  {[
                    "Unlimited analyses",
                    "Up to 50 resumes each",
                    "8-factor evidence scoring",
                    "Side-by-side comparison",
                    "Priority support",
                  ].map((f) => (
                    <div key={f} className="flex items-start gap-2">
                      <span className="text-[10px] mt-0.5" style={{ color: "#a78bfa" }}>✓</span>
                      <span className="text-[12px]" style={{ color: "var(--text-muted)" }}>{f}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── Results section ── */}
        {step === "results" && (
          <div ref={resultsRef} className="w-full max-w-[640px] mt-6">
            {/* Compare bar */}
            {selectedIds.size >= 2 && !compareMode && (
              <div
                className="mb-4 flex items-center justify-between px-4 py-3 rounded-xl"
                style={{
                  background: "rgba(124,92,255,0.08)",
                  border: "1px solid rgba(124,92,255,0.2)",
                }}
              >
                <span className="text-[13px] font-medium" style={{ color: "rgba(124,92,255,0.9)" }}>
                  {selectedIds.size} candidates selected
                </span>
                <button
                  onClick={() => setCompareMode(true)}
                  className="text-[12px] font-semibold px-4 py-1.5 rounded-lg transition-all duration-200 active:scale-[0.97]"
                  style={{
                    background: "linear-gradient(135deg, #7c5cff 0%, #6346e0 100%)",
                    color: "#fff",
                    boxShadow: "0 0 16px rgba(124,92,255,0.3)",
                  }}
                >
                  Compare →
                </button>
              </div>
            )}

            {/* Compare mode */}
            {compareMode ? (
              <CompareView
                candidates={selectedCandidates}
                onClose={() => setCompareMode(false)}
              />
            ) : (
              <div className="space-y-2">
                {sortedCandidates.map((candidate, idx) => (
                  <CandidateCard
                    key={candidate.id}
                    candidate={candidate}
                    rank={idx + 1}
                    isExpanded={expandedId === candidate.id}
                    isSelected={selectedIds.has(candidate.id)}
                    onToggleExpand={() => toggleExpand(candidate.id)}
                    onToggleSelect={(e) => toggleSelect(candidate.id, e)}
                    animDelay={idx * 0.06}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── Footer ── */}
      <footer className="relative z-10 px-6 py-6 max-w-5xl mx-auto" style={{ borderTop: "1px solid var(--divider)" }}>
        <div className="flex items-center justify-between">
          <p className="text-[11px]" style={{ color: "var(--text-faint)" }}>
            &copy; {new Date().getFullYear()} Domato AI Pty Ltd
          </p>
          <div className="flex items-center gap-4">
            <Link href="/terms" className="text-[11px] transition-colors" style={{ color: "var(--text-faint)" }}>Terms</Link>
            <Link href="/privacy" className="text-[11px] transition-colors" style={{ color: "var(--text-faint)" }}>Privacy</Link>
            <a href="mailto:support@domato.ai" className="text-[11px] transition-colors" style={{ color: "var(--text-faint)" }}>Contact</a>
          </div>
        </div>
      </footer>

      {/* ── Limit / Upgrade Modal ── */}
      {limitModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center px-4"
          style={{ background: "rgba(0,0,0,0.6)", backdropFilter: "blur(4px)" }}
        >
          <div
            className="relative w-full max-w-sm rounded-2xl p-8"
            style={{
              background: "var(--card-bg)",
              border: "1px solid var(--card-border)",
              boxShadow: "0 24px 80px rgba(0,0,0,0.4), 0 0 60px rgba(124,92,255,0.08)",
            }}
          >
            {/* Purple accent line */}
            <div
              className="absolute top-0 left-1/2 -translate-x-1/2 w-24 h-0.5 rounded-full"
              style={{ background: "linear-gradient(90deg, transparent, #7c5cff, transparent)" }}
            />

            {limitModal.plan === "anonymous" ? (
              <>
                <p className="text-[18px] font-semibold leading-snug mb-2" style={{ color: "var(--text-heading)" }}>
                  You&rsquo;ve used all {limitModal.limit} free analyses
                </p>
                <p className="text-[14px] leading-relaxed mb-6" style={{ color: "var(--text-muted)" }}>
                  Create a free account to get{" "}
                  <span className="font-semibold" style={{ color: "var(--text-body)" }}>10 analyses per month</span>
                </p>
                <Link
                  href="/signup"
                  className="block w-full text-center py-3 rounded-xl text-sm font-semibold transition-all duration-200 active:scale-[0.98] mb-4"
                  style={{
                    background: "linear-gradient(135deg, #7c5cff 0%, #6346e0 100%)",
                    color: "#fff",
                    boxShadow: "0 0 24px rgba(124,92,255,0.3), 0 2px 8px rgba(0,0,0,0.3)",
                  }}
                >
                  Create free account
                </Link>
                <p className="text-center text-[12px]" style={{ color: "var(--text-muted)" }}>
                  Already have an account?{" "}
                  <Link href="/login" className="font-medium" style={{ color: "rgba(124,92,255,0.9)" }}>
                    Sign in
                  </Link>
                </p>
              </>
            ) : (
              <>
                <p className="text-[18px] font-semibold leading-snug mb-2" style={{ color: "var(--text-heading)" }}>
                  You&rsquo;ve used all {limitModal.limit} analyses this month
                </p>
                <p className="text-[14px] leading-relaxed mb-1" style={{ color: "var(--text-muted)" }}>
                  Upgrade to Pro for{" "}
                  <span className="font-semibold" style={{ color: "var(--text-body)" }}>unlimited analyses</span>
                </p>
                <p className="text-[12px] mb-6" style={{ color: "var(--text-faint)" }}>
                  $19/month · Cancel anytime
                </p>
                <Link
                  href="/signup"
                  className="block w-full text-center py-3 rounded-xl text-sm font-semibold transition-all duration-200 active:scale-[0.98] mb-4"
                  style={{
                    background: "linear-gradient(135deg, #7c5cff 0%, #6346e0 100%)",
                    color: "#fff",
                    boxShadow: "0 0 24px rgba(124,92,255,0.3), 0 2px 8px rgba(0,0,0,0.3)",
                  }}
                >
                  Upgrade to Pro
                </Link>
                <p className="text-center text-[12px]" style={{ color: "var(--text-faint)" }}>
                  Your limit resets next month
                </p>
              </>
            )}

            {/* Dismiss */}
            <div className="flex justify-end mt-6">
              <button
                onClick={() => setLimitModal(null)}
                className="text-[12px] px-3 py-1.5 rounded-lg transition-all duration-150"
                style={{
                  color: "var(--text-faint)",
                  border: "1px solid var(--card-border)",
                  background: "var(--input-bg)",
                }}
              >
                × Dismiss
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ─── CandidateCard ──────────────────────────────────────────────────────── */

function CandidateCard({
  candidate,
  rank,
  isExpanded,
  isSelected,
  onToggleExpand,
  onToggleSelect,
  animDelay,
}: {
  candidate: CandidateResult;
  rank: number;
  isExpanded: boolean;
  isSelected: boolean;
  onToggleExpand: () => void;
  onToggleSelect: (e: React.MouseEvent) => void;
  animDelay: number;
}) {
  const sc = scoreColor(candidate.overall_score);
  const recMeta = RECOMMENDATION_META[candidate.recommendation] ?? RECOMMENDATION_META["maybe"];
  const factorEntries = Object.entries(candidate.factor_scores);

  return (
    <div
      className="rounded-xl overflow-hidden candidate-card-enter"
      style={{
        background: isSelected ? "rgba(124,92,255,0.04)" : "var(--card-bg)",
        border: isSelected ? "1px solid rgba(124,92,255,0.25)" : "1px solid var(--card-border)",
        animationDelay: `${animDelay}s`,
        transition: "border-color 0.15s, background 0.15s",
      }}
    >
      {/* ── Card header — always visible, clickable ── */}
      <div
        className="flex items-start gap-3 px-4 pt-3.5 pb-2 cursor-pointer select-none"
        onClick={onToggleExpand}
        style={{ userSelect: "none" }}
      >
        {/* Checkbox */}
        <div
          onClick={onToggleSelect}
          className="flex-shrink-0 mt-1 w-4 h-4 rounded flex items-center justify-center transition-all duration-150 cursor-pointer"
          style={{
            background: isSelected ? "#7c5cff" : "var(--input-bg)",
            border: isSelected ? "1px solid #7c5cff" : "1px solid var(--input-border)",
          }}
        >
          {isSelected && (
            <svg width="9" height="7" viewBox="0 0 9 7" fill="none">
              <path d="M1 3.5L3.5 6L8 1" stroke="#fff" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          )}
        </div>

        {/* Rank */}
        <span
          className="flex-shrink-0 mt-1 w-5 text-[11px] font-mono text-center"
          style={{ color: rank === 1 ? "#a78bfa" : "var(--text-faint)" }}
        >
          {rank}
        </span>

        {/* Name + title + recommendation badge */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="text-[14px] font-semibold leading-tight" style={{ color: "var(--text-heading)" }}>
              {candidate.name ?? "Unknown Candidate"}
            </p>
            {/* Recommendation badge */}
            <span
              className="inline-flex items-center text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wide flex-shrink-0"
              style={{
                color: recMeta.color,
                background: recMeta.bg,
                border: `1px solid ${recMeta.border}`,
              }}
            >
              {recMeta.label}
            </span>
          </div>
          <p className="text-[12px] mt-0.5 truncate" style={{ color: "var(--text-muted)" }}>
            {candidate.current_title ?? "—"}
            {candidate.current_company ? ` @ ${candidate.current_company}` : ""}
          </p>
        </div>

        {/* Score + bar */}
        <div className="flex-shrink-0 flex flex-col items-end gap-1.5 w-24">
          <div className="flex items-center gap-1">
            <span className="font-display text-[18px] font-normal leading-none" style={{ color: sc }}>
              {candidate.overall_score}
            </span>
            <span className="text-[10px]" style={{ color: "var(--text-faint)" }}>/100</span>
          </div>
          <div className="w-full h-1.5 rounded-full overflow-hidden" style={{ background: "var(--input-bg)" }}>
            <div
              className="h-full rounded-full score-bar-fill"
              style={{ width: `${candidate.overall_score}%`, background: sc, opacity: 0.8 }}
            />
          </div>
        </div>

        {/* Expand chevron */}
        <svg
          width="12"
          height="12"
          viewBox="0 0 12 12"
          fill="none"
          className="flex-shrink-0 transition-transform duration-200 mt-1"
          style={{
            color: "var(--text-faint)",
            transform: isExpanded ? "rotate(90deg)" : "rotate(0deg)",
          }}
        >
          <path d="M4.5 2.5L7.5 6l-3 3.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>

      {/* ── Summary text — key recruiter value ── */}
      {candidate.summary && (
        <div className="px-4 pb-2.5 pl-12">
          <p
            className="text-[13px] leading-relaxed"
            style={{ color: "var(--text-body)" }}
          >
            {candidate.summary}
          </p>
        </div>
      )}

      {/* ── Factor verdict pills ── */}
      {factorEntries.length > 0 && (
        <div className="flex flex-wrap gap-1.5 px-4 pb-3 pl-12">
          {factorEntries.map(([key, detail]) => {
            const vColor = VERDICT_COLOR[detail.verdict] ?? "var(--text-faint)";
            return (
              <span
                key={key}
                className="inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full"
                style={{
                  color: vColor,
                  background: VERDICT_BG[detail.verdict] ?? "var(--input-bg)",
                  border: `1px solid ${vColor}22`,
                }}
              >
                <span
                  className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                  style={{ background: vColor }}
                />
                {detail.label ?? key.replace(/_/g, " ")}
              </span>
            );
          })}
        </div>
      )}

      {/* ── Expanded panel ── */}
      {isExpanded && (
        <div style={{ borderTop: "1px solid var(--divider)" }}>
          <div className="px-4 py-4 space-y-5">

            {/* Factor evidence rows */}
            {factorEntries.length > 0 && (
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wider mb-3" style={{ color: "var(--text-muted)" }}>
                  Evidence Breakdown
                </p>
                <div className="space-y-2">
                  {factorEntries.map(([key, detail]) => (
                    <FactorEvidenceRow key={key} factorKey={key} detail={detail} />
                  ))}
                </div>
              </div>
            )}

            {/* Strengths */}
            {candidate.strengths.length > 0 && (
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wider mb-2" style={{ color: "var(--text-muted)" }}>
                  Strengths
                </p>
                <ul className="space-y-1.5">
                  {candidate.strengths.map((s, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="flex-shrink-0 text-[13px] font-bold mt-0.5" style={{ color: "#34d399" }}>+</span>
                      <span className="text-[13px] leading-snug" style={{ color: "var(--text-body)" }}>
                        {s}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Risks */}
            {candidate.risks.length > 0 && (
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wider mb-2" style={{ color: "var(--text-muted)" }}>
                  Risks
                </p>
                <ul className="space-y-1.5">
                  {candidate.risks.map((r, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="flex-shrink-0 text-[13px] font-bold mt-0.5" style={{ color: "#f87171" }}>!</span>
                      <span className="text-[13px] leading-snug" style={{ color: "var(--text-body)" }}>
                        {r}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Missing evidence */}
            {candidate.missing_evidence.length > 0 && (
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wider mb-2" style={{ color: "var(--text-muted)" }}>
                  Missing Evidence
                </p>
                <ul className="space-y-1.5">
                  {candidate.missing_evidence.map((m, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="flex-shrink-0 text-[13px] font-bold mt-0.5" style={{ color: "var(--text-faint)" }}>?</span>
                      <span className="text-[13px] leading-snug" style={{ color: "var(--text-muted)" }}>
                        {m}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Generate interview questions button */}
            <div className="pt-1">
              <button
                className="flex items-center gap-2 w-full justify-center py-2.5 rounded-xl text-[13px] font-medium transition-all duration-200"
                style={{
                  background: "var(--input-bg)",
                  border: "1px solid var(--card-border)",
                  color: "var(--text-muted)",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = "rgba(124,92,255,0.3)";
                  e.currentTarget.style.color = "var(--text-body)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = "var(--card-border)";
                  e.currentTarget.style.color = "var(--text-muted)";
                }}
              >
                Generate interview questions
                <ProBadge />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ─── FactorEvidenceRow ──────────────────────────────────────────────────── */

function FactorEvidenceRow({ factorKey, detail }: { factorKey: string; detail: FactorDetail }) {
  const [open, setOpen] = useState(false);
  const vColor = VERDICT_COLOR[detail.verdict] ?? "var(--text-faint)";
  const sc = scoreColor(detail.score);
  const label = detail.label ?? factorKey.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <div
      className="rounded-lg overflow-hidden transition-all duration-150"
      style={{
        border: "1px solid var(--card-border)",
        borderLeft: `3px solid ${vColor}`,
        background: open ? VERDICT_BG[detail.verdict] ?? "var(--input-bg)" : "var(--card-bg)",
      }}
    >
      {/* Row header — clickable to expand */}
      <div
        className="flex items-center gap-3 px-3 py-2.5 cursor-pointer select-none"
        onClick={() => setOpen((v) => !v)}
        style={{ userSelect: "none" }}
      >
        {/* Score bar */}
        <div className="flex-shrink-0 w-16">
          <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "var(--input-bg)" }}>
            <div
              className="h-full rounded-full"
              style={{ width: `${detail.score}%`, background: sc, opacity: 0.85 }}
            />
          </div>
        </div>

        {/* Label + score */}
        <div className="flex-1 min-w-0 flex items-center gap-2">
          <span className="text-[12px] font-medium truncate" style={{ color: "var(--text-body)" }}>
            {label}
          </span>
          <span className="text-[11px] font-mono flex-shrink-0" style={{ color: sc }}>
            {detail.score}/100
          </span>
        </div>

        {/* Verdict badge */}
        <span
          className="flex-shrink-0 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wide"
          style={{ color: vColor, background: VERDICT_BG[detail.verdict] ?? "var(--input-bg)" }}
        >
          {VERDICT_LABEL[detail.verdict] ?? detail.verdict}
        </span>

        {/* Chevron */}
        <svg
          width="10"
          height="10"
          viewBox="0 0 12 12"
          fill="none"
          className="flex-shrink-0 transition-transform duration-200"
          style={{ color: "var(--text-faint)", transform: open ? "rotate(90deg)" : "rotate(0deg)" }}
        >
          <path d="M4.5 2.5L7.5 6l-3 3.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>

      {/* Expanded evidence */}
      {open && (
        <div
          className="px-3 pb-3 space-y-2"
          style={{ borderTop: "1px solid var(--divider)" }}
        >
          {/* JD requires */}
          {detail.jd_required && (
            <div className="pt-2">
              <span className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: "var(--text-faint)" }}>
                JD requires:{" "}
              </span>
              <span className="text-[12px]" style={{ color: "var(--text-muted)" }}>
                {detail.jd_required}
              </span>
            </div>
          )}

          {/* Candidate has */}
          {detail.candidate_has && (
            <div>
              <span className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: "var(--text-faint)" }}>
                Candidate has:{" "}
              </span>
              <span className="text-[12px]" style={{ color: "var(--text-muted)" }}>
                {detail.candidate_has}
              </span>
            </div>
          )}

          {/* Matched pills — only if they exist */}
          {detail.matched && detail.matched.length > 0 && (
            <div className="flex flex-wrap gap-1.5 pt-0.5">
              <span className="text-[10px] font-semibold uppercase tracking-wider self-center" style={{ color: "var(--text-faint)" }}>
                Matched:
              </span>
              {detail.matched.map((m, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full"
                  style={{
                    color: "#34d399",
                    background: "rgba(52,211,153,0.08)",
                    border: "1px solid rgba(52,211,153,0.2)",
                  }}
                >
                  ✓ {m}
                </span>
              ))}
            </div>
          )}

          {/* Missing pills */}
          {detail.missing && detail.missing.length > 0 && (
            <div className="flex flex-wrap gap-1.5 pt-0.5">
              <span className="text-[10px] font-semibold uppercase tracking-wider self-center" style={{ color: "var(--text-faint)" }}>
                Missing:
              </span>
              {detail.missing.map((m, i) => (
                <span
                  key={i}
                  className="inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full"
                  style={{
                    color: "#f87171",
                    background: "rgba(248,113,113,0.08)",
                    border: "1px solid rgba(248,113,113,0.2)",
                  }}
                >
                  ✗ {m}
                </span>
              ))}
            </div>
          )}

          {/* Reasoning */}
          {detail.reasoning && (
            <div
              className="rounded-lg px-3 py-2 mt-1"
              style={{ background: "var(--input-bg)", border: "1px solid var(--card-border)" }}
            >
              <p className="text-[12px] leading-relaxed" style={{ color: "var(--text-muted)" }}>
                → {detail.reasoning}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ─── CompareView ────────────────────────────────────────────────────────── */

function CompareView({ candidates, onClose }: { candidates: CandidateResult[]; onClose: () => void }) {
  const allFactorKeys = Array.from(
    new Set(candidates.flatMap((c) => Object.keys(c.factor_scores)))
  );

  return (
    <div
      className="rounded-2xl overflow-hidden"
      style={{
        background: "var(--card-bg)",
        border: "1px solid var(--card-border)",
      }}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between px-5 py-4"
        style={{ borderBottom: "1px solid var(--divider)" }}
      >
        <p className="text-[14px] font-semibold" style={{ color: "var(--text-heading)" }}>
          Comparing {candidates.length} candidates
        </p>
        <button
          onClick={onClose}
          className="text-[12px] px-3 py-1.5 rounded-lg transition-colors"
          style={{
            color: "var(--text-muted)",
            border: "1px solid var(--card-border)",
            background: "var(--input-bg)",
          }}
        >
          Back to list
        </button>
      </div>

      {/* Candidate columns */}
      <div className="overflow-x-auto">
        <div style={{ minWidth: `${candidates.length * 200}px` }}>

          {/* Name header row */}
          <div
            className="grid px-5 py-4"
            style={{
              gridTemplateColumns: `160px repeat(${candidates.length}, 1fr)`,
              borderBottom: "1px solid var(--divider)",
            }}
          >
            <div />
            {candidates.map((c) => {
              const sc = scoreColor(c.overall_score);
              const recMeta = RECOMMENDATION_META[c.recommendation] ?? RECOMMENDATION_META["maybe"];
              return (
                <div key={c.id} className="px-3">
                  <p className="text-[13px] font-semibold truncate" style={{ color: "var(--text-heading)" }}>
                    {c.name ?? "Unknown"}
                  </p>
                  <p className="text-[11px] truncate mt-0.5" style={{ color: "var(--text-muted)" }}>
                    {c.current_title ?? "—"}
                  </p>
                  <div className="flex items-center gap-2 mt-2 flex-wrap">
                    <span className="font-display text-[22px] leading-none" style={{ color: sc }}>
                      {c.overall_score}
                    </span>
                    <span className="text-[10px]" style={{ color: "var(--text-faint)" }}>/100</span>
                    <span
                      className="inline-flex items-center text-[10px] font-bold px-1.5 py-0.5 rounded-full uppercase tracking-wide"
                      style={{ color: recMeta.color, background: recMeta.bg, border: `1px solid ${recMeta.border}` }}
                    >
                      {recMeta.label}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Factor rows */}
          {allFactorKeys.map((factorKey, idx) => {
            return (
              <div
                key={factorKey}
                className="grid px-5 py-3 items-center"
                style={{
                  gridTemplateColumns: `160px repeat(${candidates.length}, 1fr)`,
                  background: idx % 2 === 0 ? "transparent" : "rgba(255,255,255,0.015)",
                  borderBottom: "1px solid var(--divider)",
                }}
              >
                <span className="text-[12px]" style={{ color: "var(--text-muted)" }}>
                  {allFactorKeys[idx] &&
                    (candidates.find((c) => c.factor_scores[factorKey])?.factor_scores[factorKey]?.label
                      ?? factorKey.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()))}
                </span>
                {candidates.map((c) => {
                  const detail = c.factor_scores[factorKey];
                  const sc = detail ? scoreColor(detail.score) : "var(--text-faint)";
                  const vColor = detail ? (VERDICT_COLOR[detail.verdict] ?? "var(--text-faint)") : "var(--text-faint)";
                  const score = detail?.score ?? 0;
                  return (
                    <div key={c.id} className="px-3">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[13px] font-mono font-medium" style={{ color: sc }}>
                          {score}
                        </span>
                        {detail && (
                          <span
                            className="text-[9px] font-bold uppercase tracking-wide px-1.5 py-0.5 rounded-full"
                            style={{ color: vColor, background: VERDICT_BG[detail.verdict] ?? "var(--input-bg)" }}
                          >
                            {VERDICT_LABEL[detail.verdict] ?? detail.verdict}
                          </span>
                        )}
                      </div>
                      <div className="h-1 rounded-full overflow-hidden" style={{ background: "var(--input-bg)" }}>
                        <div
                          className="h-full rounded-full"
                          style={{ width: `${score}%`, background: sc, opacity: 0.7 }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            );
          })}

          {/* Summary row */}
          <div
            className="grid px-5 py-4"
            style={{
              gridTemplateColumns: `160px repeat(${candidates.length}, 1fr)`,
              borderBottom: "1px solid var(--divider)",
            }}
          >
            <span className="text-[12px] font-semibold uppercase tracking-wider pt-1" style={{ color: "var(--text-muted)" }}>
              Summary
            </span>
            {candidates.map((c) => (
              <div key={c.id} className="px-3">
                <p className="text-[12px] leading-snug" style={{ color: "var(--text-body)" }}>
                  {c.summary || "—"}
                </p>
              </div>
            ))}
          </div>

          {/* Strengths row */}
          <div
            className="grid px-5 py-4"
            style={{
              gridTemplateColumns: `160px repeat(${candidates.length}, 1fr)`,
              borderBottom: "1px solid var(--divider)",
            }}
          >
            <span className="text-[12px] font-semibold uppercase tracking-wider pt-1" style={{ color: "var(--text-muted)" }}>
              Top Strength
            </span>
            {candidates.map((c) => (
              <div key={c.id} className="px-3">
                <p className="text-[12px] leading-snug" style={{ color: "var(--text-body)" }}>
                  {c.strengths[0] ?? "—"}
                </p>
              </div>
            ))}
          </div>

          {/* Risks row */}
          <div
            className="grid px-5 py-4"
            style={{
              gridTemplateColumns: `160px repeat(${candidates.length}, 1fr)`,
            }}
          >
            <span className="text-[12px] font-semibold uppercase tracking-wider pt-1" style={{ color: "var(--text-muted)" }}>
              Top Risk
            </span>
            {candidates.map((c) => (
              <div key={c.id} className="px-3">
                <p className="text-[12px] leading-snug" style={{ color: "#f87171", opacity: 0.8 }}>
                  {c.risks[0] ?? "—"}
                </p>
              </div>
            ))}
          </div>

        </div>
      </div>
    </div>
  );
}

/* ─── Small shared components ────────────────────────────────────────────── */

function ProBadge() {
  return (
    <span
      className="inline-flex items-center text-[9px] font-bold px-1.5 py-0.5 rounded-full uppercase tracking-wide"
      style={{
        background: "rgba(124,92,255,0.12)",
        color: "rgba(124,92,255,0.9)",
        border: "1px solid rgba(124,92,255,0.2)",
      }}
    >
      Pro
    </span>
  );
}

/* ─── Input UI shared components ─────────────────────────────────────────── */

function ReadyBadge() {
  return (
    <div className="absolute top-2.5 right-2.5">
      <span
        className="inline-flex items-center gap-1.5 text-[10px] font-semibold px-2 py-0.5 rounded-full"
        style={{ color: "var(--ready-color)", background: "var(--ready-bg)", border: "1px solid var(--ready-border)" }}
      >
        <span className="w-1.5 h-1.5 rounded-full" style={{ background: "var(--ready-color)" }} />
        Ready
      </span>
    </div>
  );
}

function DropPlaceholder({ icon, label, hint }: { icon: React.ReactNode; label: string; hint: string }) {
  return (
    <div className="flex flex-col items-center py-7 px-4">
      <div
        className="w-10 h-10 rounded-xl flex items-center justify-center mb-2.5"
        style={{ background: "var(--input-bg)", border: "1px solid var(--card-border)" }}
      >
        {icon}
      </div>
      <p className="text-[13px] font-medium" style={{ color: "var(--text-muted)" }}>
        {label}
      </p>
      <p className="text-[11px] mt-0.5" style={{ color: "var(--text-faint)" }}>
        {hint}
      </p>
    </div>
  );
}

function FileRow({
  name,
  size,
  onRemove,
  accent,
}: {
  name: string;
  size: number;
  onRemove: (e: React.MouseEvent) => void;
  accent: "purple" | "green";
}) {
  const dotColor = accent === "purple" ? "var(--file-dot-purple)" : "var(--file-dot-green)";
  return (
    <div
      className="flex items-center gap-2.5 py-2 px-3 rounded-lg group/f transition-colors"
      onMouseEnter={(e) => (e.currentTarget.style.background = "var(--input-bg)")}
      onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
    >
      <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: dotColor }} />
      <p className="text-[12px] truncate flex-1 font-medium" style={{ color: "var(--text-muted)" }}>
        {name}
      </p>
      <span className="text-[10px] font-mono flex-shrink-0" style={{ color: "var(--text-faint)" }}>
        {(size / 1024).toFixed(0)} KB
      </span>
      <button onClick={onRemove} className="opacity-0 group-hover/f:opacity-100 p-0.5 transition-opacity" style={{ color: "var(--text-faint)" }}>
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
          <path d="M2.5 2.5l5 5M7.5 2.5l-5 5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
        </svg>
      </button>
    </div>
  );
}

/* ─── Icons ──────────────────────────────────────────────────────────────── */

function JDIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
      <rect x="3" y="1.5" width="12" height="15" rx="2" stroke="rgba(124,92,255,0.45)" strokeWidth="1.2" />
      <path d="M6 6h6M6 9h6M6 12h3.5" stroke="rgba(124,92,255,0.35)" strokeWidth="1.1" strokeLinecap="round" />
    </svg>
  );
}

function ResumeIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
      <circle cx="9" cy="6.5" r="2.5" stroke="rgba(52,211,153,0.45)" strokeWidth="1.2" />
      <path d="M4 15c0-2.5 2.24-4.5 5-4.5s5 2 5 4.5" stroke="rgba(52,211,153,0.45)" strokeWidth="1.2" strokeLinecap="round" />
      <rect x="3" y="1.5" width="12" height="15" rx="2" stroke="rgba(52,211,153,0.3)" strokeWidth="1" />
    </svg>
  );
}
