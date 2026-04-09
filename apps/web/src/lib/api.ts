/**
 * HireIQ API client
 *
 * Thin wrapper around fetch that handles:
 *   - Base URL configuration
 *   - Auth token injection
 *   - Consistent error handling
 *   - Response typing
 *
 * TODO: wire up real auth token retrieval (MSAL / next-auth session).
 */

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

/* ─── Error types ───────────────────────────────────────────────────────────── */

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export class UnauthorizedError extends ApiError {
  constructor() {
    super(401, "UNAUTHORIZED", "Authentication required. Please sign in.");
    this.name = "UnauthorizedError";
  }
}

export class NotFoundError extends ApiError {
  constructor(resource: string) {
    super(404, "NOT_FOUND", `${resource} not found.`);
    this.name = "NotFoundError";
  }
}

/* ─── Core fetch wrapper ────────────────────────────────────────────────────── */

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
}

async function getAuthToken(): Promise<string | null> {
  // TODO: retrieve JWT from MSAL or next-auth session
  // Server components: use getServerSession(authOptions)
  // Client components: use useSession() hook or MSAL acquireTokenSilent
  return null;
}

export async function apiFetch<T>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const token = await getAuthToken();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));

    if (response.status === 401) throw new UnauthorizedError();
    if (response.status === 404)
      throw new NotFoundError(errorBody.resource ?? "Resource");

    throw new ApiError(
      response.status,
      errorBody.code ?? "API_ERROR",
      errorBody.message ?? `Request failed with status ${response.status}`
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

/* ─── Resource clients ──────────────────────────────────────────────────────── */

// --- Workspaces ---

export interface Workspace {
  id: string;
  name: string;
  slug: string;
  createdAt: string;
  roleCount: number;
}

export const workspacesApi = {
  list: () => apiFetch<Workspace[]>("/workspaces"),

  get: (id: string) => apiFetch<Workspace>(`/workspaces/${id}`),

  create: (data: { name: string }) =>
    apiFetch<Workspace>("/workspaces", { method: "POST", body: data }),

  update: (id: string, data: Partial<Pick<Workspace, "name">>) =>
    apiFetch<Workspace>(`/workspaces/${id}`, { method: "PATCH", body: data }),

  delete: (id: string) =>
    apiFetch<void>(`/workspaces/${id}`, { method: "DELETE" }),
};

// --- Roles ---

export interface Role {
  id: string;
  workspaceId: string;
  title: string;
  jdText: string | null;
  criteria: RoleCriterion[];
  candidateCount: number;
  status: "draft" | "active" | "closed";
  createdAt: string;
}

export interface RoleCriterion {
  id: string;
  label: string;
  type: "required" | "preferred";
  weight: 1 | 2 | 3;
}

export const rolesApi = {
  list: (workspaceId: string) =>
    apiFetch<Role[]>(`/workspaces/${workspaceId}/roles`),

  get: (workspaceId: string, roleId: string) =>
    apiFetch<Role>(`/workspaces/${workspaceId}/roles/${roleId}`),

  create: (
    workspaceId: string,
    data: Pick<Role, "title"> & { jdText?: string }
  ) =>
    apiFetch<Role>(`/workspaces/${workspaceId}/roles`, {
      method: "POST",
      body: data,
    }),

  uploadJD: (workspaceId: string, roleId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return apiFetch<{ jdText: string; criteria: RoleCriterion[] }>(
      `/workspaces/${workspaceId}/roles/${roleId}/jd`,
      { method: "POST", body: formData, headers: {} } // let browser set multipart headers
    );
  },
};

// --- Candidates ---

export interface Candidate {
  id: string;
  roleId: string;
  name: string;
  title: string | null;
  overallScore: number | null;
  confidence: "strong" | "weak" | "not-found" | null;
  status: "pending" | "processing" | "scored" | "error";
  createdAt: string;
}

export interface CandidateEvidence {
  candidateId: string;
  criterionScores: CriterionScore[];
}

export interface CriterionScore {
  criterionId: string;
  criterionLabel: string;
  score: number | null;
  confidence: "strong" | "weak" | "not-found";
  quote: string | null;
  reasoning: string;
  sourceSection: string | null;
}

export const candidatesApi = {
  list: (workspaceId: string, roleId: string) =>
    apiFetch<Candidate[]>(
      `/workspaces/${workspaceId}/roles/${roleId}/candidates`
    ),

  get: (workspaceId: string, roleId: string, candidateId: string) =>
    apiFetch<Candidate>(
      `/workspaces/${workspaceId}/roles/${roleId}/candidates/${candidateId}`
    ),

  upload: (workspaceId: string, roleId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return apiFetch<Candidate>(
      `/workspaces/${workspaceId}/roles/${roleId}/candidates`,
      { method: "POST", body: formData, headers: {} }
    );
  },

  getEvidence: (
    workspaceId: string,
    roleId: string,
    candidateId: string
  ) =>
    apiFetch<CandidateEvidence>(
      `/workspaces/${workspaceId}/roles/${roleId}/candidates/${candidateId}/evidence`
    ),

  delete: (workspaceId: string, roleId: string, candidateId: string) =>
    apiFetch<void>(
      `/workspaces/${workspaceId}/roles/${roleId}/candidates/${candidateId}`,
      { method: "DELETE" }
    ),
};

// --- Billing ---

export interface BillingStatus {
  plan: "starter" | "growth" | "enterprise";
  currentPeriodEnd: string;
  candidatesUsed: number;
  candidatesLimit: number;
  rolesActive: number;
  rolesLimit: number;
}

export interface Pricing {
  currency: string;
  symbol: string;
  pro_price: number;
  pro_interval: string;
}

export const billingApi = {
  getStatus: () => apiFetch<BillingStatus>("/billing/status"),

  getPricing: () => apiFetch<Pricing>("/billing/pricing"),

  createCheckoutSession: (planId: string, currency?: string) =>
    apiFetch<{ url: string }>("/billing/checkout", {
      method: "POST",
      body: { planId },
      headers: currency ? { "x-currency": currency } : undefined,
    }),

  createPortalSession: () =>
    apiFetch<{ url: string }>("/billing/portal", { method: "POST" }),
};

/* ─── Convenience re-export ─────────────────────────────────────────────────── */

export const api = {
  workspaces: workspacesApi,
  roles: rolesApi,
  candidates: candidatesApi,
  billing: billingApi,
};
