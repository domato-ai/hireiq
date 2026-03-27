/**
 * Mock data for Phase 1 development.
 * Replace with API calls when backend is ready.
 */

/* ─── Types ─────────────────────────────────────────────────────────────────── */

export interface Workspace {
  id: string;
  name: string;
  description: string;
  roleCount: number;
  candidateCount: number;
  lastActivity: string; // ISO date string
  status: "active" | "archived";
}

export interface Role {
  id: string;
  workspaceId: string;
  title: string;
  team: string;
  level: string;
  location: string;
  status: "draft" | "active" | "closed";
  candidateCount: number;
  scoredCount: number;
  createdAt: string;
  hasJD: boolean;
  factors: string[];
}

export interface FactorScore {
  factorId: string;
  label: string;
  score: number | null; // 0–100
  confidence: "strong" | "weak" | "not-found";
  weight: number; // 1–3
}

export interface Candidate {
  id: string;
  roleId: string;
  name: string;
  currentTitle: string;
  currentCompany: string;
  location: string;
  yearsExp: number;
  overallScore: number; // 0–100
  confidence: "strong" | "weak" | "not-found";
  status: "pending" | "processing" | "scored" | "error";
  factorScores: FactorScore[];
  strengths: string[];
  risks: string[];
  missingEvidence: string[];
  resumeFileName: string;
  processedAt: string;
}

export interface EvidenceItem {
  factorId: string;
  factorLabel: string;
  score: number | null;
  confidence: "strong" | "weak" | "not-found";
  weight: number;
  quote: string | null;
  reasoning: string;
  sourceSection: string | null;
}

/* ─── Workspaces ────────────────────────────────────────────────────────────── */

export const MOCK_WORKSPACES: Workspace[] = [
  {
    id: "ws-1",
    name: "Product Leadership — Series B",
    description: "Senior PM and Director hires for the core product org.",
    roleCount: 2,
    candidateCount: 14,
    lastActivity: "2026-03-26T14:32:00Z",
    status: "active",
  },
  {
    id: "ws-2",
    name: "Engineering Expansion Q2",
    description: "Staff engineers and TL hires across Platform and Data.",
    roleCount: 1,
    candidateCount: 9,
    lastActivity: "2026-03-24T09:15:00Z",
    status: "active",
  },
];

/* ─── Roles ─────────────────────────────────────────────────────────────────── */

export const MOCK_ROLES: Role[] = [
  {
    id: "role-1",
    workspaceId: "ws-1",
    title: "Senior Product Manager",
    team: "Core Product",
    level: "Senior IC",
    location: "San Francisco / Remote",
    status: "active",
    candidateCount: 9,
    scoredCount: 9,
    createdAt: "2026-03-18T10:00:00Z",
    hasJD: true,
    factors: [
      "PM Experience",
      "B2B SaaS",
      "Cross-functional Leadership",
      "Data Fluency",
      "Communication",
    ],
  },
  {
    id: "role-2",
    workspaceId: "ws-1",
    title: "Director of Product",
    team: "Platform",
    level: "Director",
    location: "New York",
    status: "active",
    candidateCount: 5,
    scoredCount: 3,
    createdAt: "2026-03-20T11:00:00Z",
    hasJD: true,
    factors: [
      "PM Experience",
      "People Management",
      "Strategic Vision",
      "Exec Communication",
      "B2B SaaS",
    ],
  },
  {
    id: "role-3",
    workspaceId: "ws-2",
    title: "Staff Software Engineer",
    team: "Platform Infrastructure",
    level: "Staff IC",
    location: "Remote",
    status: "active",
    candidateCount: 9,
    scoredCount: 7,
    createdAt: "2026-03-22T09:00:00Z",
    hasJD: false,
    factors: [
      "Systems Design",
      "Technical Depth",
      "Distributed Systems",
      "Leadership",
      "Communication",
    ],
  },
];

/* ─── Candidates for Role 1 ─────────────────────────────────────────────────── */

