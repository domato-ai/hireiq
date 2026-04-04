"use client";

import { useState } from "react";
import Link from "next/link";
import { NavLogo } from "@/components/ui/logo";
import { ThemeToggle } from "@/components/ui/theme-toggle";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://ca-hireiq-api-dev.delightfulsea-504dfc83.australiaeast.azurecontainerapps.io";

export default function ContactPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");

  const isValid = email.includes("@") && message.trim().length > 10;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isValid) return;
    setError("");
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/v1/contact`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, message }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({ detail: "Failed to send" }));
        throw new Error(data.detail || "Something went wrong");
      }
      setSent(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen relative" style={{ background: "var(--page-bg)" }}>
      {/* Glow */}
      <div
        className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[500px] pointer-events-none"
        style={{ background: "radial-gradient(ellipse 50% 70% at 50% 0%, var(--glow-color) 0%, transparent 70%)" }}
      />
      {/* Dot grid */}
      <div className="absolute inset-0 pointer-events-none"
        style={{ backgroundImage: "radial-gradient(var(--dot-grid-color) 1px, transparent 1px)", backgroundSize: "24px 24px" }}
      />

      {/* Nav */}
      <nav className="relative z-20 flex items-center justify-between px-6 md:px-10 py-5 max-w-5xl mx-auto">
        <NavLogo variant="dark" />
        <div className="flex items-center gap-4">
          <ThemeToggle />
          <Link href="/" className="text-[13px] font-medium px-4 py-2 rounded-lg transition-all duration-200"
            style={{ color: "var(--text-heading)", background: "var(--nav-btn-bg)", border: "1px solid var(--nav-btn-border)" }}>
            Back to app
          </Link>
        </div>
      </nav>

      {/* Content */}
      <div className="relative z-10 flex flex-col items-center pt-12 md:pt-20 pb-20 px-6">
        <h1 className="font-display text-3xl md:text-4xl tracking-[-0.02em] text-center mb-3" style={{ color: "var(--text-heading)" }}>
          Get in touch
        </h1>
        <p className="text-[15px] text-center mb-10" style={{ color: "var(--text-muted)" }}>
          Questions, feedback, or partnership inquiries — we&apos;d love to hear from you.
        </p>

        {sent ? (
          /* Success state */
          <div
            className="w-full max-w-[440px] rounded-2xl p-8 text-center"
            style={{ background: "var(--card-bg)", border: "1px solid var(--card-border)", boxShadow: "var(--card-shadow)" }}
          >
            <div className="w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4"
              style={{ background: "rgba(52,211,153,0.1)" }}>
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M4 10.5L8 14.5L16 6" stroke="#34d399" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <h2 className="font-display text-xl mb-2" style={{ color: "var(--text-heading)" }}>Message sent</h2>
            <p className="text-[13px] mb-6" style={{ color: "var(--text-muted)" }}>
              We&apos;ll get back to you at <strong style={{ color: "var(--text-body)" }}>{email}</strong> as soon as possible.
            </p>
            <Link href="/"
              className="inline-flex items-center gap-2 text-[13px] font-medium px-5 py-2.5 rounded-xl transition-all duration-200"
              style={{ background: "linear-gradient(135deg, #7c5cff 0%, #6346e0 100%)", color: "#fff", boxShadow: "0 0 20px rgba(124,92,255,0.25)" }}>
              &larr; Back to HireIQ
            </Link>
          </div>
        ) : (
          /* Form */
          <form
            onSubmit={handleSubmit}
            className="w-full max-w-[440px] rounded-2xl p-6"
            style={{ background: "var(--card-bg)", border: "1px solid var(--card-border)", boxShadow: "var(--card-shadow), 0 0 80px rgba(124,92,255,0.04)" }}
          >
            {error && (
              <div className="mb-4 px-3 py-2 rounded-lg text-[12px] font-medium"
                style={{ background: "var(--error-bg)", border: "1px solid var(--error-border)", color: "var(--error-text)" }}>
                {error}
              </div>
            )}

            {/* Name */}
            <div className="mb-4">
              <label className="block text-[12px] font-medium uppercase tracking-wider mb-2" style={{ color: "var(--text-muted)" }}>
                Name <span style={{ color: "var(--text-faint)" }}>(optional)</span>
              </label>
              <input
                type="text"
                placeholder="Your name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full rounded-xl px-4 py-3 text-[13px] focus:outline-none transition-all duration-200"
                style={{ background: "var(--input-bg)", border: "1px solid var(--input-border)", color: "var(--text-body)" }}
                onFocus={(e) => { e.currentTarget.style.borderColor = "var(--input-focus-border)"; e.currentTarget.style.boxShadow = "0 0 0 3px var(--input-focus-ring)"; }}
                onBlur={(e) => { e.currentTarget.style.borderColor = "var(--input-border)"; e.currentTarget.style.boxShadow = "none"; }}
              />
            </div>

            {/* Email */}
            <div className="mb-4">
              <label className="block text-[12px] font-medium uppercase tracking-wider mb-2" style={{ color: "var(--text-muted)" }}>
                Email
              </label>
              <input
                type="email"
                placeholder="you@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full rounded-xl px-4 py-3 text-[13px] focus:outline-none transition-all duration-200"
                style={{ background: "var(--input-bg)", border: "1px solid var(--input-border)", color: "var(--text-body)" }}
                onFocus={(e) => { e.currentTarget.style.borderColor = "var(--input-focus-border)"; e.currentTarget.style.boxShadow = "0 0 0 3px var(--input-focus-ring)"; }}
                onBlur={(e) => { e.currentTarget.style.borderColor = "var(--input-border)"; e.currentTarget.style.boxShadow = "none"; }}
              />
            </div>

            {/* Message */}
            <div className="mb-5">
              <label className="block text-[12px] font-medium uppercase tracking-wider mb-2" style={{ color: "var(--text-muted)" }}>
                Message
              </label>
              <textarea
                placeholder="How can we help?"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                required
                rows={5}
                className="w-full rounded-xl px-4 py-3 text-[13px] leading-relaxed resize-none focus:outline-none transition-all duration-200"
                style={{ background: "var(--input-bg)", border: "1px solid var(--input-border)", color: "var(--text-body)" }}
                onFocus={(e) => { e.currentTarget.style.borderColor = "var(--input-focus-border)"; e.currentTarget.style.boxShadow = "0 0 0 3px var(--input-focus-ring)"; }}
                onBlur={(e) => { e.currentTarget.style.borderColor = "var(--input-border)"; e.currentTarget.style.boxShadow = "none"; }}
              />
            </div>

            <button
              type="submit"
              disabled={!isValid || loading}
              className="w-full py-3 rounded-xl text-sm font-semibold transition-all duration-300 active:scale-[0.98]"
              style={isValid && !loading ? {
                background: "linear-gradient(135deg, #7c5cff 0%, #6346e0 100%)",
                color: "#fff",
                boxShadow: "0 0 24px rgba(124,92,255,0.3), 0 2px 8px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.15)",
              } : {
                background: "var(--btn-disabled-bg)",
                color: "var(--btn-disabled-text)",
                cursor: "not-allowed",
              }}
            >
              {loading ? "Sending..." : "Send message"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
