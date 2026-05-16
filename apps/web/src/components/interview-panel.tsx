"use client";

import { useState } from "react";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "https://ca-hireiq-api-dev.delightfulsea-504dfc83.australiaeast.azurecontainerapps.io";

type Tab = "kit" | "phone";

interface BehavioralQ { question: string; what_to_listen_for?: string; anchor?: string }
interface TechnicalQ { question: string; what_to_listen_for?: string; targets_gap?: string }
interface ScorecardRow { competency: string; definition: string }

interface InterviewKit {
  behavioral: BehavioralQ[];
  technical: TechnicalQ[];
  scorecard: ScorecardRow[];
}

interface PhoneQ { question: string; why?: string }
interface PhoneScreen {
  opener: string;
  questions: PhoneQ[];
  closer: string;
}

export interface CandidatePayload {
  name?: string | null;
  current_title?: string | null;
  current_company?: string | null;
  years_experience?: number | null;
  experience?: unknown[];
  skills?: unknown[];
  strengths?: string[];
  risks?: string[];
  missing_evidence?: string[];
}

interface Props {
  candidate: CandidatePayload;
  jdRequirements: Record<string, unknown>;
  onEvent?: (event: string) => void;
}

function fireEvent(event: string) {
  try {
    fetch(`${API_URL}/api/v1/events`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        event,
        session_id: typeof window !== "undefined" ? localStorage.getItem("hireiq_session") : null,
        url: typeof window !== "undefined" ? window.location.pathname : null,
      }),
      keepalive: true,
    }).catch(() => {});
  } catch {}
}

function SkeletonLines({ rows = 4 }: { rows?: number }) {
  return (
    <div className="space-y-2 py-2">
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="h-2.5 rounded"
          style={{
            background: "var(--input-bg)",
            width: `${85 - (i % 3) * 15}%`,
            opacity: 0.6,
          }}
        />
      ))}
    </div>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p
      className="text-[10px] font-semibold uppercase mb-2"
      style={{ color: "var(--text-faint)", letterSpacing: "0.15em" }}
    >
      {children}
    </p>
  );
}

function QNum({ n }: { n: number }) {
  return (
    <span
      className="text-[10px] font-mono tabular-nums flex-shrink-0"
      style={{ color: "var(--text-faint)", letterSpacing: "0.05em" }}
    >
      {String(n).padStart(2, "0")}
    </span>
  );
}

function AnchorPill({ label, kind }: { label: string; kind: "strength" | "gap" | "context" }) {
  const color = kind === "strength" ? "#34d399" : kind === "gap" ? "#f87171" : "var(--text-faint)";
  return (
    <span
      className="text-[9px] uppercase font-semibold"
      style={{ color, letterSpacing: "0.12em", whiteSpace: "nowrap" }}
    >
      {kind === "strength" ? "+ " : kind === "gap" ? "- " : "ctx "}{label}
    </span>
  );
}

