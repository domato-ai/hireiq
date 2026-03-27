import { redirect } from "next/navigation";
import { getRolesByWorkspace } from "@/lib/mock-data";

interface WorkspacePageProps {
  params: Promise<{ workspaceId: string }>;
}

/**
 * Workspace index — redirect to the first role.
 * Uses mock data in development; swap for API call when backend is ready.
 */
export default async function WorkspacePage({ params }: WorkspacePageProps) {
  const { workspaceId } = await params;

  const roles = getRolesByWorkspace(workspaceId);
  const firstRole = roles[0];

  if (firstRole) {
    redirect(`/workspaces/${workspaceId}/roles/${firstRole.id}`);
  }

  // Fallback if no roles exist yet
  redirect(`/workspaces`);
}
