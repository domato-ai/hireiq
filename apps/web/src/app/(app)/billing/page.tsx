import type { Metadata } from "next";
import { Button } from "@/components/ui/button";

export const metadata: Metadata = {
  title: "Billing",
};

const PLANS = [
  {
    id: "starter",
    name: "Starter",
    price: "$49",
    period: "/month",
    description: "For small teams running occasional searches.",
    limits: ["3 active roles", "50 candidates/month", "Email support"],
    current: false,
  },
  {
    id: "growth",
    name: "Growth",
    price: "$149",
    period: "/month",
    description: "For recruiting teams with regular hiring volume.",
    limits: ["15 active roles", "500 candidates/month", "Priority support"],
    current: true,
  },
  {
    id: "enterprise",
    name: "Enterprise",
    price: "Custom",
    period: "",
    description: "For organizations with high volume or compliance needs.",
    limits: [
      "Unlimited roles",
      "Custom candidate volume",
      "SSO & audit logs",
      "Dedicated CSM",
    ],
    current: false,
  },
] as const;

export default function BillingPage() {
  return (
    <div className="flex-1 overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-bone border-b border-ink/8 px-8 py-5">
        <h1 className="text-lg font-semibold text-ink tracking-tight">
          Billing
        </h1>
        <p className="text-sm text-ink-400 mt-0.5">
          Manage your subscription and usage.
        </p>
      </div>

      <div className="px-8 py-6 max-w-4xl space-y-8">
        {/* Current usage */}
        <section className="space-y-3">
          <h2 className="text-sm font-semibold text-ink">Usage this period</h2>
          <div className="grid grid-cols-3 gap-4">
            {[
              { label: "Active roles", value: "4", limit: "15" },
              { label: "Candidates processed", value: "87", limit: "500" },
              { label: "Billing period resets", value: "Apr 1", limit: "" },
            ].map((stat) => (
              <div
                key={stat.label}
                className="bg-bone-50 border border-ink/8 rounded-md px-4 py-3"
              >
                <p className="text-xs text-ink-400">{stat.label}</p>
                <p className="text-xl font-semibold text-ink mt-1">
                  {stat.value}
                  {stat.limit && (
                    <span className="text-sm font-normal text-ink-400">
                      {" "}
                      / {stat.limit}
                    </span>
                  )}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* Plans */}
        <section className="space-y-3">
          <h2 className="text-sm font-semibold text-ink">Plans</h2>
          <div className="grid grid-cols-3 gap-4">
            {PLANS.map((plan) => (
              <div
                key={plan.id}
                className={`
                  rounded-lg border px-5 py-5 space-y-4 relative
                  ${
                    plan.current
                      ? "border-ink bg-bone-50 shadow-card"
                      : "border-ink/10 bg-bone-50"
                  }
                `}
              >
                {plan.current && (
                  <span className="absolute top-4 right-4 text-2xs font-semibold uppercase tracking-wider text-ink bg-bone-200 px-2 py-0.5 rounded">
                    Current
                  </span>
                )}
                <div>
                  <h3 className="text-sm font-semibold text-ink">
                    {plan.name}
                  </h3>
                  <div className="flex items-baseline gap-0.5 mt-1">
                    <span className="text-2xl font-semibold text-ink">
                      {plan.price}
                    </span>
                    <span className="text-sm text-ink-400">{plan.period}</span>
                  </div>
                  <p className="text-xs text-ink-400 mt-1.5">
                    {plan.description}
                  </p>
                </div>

                <ul className="space-y-1.5">
                  {plan.limits.map((limit) => (
                    <li key={limit} className="flex items-start gap-2 text-xs">
                      <CheckIcon />
                      <span className="text-ink-600">{limit}</span>
                    </li>
                  ))}
                </ul>

                <Button
                  size="sm"
                  variant={plan.current ? "secondary" : "primary"}
                  className="w-full"
                  disabled={plan.current}
                >
                  {plan.current
                    ? "Current plan"
                    : plan.id === "enterprise"
                    ? "Contact sales"
                    : "Upgrade"}
                </Button>
              </div>
            ))}
          </div>
        </section>

        {/* Payment method */}
        <section className="space-y-3">
          <h2 className="text-sm font-semibold text-ink">Payment method</h2>
          <div className="bg-bone-50 border border-ink/8 rounded-md px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-6 bg-ink-800 rounded flex items-center justify-center text-2xs text-bone font-mono">
                VISA
              </div>
              <div>
                <p className="text-sm text-ink">•••• •••• •••• 4242</p>
                <p className="text-xs text-ink-400">Expires 08 / 2026</p>
              </div>
            </div>
            <button className="text-xs text-ink underline underline-offset-2 hover:text-ink-600 transition-colors">
              Update
            </button>
          </div>
        </section>

        {/* Invoice history */}
        <section className="space-y-3">
          <h2 className="text-sm font-semibold text-ink">Invoice history</h2>
          <div className="bg-bone-50 border border-ink/8 rounded-md divide-y divide-ink/6">
            {[
              { date: "Mar 1, 2026", amount: "$149.00", status: "Paid" },
              { date: "Feb 1, 2026", amount: "$149.00", status: "Paid" },
              { date: "Jan 1, 2026", amount: "$149.00", status: "Paid" },
            ].map((invoice) => (
              <div
                key={invoice.date}
                className="px-4 py-3 flex items-center justify-between text-sm"
              >
                <span className="text-ink-600">{invoice.date}</span>
                <span className="text-ink font-medium">{invoice.amount}</span>
                <span className="text-signal-green text-xs font-medium">
                  {invoice.status}
                </span>
                <button className="text-xs text-ink-400 hover:text-ink underline underline-offset-2 transition-colors">
                  PDF
                </button>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}

function CheckIcon() {
  return (
    <svg
      width="12"
      height="12"
      viewBox="0 0 12 12"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="text-signal-green mt-0.5 flex-shrink-0"
      aria-hidden="true"
    >
      <path
        d="M2 6l3 3 5-5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
