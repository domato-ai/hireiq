// ============================================================
// Shared TypeScript Types — RoleFitAI
// ============================================================

// ---------------------
// Enums
// ---------------------

export enum Plan {
  free = 'free',
  pro = 'pro',
  team = 'team',
}

export type ConfidenceLevel = 'strong' | 'weak' | 'not_found';

// ---------------------
// Core Domain Types
// ---------------------

export interface User {
  id: string;
  email: string;
  name: string;
  plan: Plan;
}

export interface Workspace {
  id: string;
  name: string;
  ownerId: string;
  createdAt: string; // ISO 8601
}

export interface Role {
  id: string;
  workspaceId: string;
  title: string;
  description: string;
  requirements: string[];
  status: 'draft' | 'active' | 'closed';
}

export interface Candidate {
  id: string;
  roleId: string;
  name: string;
  email: string;
  status: 'pending' | 'parsed' | 'scored' | 'rejected' | 'shortlisted';
  overallScore: number | null;
}

// ---------------------
// Scoring
// ---------------------

export interface ScoreFactor {
  name: string;
  score: number;        // 0–100
  weight: number;       // 0–1, weights should sum to 1
  reason: string;
  confidence: ConfidenceLevel;
}

export interface CandidateScore {
  overall: number;      // 0–100
  factors: ScoreFactor[];
  strengths: string[];
  risks: string[];
  missingEvidence: string[];
}

// ---------------------
// Documents
// ---------------------

export interface CandidateDocument {
  id: string;
  candidateId: string | null; // null before candidate record is created
  filename: string;
  fileType: string;
  sizeBytes: number;
  uploadedAt: string; // ISO 8601
}

// ---------------------
// Billing & Usage
// ---------------------

export interface Subscription {
  id: string;
  plan: Plan;
  status: 'active' | 'past_due' | 'canceled' | 'trialing';
  currentPeriodEnd: string; // ISO 8601
}

export interface UsageEvent {
  id: string;
  eventType: string;
  quantity: number;
  createdAt: string; // ISO 8601
}
