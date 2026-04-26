import { createFileRoute, Link } from "@tanstack/react-router";
import { Logo } from "@/components/silicore/Logo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { LogIn, Shield } from "lucide-react";

export const Route = createFileRoute("/login")({
  head: () => ({ meta: [{ title: "Sign in — Silicore" }] }),
  component: Login,
});

function Login() {
  return (
    <div className="relative flex min-h-screen items-center justify-center bg-background px-4">
      <div className="bg-hero-glow pointer-events-none absolute inset-0 opacity-40" />
      <div className="relative w-full max-w-md">
        <div className="mb-8 flex justify-center">
          <Logo />
        </div>
        <div className="rounded-2xl border border-border bg-surface p-8 shadow-xl">
          <div className="mb-6">
            <h1 className="text-xl font-medium tracking-tight">Sign in to Silicore</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Use your workspace credentials to continue.
            </p>
          </div>

          <form className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="email" className="text-xs uppercase tracking-wider text-muted-foreground">Email</Label>
              <Input id="email" type="email" placeholder="elena@astrabit.io" />
            </div>
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label htmlFor="password" className="text-xs uppercase tracking-wider text-muted-foreground">Password</Label>
                <button type="button" className="text-xs text-primary hover:underline">Forgot?</button>
              </div>
              <Input id="password" type="password" placeholder="••••••••" />
            </div>

            <Button type="submit" className="w-full rounded-full">
              <LogIn className="mr-1.5 h-4 w-4" /> Sign in
            </Button>
          </form>

          <div className="mt-6 flex items-center gap-2 rounded-md border border-border bg-background/40 p-3 text-xs text-muted-foreground">
            <Shield className="h-3.5 w-3.5 text-primary" />
            <span>Protected by Silicore Sentinel auth · SSO available on Pro.</span>
          </div>
        </div>

        <p className="mt-6 text-center text-xs text-muted-foreground">
          New to Silicore? <Link to="/" className="text-primary hover:underline">Request access</Link>
        </p>
      </div>
    </div>
  );
}
