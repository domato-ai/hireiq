import type { Metadata } from "next";

export const metadata: Metadata = {
  title: {
    default: "HireIQ",
    template: "%s — HireIQ",
  },
};

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
