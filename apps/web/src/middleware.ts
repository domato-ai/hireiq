import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { isProtectedRoute, isPublicRoute, buildLoginUrl } from "@/lib/auth";

/**
 * Next.js middleware — auth route guard.
 *
 * Runs on every request matching the config.matcher pattern.
 * Redirects unauthenticated users from protected routes to /login.
 *
 * TODO: replace the placeholder session check with a real token validation
 * once next-auth or MSAL is wired up.
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Skip Next.js internals
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/favicon") ||
    pathname.includes(".")
  ) {
    return NextResponse.next();
  }

  // TODO: validate the session cookie / token here.
  // Example with next-auth:
  //   const token = await getToken({ req: request, secret: process.env.NEXTAUTH_SECRET });
  //   const isAuthenticated = !!token;
  //
  // For now, we allow all traffic through (no-op guard).
  const isAuthenticated = true; // REPLACE with real check

  if (!isAuthenticated && isProtectedRoute(pathname)) {
    const loginUrl = new URL(buildLoginUrl(pathname), request.url);
    return NextResponse.redirect(loginUrl);
  }

  if (isAuthenticated && isPublicRoute(pathname) && pathname !== "/") {
    // Don't redirect from login/signup if already authenticated —
    // let the user sign in with a different account if needed.
    // Remove this block if you prefer hard redirects.
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths EXCEPT:
     *   - _next/static (static files)
     *   - _next/image (image optimization)
     *   - favicon.ico
     */
    "/((?!_next/static|_next/image|favicon.ico).*)",
  ],
};
