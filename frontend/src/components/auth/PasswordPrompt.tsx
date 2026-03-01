/** Password prompt modal for shared-password authentication. */

import { useState } from "react";
import { LockKeyhole } from "lucide-react";

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
    <div className="flex min-h-screen items-center justify-center bg-slate-50 p-4">
      <div className="w-full max-w-sm border border-slate-200 bg-white p-6">
        <div className="mb-4 flex items-center gap-2">
          <LockKeyhole className="h-5 w-5 text-slate-600" />
          <h1 className="text-lg font-semibold">ReformLab</h1>
        </div>
        <p className="mb-4 text-sm text-slate-600">
          Enter the shared workspace password to continue.
        </p>
        <form onSubmit={handleSubmit} className="space-y-3">
          <label htmlFor="password" className="sr-only">Password</label>
          <Input
            id="password"
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoFocus
            disabled={loading}
            aria-describedby={error ? "password-error" : undefined}
          />
          {error ? (
            <p id="password-error" className="text-sm text-red-600" role="alert">{error}</p>
          ) : null}
          <Button type="submit" className="w-full" disabled={loading || !password}>
            {loading ? "Authenticating..." : "Enter"}
          </Button>
        </form>
      </div>
    </div>
  );
}
