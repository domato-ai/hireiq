"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { billingApi, type BillingStatus, type Pricing } from "@/lib/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://ca-hireiq-api-dev.delightfulsea-504dfc83.australiaeast.azurecontainerapps.io";

function getPlans(pricing: Pricing | null) {
  const symbol = pricing?.symbol || "A$";
  const proPrice = pricing?.pro_price || 19;
  return [
    {
      id: "starter",
      backendPlan: "free",
      name: "Starter",
      price: "Free",
      period: "",
      description: "For small teams running occasional searches.",
      limits: ["3 active roles", "10 candidates/month", "Email support"],
    },
    {
      id: "growth",
      backendPlan: "pro",
      name: "Growth",
      price: `${symbol}${proPrice}`,
      period: "/month",
      description: "For recruiting teams with regular hiring volume.",
      limits: ["50 active roles", "500 candidates/month", "Priority support"],
    },
    {
      id: "enterprise",
      backendPlan: "team",
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
    },
  ] as const;
}

export default function BillingPage() {
  const [status, setStatus] = useState<BillingStatus | null>(null);
  const [pricing, setPricing] = useState<Pricing | null>(null);
  const [loading, setLoading] = useState(true);
  const [upgrading, setUpgrading] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      billingApi.getStatus().catch(() => null),
      billingApi.getPricing().catch(() => null),
    ]).then(([s, p]) => {
      setStatus(s);
      setPricing(p);
    }).finally(() => setLoading(false));
  }, []);

  const currentPlanId = status?.plan || "starter";
  const PLANS = getPlans(pricing);

  const handleUpgrade = async (planId: string) => {
    setUpgrading(planId);
    setError("");
    try {
      const { url } = await billingApi.createCheckoutSession(planId, pricing?.currency);
      window.location.href = url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start checkout");
      setUpgrading(null);
    }
  };

  const handleManageSubscription = async () => {
    setError("");
    try {
      const { url } = await billingApi.createPortalSession();
      window.location.href = url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to open subscription management");
    }
  };

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
        {error && (
          <div className="px-4 py-3 rounded-md bg-red-50 border border-red-200 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Current usage */}
        <section className="space-y-3">
          <h2 className="text-sm font-semibold text-ink">Usage this period</h2>
          <div className="grid grid-cols-3 gap-4">
            {[
              {
                label: "Active roles",
                value: loading ? "-" : String(status?.rolesActive ?? 0),
                limit: loading ? "" : String(status?.rolesLimit ?? 3),
              },
              {
                label: "Candidates processed",
                value: loading ? "-" : String(status?.candidatesUsed ?? 0),
                limit: loading ? "" : String(status?.candidatesLimit ?? 10),
              },
              {
                label: "Current plan",
                value: loading ? "-" : PLANS.find(p => p.id === currentPlanId)?.name ?? "Starter",
                limit: "",
              },
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
            {PLANS.map((plan) => {
              const isCurrent = plan.id === currentPlanId;
              return (
                <div
                  key={plan.id}
                  className={`
                    rounded-lg border px-5 py-5 space-y-4 relative
                    ${
                      isCurrent
                        ? "border-ink bg-bone-50 shadow-card"
                        : "border-ink/10 bg-bone-50"
                    }
                  `}
                >
                  {isCurrent && (
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
                    variant={isCurrent ? "secondary" : "primary"}
                    className="w-full"
                    disabled={isCurrent || upgrading === plan.id}
                    onClick={() => {
                      if (plan.id === "enterprise") {
                        window.location.href = "mailto:support@domato.ai?subject=HireIQ Enterprise inquiry";
                      } else if (!isCurrent) {
                        handleUpgrade(plan.id);
                      }
                    }}
                  >
                    {upgrading === plan.id
                      ? "Redirecting..."
                      : isCurrent
                      ? "Current plan"
                      : plan.id === "enterprise"
                      ? "Contact sales"
                      : "Upgrade"}
                  </Button>
                </div>
              );
            })}
          </div>
        </section>

        {/* Manage subscription (only for paid plans) */}
        {currentPlanId !== "starter" && (
          <section className="space-y-3">
            <h2 className="text-sm font-semibold text-ink">Subscription</h2>
            <div className="bg-bone-50 border border-ink/8 rounded-md px-4 py-3 flex items-center justify-between">
              <div>
                <p className="text-sm text-ink">
                  Manage your payment method, invoices, and subscription
                </p>
                {status?.currentPeriodEnd && (
                  <p className="text-xs text-ink-400 mt-0.5">
                    Current period ends {new Date(status.currentPeriodEnd).toLocaleDateString()}
                  </p>
                )}
              </div>
              <Button size="sm" variant="secondary" onClick={handleManageSubscription}>
                Manage in Stripe
              </Button>
            </div>
          </section>
        )}
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
