export interface BlogPost {
  slug: string;
  title: string;
  description: string;
  date: string;
  readTime: string;
  category: string;
}

export const BLOG_POSTS: BlogPost[] = [
  {
    slug: "ai-resume-screening-guide",
    title: "AI Resume Screening: The Complete Guide for Recruiters in 2026",
    description: "How AI-powered resume screening works, what to look for in a tool, and how to screen 50+ resumes in under a minute without missing qualified candidates.",
    date: "2026-04-10",
    readTime: "8 min",
    category: "Guide",
  },
  {
    slug: "reduce-time-to-shortlist",
    title: "How to Reduce Time-to-Shortlist from Days to Minutes",
    description: "The average recruiter spends 23 hours screening resumes for a single role. Here's how evidence-based scoring eliminates the bottleneck.",
    date: "2026-04-08",
    readTime: "6 min",
    category: "Productivity",
  },
  {
    slug: "bias-in-resume-screening",
    title: "Unconscious Bias in Resume Screening: How Structured Scoring Helps",
    description: "Research shows recruiters spend 7.4 seconds per resume. Structured, criteria-based scoring removes gut-feel decisions and improves hiring outcomes.",
    date: "2026-04-06",
    readTime: "7 min",
    category: "Best Practices",
  },
  {
    slug: "recruitment-agency-ai-tools",
    title: "5 Ways Recruitment Agencies Use AI to Win More Clients",
    description: "Agencies that deliver shortlists faster win more retained searches. Here's how AI scoring gives your agency a competitive edge.",
    date: "2026-04-04",
    readTime: "5 min",
    category: "Agencies",
  },
  {
    slug: "job-description-matching-explained",
    title: "How Job Description Matching Works: From Keywords to Evidence Scoring",
    description: "Keyword matching misses context. Evidence-based JD matching scores candidates on skills, experience, domain knowledge, and 5 more factors.",
    date: "2026-04-02",
    readTime: "7 min",
    category: "Technology",
  },
  {
    slug: "screen-tech-resumes-faster",
    title: "How to Screen 50 Developer Resumes Without Reading Every Line",
    description: "Technical hiring is brutal — frameworks change, titles vary, and every CV is formatted differently. AI parsing extracts structured data from any format.",
    date: "2026-03-30",
    readTime: "6 min",
    category: "Tech Hiring",
  },
  {
    slug: "candidate-comparison-side-by-side",
    title: "Side-by-Side Candidate Comparison: Making Better Shortlist Decisions",
    description: "Comparing candidates in spreadsheets is error-prone and slow. Side-by-side evidence comparison surfaces the right differences instantly.",
    date: "2026-03-28",
    readTime: "5 min",
    category: "Best Practices",
  },
  {
    slug: "skills-gap-analysis-hiring",
    title: "Skills Gap Analysis in Hiring: Know What Each Candidate Is Missing",
    description: "Every candidate has gaps. The question is which gaps matter. Automated skills gap analysis maps candidate evidence against every JD requirement.",
    date: "2026-03-26",
    readTime: "6 min",
    category: "Best Practices",
  },
  {
    slug: "ai-recruitment-tools-australia",
    title: "The Best AI Recruitment Tools for Australian Agencies in 2026",
    description: "A practical comparison of AI hiring tools available in Australia — what they do, what they cost, and which ones actually save recruiters time.",
    date: "2026-03-24",
    readTime: "9 min",
    category: "Industry",
  },
  {
    slug: "evidence-based-hiring-decisions",
    title: "Evidence-Based Hiring: Why Gut Feel Isn't Good Enough Anymore",
    description: "68% of hiring managers admit to making gut-feel decisions. Evidence-based hiring replaces intuition with structured, defensible candidate evaluation.",
    date: "2026-03-22",
    readTime: "7 min",
    category: "Best Practices",
  },
];
