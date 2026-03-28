"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export function ClientRedirect({ to }: { to: string }) {
  const router = useRouter();
  useEffect(() => { router.replace(to); }, [to, router]);
  return (
    <div className="flex-1 flex items-center justify-center" style={{ color: 'var(--text-muted)' }}>
      <p className="text-sm">Redirecting…</p>
    </div>
  );
}
