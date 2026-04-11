/**
 * Lightweight funnel event tracking — fires to own API, no third-party deps.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://ca-hireiq-api-dev.delightfulsea-504dfc83.australiaeast.azurecontainerapps.io";

let sessionId: string | null = null;

function getSessionId(): string {
  if (typeof window === "undefined") return "ssr";
  if (!sessionId) {
    sessionId = sessionStorage.getItem("hireiq-sid");
    if (!sessionId) {
      sessionId = crypto.randomUUID();
      sessionStorage.setItem("hireiq-sid", sessionId);
    }
  }
  return sessionId;
}

export function track(event: string, props?: Record<string, unknown>) {
  if (typeof window === "undefined") return;
  const ref = localStorage.getItem("hireiq-ref") || undefined;
  const payload = {
    event,
    session_id: getSessionId(),
    ref,
    url: window.location.pathname,
    ...props,
  };
  // Fire and forget — never block UI
  fetch(`${API_URL}/api/v1/events`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    keepalive: true,
  }).catch(() => {});
}
