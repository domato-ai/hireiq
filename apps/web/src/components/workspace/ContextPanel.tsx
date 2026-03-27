"use client";

import { useState, useRef } from "react";
import { clsx } from "clsx";
import { Button } from "@/components/ui/button";

interface ContextPanelProps {
  roleId: string;
  workspaceId: string;
  hasJD?: boolean;
  roleTitle?: string;
  factors?: string[];
}

type Tab = "jd" | "resumes";

interface UploadedFile {
  id: string;
  name: string;
  size: string;
  status: "uploading" | "processing" | "done" | "error";
  progress: number;
  candidateName?: string;
}

// Mock uploaded resumes to show populated state
const MOCK_RESUMES: UploadedFile[] = [
  { id: "r1", name: "sarah-chen-resume.pdf", size: "142 KB", status: "done", progress: 100, candidateName: "Sarah Chen" },
  { id: "r2", name: "marcus-webb-cv.pdf", size: "98 KB", status: "done", progress: 100, candidateName: "Marcus Webb" },
  { id: "r3", name: "priya-nair-resume.pdf", size: "115 KB", status: "done", progress: 100, candidateName: "Priya Nair" },
  { id: "r4", name: "jordan-kim-resume.pdf", size: "88 KB", status: "done", progress: 100, candidateName: "Jordan Kim" },
  { id: "r5", name: "devon-marsh-cv.pdf", size: "201 KB", status: "done", progress: 100, candidateName: "Devon Marsh" },
  { id: "r6", name: "aisha-okonkwo-resume.pdf", size: "134 KB", status: "done", progress: 100, candidateName: "Aisha Okonkwo" },
  { id: "r7", name: "tomas-rivera-cv.pdf", size: "76 KB", status: "done", progress: 100, candidateName: "Tomás Rivera" },
  { id: "r8", name: "riley-donovan-resume.pdf", size: "109 KB", status: "done", progress: 100, candidateName: "Riley Donovan" },
  { id: "r9", name: "nadia-volkov-cv.pdf", size: "122 KB", status: "done", progress: 100, candidateName: "Nadia Volkov" },
];

const MOCK_CRITERIA = [
  { id: "1", label: "5+ years product management", type: "required" as const, weight: 3 },
  { id: "2", label: "B2B SaaS experience", type: "required" as const, weight: 3 },
  { id: "3", label: "Cross-functional leadership", type: "preferred" as const, weight: 2 },
  { id: "4", label: "Data-driven decision making", type: "preferred" as const, weight: 2 },
  { id: "5", label: "SQL / data analysis skills", type: "preferred" as const, weight: 1 },
];

