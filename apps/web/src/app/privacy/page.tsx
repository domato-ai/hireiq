import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = { title: "Privacy Policy" };

export default function PrivacyPage() {
  return (
    <div className="min-h-screen relative" style={{ background: "var(--page-bg)" }}>
      <div className="max-w-2xl mx-auto px-6 py-16">
        <Link href="/" className="text-[12px] inline-block mb-8 transition-colors" style={{ color: "var(--text-muted)" }}>
          &larr; Back to HireIQ
        </Link>
        <h1 className="font-display text-3xl mb-2" style={{ color: "var(--text-heading)" }}>Privacy Policy</h1>
        <p className="text-[13px] mb-8" style={{ color: "var(--text-faint)" }}>Last updated: April 2026</p>

        <div className="space-y-6 text-[14px] leading-relaxed" style={{ color: "var(--text-muted)" }}>
          <section>
            <h2 className="font-semibold text-[15px] mb-2" style={{ color: "var(--text-body)" }}>Who We Are</h2>
            <p>Domato AI Pty Ltd operates HireIQ. We are an Australian company committed to protecting the privacy of our users and the candidates whose resumes are processed through our service.</p>
          </section>

          <section>
            <h2 className="font-semibold text-[15px] mb-2" style={{ color: "var(--text-body)" }}>What We Collect</h2>
            <p><strong>Account data:</strong> Email address and hashed password when you create an account.</p>
            <p className="mt-2"><strong>Usage data:</strong> Number of analyses performed, timestamps, and IP addresses for rate limiting.</p>
            <p className="mt-2"><strong>Uploaded content:</strong> Job descriptions and resumes you submit for analysis. These are processed in real-time and are not permanently stored for anonymous users.</p>
          </section>

          <section>
            <h2 className="font-semibold text-[15px] mb-2" style={{ color: "var(--text-body)" }}>How We Use Your Data</h2>
            <p>We process uploaded documents solely to generate candidate scoring and analysis results. We use Azure OpenAI (hosted in Australia) for AI processing. Your data is not used to train AI models. Usage data helps us enforce rate limits and improve the service.</p>
          </section>

          <section>
            <h2 className="font-semibold text-[15px] mb-2" style={{ color: "var(--text-body)" }}>Data Storage & Security</h2>
            <p>All data is processed and stored on Microsoft Azure infrastructure in Australia. Passwords are hashed using PBKDF2-HMAC-SHA256. All connections use TLS 1.2+. We do not sell, share, or transfer personal data to third parties except as required by law.</p>
          </section>

          <section>
            <h2 className="font-semibold text-[15px] mb-2" style={{ color: "var(--text-body)" }}>Candidate Data</h2>
            <p>Resume data is processed to extract skills, experience, and qualifications for scoring purposes. We do not extract or store sensitive personal information such as race, religion, disability status, or age beyond what is relevant to role qualification. Candidate data from anonymous analyses is discarded after the session.</p>
          </section>

          <section>
            <h2 className="font-semibold text-[15px] mb-2" style={{ color: "var(--text-body)" }}>Your Rights</h2>
            <p>You may request deletion of your account and all associated data at any time by emailing support@domato.ai. Under Australian Privacy Principles, you have the right to access and correct your personal information.</p>
          </section>

          <section>
            <h2 className="font-semibold text-[15px] mb-2" style={{ color: "var(--text-body)" }}>Cookies</h2>
            <p>We use localStorage (not cookies) to store your authentication token and theme preference. We do not use tracking cookies or third-party analytics.</p>
          </section>

          <section>
            <h2 className="font-semibold text-[15px] mb-2" style={{ color: "var(--text-body)" }}>Contact</h2>
            <p>Privacy questions? Email <a href="mailto:support@domato.ai" className="underline underline-offset-2" style={{ color: "var(--text-body)" }}>support@domato.ai</a></p>
          </section>
        </div>
      </div>
    </div>
  );
}
