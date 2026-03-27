import type { Metadata } from "next";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  MOCK_WORKSPACES,
  MOCK_ROLES,
  MOCK_CANDIDATES,
  formatRelativeTime,
  type Workspace,
  type Role,
} from "@/lib/mock-data";

export const metadata: Metadata = {
  title: "Workspaces",
};

export default function WorkspacesPage() {
  const workspaces = MOCK_WORKSPACES;
  const totalRoles = MOCK_ROLES.length;
  const totalCandidates = MOCK_ROLES.reduce((s, r) => s + r.candidateCount, 0);
  const totalScored = MOCK_ROLES.reduce((s, r) => s + r.scoredCount, 0);
  const topCandidate = MOCK_CANDIDATES.reduce((best, c) =>
    c.overallScore > best.overallScore ? c : best
  );

  return (
    <div className="flex-1 overflow-y-auto bg-bone">
      {/* ── Top bar: dense metrics strip ── */}
      <div className="sticky top-0 z-20 bg-ink-900 border-b border-ink-700">
        <div className="px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="font-display text-xl text-bone-100">Workspaces</h1>
            <span className="text-bone-600 text-xs font-mono">
              {workspaces.length} active
            </span>
          </div>
          <Button size="sm">
            <PlusIcon />
            New workspace
          </Button>
        </div>

        {/* Metrics ticker */}
        <div className="px-8 pb-3 flex items-center gap-8">
          <TickerMetric
            value={totalRoles.toString()}
            label="Open roles"
            trend="+2 this week"
          />
          <div className="w-px h-6 bg-ink-700" />
          <TickerMetric
            value={totalCandidates.toString()}
            label="Candidates"
            trend={`${totalScored} scored`}
          />
          <div className="w-px h-6 bg-ink-700" />
          <TickerMetric
            value={`${Math.round((totalScored / totalCandidates) * 100)}%`}
            label="Scored"
            trend="pipeline complete"
          />
          <div className="w-px h-6 bg-ink-700" />
          <TickerMetric
            value={topCandidate.name.split(" ")[0]}
            label="Top signal"
            trend={`${topCandidate.overallScore}/100`}
          />
        </div>
      </div>

      {/* ── Workspace grid ── */}
      <div className="px-8 py-6">
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 max-w-6xl">
          {workspaces.map((ws) => (
            <WorkspaceCard key={ws.id} workspace={ws} />
          ))}

          {/* New workspace card */}
          <button className="ws-card-enter group border border-dashed border-ink/15 rounded-lg hover:border-ink/30 transition-all duration-200 flex items-center justify-center min-h-[200px] bg-bone-50/50 hover:bg-bone-50">
            <div className="text-center">
              <div className="w-10 h-10 rounded-full border border-ink/15 flex items-center justify-center mx-auto mb-3 group-hover:border-ink/30 group-hover:bg-ink/5 transition-all">
                <PlusIcon />
              </div>
              <p className="text-sm font-medium text-ink-400 group-hover:text-ink transition-colors">
                Create workspace
              </p>
              <p className="text-xs text-ink-300 mt-1">
                Start a new hiring pipeline
              </p>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}

/* ─── Components ──────────────────────────────────────────────────────────── */

function TickerMetric({
  value,
  label,
  trend,
}: {
  value: string;
  label: string;
  trend: string;
}) {
  return (
    <div className="flex items-baseline gap-2">
      <span className="text-bone-100 text-lg font-display">{value}</span>
      <div>
        <span className="text-bone-400 text-xs">{label}</span>
        <span className="text-bone-600 text-xs ml-2">· {trend}</span>
      </div>
    </div>
  );
}

function WorkspaceCard({ workspace }: { workspace: Workspace }) {
  const roles = MOCK_ROLES.filter((r) => r.workspaceId === workspace.id);
  const totalCandidates = roles.reduce((s, r) => s + r.candidateCount, 0);
  const totalScored = roles.reduce((s, r) => s + r.scoredCount, 0);
  const scorePct =
    totalCandidates > 0 ? Math.round((totalScored / totalCandidates) * 100) : 0;
  const firstRole = roles[0];

  return (
    <div className="ws-card-enter border border-ink/10 rounded-lg bg-bone-50 hover:shadow-elevated transition-all duration-200 group overflow-hidden">
      {/* Card header */}
      <div className="p-5 pb-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2.5 mb-1">
              <StatusIndicator active={workspace.status === "active"} />
              <Link
                href={
                  firstRole
                    ? `/workspaces/${workspace.id}/roles/${firstRole.id}`
                    : `/workspaces/${workspace.id}`
                }
                className="text-sm font-semibold text-ink hover:underline underline-offset-2 truncate"
              >
                {workspace.name}
              </Link>
            </div>
            <p className="text-xs text-ink-400 ml-[18px]">
              {workspace.description}
            </p>
          </div>
          <span className="text-2xs text-ink-300 font-mono flex-shrink-0 mt-0.5">
            {formatRelativeTime(workspace.lastActivity)}
          </span>
        </div>

        {/* Metrics row */}
        <div className="flex items-center gap-5 mt-4 ml-[18px]">
          <CardMetric value={roles.length} label="roles" />
          <CardMetric value={totalCandidates} label="candidates" />
          <CardMetric value={totalScored} label="scored" />
          <div className="flex-1" />
          {/* Score progress ring */}
          <div className="flex items-center gap-2">
            <svg width="28" height="28" viewBox="0 0 28 28" className="flex-shrink-0">
              <circle
                cx="14"
                cy="14"
                r="11"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                className="text-bone-200"
              />
              <circle
                cx="14"
                cy="14"
                r="11"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeDasharray={`${scorePct * 0.691} 69.1`}
                strokeDashoffset="17.3"
                strokeLinecap="round"
                className="text-ink-800 transition-all duration-500"
              />
            </svg>
            <span className="text-xs font-mono text-ink-400">{scorePct}%</span>
          </div>
        </div>
      </div>

      {/* Roles list — table-like density */}
      {roles.length > 0 && (
        <div className="border-t border-ink/6">
          {/* Column headers */}
          <div className="flex items-center gap-3 px-5 py-1.5 text-[10px] font-semibold text-ink-300 uppercase tracking-wider">
            <span className="flex-1">Role</span>
            <span className="w-16 text-right">Pipeline</span>
            <span className="w-14 text-right">Status</span>
            <span className="w-5" />
          </div>

          {roles.map((role) => (
            <RoleRow key={role.id} role={role} workspaceId={workspace.id} />
          ))}
        </div>
      )}
    </div>
  );
}

function RoleRow({
  role,
  workspaceId,
}: {
  role: Role;
  workspaceId: string;
}) {
  const pipelineWidth =
    role.candidateCount > 0
      ? Math.round((role.scoredCount / role.candidateCount) * 100)
      : 0;

  return (
    <Link
      href={`/workspaces/${workspaceId}/roles/${role.id}`}
      className="flex items-center gap-3 px-5 py-2.5 hover:bg-bone-200/50 transition-colors border-t border-ink/4 group/row"
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <RoleIcon />
          <span className="text-xs font-medium text-ink truncate">
            {role.title}
          </span>
        </div>
        <span className="text-[10px] text-ink-300 ml-[18px]">
          {role.team} · {role.level}
        </span>
      </div>

      {/* Mini pipeline bar */}
      <div className="w-16 flex items-center gap-1.5 justify-end">
        <div className="w-8 h-1 bg-bone-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-ink/40 rounded-full"
            style={{ width: `${pipelineWidth}%` }}
          />
        </div>
        <span className="text-[10px] font-mono text-ink-400 w-7 text-right">
          {role.scoredCount}/{role.candidateCount}
        </span>
      </div>

      {/* Status */}
      <div className="w-14 flex justify-end">
        <RoleStatusBadge status={role.status} />
      </div>

      {/* Chevron */}
      <ChevronIcon className="text-ink-200 group-hover/row:text-ink-400 transition-colors" />
    </Link>
  );
}

function CardMetric({ value, label }: { value: number; label: string }) {
  return (
    <div className="flex items-baseline gap-1">
      <span className="text-sm font-mono font-semibold text-ink">{value}</span>
      <span className="text-[10px] text-ink-400">{label}</span>
    </div>
  );
}

function RoleStatusBadge({
  status,
}: {
  status: "draft" | "active" | "closed";
}) {
  const styles = {
    draft: "text-ink-400 bg-bone-200 border-ink/6",
    active: "text-signal-green-dark bg-signal-green-light border-signal-green/10",
    closed: "text-ink-300 bg-bone-200 border-ink/6",
  };
  return (
    <span
      className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold border ${styles[status]}`}
    >
      {status}
    </span>
  );
}

function StatusIndicator({ active }: { active: boolean }) {
  return (
    <span className="relative flex-shrink-0">
      <span
        className={`block w-2 h-2 rounded-full ${
          active ? "bg-signal-green" : "bg-ink-300"
        }`}
      />
      {active && (
        <span className="absolute inset-0 w-2 h-2 rounded-full bg-signal-green metric-pulse" />
      )}
    </span>
  );
}

/* ─── Icons ───────────────────────────────────────────────────────────────── */

function PlusIcon() {
  return (
    <svg
      width="12"
      height="12"
      viewBox="0 0 12 12"
      fill="none"
      aria-hidden="true"
    >
      <path
        d="M6 1v10M1 6h10"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

function RoleIcon() {
  return (
    <svg
      width="12"
      height="12"
      viewBox="0 0 12 12"
      fill="none"
      className="text-ink-300 flex-shrink-0"
      aria-hidden="true"
    >
      <circle cx="6" cy="4" r="2" stroke="currentColor" strokeWidth="1.2" />
      <path
        d="M1 10.5C1 8.567 3.239 7 6 7s5 1.567 5 3.5"
        stroke="currentColor"
        strokeWidth="1.2"
        strokeLinecap="round"
      />
    </svg>
  );
}

function ChevronIcon({ className = "" }: { className?: string }) {
  return (
    <svg
      width="10"
      height="10"
      viewBox="0 0 10 10"
      fill="none"
      className={className}
      aria-hidden="true"
    >
      <path
        d="M3.5 2L6.5 5l-3 3"
        stroke="currentColor"
        strokeWidth="1.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