export function ContextPanel({
  roleId,
  workspaceId,
  hasJD = false,
  roleTitle,
  factors = [],
}: ContextPanelProps) {
  void roleId;
  void workspaceId;

  const [activeTab, setActiveTab] = useState<Tab>(hasJD ? "resumes" : "jd");

  return (
    <div className="flex flex-col h-full">
      {/* Panel header */}
      <div className="flex-shrink-0 px-4 pt-4 pb-0 space-y-3">
        <div className="flex items-start justify-between gap-2">
          <div>
            <h2 className="text-2xs font-semibold uppercase tracking-widest text-ink-400">
              Role context
            </h2>
            {roleTitle && (
              <p className="text-sm font-semibold text-ink mt-0.5 leading-tight">
                {roleTitle}
              </p>
            )}
          </div>
          {hasJD && (
            <span className="text-2xs text-signal-green-dark bg-signal-green-light px-1.5 py-0.5 rounded font-semibold flex-shrink-0 mt-1">
              JD loaded
            </span>
          )}
        </div>

        {/* Tabs */}
        <div className="flex border-b border-ink/8">
          {(
            [
              { id: "jd" as Tab, label: "Job description" },
              { id: "resumes" as Tab, label: `Resumes (${MOCK_RESUMES.length})` },
            ] as { id: Tab; label: string }[]
          ).map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={clsx(
                "px-3 py-2 text-xs font-medium border-b-2 -mb-px transition-colors",
                activeTab === tab.id
                  ? "border-ink text-ink"
                  : "border-transparent text-ink-400 hover:text-ink hover:border-ink/30"
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Panel body */}
      <div className="flex-1 overflow-y-auto px-4 py-4">
        {activeTab === "jd" && <JDTab hasJD={hasJD} factors={factors} />}
        {activeTab === "resumes" && <ResumesTab />}
      </div>
    </div>
  );
}

/* ─── JD Tab ────────────────────────────────────────────────────────────────── */

function JDTab({ hasJD, factors }: { hasJD: boolean; factors: string[] }) {
  const [dragOver, setDragOver] = useState(false);
  const [jdText, setJdText] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (hasJD) {
    return (
      <div className="space-y-5">
        {/* JD loaded state */}
        <div className="bg-bone-200 border border-ink/10 rounded-lg p-3 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <DocumentIcon />
              <span className="text-xs font-medium text-ink">senior-pm-jd.pdf</span>
            </div>
            <button className="text-2xs text-ink-400 hover:text-ink transition-colors underline underline-offset-2">
              Replace
            </button>
          </div>
          <p className="text-2xs text-ink-400">Uploaded Mar 19 · 2,847 words · parsed</p>
        </div>

        {/* Extracted factors */}
        {factors.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="text-label">Scoring factors</h3>
              <button className="text-2xs text-ink-400 hover:text-ink transition-colors underline underline-offset-2">
                Edit
              </button>
            </div>
            <p className="text-2xs text-ink-400">
              Extracted from JD. Drag to reorder, click weight dots to adjust.
            </p>
            <div className="space-y-1">
              {MOCK_CRITERIA.map((c) => (
                <CriterionRow key={c.id} criterion={c} />
              ))}
            </div>
          </div>
        )}

        <Button size="sm" variant="secondary" className="w-full">
          Re-score all candidates
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Upload zone */}
      <div
        className={clsx("upload-zone cursor-pointer", dragOver && "dragging")}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          // TODO: handle file drop
        }}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          className="hidden"
          onChange={() => {
            // TODO: handle file upload
          }}
        />
        <UploadIcon />
        <p className="text-sm font-medium text-ink mt-2">
          Drop job description
        </p>
        <p className="text-xs text-ink-400 mt-0.5">PDF, DOCX, or plain text</p>
      </div>

      {/* Divider */}
      <div className="flex items-center gap-2">
        <div className="flex-1 h-px bg-ink/8" />
        <span className="text-2xs text-ink-400 uppercase tracking-wide">or paste</span>
        <div className="flex-1 h-px bg-ink/8" />
      </div>

      {/* Paste fallback */}
      <div className="space-y-1.5">
        <label className="text-label">Paste JD text</label>
        <textarea
          rows={10}
          value={jdText}
          onChange={(e) => setJdText(e.target.value)}
          placeholder="Paste the full job description here. The more complete the JD, the more accurate the scoring."
          className="
            w-full text-xs text-ink placeholder:text-ink-300
            bg-bone-50 border border-ink/12 rounded
            px-3 py-2.5 resize-none
            focus:outline-none focus:border-ink/30 focus:ring-1 focus:ring-ink/20
            transition-colors leading-relaxed
          "
        />
        {jdText.length > 0 && (
          <p className="text-2xs text-ink-400 text-right font-mono">
            {jdText.length} chars · ~{Math.round(jdText.split(/\s+/).length)} words
          </p>
        )}
      </div>

      <Button
        size="sm"
        className="w-full"
        disabled={jdText.length < 50}
      >
        Analyze job description
      </Button>
    </div>
  );
}

/* ─── Criterion row ─────────────────────────────────────────────────────────── */

interface Criterion {
  id: string;
  label: string;
  type: "required" | "preferred";
  weight: number;
}

function CriterionRow({ criterion }: { criterion: Criterion }) {
  return (
    <div className="flex items-start gap-2 py-1.5 px-2 rounded hover:bg-bone-200 group cursor-default">
      <span
        className={clsx(
          "text-2xs font-semibold px-1 py-0.5 rounded mt-0.5 flex-shrink-0",
          criterion.type === "required"
            ? "text-signal-red-dark bg-signal-red-light"
            : "text-ink-400 bg-bone-300"
        )}
      >
        {criterion.type === "required" ? "REQ" : "PREF"}
      </span>
      <div className="flex-1 min-w-0">
        <p className="text-xs text-ink leading-snug">{criterion.label}</p>
      </div>
      {/* Weight indicator */}
      <div className="flex gap-0.5 mt-1.5 flex-shrink-0">
        {[1, 2, 3].map((w) => (
          <div
            key={w}
            className={clsx(
              "w-1.5 h-1.5 rounded-full cursor-pointer hover:opacity-80",
              w <= criterion.weight ? "bg-ink-500" : "bg-ink-200"
            )}
          />
        ))}
      </div>
    </div>
  );
}

/* ─── Resumes Tab ───────────────────────────────────────────────────────────── */

