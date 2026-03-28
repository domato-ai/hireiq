import { MOCK_WORKSPACES, MOCK_ROLES, getRolesByWorkspace } from "@/lib/mock-data";
import { ClientRedirect } from "./client-redirect";

export function generateStaticParams() {
  return MOCK_WORKSPACES.map((ws) => ({ workspaceId: ws.id }));
}

export default function WorkspacePage({ params }: { params: { workspaceId: string } }) {
  const roles = getRolesByWorkspace(params.workspaceId);
  const target = roles.length > 0
    ? `/workspaces/${params.workspaceId}/roles/${roles[0].id}`
    : "/workspaces";

  return <ClientRedirect to={target} />;
}
