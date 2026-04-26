import { useState, type ReactNode } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { Logo } from "@/components/silicore/Logo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  ArrowLeft,
  CheckCircle2,
  CirclePlus,
  KeyRound,
  LogIn,
  MailCheck,
  Shield,
  Sparkles,
} from "lucide-react";

export const Route = createFileRoute("/login")({
  head: () => ({ meta: [{ title: "Sign in — Silicore" }] }),
  component: Login,
});

type AuthMode = "login" | "signup" | "reset" | "verify";

function Login() {
  const [mode, setMode] = useState<AuthMode>("login");
  const [resetEmail, setResetEmail] = useState("");

  return (
    <div className="relative min-h-screen overflow-hidden bg-background">
      <div className="bg-grid pointer-events-none absolute inset-0 opacity-25 [mask-image:radial-gradient(circle_at_top,black_35%,transparent_82%)]" />
      <div className="bg-hero-glow pointer-events-none absolute inset-0 opacity-60" />
      <div
        className="pointer-events-none absolute -left-24 top-24 h-[420px] w-[420px] rounded-full blur-3xl"
        style={{ background: "radial-gradient(circle, oklch(0.82 0.13 200 / 0.2), transparent 68%)" }}
      />
      <div
        className="pointer-events-none absolute right-[-100px] top-[-40px] h-[520px] w-[520px] rounded-full blur-3xl"
        style={{ background: "radial-gradient(circle, oklch(0.74 0.14 258 / 0.22), transparent 70%)" }}
      />

      <div className="relative mx-auto flex min-h-screen max-w-7xl flex-col px-4 py-6 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between gap-4">
          <Link to="/" className="inline-flex items-center gap-3 rounded-full border border-white/10 bg-white/4 px-4 py-2 text-sm text-muted-foreground transition-colors hover:bg-white/8 hover:text-foreground">
            <ArrowLeft className="h-4 w-4" />
            Back to site
          </Link>
          <div className="hidden items-center gap-2 rounded-full border border-primary/18 bg-primary/8 px-4 py-2 font-mono text-[10px] uppercase tracking-[0.24em] text-primary md:inline-flex">
            <Shield className="h-3.5 w-3.5" />
            Sentinel identity access
          </div>
        </div>

        <div className="flex flex-1 items-center py-8 lg:py-10">
          <div className="grid w-full gap-6 lg:grid-cols-[minmax(0,1.05fr)_minmax(420px,0.95fr)] xl:gap-10">
            <section className="relative overflow-hidden rounded-[34px] border border-white/8 bg-[linear-gradient(155deg,rgba(7,15,24,0.97),rgba(9,18,30,0.92))] px-6 py-8 shadow-[0_32px_120px_-60px_rgba(0,0,0,0.95)] sm:px-8 sm:py-10">
              <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/60 to-transparent" />
              <div className="relative">
                <div className="inline-flex items-center gap-3 rounded-full border border-white/8 bg-white/4 px-4 py-3">
                  <Logo />
                  <div className="min-w-0">
                    <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-muted-foreground">Silicore</div>
                    <div className="text-sm text-foreground">Engineering intelligence access</div>
                  </div>
                </div>

                <div className="mt-8 max-w-2xl">
                  <div className="inline-flex items-center gap-2 rounded-full border border-primary/18 bg-primary/10 px-3 py-1 font-mono text-[10px] uppercase tracking-[0.22em] text-primary">
                    <Sparkles className="h-3.5 w-3.5" />
                    Secure workspace entry
                  </div>
                  <h1 className="mt-5 text-4xl font-semibold tracking-tight text-foreground sm:text-5xl sm:leading-[1.02]">
                    Sign into the Silicore command surface without losing your engineering context.
                  </h1>
                  <p className="mt-4 max-w-xl text-base leading-8 text-muted-foreground">
                    Use the same backend identity flow for board analysis, compare, Atlas, and workspace review. This screen is now the single sign-in and sign-up destination across the UI.
                  </p>
                </div>

                <div className="mt-8 grid gap-4 sm:grid-cols-3">
                  <SignalTile
                    icon={<LogIn className="h-4 w-4" />}
                    label="Live sessions"
                    value="Backend-auth"
                    copy="Posts directly into the Flask identity flow."
                  />
                  <SignalTile
                    icon={<MailCheck className="h-4 w-4" />}
                    label="Recovery"
                    value="Email reset"
                    copy="Password resets and verification stay linked."
                  />
                  <SignalTile
                    icon={<CheckCircle2 className="h-4 w-4" />}
                    label="Protected"
                    value="Role aware"
                    copy="Workspace access and review permissions stay intact."
                  />
                </div>

                <div className="mt-8 rounded-[28px] border border-white/8 bg-black/12 p-5">
                  <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground">Access lanes</div>
                  <div className="mt-4 grid gap-3 md:grid-cols-3">
                    <AccessLane
                      title="Engineers"
                      copy="Sign in and move straight into board analysis or workspace review."
                    />
                    <AccessLane
                      title="Review leads"
                      copy="Keep release gates, compare, and approval trails inside the same session."
                    />
                    <AccessLane
                      title="Internal ops"
                      copy="Identity, health, and admin surfaces remain behind the same auth perimeter."
                    />
                  </div>
                </div>
              </div>
            </section>

            <section className="relative overflow-hidden rounded-[34px] border border-white/8 bg-[linear-gradient(180deg,rgba(8,17,27,0.98),rgba(7,14,22,0.98))] p-5 shadow-[0_30px_110px_-54px_rgba(0,0,0,0.94)] sm:p-6">
              <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/60 to-transparent" />
              <div className="relative">
                <div className="flex flex-wrap gap-2 rounded-full border border-white/8 bg-white/4 p-1">
                  {[
                    { id: "login", label: "Sign in" },
                    { id: "signup", label: "Sign up" },
                    { id: "reset", label: "Reset password" },
                    { id: "verify", label: "Verify / MFA" },
                  ].map((item) => {
                    const active = mode === item.id;
                    return (
                      <button
                        key={item.id}
                        type="button"
                        onClick={() => setMode(item.id as AuthMode)}
                        className={`rounded-full px-4 py-2 text-sm transition-all ${
                          active
                            ? "bg-primary/16 text-primary shadow-[0_0_0_1px_rgba(86,211,240,0.12)]"
                            : "text-muted-foreground hover:text-foreground"
                        }`}
                      >
                        {item.label}
                      </button>
                    );
                  })}
                </div>

                <div className="mt-6">
                  {mode === "login" ? (
                    <AuthPanel
                      eyebrow="Primary access"
                      title="Sign in to Silicore"
                      copy="Use your workspace credentials to continue into Nexus, project review, and Atlas workflows."
                    >
                      <form className="space-y-4" method="post" action="/login">
                        <input type="hidden" name="action" value="login" />
                        <Field label="Email" htmlFor="email">
                          <Input id="email" name="email" type="email" placeholder="elena@astrabit.io" required />
                        </Field>
                        <Field label="Password" htmlFor="password">
                          <Input id="password" name="password" type="password" placeholder="••••••••" required />
                        </Field>
                        <Button type="submit" className="h-12 w-full rounded-full text-sm">
                          <LogIn className="mr-2 h-4 w-4" />
                          Sign in
                        </Button>
                      </form>
                    </AuthPanel>
                  ) : null}

                  {mode === "signup" ? (
                    <AuthPanel
                      eyebrow="Account creation"
                      title="Create a Silicore workspace account"
                      copy="Register a new user directly against the existing Flask identity backend so your session, organization, and verification flow all stay connected."
                    >
                      <form className="space-y-4" method="post" action="/login">
                        <input type="hidden" name="action" value="register" />
                        <div className="grid gap-4 sm:grid-cols-2">
                          <Field label="Full name" htmlFor="signup_name">
                            <Input id="signup_name" name="name" placeholder="Elena Rivera" required />
                          </Field>
                          <Field label="Organization" htmlFor="organization_name">
                            <Input id="organization_name" name="organization_name" placeholder="Astrabit Labs" />
                          </Field>
                        </div>
                        <Field label="Email" htmlFor="signup_email">
                          <Input id="signup_email" name="email" type="email" placeholder="elena@astrabit.io" required />
                        </Field>
                        <Field label="Password" htmlFor="signup_password">
                          <Input id="signup_password" name="password" type="password" placeholder="Create a strong password" required />
                        </Field>
                        <div className="rounded-[22px] border border-white/8 bg-white/4 px-4 py-3 text-sm leading-6 text-muted-foreground">
                          New accounts are created in the backend identity system, then follow the same verification and session setup as every other Silicore workspace user.
                        </div>
                        <Button type="submit" className="h-12 w-full rounded-full text-sm">
                          <CirclePlus className="mr-2 h-4 w-4" />
                          Create account
                        </Button>
                      </form>
                    </AuthPanel>
                  ) : null}

                  {mode === "reset" ? (
                    <AuthPanel
                      eyebrow="Recovery lane"
                      title="Request a password reset"
                      copy="Silicore will push your reset token through the existing backend email flow so your workspace access stays intact."
                    >
                      <form className="space-y-4" method="post" action="/login">
                        <input type="hidden" name="action" value="request_reset" />
                        <Field label="Workspace email" htmlFor="reset_email">
                          <Input
                            id="reset_email"
                            name="email"
                            type="email"
                            value={resetEmail}
                            onChange={(event) => setResetEmail(event.target.value)}
                            placeholder="elena@astrabit.io"
                            required
                          />
                        </Field>
                        <Button type="submit" className="h-12 w-full rounded-full text-sm">
                          <KeyRound className="mr-2 h-4 w-4" />
                          Send reset link
                        </Button>
                      </form>
                    </AuthPanel>
                  ) : null}

                  {mode === "verify" ? (
                    <div className="space-y-4">
                      <AuthPanel
                        eyebrow="Verification"
                        title="Verify email access"
                        copy="Paste a verification token if you already have one, or request a fresh email to keep your identity trusted."
                      >
                        <form className="space-y-4" method="post" action="/login">
                          <input type="hidden" name="action" value="verify_email" />
                          <Field label="Verification token" htmlFor="verification_token">
                            <Input id="verification_token" name="verification_token" placeholder="Paste email token" required />
                          </Field>
                          <Button type="submit" className="h-12 w-full rounded-full text-sm">
                            <MailCheck className="mr-2 h-4 w-4" />
                            Verify email
                          </Button>
                        </form>
                      </AuthPanel>

                      <div className="grid gap-4 sm:grid-cols-2">
                        <form className="rounded-[24px] border border-white/8 bg-white/3 p-4" method="post" action="/login">
                          <input type="hidden" name="action" value="request_verification" />
                          <Field label="Request verification" htmlFor="request_verification_email">
                            <Input id="request_verification_email" name="email" type="email" placeholder="elena@astrabit.io" required />
                          </Field>
                          <Button type="submit" variant="secondary" className="mt-4 h-11 w-full rounded-full">Send verification email</Button>
                        </form>

                        <form className="rounded-[24px] border border-white/8 bg-white/3 p-4" method="post" action="/login">
                          <input type="hidden" name="action" value="verify_mfa" />
                          <div className="space-y-3">
                            <Field label="MFA challenge token" htmlFor="mfa_token">
                              <Input id="mfa_token" name="mfa_token" placeholder="Challenge token" required />
                            </Field>
                            <Field label="MFA code" htmlFor="mfa_code">
                              <Input id="mfa_code" name="mfa_code" placeholder="123456" required />
                            </Field>
                          </div>
                          <Button type="submit" variant="secondary" className="mt-4 h-11 w-full rounded-full">Complete MFA</Button>
                        </form>
                      </div>
                    </div>
                  ) : null}
                </div>

                <div className="mt-6 rounded-[24px] border border-primary/14 bg-primary/8 px-4 py-3 text-sm leading-6 text-muted-foreground">
                  Sign in, sign up, password reset, verification, and MFA still run through the original Flask auth backend. This page simply gives those flows a proper modern surface.
                </div>

                <div className="mt-6 flex flex-wrap items-center justify-between gap-3 text-xs text-muted-foreground">
                  <span>{mode === "signup" ? "Already have an account?" : "Need a new workspace account?"}</span>
                  <button
                    type="button"
                    onClick={() => setMode(mode === "signup" ? "login" : "signup")}
                    className="text-primary hover:underline"
                  >
                    {mode === "signup" ? "Go back to sign in" : "Create an account here"}
                  </button>
                </div>
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}

function AuthPanel({
  eyebrow,
  title,
  copy,
  children,
}: {
  eyebrow: string;
  title: string;
  copy: string;
  children: ReactNode;
}) {
  return (
    <div className="rounded-[28px] border border-white/8 bg-[linear-gradient(180deg,rgba(255,255,255,0.03),rgba(255,255,255,0.02))] p-5 sm:p-6">
      <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground">{eyebrow}</div>
      <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{title}</h2>
      <p className="mt-3 text-sm leading-7 text-muted-foreground">{copy}</p>
      <div className="mt-5">{children}</div>
    </div>
  );
}

function Field({
  label,
  htmlFor,
  children,
}: {
  label: string;
  htmlFor: string;
  children: ReactNode;
}) {
  return (
    <div className="space-y-2">
      <Label htmlFor={htmlFor} className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
        {label}
      </Label>
      {children}
    </div>
  );
}

function SignalTile({
  icon,
  label,
  value,
  copy,
}: {
  icon: ReactNode;
  label: string;
  value: string;
  copy: string;
}) {
  return (
    <div className="rounded-[24px] border border-white/8 bg-white/4 p-4">
      <div className="flex items-center justify-between gap-3">
        <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{label}</div>
        <span className="text-primary">{icon}</span>
      </div>
      <div className="mt-3 text-xl font-semibold text-foreground">{value}</div>
      <div className="mt-2 text-sm leading-6 text-muted-foreground">{copy}</div>
    </div>
  );
}

function AccessLane({ title, copy }: { title: string; copy: string }) {
  return (
    <div className="rounded-[22px] border border-white/8 bg-white/4 p-4">
      <div className="text-sm font-medium text-foreground">{title}</div>
      <div className="mt-2 text-sm leading-6 text-muted-foreground">{copy}</div>
    </div>
  );
}