export const MOCK_CANDIDATES: Candidate[] = [
  {
    id: "cand-1",
    roleId: "role-1",
    name: "Sarah Chen",
    currentTitle: "Senior Product Manager",
    currentCompany: "Stripe",
    location: "San Francisco, CA",
    yearsExp: 7,
    overallScore: 91,
    confidence: "strong",
    status: "scored",
    resumeFileName: "sarah-chen-resume.pdf",
    processedAt: "2026-03-25T14:02:00Z",
    strengths: [
      "7 years PM experience at Stripe and Square — senior scope, two credible companies",
      "Direct B2B SaaS billing ownership: 200k+ business customers, ARR accountability",
      "Multi-stakeholder delivery: partnered with Sales, Finance, Legal across three eng teams",
    ],
    risks: [
      "No explicit metrics in resume — A/B testing mentioned once, no numbers",
      "Small company experience only — no enterprise or mid-market context",
    ],
    missingEvidence: ["SQL / self-serve data tools", "Enterprise sales cycle exposure"],
    factorScores: [
      { factorId: "pm-exp", label: "PM Experience", score: 92, confidence: "strong", weight: 3 },
      { factorId: "b2b", label: "B2B SaaS", score: 90, confidence: "strong", weight: 3 },
      { factorId: "xfn", label: "Cross-functional Leadership", score: 94, confidence: "strong", weight: 2 },
      { factorId: "data", label: "Data Fluency", score: 68, confidence: "weak", weight: 2 },
      { factorId: "comms", label: "Communication", score: 85, confidence: "strong", weight: 1 },
    ],
  },
  {
    id: "cand-2",
    roleId: "role-1",
    name: "Marcus Webb",
    currentTitle: "Product Lead",
    currentCompany: "Notion",
    location: "New York, NY",
    yearsExp: 6,
    overallScore: 78,
    confidence: "strong",
    status: "scored",
    resumeFileName: "marcus-webb-cv.pdf",
    processedAt: "2026-03-25T14:15:00Z",
    strengths: [
      "Strong consumer-to-B2B transition story: Notion Teams has measurable B2B traction",
      "Led 4-person PM team, clear people management instinct",
    ],
    risks: [
      "Primarily consumer product background — B2B enterprise exposure is thin",
      "Notion Teams is quasi-B2B; no complex sales cycle or procurement experience",
    ],
    missingEvidence: ["Revenue/ARR accountability", "Enterprise compliance requirements"],
    factorScores: [
      { factorId: "pm-exp", label: "PM Experience", score: 82, confidence: "strong", weight: 3 },
      { factorId: "b2b", label: "B2B SaaS", score: 61, confidence: "weak", weight: 3 },
      { factorId: "xfn", label: "Cross-functional Leadership", score: 79, confidence: "strong", weight: 2 },
      { factorId: "data", label: "Data Fluency", score: 84, confidence: "strong", weight: 2 },
      { factorId: "comms", label: "Communication", score: 88, confidence: "strong", weight: 1 },
    ],
  },
  {
    id: "cand-3",
    roleId: "role-1",
    name: "Priya Nair",
    currentTitle: "Product Manager",
    currentCompany: "Loom (Atlassian)",
    location: "Austin, TX",
    yearsExp: 5,
    overallScore: 72,
    confidence: "strong",
    status: "scored",
    resumeFileName: "priya-nair-resume.pdf",
    processedAt: "2026-03-25T14:28:00Z",
    strengths: [
      "Loom acquisition gives direct enterprise distribution exposure",
      "5 years clean PM trajectory, shipped multiple 0→1 features",
    ],
    risks: [
      "Borderline on years of experience — exactly at threshold, no buffer",
      "No direct revenue ownership — worked on engagement, not monetization",
    ],
    missingEvidence: ["P&L or ARR visibility", "Complex stakeholder environments"],
    factorScores: [
      { factorId: "pm-exp", label: "PM Experience", score: 74, confidence: "strong", weight: 3 },
      { factorId: "b2b", label: "B2B SaaS", score: 72, confidence: "strong", weight: 3 },
      { factorId: "xfn", label: "Cross-functional Leadership", score: 68, confidence: "weak", weight: 2 },
      { factorId: "data", label: "Data Fluency", score: 76, confidence: "strong", weight: 2 },
      { factorId: "comms", label: "Communication", score: 70, confidence: "weak", weight: 1 },
    ],
  },
  {
    id: "cand-4",
    roleId: "role-1",
    name: "Jordan Kim",
    currentTitle: "Product Manager",
    currentCompany: "Salesforce",
    location: "Chicago, IL",
    yearsExp: 4,
    overallScore: 61,
    confidence: "weak",
    status: "scored",
    resumeFileName: "jordan-kim-resume.pdf",
    processedAt: "2026-03-25T14:41:00Z",
    strengths: [
      "Salesforce gives enterprise B2B credibility on brand recognition",
      "Exposure to complex procurement and compliance environments",
    ],
    risks: [
      "4 years only — below the 5-year threshold; no senior scope demonstrated",
      "Salesforce PMs often have narrow scope; resume doesn't show breadth",
      "No 0→1 experience — maintenance and iteration work only",
    ],
    missingEvidence: ["Product ownership beyond roadmap execution", "Cross-org influence without authority"],
    factorScores: [
      { factorId: "pm-exp", label: "PM Experience", score: 58, confidence: "weak", weight: 3 },
      { factorId: "b2b", label: "B2B SaaS", score: 72, confidence: "strong", weight: 3 },
      { factorId: "xfn", label: "Cross-functional Leadership", score: 55, confidence: "weak", weight: 2 },
      { factorId: "data", label: "Data Fluency", score: 60, confidence: "weak", weight: 2 },
      { factorId: "comms", label: "Communication", score: 63, confidence: "weak", weight: 1 },
    ],
  },
  {
    id: "cand-5",
    roleId: "role-1",
    name: "Devon Marsh",
    currentTitle: "Senior Product Manager",
    currentCompany: "HubSpot",
    location: "Boston, MA",
    yearsExp: 6,
    overallScore: 69,
    confidence: "weak",
    status: "scored",
    resumeFileName: "devon-marsh-cv.pdf",
    processedAt: "2026-03-25T14:54:00Z",
    strengths: [
      "HubSpot is textbook B2B SaaS — SMB-to-mid-market motion is directly relevant",
      "6 years shows trajectory, recently promoted to Senior",
    ],
    risks: [
      "Resume is generic — no specifics on outcomes, no numbers, no quotes of impact",
      "Cross-functional evidence is thin — mentions teams but no concrete examples",
    ],
    missingEvidence: ["Quantified impact (ARR, retention, activation)", "Data tool fluency"],
    factorScores: [
      { factorId: "pm-exp", label: "PM Experience", score: 70, confidence: "weak", weight: 3 },
      { factorId: "b2b", label: "B2B SaaS", score: 80, confidence: "strong", weight: 3 },
      { factorId: "xfn", label: "Cross-functional Leadership", score: 58, confidence: "weak", weight: 2 },
      { factorId: "data", label: "Data Fluency", score: 50, confidence: "weak", weight: 2 },
      { factorId: "comms", label: "Communication", score: 72, confidence: "strong", weight: 1 },
    ],
  },
  {
    id: "cand-6",
    roleId: "role-1",
    name: "Aisha Okonkwo",
    currentTitle: "Product Manager II",
    currentCompany: "Intercom",
    location: "Remote",
    yearsExp: 5,
    overallScore: 65,
    confidence: "weak",
    status: "scored",
    resumeFileName: "aisha-okonkwo-resume.pdf",
    processedAt: "2026-03-25T15:07:00Z",
    strengths: [
      "Intercom is a strong B2B SaaS signal — customer communications platform",
      "Built and shipped integrations used by 10k+ accounts",
    ],
    risks: [
      "PM II title suggests mid-level — hasn't crossed into senior scope yet",
      "No people management, no org-level influence demonstrated",
    ],
    missingEvidence: ["Senior IC scope or equivalent", "Cross-org stakeholder ownership"],
    factorScores: [
      { factorId: "pm-exp", label: "PM Experience", score: 62, confidence: "weak", weight: 3 },
      { factorId: "b2b", label: "B2B SaaS", score: 78, confidence: "strong", weight: 3 },
      { factorId: "xfn", label: "Cross-functional Leadership", score: 55, confidence: "weak", weight: 2 },
      { factorId: "data", label: "Data Fluency", score: 66, confidence: "weak", weight: 2 },
      { factorId: "comms", label: "Communication", score: 70, confidence: "strong", weight: 1 },
    ],
  },
  {
    id: "cand-7",
    roleId: "role-1",
    name: "Tomás Rivera",
    currentTitle: "Associate Product Manager",
    currentCompany: "Brex",
    location: "San Francisco, CA",
    yearsExp: 2,
    overallScore: 38,
    confidence: "not-found",
    status: "scored",
    resumeFileName: "tomas-rivera-cv.pdf",
    processedAt: "2026-03-25T15:19:00Z",
    strengths: [
      "Brex is strong fintech B2B signal — understanding of finance workflows",
      "Shows strong first principles thinking in writing samples",
    ],
    risks: [
      "2 years only — significantly below the 5-year requirement",
      "APM programs produce generalists, not senior operators",
      "No evidence of ownership beyond assigned features",
    ],
    missingEvidence: [
      "5+ years PM experience",
      "Cross-functional leadership at scale",
      "Strategic product decisions",
    ],
    factorScores: [
      { factorId: "pm-exp", label: "PM Experience", score: 28, confidence: "not-found", weight: 3 },
      { factorId: "b2b", label: "B2B SaaS", score: 55, confidence: "weak", weight: 3 },
      { factorId: "xfn", label: "Cross-functional Leadership", score: 30, confidence: "not-found", weight: 2 },
      { factorId: "data", label: "Data Fluency", score: 45, confidence: "weak", weight: 2 },
      { factorId: "comms", label: "Communication", score: 50, confidence: "weak", weight: 1 },
    ],
  },
  {
    id: "cand-8",
    roleId: "role-1",
    name: "Riley Donovan",
    currentTitle: "Senior PM",
    currentCompany: "Workday",
    location: "Pleasanton, CA",
    yearsExp: 8,
    overallScore: 55,
    confidence: "weak",
    status: "scored",
    resumeFileName: "riley-donovan-resume.pdf",
    processedAt: "2026-03-25T15:32:00Z",
    strengths: [
      "8 years experience — well above threshold",
      "Workday gives enterprise HCM context — strong for HR-adjacent products",
    ],
    risks: [
      "Workday PMs work in heavily constrained product org — limited autonomy",
      "Resume language is passive — hard to attribute outcomes to this person specifically",
      "No consumer or startup experience — may struggle with ambiguity",
    ],
    missingEvidence: ["Autonomous product ownership", "0→1 or greenfield work"],
    factorScores: [
      { factorId: "pm-exp", label: "PM Experience", score: 65, confidence: "strong", weight: 3 },
      { factorId: "b2b", label: "B2B SaaS", score: 70, confidence: "strong", weight: 3 },
      { factorId: "xfn", label: "Cross-functional Leadership", score: 45, confidence: "not-found", weight: 2 },
      { factorId: "data", label: "Data Fluency", score: 40, confidence: "not-found", weight: 2 },
      { factorId: "comms", label: "Communication", score: 55, confidence: "weak", weight: 1 },
    ],
  },
  {
    id: "cand-9",
    roleId: "role-1",
    name: "Nadia Volkov",
    currentTitle: "Head of Product",
    currentCompany: "Series A startup",
    location: "Remote (EU)",
    yearsExp: 6,
    overallScore: 74,
    confidence: "strong",
    status: "scored",
    resumeFileName: "nadia-volkov-cv.pdf",
    processedAt: "2026-03-25T15:44:00Z",
    strengths: [
      "Head of Product at Series A — full stack product ownership, built team from scratch",
      "B2B SaaS product (sales intelligence), understands the buyer journey",
      "Strong data culture: built first analytics stack, led quarterly business reviews",
    ],
    risks: [
      "Non-US startup — no brand recognition, harder to validate claims",
      "Small company: may not have operated at scale of a US Series B+",
    ],
    missingEvidence: ["US market experience", "Working within a larger PM org"],
    factorScores: [
      { factorId: "pm-exp", label: "PM Experience", score: 78, confidence: "strong", weight: 3 },
      { factorId: "b2b", label: "B2B SaaS", score: 82, confidence: "strong", weight: 3 },
      { factorId: "xfn", label: "Cross-functional Leadership", score: 76, confidence: "strong", weight: 2 },
      { factorId: "data", label: "Data Fluency", score: 80, confidence: "strong", weight: 2 },
      { factorId: "comms", label: "Communication", score: 65, confidence: "weak", weight: 1 },
    ],
  },
];

