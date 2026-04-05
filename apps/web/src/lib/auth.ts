/**
 * HireIQ auth utilities
 *
 * Authentication strategy: Microsoft Entra ID (Azure Active Directory)
 * via OAuth 2.0 / OIDC.
 *
 * Implementation options (choose one):
 *   A) next-auth with Azure AD provider (simpler, recommended)
 *   B) MSAL.js directly for fine-grained token control
 *
 * TODO: implement one of the two options above.
 */

/* ─── Types ─────────────────────────────────────────────────────────────────── */

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  /** Microsoft Entra object ID */
  entraId: string;
  /** Organization tenant ID */
  tenantId: string;
  /** Avatar URL from Microsoft Graph */
  avatarUrl?: string;
}

export interface AuthSession {
  user: AuthUser;
  accessToken: string;
  expiresAt: number; // Unix timestamp
}

/* ─── Auth config ───────────────────────────────────────────────────────────── */

export const AUTH_CONFIG = {
  /** Azure AD tenant ID — set in .env.local */
  tenantId: process.env.NEXT_PUBLIC_AZURE_TENANT_ID ?? "",
  /** Azure AD app client ID */
  clientId: process.env.NEXT_PUBLIC_AZURE_CLIENT_ID ?? "",
  /** Redirect URI after login */
  redirectUri:
    process.env.NEXT_PUBLIC_AUTH_REDIRECT_URI ?? "http://localhost:3000/api/auth/callback",
  /** OAuth scopes */
  scopes: [
    "openid",
    "profile",
    "email",
    "offline_access",
    `api://${process.env.NEXT_PUBLIC_AZURE_CLIENT_ID ?? ""}/access_as_user`,
  ],
} as const;

/* ─── Session helpers ───────────────────────────────────────────────────────── */

/**
 * Get the current session on the SERVER.
 * For use in Server Components and API routes.
 *
 * TODO: implement with next-auth getServerSession or MSAL node.
 */
export async function getServerSession(): Promise<AuthSession | null> {
  // TODO: return getServerSession(authOptions) from next-auth
  // or decode / verify the JWT from cookies
  return null;
}

/**
 * Check if a session is still valid (not expired).
 */
export function isSessionValid(session: AuthSession): boolean {
  return Date.now() < session.expiresAt * 1000;
}

/**
 * Extract user initials for avatar fallback.
 */
export function getUserInitials(name: string): string {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((n) => n[0].toUpperCase())
    .join("");
}

/* ─── Route protection ──────────────────────────────────────────────────────── */

/**
 * Protected routes — paths that require authentication.
 * The middleware.ts file will check these and redirect to /login.
 */
export const PROTECTED_ROUTES = ["/workspaces", "/billing", "/settings"];

/**
 * Public routes — always accessible without auth.
 */
export const PUBLIC_ROUTES = [
  "/login",
  "/signup",
  "/terms",
  "/privacy",
  "/api/auth",
];

/**
 * Determine whether a path requires authentication.
 */
export function isProtectedRoute(pathname: string): boolean {
  return PROTECTED_ROUTES.some(
    (route) => pathname === route || pathname.startsWith(`${route}/`)
  );
}

export function isPublicRoute(pathname: string): boolean {
  return PUBLIC_ROUTES.some(
    (route) => pathname === route || pathname.startsWith(`${route}/`)
  );
}

/* ─── Middleware helper ─────────────────────────────────────────────────────── */

/**
 * Generate the login URL with a returnTo parameter.
 * Used by Next.js middleware to redirect unauthenticated requests.
 */
export function buildLoginUrl(returnTo: string): string {
  const params = new URLSearchParams({ returnTo });
  return `/login?${params.toString()}`;
}
