import type { Metadata } from "next";
import Link from "next/link";
import { BLOG_POSTS } from "./posts";

export const metadata: Metadata = {
  title: "Blog — AI Recruitment, Resume Screening & Hiring Best Practices",
  description: "Practical guides on AI resume screening, candidate ranking, recruitment automation, and evidence-based hiring decisions. By HireIQ.",
  alternates: { canonical: "https://hireiq.domato.ai/blog" },
};

export default function BlogIndex() {
  return (
    <div className="min-h-screen" style={{ background: "var(--page-bg)" }}>
      <div className="max-w-3xl mx-auto px-6 py-16">
        <Link href="/" className="text-[12px] inline-block mb-8 transition-colors" style={{ color: "var(--text-muted)" }}>
          &larr; Back to HireIQ
        </Link>

        <h1 className="font-display text-3xl md:text-4xl tracking-tight mb-3" style={{ color: "var(--text-heading)" }}>
          Blog
        </h1>
        <p className="text-[15px] mb-12" style={{ color: "var(--text-muted)" }}>
          Practical guides on AI recruitment, resume screening, and making better hiring decisions.
        </p>

        <div className="space-y-8">
          {BLOG_POSTS.map((post) => (
            <Link
              key={post.slug}
              href={`/blog/${post.slug}`}
              className="block group rounded-xl p-5 -mx-5 transition-all duration-200 hover:bg-[var(--card-bg)] border border-transparent hover:border-[var(--card-border)]"
            >
              <div className="flex items-center gap-3 mb-2">
                <span className="text-[11px] font-medium px-2 py-0.5 rounded-full"
                  style={{ background: "rgba(124,92,255,0.1)", color: "#a78bfa" }}>
                  {post.category}
                </span>
                <span className="text-[11px]" style={{ color: "var(--text-faint)" }}>
                  {post.date} &middot; {post.readTime} read
                </span>
              </div>
              <h2 className="text-[16px] font-semibold mb-1.5 group-hover:underline underline-offset-2"
                style={{ color: "var(--text-heading)" }}>
                {post.title}
              </h2>
              <p className="text-[13px] leading-relaxed" style={{ color: "var(--text-muted)" }}>
                {post.description}
              </p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