/* ─── Evidence by candidate ─────────────────────────────────────────────────── */

export const MOCK_EVIDENCE: Record<string, EvidenceItem[]> = {
  "cand-1": [
    {
      factorId: "pm-exp",
      factorLabel: "PM Experience",
      score: 92,
      confidence: "strong",
      weight: 3,
      quote:
        '"Led product strategy for Stripe Billing from 0→1, managing a 6-person squad over 4 years. Previously 2 years PM at Square."',
      reasoning:
        "Clearly meets the 5-year threshold with senior scope at two credible companies. 7 total years, rising responsibility.",
      sourceSection: "Work Experience · Stripe · 2019–2023",
    },
    {
      factorId: "b2b",
      factorLabel: "B2B SaaS",
      score: 90,
      confidence: "strong",
      weight: 3,
      quote:
        '"Stripe Billing serves 200k+ businesses globally, with ARR accountability shared across the PM squad."',
      reasoning:
        "Core B2B experience. SaaS billing is among the most complex B2B product surfaces — invoicing, revenue recognition, tax.",
      sourceSection: "Work Experience · Stripe",
    },
    {
      factorId: "xfn",
      factorLabel: "Cross-functional Leadership",
      score: 94,
      confidence: "strong",
      weight: 2,
      quote:
        '"Partnered with Sales, Finance, Legal and 3 engineering teams to launch pricing overhaul in Q3 2022. Chaired weekly xfn sync for 14 months."',
      reasoning:
        "Concrete, multi-stakeholder coordination with measurable outcomes. The 14-month xfn sync is a strong signal of sustained leadership.",
      sourceSection: "Work Experience · Stripe",
    },
    {
      factorId: "data",
      factorLabel: "Data Fluency",
      score: 68,
      confidence: "weak",
      weight: 2,
      quote: null,
      reasoning:
        "Mentions dashboards and A/B testing in passing, but no specific metrics cited in the resume. \"Data-driven\" is used but not evidenced.",
      sourceSection: null,
    },
    {
      factorId: "comms",
      factorLabel: "Communication",
      score: 85,
      confidence: "strong",
      weight: 1,
      quote:
        '"Authored quarterly strategy memos distributed to C-suite and Board. Facilitated product council with VP Engineering and CFO."',
      reasoning:
        "Clear evidence of exec-level written and verbal communication. Strategy memos at board level is an unusually strong signal.",
      sourceSection: "Work Experience · Stripe",
    },
  ],
  "cand-2": [
    {
      factorId: "pm-exp",
      factorLabel: "PM Experience",
      score: 82,
      confidence: "strong",
      weight: 3,
      quote:
        '"6 years as PM at Notion, progressed from IC to Product Lead. Managed team of 4 PMs across Collaboration and Teams products."',
      reasoning:
        "Solid PM trajectory with management responsibility. Notion is a credible company. Good overall signal.",
      sourceSection: "Work Experience · Notion · 2020–present",
    },
    {
      factorId: "b2b",
      factorLabel: "B2B SaaS",
      score: 61,
      confidence: "weak",
      weight: 3,
      quote:
        '"Led Teams product — onboarding and permissioning for workspace admins and IT buyers at mid-market companies."',
      reasoning:
        "Notion Teams is quasi-B2B but primarily PLG/consumer. Admin workflows are B2B-adjacent, but no true enterprise sales cycle or procurement exposure.",
      sourceSection: "Work Experience · Notion",
    },
    {
      factorId: "xfn",
      factorLabel: "Cross-functional Leadership",
      score: 79,
      confidence: "strong",
      weight: 2,
      quote: '"Drove quarterly planning across Design, Research, Engineering (3 teams) and GTM."',
      reasoning:
        "Good breadth of cross-functional partnership. Evidence is consistent across multiple resume entries.",
      sourceSection: "Work Experience · Notion",
    },
    {
      factorId: "data",
      factorLabel: "Data Fluency",
      score: 84,
      confidence: "strong",
      weight: 2,
      quote:
        '"Built Notion\'s first product metrics framework; introduced activation funnels that improved D7 retention by 12%."',
      reasoning:
        "Strong data signal — quantified outcome with specific metric. Framework-building shows deeper data thinking than typical.",
      sourceSection: "Work Experience · Notion",
    },
    {
      factorId: "comms",
      factorLabel: "Communication",
      score: 88,
      confidence: "strong",
      weight: 1,
      quote: '"Presented product vision to board in two consecutive off-sites. Authored PM team\'s roadmap principles doc (now used company-wide)."',
      reasoning:
        "Board-level communication and cross-company documentation influence. Strong written comms signal.",
      sourceSection: "Work Experience · Notion",
    },
  ],
};