function ResumesTab() {
  const [files, setFiles] = useState<UploadedFile[]>(MOCK_RESUMES);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function simulateUpload(fileName: string, fileSize: string) {
    const id = `r-${Date.now()}`;
    const newFile: UploadedFile = {
      id,
      name: fileName,
      size: fileSize,
      status: "uploading",
      progress: 0,
    };
    setFiles((prev) => [newFile, ...prev]);

    // Simulate progress
    let progress = 0;
    const interval = setInterval(() => {
      progress += Math.random() * 25 + 10;
      if (progress >= 100) {
        progress = 100;
        clearInterval(interval);
        setFiles((prev) =>
          prev.map((f) =>
            f.id === id ? { ...f, progress: 100, status: "processing" } : f
          )
        );
        // Simulate processing
        setTimeout(() => {
          setFiles((prev) =>
            prev.map((f) =>
              f.id === id ? { ...f, status: "done" } : f
            )
          );
        }, 1500);
      } else {
        setFiles((prev) =>
          prev.map((f) => (f.id === id ? { ...f, progress } : f))
        );
      }
    }, 200);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    const droppedFiles = Array.from(e.dataTransfer.files);
    droppedFiles.forEach((f) => {
      const kb = Math.round(f.size / 1024);
      simulateUpload(f.name, `${kb} KB`);
    });
  }

  function handleFileInput(e: React.ChangeEvent<HTMLInputElement>) {
    const selected = Array.from(e.target.files ?? []);
    selected.forEach((f) => {
      const kb = Math.round(f.size / 1024);
      simulateUpload(f.name, `${kb} KB`);
    });
  }

  const done = files.filter((f) => f.status === "done").length;
  const processing = files.filter((f) => f.status === "processing" || f.status === "uploading").length;

  return (
    <div className="space-y-4">
      {/* Upload zone */}
      <div
        className={clsx("upload-zone cursor-pointer", dragOver && "dragging")}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          multiple
          className="hidden"
          onChange={handleFileInput}
        />
        <UploadIcon />
        <p className="text-sm font-medium text-ink mt-2">Drop CVs / resumes</p>
        <p className="text-xs text-ink-400 mt-0.5">Multiple files · PDF, DOCX, TXT</p>
      </div>

      {/* Stats */}
      <div className="flex items-center gap-4 text-2xs text-ink-400">
        <span>
          <span className="text-ink font-semibold font-mono">{done}</span> processed
        </span>
        {processing > 0 && (
          <span className="text-signal-amber-dark">
            <span className="font-semibold font-mono">{processing}</span> in progress
          </span>
        )}
        <span>
          <span className="text-ink font-semibold font-mono">{files.length}</span> total
        </span>
      </div>

      {/* File list */}
      <div className="space-y-1">
        {files.map((file) => (
          <ResumeFileRow key={file.id} file={file} />
        ))}
      </div>
    </div>
  );
}

function ResumeFileRow({ file }: { file: UploadedFile }) {
  const statusConfig = {
    uploading: { label: "Uploading", color: "text-signal-amber-dark" },
    processing: { label: "Processing", color: "text-signal-amber-dark" },
    done: { label: "Scored", color: "text-signal-green-dark" },
    error: { label: "Error", color: "text-signal-red-dark" },
  }[file.status];

  const isActive = file.status === "uploading" || file.status === "processing";

  return (
    <div className="group px-2 py-2 rounded hover:bg-bone-200 transition-colors">
      <div className="flex items-start gap-2">
        <div className="flex-shrink-0 mt-0.5">
          <DocumentIcon />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-ink truncate">{file.name}</p>
          <div className="flex items-center gap-2 mt-0.5">
            {file.candidateName && (
              <span className="text-2xs text-ink-500">{file.candidateName}</span>
            )}
            {!file.candidateName && (
              <span className="text-2xs text-ink-400">{file.size}</span>
            )}
            <span className={clsx("text-2xs font-medium", statusConfig.color)}>
              {isActive && <span className="inline-block mr-0.5 animate-pulse">·</span>}
              {statusConfig.label}
            </span>
          </div>
          {isActive && (
            <div className="mt-1.5 h-0.5 bg-bone-300 rounded-full overflow-hidden w-full">
              <div
                className="h-full bg-signal-amber rounded-full transition-all duration-300"
                style={{ width: `${file.progress}%` }}
              />
            </div>
          )}
        </div>
        <button className="text-2xs text-ink-300 hover:text-ink-400 opacity-0 group-hover:opacity-100 transition-all flex-shrink-0 mt-0.5">
          ✕
        </button>
      </div>
    </div>
  );
}

/* ─── Icons ─────────────────────────────────────────────────────────────────── */

function UploadIcon() {
  return (
    <svg
      width="22"
      height="22"
      viewBox="0 0 24 24"
      fill="none"
      className="mx-auto text-ink-300"
      aria-hidden="true"
    >
      <path
        d="M12 16V8M12 8l-3 3M12 8l3 3"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M20 16.5A3.5 3.5 0 0016.5 20h-9A3.5 3.5 0 004 16.5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

function DocumentIcon() {
  return (
    <svg
      width="12"
      height="12"
      viewBox="0 0 12 12"
      fill="none"
      className="text-ink-400"
      aria-hidden="true"
    >
      <path
        d="M2 1.5h6l2 2V10.5a.5.5 0 01-.5.5H2.5a.5.5 0 01-.5-.5v-9a.5.5 0 01.5-.5z"
        stroke="currentColor"
        strokeWidth="1"
        strokeLinejoin="round"
      />
      <path d="M8 1.5V4h2.5" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M4 6h4M4 8h2.5" stroke="currentColor" strokeWidth="0.9" strokeLinecap="round" />
    </svg>
  );
}
