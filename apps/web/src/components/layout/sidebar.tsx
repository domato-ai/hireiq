"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { clsx } from "clsx";
import { DomatoIconWhite } from "@/components/ui/logo";

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
  exact?: boolean;
}

const navItems: NavItem[] = [
  {
    label: "Workspaces",
    href: "/workspaces",
    icon: <GridIcon />,
  },
  {
    label: "Billing",
    href: "/billing",
    icon: <BillingIcon />,
    exact: true,
  },
  {
    label: "Settings",
    href: "/settings",
    icon: <SettingsIcon />,
    exact: true,
  },
];

export function Sidebar() {
  const pathname = usePathname();

  function isActive(item: NavItem) {
    if (item.exact) return pathname === item.href;
    return pathname.startsWith(item.href);
  }

  return (
    <aside
      className="
        w-[220px] flex-shrink-0 h-full
        flex flex-col
        bg-ink-900 text-bone-300
        border-r border-ink-800
      "
    >
      {/* Logo */}
      <div className="px-5 py-5 border-b border-ink-800">
        <Link href="/workspaces" className="flex items-center gap-2.5 group">
          <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)' }}>
            <DomatoIconWhite size={16} />
          </div>
          <span className="text-sm font-semibold text-bone-100 tracking-tight">
            HireIQ
          </span>
        </Link>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
        {navItems.map((item) => {
          const active = isActive(item);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                "flex items-center gap-2.5 px-3 py-2 rounded text-sm transition-colors duration-100",
                active
                  ? "bg-ink-700 text-bone-50"
                  : "text-bone-400 hover:bg-ink-800 hover:text-bone-200"
              )}
            >
              <span
                className={clsx(
                  "flex-shrink-0",
                  active ? "text-bone-100" : "text-bone-500"
                )}
              >
                {item.icon}
              </span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* User footer */}
      <div className="border-t border-ink-800 px-3 py-3">
        <UserFooter />
      </div>
    </aside>
  );
}

function UserFooter() {
  // TODO: replace with real user session data
  const user = {
    name: "Recruiting Team",
    email: "team@company.com",
    initials: "RT",
  };

  return (
    <div className="flex items-center gap-2.5 px-2 py-1.5 rounded hover:bg-ink-800 cursor-pointer transition-colors group">
      {/* Avatar */}
      <div className="w-6 h-6 rounded-full bg-ink-600 flex items-center justify-center text-2xs font-semibold text-bone-300 flex-shrink-0">
        {user.initials}
      </div>
      {/* Info */}
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium text-bone-200 truncate">
          {user.name}
        </p>
        <p className="text-2xs text-bone-500 truncate">{user.email}</p>
      </div>
      {/* Sign out hint */}
      <button
        className="text-bone-600 hover:text-bone-300 transition-colors opacity-0 group-hover:opacity-100"
        title="Sign out"
        onClick={() => {
          // TODO: sign out
        }}
      >
        <SignOutIcon />
      </button>
    </div>
  );
}

/* ─── Icons ─────────────────────────────────────────────────────────────────── */

function GridIcon() {
  return (
    <svg
      width="15"
      height="15"
      viewBox="0 0 15 15"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <rect x="1" y="1" width="5.5" height="5.5" rx="1" stroke="currentColor" strokeWidth="1.2" />
      <rect x="8.5" y="1" width="5.5" height="5.5" rx="1" stroke="currentColor" strokeWidth="1.2" />
      <rect x="1" y="8.5" width="5.5" height="5.5" rx="1" stroke="currentColor" strokeWidth="1.2" />
      <rect x="8.5" y="8.5" width="5.5" height="5.5" rx="1" stroke="currentColor" strokeWidth="1.2" />
    </svg>
  );
}

function BillingIcon() {
  return (
    <svg
      width="15"
      height="15"
      viewBox="0 0 15 15"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <rect x="1" y="3" width="13" height="9" rx="1.5" stroke="currentColor" strokeWidth="1.2" />
      <path d="M1 6h13" stroke="currentColor" strokeWidth="1.2" />
      <rect x="3" y="8.5" width="3" height="1.5" rx="0.5" fill="currentColor" />
    </svg>
  );
}

function SettingsIcon() {
  return (
    <svg
      width="15"
      height="15"
      viewBox="0 0 15 15"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <circle cx="7.5" cy="7.5" r="2" stroke="currentColor" strokeWidth="1.2" />
      <path
        d="M7.5 1v1.5M7.5 12.5V14M14 7.5h-1.5M2.5 7.5H1M12.02 2.98l-1.06 1.06M4.04 10.96l-1.06 1.06M12.02 12.02l-1.06-1.06M4.04 4.04L2.98 2.98"
        stroke="currentColor"
        strokeWidth="1.2"
        strokeLinecap="round"
      />
    </svg>
  );
}

function SignOutIcon() {
  return (
    <svg
      width="13"
      height="13"
      viewBox="0 0 13 13"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path
        d="M5 1.5H2a1 1 0 00-1 1v8a1 1 0 001 1h3M9 9.5l3-3-3-3M12 6.5H5"
        stroke="currentColor"
        strokeWidth="1.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
