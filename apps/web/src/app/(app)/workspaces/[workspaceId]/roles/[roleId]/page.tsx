import { MOCK_WORKSPACES, MOCK_ROLES } from "@/lib/mock-data";
import { RoleWorkspaceClient } from "./role-workspace-client";

export function generateStaticParams() {
  const params: { workspaceId: string; roleId: string }[] = [];
  for (const ws of MOCK_WORKSPACES) {
    for (const role of MOCK_ROLES.filter((r) => r.workspaceId === ws.id)) {
      params.push({ workspaceId: ws.id, roleId: role.id });
    }
  }
  return params;
}

export default function RoleWorkspacePage({
  params,
}: {
  params: { workspaceId: string; roleId: string };
}) {
  return (
    <RoleWorkspaceClient
      workspaceId={params.workspaceId}
      roleId={params.roleId}
    />
  );
}
