import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = { title: "Terms of Service" };

export default function TermsPage() {
  return (
    <div className="min-h-screen relative" style={{ background: "var(--page-bg)" }}>
      <div className="max-w-2xl mx-auto px-6 py-16">
        <Link href="/" className="text-[12px] inline-block mb-8 transition-colors" style={{ color: "var(--text-muted)" }}>
          &larr; Back to HireIQ
        </Link>
        <h1 className="font-display text-3xl mb-2" style={{ color: "var(--text-heading)" }}>Terms of Service</h1>
        <p className="text-[13px] mb-8" style={{ color: "var(--text-faint)" }}>Last updated: April 2026</p>

        <div className="space-y-6 text-[14px] leading-relaxed" style={{ color: "var(--text-muted)" }}>
          <section>
            <h2 className="font-semibold text-[15px] mb-2" style={{ color: "var(--text-body)" }}>1. Service</h2>
            <p>HireIQ is a hiring decision tool operated by Domato AI Pty Ltd (ABN pending). The service analyses job descriptions and resumes to provide evidence-based candidate scoring.</p>
          </section>

          <section>
            <h2 className="font-semibold text-[15px] mb-2" style={{ color: "var(--text-body)" }}>2. Accounts</h2>
            <p>You may use HireIQ without an account (limited to 3 analyses per month). Creating a free account increases your limit to 10 analyses per month. Pro subscribers ($19/month) receive unlimited analyses. You are responsible for maintaining the confidentiality of your account credentials.</p>
          </section>

          <section>
            <h2 className="font-semibold text-[15px] mb-2" style={{ color: "var(--text-body)" }}>3. Acceptable Use</h2>
            <p>You may not use the service to discriminate against candidates on the basis of race, gender, age, disability, religion, or any other protected characteristic. HireIQ scores are based solely on skills, experience, and qualifications as stated in resumes and job descriptions.</p>
          </section>

          <section>
            <h2 className="font-semibold text-[15px] mb-2" style={{ color: "var(--text-body)" }}>4. Data Handling</h2>
            <p>Uploaded resumes and job descriptions are processed by AI models to generate scores. We do not store uploaded documents beyond the duration of the analysis session unless you have an active account with saved results enabled. See our Privacy Policy for full details.</p>
          </section>

          <section>
            <h2 className="font-semibold text-[15px] mb-2" style={{ color: "var(--text-body)" }}>5. AI Disclaimer</h2>
            <p>HireIQ provides automated scoring as a decision-support tool. Scores and recommendations should not be the sole basis for hiring decisions. We do not guarantee the accuracy of AI-generated analyses. You are responsible for verifying candidate information independently.</p>
          </section>

          <section>
            <h2 className="font-semibold text-[15px] mb-2" style={{ color: "var(--text-body)" }}>6. Payment & Cancellation</h2>
            <p>Pro subscriptions are billed monthly. You may cancel at any time. Cancellation takes effect at the end of your current billing period. No refunds are provided for partial months.</p>
          </section>

          <section>
            <h2 className="font-semibold text-[15px] mb-2" style={{ color: "var(--text-body)" }}>7. Liability</h2>
            <p>The service is provided &ldquo;as is&rdquo; without warranty. Domato AI Pty Ltd is not liable for hiring decisions made using the service, data loss, or service interruptions. Our total liability is limited to the amount you paid for the service in the preceding 12 months.</p>
          </section>

          <section>
            <h2 className="font-semibold text-[15px] mb-2" style={{ color: "var(--text-body)" }}>8. Changes</h2>
            <p>We may update these terms at any time. Continued use of the service after changes constitutes acceptance. We will notify registered users of material changes via email.</p>
          </section>

          <section>
            <h2 className="font-semibold text-[15px] mb-2" style={{ color: "var(--text-body)" }}>9. Contact</h2>
            <p>Questions about these terms? Email <a href="mailto:support@domato.ai" className="underline underline-offset-2" style={{ color: "var(--text-body)" }}>support@domato.ai</a></p>
          </section>
        </div>
      </div>
    </div>
  );
}
