import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "History",
};

export default function HistoryPage() {
  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center px-6"
      style={{ background: "var(--page-bg)" }}
    >
      <div
        className="w-full max-w-md rounded-2xl p-8 text-center"
        style={{
          background: "var(--card-bg)",
          border: "1px solid var(--card-border)",
        }}
      >
        <div
          className="w-12 h-12 rounded-xl flex items-center justify-center mx-auto mb-4"
          style={{ background: "var(--input-bg)", border: "1px solid var(--card-border)" }}
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <circle cx="10" cy="10" r="8" stroke="rgba(124,92,255,0.4)" strokeWidth="1.4" />
            <path d="M10 6v4.5l2.5 2.5" stroke="rgba(124,92,255,0.4)" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <h1
          className="font-display text-2xl mb-2"
          style={{ color: "var(--text-heading)" }}
        >
          Analysis History
        </h1>
        <p className="text-sm leading-relaxed mb-6" style={{ color: "var(--text-muted)" }}>
          Your past analyses will appear here once you sign in. Coming soon.
        </p>
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-[13px] font-medium px-5 py-2.5 rounded-xl transition-all duration-200"
          style={{
            background: "linear-gradient(135deg, #7c5cff 0%, #6346e0 100%)",
            color: "#fff",
            boxShadow: "0 0 20px rgba(124,92,255,0.25)",
          }}
        >
          ← Back to home
        </Link>
      </div>
    </div>
  );
}