/* ─── Helper functions ──────────────────────────────────────────────────────── */

export function getWorkspaceById(id: string): Workspace | undefined {
  return MOCK_WORKSPACES.find((ws) => ws.id === id);
}

export function getRoleById(id: string): Role | undefined {
  return MOCK_ROLES.find((r) => r.id === id);
}

export function getRolesByWorkspace(workspaceId: string): Role[] {
  return MOCK_ROLES.filter((r) => r.workspaceId === workspaceId);
}

export function getCandidatesByRole(roleId: string): Candidate[] {
  return MOCK_CANDIDATES.filter((c) => c.roleId === roleId).sort(
    (a, b) => b.overallScore - a.overallScore
  );
}

export function getCandidateById(id: string): Candidate | undefined {
  return MOCK_CANDIDATES.find((c) => c.id === id);
}

export function getEvidenceForCandidate(candidateId: string): EvidenceItem[] {
  return MOCK_EVIDENCE[candidateId] ?? [];
}

export function formatRelativeTime(isoDate: string): string {
  const now = new Date("2026-03-27T00:00:00Z");
  const date = new Date(isoDate);
  const diff = now.getTime() - date.getTime();
  const hours = Math.floor(diff / (1000 * 60 * 60));
  const days = Math.floor(hours / 24);

  if (hours < 1) return "just now";
  if (hours < 24) return `${hours}h ago`;
  if (days === 1) return "yesterday";
  if (days < 7) return `${days}d ago`;
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}
