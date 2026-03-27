"use client";

import { useState } from "react";
import Link from "next/link";
import { NavLogo } from "@/components/ui/logo";
import { ThemeToggle } from "@/components/ui/theme-toggle";

export default function SignupPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const isValid =
    email.includes("@") &&
    password.length >= 8 &&
    password === confirmPassword;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isValid) return;
    setError("");
    setLoading(true);
    // TODO: wire to API
    setTimeout(() => {
      window.location.href = "/workspaces";
    }, 1200);
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
          <Link href="/login" className="text-[13px] font-medium px-4 py-2 rounded-lg transition-all duration-200"
            style={{ color: 'var(--text-heading)', background: 'var(--nav-btn-bg)', border: '1px solid var(--nav-btn-border)' }}>
            Sign in
          </Link>
        </div>
      </nav>

      {/* Form */}
      <div className="relative z-10 flex flex-col items-center pt-16 md:pt-20 pb-20 px-6">
        <h1 className="font-display text-3xl md:text-4xl tracking-[-0.02em] text-center mb-3 home-stagger-1" style={{ color: 'var(--text-heading)' }}>
          Create your account
        </h1>
        <p className="text-[15px] text-center mb-10 home-stagger-1" style={{ color: 'var(--text-muted)' }}>
          Start ranking candidates in seconds. Free to try.
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
          <InputField label="Password" type="password" placeholder="At least 8 characters" value={password} onChange={setPassword} />
          <InputField label="Confirm password" type="password" placeholder="Repeat your password" value={confirmPassword} onChange={setConfirmPassword}
            error={confirmPassword.length > 0 && password !== confirmPassword ? "Passwords don't match" : undefined}
          />

          <button
            type="submit"
            disabled={!isValid || loading}
            className="w-full py-3 rounded-xl text-sm font-semibold transition-all duration-300 active:scale-[0.98] mt-5"
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
            {loading ? "Creating account..." : "Create account"}
          </button>

          <p className="text-center text-[11px] mt-4" style={{ color: 'var(--text-faint)' }}>
            Already have an account?{" "}
            <Link href="/login" className="underline underline-offset-2 transition-colors" style={{ color: 'var(--text-muted)' }}>
              Sign in
            </Link>
          </p>
        </form>

        <p className="text-[11px] mt-6 text-center max-w-sm home-stagger-4" style={{ color: 'var(--text-faint)' }}>
          By creating an account you agree to our{" "}
          <a href="/legal/terms" className="underline underline-offset-2">Terms</a> and{" "}
          <a href="/legal/privacy" className="underline underline-offset-2">Privacy Policy</a>
        </p>
      </div>
    </div>
  );
}

function InputField({ label, type, placeholder, value, onChange, error }: {
  label: string; type: string; placeholder: string; value: string;
  onChange: (v: string) => void; error?: string;
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
          border: `1px solid ${error ? 'var(--error-border)' : 'var(--input-border)'}`,
          color: 'var(--text-body)',
        }}
        onFocus={(e) => {
          if (!error) {
            e.currentTarget.style.borderColor = 'var(--input-focus-border)';
            e.currentTarget.style.boxShadow = '0 0 0 3px var(--input-focus-ring)';
          }
        }}
        onBlur={(e) => {
          e.currentTarget.style.borderColor = error ? 'var(--error-border)' : 'var(--input-border)';
          e.currentTarget.style.boxShadow = 'none';
        }}
      />
      {error && <p className="text-[11px] mt-1.5" style={{ color: 'var(--error-text)' }}>{error}</p>}
    </div>
  );
}
