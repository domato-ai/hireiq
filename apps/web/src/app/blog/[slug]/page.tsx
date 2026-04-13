import type { Metadata } from "next";
import Link from "next/link";
import { BLOG_POSTS } from "../posts";
import { BLOG_CONTENT } from "./content";

export function generateStaticParams() {
  return BLOG_POSTS.map((post) => ({ slug: post.slug }));
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const post = BLOG_POSTS.find((p) => p.slug === slug);
  if (!post) return {};
  return {
    title: post.title,
    description: post.description,
    alternates: { canonical: `https://hireiq.domato.ai/blog/${slug}` },
    openGraph: {
      title: post.title,
      description: post.description,
      type: "article",
      publishedTime: post.date,
      authors: ["HireIQ"],
    },
  };
}

export default async function BlogPostPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const post = BLOG_POSTS.find((p) => p.slug === slug);
  const content = BLOG_CONTENT[slug];

  if (!post || !content) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "var(--page-bg)" }}>
        <p style={{ color: "var(--text-muted)" }}>Post not found.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ background: "var(--page-bg)" }}>
      <article className="max-w-2xl mx-auto px-6 py-16">
        <Link href="/blog" className="text-[12px] inline-block mb-8 transition-colors" style={{ color: "var(--text-muted)" }}>
          &larr; All posts
        </Link>

        <div className="flex items-center gap-3 mb-4">
          <span className="text-[11px] font-medium px-2 py-0.5 rounded-full"
            style={{ background: "rgba(124,92,255,0.1)", color: "#a78bfa" }}>
            {post.category}
          </span>
          <span className="text-[11px]" style={{ color: "var(--text-faint)" }}>
            {post.date} &middot; {post.readTime} read
          </span>
        </div>

        <h1 className="font-display text-3xl md:text-4xl tracking-tight mb-4 leading-tight" style={{ color: "var(--text-heading)" }}>
          {post.title}
        </h1>
        <p className="text-[15px] mb-10 leading-relaxed" style={{ color: "var(--text-muted)" }}>
          {post.description}
        </p>

        <div
          className="space-y-5 text-[14px] leading-[1.75]"
          style={{ color: "var(--text-body)" }}
          dangerouslySetInnerHTML={{ __html: content }}
        />

        {/* CTA */}
        <div className="mt-12 p-6 rounded-2xl text-center"
          style={{ background: "var(--card-bg)", border: "1px solid var(--card-border)" }}>
          <p className="text-[16px] font-semibold mb-2" style={{ color: "var(--text-heading)" }}>
            Ready to try evidence-based resume screening?
          </p>
          <p className="text-[13px] mb-4" style={{ color: "var(--text-muted)" }}>
            Paste a job description, upload resumes, get a ranked shortlist in 30 seconds. Free to start.
          </p>
          <Link href="/"
            className="inline-block px-6 py-3 rounded-xl text-[14px] font-semibold"
            style={{ background: "linear-gradient(135deg, #7c5cff 0%, #6346e0 100%)", color: "#fff", boxShadow: "0 0 20px rgba(124,92,255,0.3)" }}>
            Try HireIQ Free
          </Link>
        </div>

        {/* Product Hunt */}
        <div className="mt-6 flex justify-center">
          <div style={{
            fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
            border: "1px solid #e0e0e0", borderRadius: 12, padding: 20, maxWidth: 500,
            background: "#fff", boxShadow: "0 2px 8px rgba(0,0,0,0.05)",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
              <img alt="HireIQ" src="https://ph-files.imgix.net/bbc1543c-2a99-4c31-b1c2-54d8eee33070.png?auto=format&fit=crop&w=80&h=80"
                style={{ width: 64, height: 64, borderRadius: 8, objectFit: "cover", flexShrink: 0 }} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <h3 style={{ margin: 0, fontSize: 18, fontWeight: 600, color: "#1a1a1a", lineHeight: 1.3 }}>HireIQ</h3>
                <p style={{ margin: "4px 0 0", fontSize: 14, color: "#666", lineHeight: 1.4 }}>
                  Instantly see which candidates actually match your job
                </p>
              </div>
            </div>
            <a href="https://www.producthunt.com/products/hireiq?embed=true&utm_source=embed&utm_medium=post_embed"
              target="_blank" rel="noopener"
              style={{
                display: "inline-flex", alignItems: "center", gap: 4, marginTop: 12,
                padding: "8px 16px", background: "#ff6154", color: "#fff",
                textDecoration: "none", borderRadius: 8, fontSize: 14, fontWeight: 600,
              }}>
              Check it out on Product Hunt &rarr;
            </a>
          </div>
        </div>

        {/* Related posts */}
        <div className="mt-12 pt-8" style={{ borderTop: "1px solid var(--divider)" }}>
          <h3 className="text-[13px] font-semibold uppercase tracking-wider mb-4" style={{ color: "var(--text-faint)" }}>
            Related articles
          </h3>
          <div className="space-y-3">
            {BLOG_POSTS.filter((p) => p.slug !== slug).slice(0, 3).map((p) => (
              <Link key={p.slug} href={`/blog/${p.slug}`} className="block text-[13px] hover:underline underline-offset-2"
                style={{ color: "var(--text-muted)" }}>
                {p.title}
              </Link>
            ))}
          </div>
        </div>
      </article>
    </div>
  );
}
