"use client";

/**
 * Microsoft Entra ID (Azure AD) sign-in button.
 * Triggers the OAuth 2.0 / OIDC redirect flow.
 *
 * TODO: wire up MSAL.js or next-auth with Azure AD provider.
 */
export function MicrosoftSignInButton() {
  function handleSignIn() {
    // TODO: initiate Microsoft Entra OIDC flow
    // Option A: next-auth  → signIn("azure-ad")
    // Option B: MSAL.js    → msalInstance.loginRedirect(loginRequest)
    console.warn("[HireIQ] Microsoft Entra sign-in not yet wired up.");
  }

  return (
    <button
      type="button"
      onClick={handleSignIn}
      className="
        w-full flex items-center justify-center gap-3
        px-4 py-3 rounded
        bg-ink text-bone-50
        text-sm font-medium
        border border-ink
        hover:bg-ink-700
        active:bg-ink-900
        transition-colors duration-150
        focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink
      "
    >
      <MicrosoftLogo />
      Continue with Microsoft
    </button>
  );
}

function MicrosoftLogo() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 21 21"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <rect x="0" y="0" width="10" height="10" fill="#F25022" />
      <rect x="11" y="0" width="10" height="10" fill="#7FBA00" />
      <rect x="0" y="11" width="10" height="10" fill="#00A4EF" />
      <rect x="11" y="11" width="10" height="10" fill="#FFB900" />
    </svg>
  );
}
