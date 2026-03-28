"use client";

import { Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ContextPanel } from "@/components/workspace/ContextPanel";
import { CandidateTable } from "@/components/workspace/CandidateTable";
import { EvidencePanel } from "@/components/workspace/EvidencePanel";
import { getRoleById, getWorkspaceById, getCandidatesByRole } from "@/lib/mock-data";

export function RoleWorkspaceClient({
  workspaceId,
  roleId,
}: {
  workspaceId: string;
  roleId: string;
}) {
  return (
    <Suspense fallback={<div className="flex-1 flex items-center justify-center text-sm" style={{ color: 'var(--text-muted)' }}>Loading…</div>}>
      <RoleWorkspaceInner workspaceId={workspaceId} roleId={roleId} />
    </Suspense>
  );
}

function RoleWorkspaceInner({
  workspaceId,
  roleId,
}: {
  workspaceId: string;
  roleId: string;
}) {
  const searchParams = useSearchParams();
  const candidateId = searchParams.get("candidateId") ?? undefined;

  const role = getRoleById(roleId);
  const workspace = getWorkspaceById(workspaceId);
  const candidates = getCandidatesByRole(roleId);

  return (
    <div className="flex-1 overflow-hidden flex flex-col h-full">
      <RoleToolbar
        workspaceName={workspace?.name ?? workspaceId}
        workspaceId={workspaceId}
        roleName={role?.title ?? "Role"}
        roleId={roleId}
        candidateCount={candidates.length}
        scoredCount={candidates.filter((c) => c.status === "scored").length}
        hasJD={role?.hasJD ?? false}
      />

      <div className="flex-1 overflow-hidden grid grid-cols-[300px_1fr_340px] divide-x divide-ink/8">
        <div className="workspace-panel bg-bone">
          <ContextPanel roleId={roleId} workspaceId={workspaceId} hasJD={role?.hasJD ?? false} roleTitle={role?.title} factors={role?.factors ?? []} />
        </div>
        <div className="workspace-panel bg-bone-50">
          <CandidateTable roleId={roleId} workspaceId={workspaceId} selectedCandidateId={candidateId} factors={role?.factors ?? []} />
        </div>
        <div className="workspace-panel bg-bone">
          <EvidencePanel roleId={roleId} workspaceId={workspaceId} candidateId={candidateId} />
        </div>
      </div>
    </div>
  );
}

function RoleToolbar({ workspaceName, workspaceId, roleName, candidateCount, scoredCount, hasJD }: {
  workspaceName: string; workspaceId: string; roleName: string; roleId: string; candidateCount: number; scoredCount: number; hasJD: boolean;
}) {
  return (
    <div className="flex-shrink-0 h-12 border-b border-ink/8 bg-bone flex items-center px-4 gap-4">
      <nav className="flex items-center gap-1.5 text-sm min-w-0">
        <Link href="/workspaces" className="text-ink-400 hover:text-ink transition-colors truncate text-xs">Workspaces</Link>
        <ChevronRight />
        <Link href={`/workspaces/${workspaceId}`} className="text-ink-400 hover:text-ink transition-colors truncate text-xs max-w-[180px]">{workspaceName}</Link>
        <ChevronRight />
        <span className="font-medium text-ink truncate text-xs">{roleName}</span>
      </nav>
      <div className="h-4 w-px bg-ink/12 flex-shrink-0" />
      <div className="flex items-center gap-3 text-2xs text-ink-400">
        <span className="font-mono"><span className="text-ink font-semibold">{scoredCount}</span>/{candidateCount} scored</span>
        {hasJD ? (
          <span className="text-signal-green-dark bg-signal-green-light px-1.5 py-0.5 rounded text-2xs font-semibold">JD loaded</span>
        ) : (
          <span className="text-signal-amber-dark bg-signal-amber-light px-1.5 py-0.5 rounded text-2xs font-semibold">No JD</span>
        )}
      </div>
      <div className="flex-1" />
      <div className="flex items-center gap-1">
        {["Export", "Share", "Settings"].map((l) => (
          <button key={l} className="text-xs text-ink-400 hover:text-ink px-2.5 py-1.5 rounded hover:bg-ink/6 transition-colors">{l}</button>
        ))}
      </div>
    </div>
  );
}

function ChevronRight() {
  return (
    <svg width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden="true" className="text-ink-300 flex-shrink-0">
      <path d="M3.5 2L6.5 5l-3 3" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
