// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** Password prompt — full-screen auth gate with brand identity. */

import { useState } from "react";
import { ArrowRight, LockKeyhole } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface PasswordPromptProps {
  onSubmit: (password: string) => Promise<boolean>;
  loading: boolean;
}

export function PasswordPrompt({ onSubmit, loading }: PasswordPromptProps) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    const success = await onSubmit(password);
    if (!success) {
      setError("Invalid password");
      setPassword("");
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-white px-4">
      {/* Logo */}
      <img
        src="/logo.svg"
        alt=""
        className="h-16 w-auto"
        aria-hidden="true"
      />

      {/* Wordmark */}
      <h1 className="mt-5 text-2xl font-semibold text-slate-700">
        Reform<span className="text-emerald-500">Lab</span>
      </h1>

      {/* Tagline */}
      <p className="mt-1.5 text-sm text-slate-500">
        See the impact before the vote.
      </p>

      {/* Auth card */}
      <div className="mt-10 w-full max-w-xs">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <LockKeyhole className="h-3.5 w-3.5" />
          <span>Shared workspace password</span>
        </div>

        <form onSubmit={handleSubmit} className="mt-3 space-y-3">
          <label htmlFor="password" className="sr-only">Password</label>
          <Input
            id="password"
            type="password"
            placeholder="Enter password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoFocus
            disabled={loading}
            className="h-11"
            aria-describedby={error ? "password-error" : undefined}
          />
          {error ? (
            <p id="password-error" className="text-sm text-red-500" role="alert">{error}</p>
          ) : null}
          <Button
            type="submit"
            className="h-11 w-full gap-2"
            disabled={loading || !password}
          >
            {loading ? "Authenticating..." : (
              <>
                Enter workspace
                <ArrowRight className="h-4 w-4" />
              </>
            )}
          </Button>
        </form>
      </div>

      {/* Footer */}
      <p className="mt-16 text-xs text-slate-300">
        Open-source &middot; Open-data-first &middot; France &amp; Europe
      </p>
    </div>
  );
}
