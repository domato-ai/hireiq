"use client";

import { useState } from "react";
import Link from "next/link";
import { NavLogo } from "@/components/ui/logo";
import { ThemeToggle } from "@/components/ui/theme-toggle";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://ca-hireiq-api-dev.delightfulsea-504dfc83.australiaeast.azurecontainerapps.io";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const isValid = email.includes("@") && password.length >= 1;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isValid) return;
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Invalid email or password");
      }
      localStorage.setItem("hireiq-token", data.access_token);
      localStorage.setItem("hireiq-user", JSON.stringify(data.user));
      window.location.href = "/";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen relative" style={{ background: 'var(--page-bg)' }}>
      {/* Glow */}
      <div
        className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[500px] pointer-events-none"
        style={{ background: 'radial-gradient(ellipse 50% 70% at 50% 0%, var(--glow-color) 0%, transparent 70%)' }}
      />
      {/* Dot grid */}
      <div className="absolute inset-0 pointer-events-none"
        style={{ backgroundImage: 'radial-gradient(var(--dot-grid-color) 1px, transparent 1px)', backgroundSize: '24px 24px' }}
      />

      {/* Nav */}
      <nav className="relative z-20 flex items-center justify-between px-6 md:px-10 py-5 max-w-5xl mx-auto">
        <NavLogo variant="dark" />
        <div className="flex items-center gap-4">
          <ThemeToggle />
          <Link href="/signup" className="text-[13px] font-medium px-4 py-2 rounded-lg transition-all duration-200"
            style={{ color: 'var(--text-heading)', background: 'var(--nav-btn-bg)', border: '1px solid var(--nav-btn-border)' }}>
            Create account
          </Link>
        </div>
      </nav>

      {/* Form */}
      <div className="relative z-10 flex flex-col items-center pt-16 md:pt-24 pb-20 px-6">
        <h1 className="font-display text-3xl md:text-4xl tracking-[-0.02em] text-center mb-3 home-stagger-1" style={{ color: 'var(--text-heading)' }}>
          Welcome back
        </h1>
        <p className="text-[15px] text-center mb-10 home-stagger-1" style={{ color: 'var(--text-muted)' }}>
          Sign in to continue to your workspace.
        </p>

        <form
          onSubmit={handleSubmit}
          className="w-full max-w-[400px] rounded-2xl p-6 home-stagger-3"
          style={{
            background: 'var(--card-bg)',
            border: '1px solid var(--card-border)',
            boxShadow: 'var(--card-shadow), 0 0 80px rgba(124,92,255,0.04)',
          }}
        >
          {error && (
            <div className="mb-4 px-3 py-2 rounded-lg text-[12px] font-medium"
              style={{ background: 'var(--error-bg)', border: '1px solid var(--error-border)', color: 'var(--error-text)' }}>
              {error}
            </div>
          )}

          <InputField label="Email" type="email" placeholder="you@company.com" value={email} onChange={setEmail} />
          <InputField label="Password" type="password" placeholder="Your password" value={password} onChange={setPassword} />

          <div className="flex justify-end mb-5">
            <Link href="/forgot-password" className="text-[11px] underline underline-offset-2 transition-colors"
              style={{ color: 'var(--badge-inactive-text)' }}>
              Forgot password?
            </Link>
          </div>

          <button
            type="submit"
            disabled={!isValid || loading}
            className="w-full py-3 rounded-xl text-sm font-semibold transition-all duration-300 active:scale-[0.98]"
            style={isValid && !loading ? {
              background: 'linear-gradient(135deg, #7c5cff 0%, #6346e0 100%)',
              color: '#fff',
              boxShadow: '0 0 24px rgba(124,92,255,0.3), 0 2px 8px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.15)',
            } : {
              background: 'var(--btn-disabled-bg)',
              color: 'var(--btn-disabled-text)',
              cursor: 'not-allowed',
            }}
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>

          <p className="text-center text-[11px] mt-4" style={{ color: 'var(--text-faint)' }}>
            Don&apos;t have an account?{" "}
            <Link href="/signup" className="underline underline-offset-2 transition-colors" style={{ color: 'var(--text-muted)' }}>
              Create one
            </Link>
          </p>
        </form>

        <p className="text-[11px] mt-6 text-center max-w-sm home-stagger-4" style={{ color: 'var(--text-faint)' }}>
          By signing in you agree to our{" "}
          <a href="/terms" className="underline underline-offset-2">Terms</a> and{" "}
          <a href="/privacy" className="underline underline-offset-2">Privacy Policy</a>
        </p>
      </div>
    </div>
  );
}

function InputField({ label, type, placeholder, value, onChange }: {
  label: string; type: string; placeholder: string; value: string; onChange: (v: string) => void;
}) {
  return (
    <div className="mb-4">
      <label className="block text-[12px] font-medium uppercase tracking-wider mb-2" style={{ color: 'var(--text-muted)' }}>
        {label}
      </label>
      <input
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-xl px-4 py-3 text-[13px] focus:outline-none transition-all duration-200"
        style={{
          background: 'var(--input-bg)',
          border: '1px solid var(--input-border)',
          color: 'var(--text-body)',
        }}
        onFocus={(e) => {
          e.currentTarget.style.borderColor = 'var(--input-focus-border)';
          e.currentTarget.style.boxShadow = '0 0 0 3px var(--input-focus-ring)';
        }}
        onBlur={(e) => {
          e.currentTarget.style.borderColor = 'var(--input-border)';
          e.currentTarget.style.boxShadow = 'none';
        }}
      />
    </div>
  );
}
