"use client";

import { useState, useRef, useCallback } from "react";
import Link from "next/link";
import { NavLogo } from "@/components/ui/logo";
import { ThemeToggle } from "@/components/ui/theme-toggle";

export default function HomePage() {
  const [jdText, setJdText] = useState("");
  const [jdFile, setJdFile] = useState<File | null>(null);
  const [jdMode, setJdMode] = useState<"paste" | "upload">("paste");
  const [files, setFiles] = useState<File[]>([]);
  const [dragging, setDragging] = useState(false);
  const [step, setStep] = useState<"idle" | "analyzing">("idle");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const jdFileInputRef = useRef<HTMLInputElement>(null);

  const hasJD = jdMode === "paste" ? jdText.trim().length > 20 : jdFile !== null;
  const hasFiles = files.length > 0;
  const canStart = hasJD && hasFiles;

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

  const handleStart = () => {
    setStep("analyzing");
    setTimeout(() => {
      window.location.href = "/workspaces/ws-1/roles/role-1";
    }, 2400);
  };

  return (
    <div className="min-h-screen relative" style={{ background: 'var(--page-bg)' }}>
      {/* Radial glow behind hero */}
      <div
        className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] pointer-events-none"
        style={{
          background: 'radial-gradient(ellipse 50% 70% at 50% 0%, var(--glow-color) 0%, transparent 70%)',
        }}
      />

      {/* Dot grid */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage: 'radial-gradient(var(--dot-grid-color) 1px, transparent 1px)',
          backgroundSize: '24px 24px',
        }}
      />

      {/* ── Nav ── */}
      <nav className="relative z-20 flex items-center justify-between px-6 md:px-10 py-5 max-w-5xl mx-auto">
        <NavLogo variant="dark" />
        <div className="flex items-center gap-4">
          <Link href="/signup" className="text-[13px] transition-colors" style={{ color: 'var(--text-muted)' }}>
            Create workspace
          </Link>
          <ThemeToggle />
          <Link
            href="/login"
            className="text-[13px] font-medium px-4 py-2 rounded-lg transition-all duration-200"
            style={{
              color: 'var(--text-heading)',
              background: 'var(--nav-btn-bg)',
              border: '1px solid var(--nav-btn-border)',
            }}
          >
            Sign in
          </Link>
        </div>
      </nav>

      {/* ── Hero ── */}
      <div className="relative z-10 flex flex-col items-center pt-16 md:pt-24 pb-20 px-6">
        {/* Badge */}
        <div
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full mb-8 home-stagger-1"
          style={{
            background: 'rgba(124,92,255,0.08)',
            border: '1px solid rgba(124,92,255,0.15)',
          }}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-[#7c5cff] metric-pulse" />
          <span className="text-[12px] font-medium" style={{ color: 'rgba(124,92,255,0.9)' }}>
            Evidence-first hiring decisions
          </span>
        </div>

        {/* Heading */}
        <h1
          className="text-center font-display text-5xl md:text-6xl lg:text-7xl tracking-[-0.03em] leading-[1.05] max-w-3xl home-stagger-2"
          style={{ color: 'var(--text-heading)' }}
        >
          {step === "analyzing" ? (
            "Analyzing candidates"
          ) : (
            <>
              Find the <span className="italic" style={{ color: '#a78bfa' }}>right</span> hire
            </>
          )}
        </h1>

        <p
          className="text-center text-base md:text-lg mt-5 max-w-xl leading-relaxed home-stagger-2"
          style={{ color: 'var(--text-muted)' }}
        >
          Paste a job description, upload resumes, and get an evidence-backed shortlist in seconds.
        </p>

        {/* ── Main card ── */}
        <div
          className="w-full max-w-[640px] mt-12 rounded-2xl p-5 home-stagger-3"
          style={{
            background: 'var(--card-bg)',
            border: '1px solid var(--card-border)',
            boxShadow: 'var(--card-shadow), 0 0 80px rgba(124,92,255,0.04)',
          }}
        >
          {step === "analyzing" ? (
            <div className="py-10 text-center">
              <div className="relative w-14 h-14 mx-auto mb-5">
                <svg className="w-14 h-14 analyzing-spinner" viewBox="0 0 56 56">
                  <circle cx="28" cy="28" r="22" fill="none" stroke="var(--input-border)" strokeWidth="2" />
                  <circle cx="28" cy="28" r="22" fill="none" strokeWidth="2.5" strokeDasharray="35 105" strokeLinecap="round" stroke="url(#sg)" />
                  <defs>
                    <linearGradient id="sg" x1="0" y1="0" x2="1" y2="1">
                      <stop offset="0%" stopColor="#7c5cff" />
                      <stop offset="100%" stopColor="#7c5cff" stopOpacity="0.1" />
                    </linearGradient>
                  </defs>
                </svg>
              </div>
              <p className="text-sm font-medium" style={{ color: 'var(--badge-active-text)' }}>
                Processing {files.length} resume{files.length !== 1 ? "s" : ""}
              </p>
              <p className="text-xs mt-1.5" style={{ color: 'var(--badge-inactive-text)' }}>
                Extracting · Matching criteria · Scoring
              </p>
            </div>
          ) : (
            <>
              {/* ── JD Section ── */}
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2.5">
                  <label className="text-[12px] font-medium uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
                    Job Description
                  </label>
                  {/* Toggle */}
                  <div className="flex items-center gap-0.5 p-0.5 rounded-md" style={{ background: 'var(--input-bg)' }}>
                    {(["paste", "upload"] as const).map((mode) => (
                      <button
                        key={mode}
                        onClick={() => setJdMode(mode)}
                        className="px-2.5 py-1 rounded text-[11px] font-medium transition-all duration-200"
                        style={jdMode === mode ? {
                          background: 'var(--badge-active-bg)',
                          color: 'var(--badge-active-text)',
                        } : {
                          color: 'var(--badge-inactive-text)',
                        }}
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
                        background: 'var(--input-bg)',
                        border: '1px solid var(--input-border)',
                        color: 'var(--text-body)',
                      }}
                      onFocus={(e) => {
                        e.currentTarget.style.borderColor = 'var(--input-focus-border)';
                        e.currentTarget.style.boxShadow = '0 0 0 3px var(--input-focus-ring)';
                      }}
                      onBlur={(e) => {
                        e.currentTarget.style.borderColor = 'var(--input-border)';
                        e.currentTarget.style.boxShadow = 'none';
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
                        border: jdFile ? '1px solid var(--card-border)' : '1.5px dashed var(--input-border)',
                        background: jdFile ? 'var(--input-bg)' : 'transparent',
                      }}
                    >
                      <input ref={jdFileInputRef} type="file" accept=".pdf,.doc,.docx,.txt" className="hidden"
                        onChange={(e) => { if (e.target.files?.[0]) setJdFile(e.target.files[0]); e.target.value = ""; }}
                      />
                      {jdFile ? (
                        <FileRow name={jdFile.name} size={jdFile.size} onRemove={(e) => { e.stopPropagation(); setJdFile(null); }} accent="purple" />
                      ) : (
                        <DropPlaceholder icon={<JDIcon />} label="Upload job description" hint="PDF, DOCX, or TXT" />
                      )}
                    </div>
                    {hasJD && <ReadyBadge />}
                  </div>
                )}
              </div>

              {/* ── Divider ── */}
              <div className="h-px my-1" style={{ background: 'var(--divider)' }} />

              {/* ── Resumes Section ── */}
              <div className="mt-4 mb-5">
                <label className="text-[12px] font-medium uppercase tracking-wider mb-2.5 block" style={{ color: 'var(--text-muted)' }}>
                  Resumes
                </label>
                <div
                  onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                  onDragLeave={() => setDragging(false)}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  className="rounded-xl cursor-pointer transition-all duration-200"
                  style={{
                    border: dragging
                      ? '1.5px solid rgba(52,211,153,0.4)'
                      : files.length > 0
                        ? '1px solid var(--card-border)'
                        : '1.5px dashed var(--input-border)',
                    background: dragging ? 'rgba(52,211,153,0.04)' : files.length > 0 ? 'var(--input-bg)' : 'transparent',
                  }}
                >
                  <input ref={fileInputRef} type="file" multiple accept=".pdf,.doc,.docx" className="hidden"
                    onChange={(e) => { if (e.target.files) handleFiles(e.target.files); e.target.value = ""; }}
                  />
                  {files.length === 0 ? (
                    <DropPlaceholder icon={<ResumeIcon />} label="Drop resume files here" hint="PDF or DOCX · up to 50 files" />
                  ) : (
                    <div className="p-3">
                      <div className="flex items-center justify-between mb-2 px-1">
                        <span className="text-[11px] font-medium" style={{ color: 'var(--text-muted)' }}>
                          {files.length} file{files.length !== 1 ? "s" : ""}
                        </span>
                        <button onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click(); }}
                          className="text-[11px] font-medium transition-colors" style={{ color: 'var(--text-faint)' }}>
                          + Add more
                        </button>
                      </div>
                      <div className="space-y-0.5 max-h-[140px] overflow-y-auto">
                        {files.map((file, i) => (
                          <FileRow key={file.name + file.size} name={file.name} size={file.size}
                            onRemove={(e) => { e.stopPropagation(); removeFile(i); }} accent="green" />
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* ── CTA Button ── */}
              <button
                onClick={handleStart}
                disabled={!canStart}
                className="w-full py-3 rounded-xl text-sm font-semibold transition-all duration-300 active:scale-[0.98]"
                style={canStart ? {
                  background: 'linear-gradient(135deg, #7c5cff 0%, #6346e0 100%)',
                  color: '#fff',
                  boxShadow: '0 0 24px rgba(124,92,255,0.3), 0 2px 8px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.15)',
                } : {
                  background: 'var(--btn-disabled-bg)',
                  color: 'var(--btn-disabled-text)',
                  cursor: 'not-allowed',
                }}
              >
                {canStart
                  ? `Analyze ${files.length} candidate${files.length !== 1 ? "s" : ""} →`
                  : !hasJD ? "Paste a job description to start" : "Add resume files above"
                }
              </button>
              <p className="text-center text-[11px] mt-3" style={{ color: 'var(--text-faint)' }}>
                Free to try · No account needed
              </p>
            </>
          )}
        </div>

        {/* ── Feature pills ── */}
        {step !== "analyzing" && (
          <div className="flex flex-wrap items-center justify-center gap-3 mt-10 home-stagger-4">
            {[
              "Evidence-backed scores",
              "No hallucinations",
              "Private & secure",
              "Works in seconds",
            ].map((text) => (
              <span
                key={text}
                className="text-[11px] font-medium px-3 py-1.5 rounded-full"
                style={{
                  color: 'var(--text-muted)',
                  border: '1px solid var(--card-border)',
                  background: 'var(--input-bg)',
                }}
              >
                {text}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* ── Footer ── */}
      <footer className="relative z-10 px-6 py-6 text-center" style={{ borderTop: '1px solid var(--divider)' }}>
        <p className="text-[11px]" style={{ color: 'var(--text-faint)' }}>
          &copy; {new Date().getFullYear()} HireIQ · Evidence-first hiring
        </p>
      </footer>
    </div>
  );
}

/* ─── Shared components ───────────────────────────────────────────────────── */

function ReadyBadge() {
  return (
    <div className="absolute top-2.5 right-2.5">
      <span className="inline-flex items-center gap-1.5 text-[10px] font-semibold px-2 py-0.5 rounded-full"
        style={{ color: 'var(--ready-color)', background: 'var(--ready-bg)', border: '1px solid var(--ready-border)' }}>
        <span className="w-1.5 h-1.5 rounded-full" style={{ background: 'var(--ready-color)' }} />
        Ready
      </span>
    </div>
  );
}

function DropPlaceholder({ icon, label, hint }: { icon: React.ReactNode; label: string; hint: string }) {
  return (
    <div className="flex flex-col items-center py-7 px-4">
      <div className="w-10 h-10 rounded-xl flex items-center justify-center mb-2.5"
        style={{ background: 'var(--input-bg)', border: '1px solid var(--card-border)' }}>
        {icon}
      </div>
      <p className="text-[13px] font-medium" style={{ color: 'var(--text-muted)' }}>{label}</p>
      <p className="text-[11px] mt-0.5" style={{ color: 'var(--text-faint)' }}>{hint}</p>
    </div>
  );
}

function FileRow({ name, size, onRemove, accent }: { name: string; size: number; onRemove: (e: React.MouseEvent) => void; accent: "purple" | "green" }) {
  const dotColor = accent === "purple" ? 'var(--file-dot-purple)' : 'var(--file-dot-green)';
  return (
    <div className="flex items-center gap-2.5 py-2 px-3 rounded-lg group/f transition-colors"
      onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--input-bg)')}
      onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}>
      <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: dotColor }} />
      <p className="text-[12px] truncate flex-1 font-medium" style={{ color: 'var(--text-muted)' }}>{name}</p>
      <span className="text-[10px] font-mono flex-shrink-0" style={{ color: 'var(--text-faint)' }}>{(size / 1024).toFixed(0)} KB</span>
      <button onClick={onRemove} className="opacity-0 group-hover/f:opacity-100 p-0.5 transition-opacity" style={{ color: 'var(--text-faint)' }}>
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none"><path d="M2.5 2.5l5 5M7.5 2.5l-5 5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" /></svg>
      </button>
    </div>
  );
}

/* ─── Icons ───────────────────────────────────────────────────────────────── */

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