export default function InterviewPanel({ candidate, jdRequirements, onEvent }: Props) {
  const [tab, setTab] = useState<Tab>("kit");
  const [kit, setKit] = useState<InterviewKit | null>(null);
  const [phone, setPhone] = useState<PhoneScreen | null>(null);
  const [loadingKit, setLoadingKit] = useState(false);
  const [loadingPhone, setLoadingPhone] = useState(false);
  const [kitError, setKitError] = useState("");
  const [phoneError, setPhoneError] = useState("");

  const loadKit = async () => {
    if (kit || loadingKit) return;
    setLoadingKit(true);
    setKitError("");
    fireEvent("interview_kit_opened");
    onEvent?.("interview_kit_opened");
    try {
      const res = await fetch(`${API_URL}/api/v1/analyze/interview-kit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ candidate, jd_requirements: jdRequirements }),
      });
      if (!res.ok) throw new Error(`Request failed (${res.status})`);
      setKit(await res.json());
    } catch (e) {
      setKitError(e instanceof Error ? e.message : "Failed to generate kit");
    } finally {
      setLoadingKit(false);
    }
  };

  const loadPhone = async () => {
    if (phone || loadingPhone) return;
    setLoadingPhone(true);
    setPhoneError("");
    fireEvent("phone_screen_opened");
    onEvent?.("phone_screen_opened");
    try {
      const res = await fetch(`${API_URL}/api/v1/analyze/phone-screen`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ candidate, jd_requirements: jdRequirements }),
      });
      if (!res.ok) throw new Error(`Request failed (${res.status})`);
      setPhone(await res.json());
    } catch (e) {
      setPhoneError(e instanceof Error ? e.message : "Failed to generate phone screen");
    } finally {
      setLoadingPhone(false);
    }
  };

  const selectTab = (t: Tab) => {
    setTab(t);
    if (t === "kit") loadKit();
    else loadPhone();
  };

  return (
    <div
      className="mt-3 pt-3"
      style={{ borderTop: "1px solid var(--card-border)" }}
    >
      {/* Header strip: segmented tabs + "what is this" hint */}
      <div className="flex items-center justify-between mb-3">
        <div
          className="inline-flex rounded-md p-0.5"
          style={{ background: "var(--input-bg)" }}
        >
          {(
            [
              ["kit", "Interview Kit"],
              ["phone", "Phone Screen"],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              type="button"
              onClick={() => selectTab(key)}
              className="text-[11px] font-semibold px-2.5 py-1 rounded transition-colors"
              style={{
                background: tab === key ? "var(--card-bg)" : "transparent",
                color: tab === key ? "var(--text-heading)" : "var(--text-muted)",
                boxShadow: tab === key ? "0 1px 0 rgba(0,0,0,0.06)" : "none",
              }}
            >
              {label}
            </button>
          ))}
        </div>
        <p
          className="text-[10px] font-mono uppercase"
          style={{ color: "var(--text-faint)", letterSpacing: "0.12em" }}
        >
          tailored · evidence-anchored
        </p>
      </div>

      {/* KIT tab */}
      {tab === "kit" && (
        <div>
          {!kit && !loadingKit && !kitError && (
            <button
              type="button"
              onClick={loadKit}
              className="w-full text-[11px] font-semibold py-2.5 rounded-md transition-opacity hover:opacity-90"
              style={{
                background: "transparent",
                border: "1px dashed var(--card-border)",
                color: "var(--text-muted)",
                letterSpacing: "0.04em",
              }}
            >
              Generate interview kit for this candidate
            </button>
          )}

          {loadingKit && <SkeletonLines rows={5} />}

          {kitError && (
            <div className="text-[11px] py-2" style={{ color: "#f87171" }}>
              {kitError}.{" "}
              <button
                type="button"
                onClick={loadKit}
                className="underline"
                style={{ color: "var(--text-muted)" }}
              >
                Retry
              </button>
            </div>
          )}

          {kit && (
            <div className="space-y-4">
              {/* Behavioral */}
              <div>
                <SectionLabel>Behavioral · {kit.behavioral.length}</SectionLabel>
                <div className="space-y-2.5">
                  {kit.behavioral.map((q, i) => (
                    <div key={i} className="flex gap-3">
                      <QNum n={i + 1} />
                      <div className="flex-1 min-w-0">
                        <p
                          className="text-[12px] leading-snug"
                          style={{ color: "var(--text-heading)" }}
                        >
                          {q.question}
                        </p>
                        {q.what_to_listen_for && (
                          <p
                            className="text-[11px] italic mt-0.5"
                            style={{ color: "var(--text-muted)" }}
                          >
                            listen for: {q.what_to_listen_for}
                          </p>
                        )}
                        {q.anchor && (
                          <div className="mt-1">
                            <AnchorPill label={q.anchor} kind="strength" />
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Technical */}
              <div>
                <SectionLabel>Technical · {kit.technical.length}</SectionLabel>
                <div className="space-y-2.5">
                  {kit.technical.map((q, i) => (
                    <div key={i} className="flex gap-3">
                      <QNum n={i + 1} />
                      <div className="flex-1 min-w-0">
                        <p
                          className="text-[12px] leading-snug"
                          style={{ color: "var(--text-heading)" }}
                        >
                          {q.question}
                        </p>
                        {q.what_to_listen_for && (
                          <p
                            className="text-[11px] italic mt-0.5"
                            style={{ color: "var(--text-muted)" }}
                          >
                            listen for: {q.what_to_listen_for}
                          </p>
                        )}
                        {q.targets_gap && (
                          <div className="mt-1">
                            <AnchorPill label={q.targets_gap} kind="gap" />
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Scorecard */}
              {kit.scorecard.length > 0 && (
                <div>
                  <SectionLabel>Scorecard rubric</SectionLabel>
                  <div
                    className="rounded-md overflow-hidden"
                    style={{ border: "1px solid var(--card-border)" }}
                  >
                    {kit.scorecard.map((row, i) => (
                      <div
                        key={i}
                        className="grid grid-cols-[140px_1fr] gap-3 px-3 py-2"
                        style={{
                          background: i % 2 === 0 ? "transparent" : "var(--input-bg)",
                          borderTop: i === 0 ? "none" : "1px solid var(--card-border)",
                        }}
                      >
                        <span
                          className="text-[11px] font-semibold"
                          style={{ color: "var(--text-heading)" }}
                        >
                          {row.competency}
                        </span>
                        <span
                          className="text-[11px]"
                          style={{ color: "var(--text-muted)" }}
                        >
                          {row.definition}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* PHONE tab */}
      {tab === "phone" && (
        <div>
          {!phone && !loadingPhone && !phoneError && (
            <button
              type="button"
              onClick={loadPhone}
              className="w-full text-[11px] font-semibold py-2.5 rounded-md transition-opacity hover:opacity-90"
              style={{
                background: "transparent",
                border: "1px dashed var(--card-border)",
                color: "var(--text-muted)",
                letterSpacing: "0.04em",
              }}
            >
              Generate phone-screen script
            </button>
          )}

          {loadingPhone && <SkeletonLines rows={6} />}

          {phoneError && (
            <div className="text-[11px] py-2" style={{ color: "#f87171" }}>
              {phoneError}.{" "}
              <button
                type="button"
                onClick={loadPhone}
                className="underline"
                style={{ color: "var(--text-muted)" }}
              >
                Retry
              </button>
            </div>
          )}

          {phone && (
            <div className="space-y-4">
              {phone.opener && (
                <div>
                  <SectionLabel>Opener</SectionLabel>
                  <p
                    className="text-[12px] italic leading-snug"
                    style={{ color: "var(--text-heading)" }}
                  >
                    &ldquo;{phone.opener}&rdquo;
                  </p>
                </div>
              )}

              <div>
                <SectionLabel>Questions · {phone.questions.length}</SectionLabel>
                <div className="space-y-2.5">
                  {phone.questions.map((q, i) => (
                    <div key={i} className="flex gap-3">
                      <QNum n={i + 1} />
                      <div className="flex-1 min-w-0">
                        <p
                          className="text-[12px] leading-snug"
                          style={{ color: "var(--text-heading)" }}
                        >
                          {q.question}
                        </p>
                        {q.why && (
                          <p
                            className="text-[11px] italic mt-0.5"
                            style={{ color: "var(--text-muted)" }}
                          >
                            resolves: {q.why}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {phone.closer && (
                <div>
                  <SectionLabel>Close</SectionLabel>
                  <p
                    className="text-[12px] italic leading-snug"
                    style={{ color: "var(--text-heading)" }}
                  >
                    &ldquo;{phone.closer}&rdquo;
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
