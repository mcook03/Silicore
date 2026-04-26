import { createFileRoute } from "@tanstack/react-router";
import type { ReactNode } from "react";
import { AppShell } from "@/components/silicore/AppShell";
import { CheckCircle2, AlertCircle, Server, Database, Cpu } from "lucide-react";
import { useApiData } from "@/lib/api";

export const Route = createFileRoute("/health")({
  head: () => ({ meta: [{ title: "System health — Silicore" }] }),
  component: Health,
});

type HealthPayload = {
  live: { status: string; service: string; environment: string };
  ready: { status?: string; checks?: Record<string, unknown> };
  ready_status: number;
  database: { ok: boolean; error?: string };
  runtime: Record<string, unknown>;
};

function Health() {
  const { data, error, loading, reload } = useApiData<HealthPayload>("/api/frontend/health");
  const allOperational = Boolean(data?.database.ok) && data?.ready_status === 200;

  const services = [
    {
      name: data?.live.service || "silicore-web",
      detail: data?.live.environment || "unknown",
      ok: data?.live.status === "ok",
      icon: Server,
    },
    {
      name: "Readiness probe",
      detail: `HTTP ${data?.ready_status ?? "—"}`,
      ok: data?.ready_status === 200,
      icon: CheckCircle2,
    },
    {
      name: "Database",
      detail: data?.database.ok ? "ready" : data?.database.error || "unavailable",
      ok: Boolean(data?.database.ok),
      icon: Database,
    },
    {
      name: "Runtime metadata",
      detail: Object.keys(data?.runtime || {}).length ? `${Object.keys(data?.runtime || {}).length} signals` : "not reported",
      ok: true,
      icon: Cpu,
    },
  ];

  return (
    <AppShell title="System health">
      <div className="space-y-6">
        <div className={`rounded-2xl border p-6 ${allOperational ? "border-success/20 bg-success/5" : "border-warning/20 bg-warning/5"}`}>
          <div className="flex items-center gap-3">
            {allOperational ? <CheckCircle2 className="h-5 w-5 text-success" /> : <AlertCircle className="h-5 w-5 text-warning" />}
            <div>
              <div className="text-sm font-medium">{allOperational ? "Core systems operational" : "One or more services need attention"}</div>
              <div className="font-mono text-xs text-muted-foreground">{loading ? "Checking live status…" : "Live status pulled from Flask health endpoints."}</div>
            </div>
            <button onClick={() => void reload()} className="ml-auto rounded-full border border-border px-3 py-1 font-mono text-[11px] uppercase tracking-wider text-muted-foreground hover:text-foreground">
              refresh
            </button>
          </div>
        </div>

        {error ? <div className="rounded-xl border border-danger/20 bg-danger/10 px-4 py-3 text-sm text-danger">{error}</div> : null}

        <HealthStage title="Services" rail="service mesh">
          <div className="space-y-2">
            {services.map((service) => (
              <div key={service.name} className="flex items-center justify-between rounded-xl border border-border bg-background/40 p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <service.icon className="h-4 w-4" />
                  </div>
                  <div>
                    <div className="text-sm">{service.name}</div>
                    <div className="font-mono text-[11px] text-muted-foreground">{service.detail}</div>
                  </div>
                </div>
                <StatusBadge ok={service.ok} />
              </div>
            ))}
          </div>
        </HealthStage>

        <HealthStage title="Readiness checks" rail="probe detail">
          <div className="grid gap-3 md:grid-cols-2">
            {Object.entries(data?.ready.checks || {}).map(([key, value]) => (
              <Meta key={key} label={key.replaceAll("_", " ")} value={typeof value === "object" ? JSON.stringify(value) : String(value)} />
            ))}
            {!Object.keys(data?.ready.checks || {}).length ? <p className="text-sm text-muted-foreground">No detailed readiness checks were reported.</p> : null}
          </div>
        </HealthStage>

        <HealthStage title="Runtime" rail="runtime metadata">
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {Object.entries(data?.runtime || {}).map(([key, value]) => (
              <Meta key={key} label={key.replaceAll("_", " ")} value={typeof value === "object" ? JSON.stringify(value) : String(value)} />
            ))}
            {!Object.keys(data?.runtime || {}).length ? <p className="text-sm text-muted-foreground">Runtime metadata is not available.</p> : null}
          </div>
        </HealthStage>
      </div>
    </AppShell>
  );
}

function StatusBadge({ ok }: { ok: boolean }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-md border px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider ${ok ? "border-success/20 bg-success/10 text-success" : "border-warning/20 bg-warning/10 text-warning"}`}>
      {ok ? <CheckCircle2 className="h-3 w-3" /> : <AlertCircle className="h-3 w-3" />}
      {ok ? "ok" : "attention"}
    </span>
  );
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-background/40 p-4">
      <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className="mt-1 break-words font-mono text-sm">{value}</div>
    </div>
  );
}

function HealthStage({
  title,
  rail,
  children,
}: {
  title: string;
  rail?: string;
  children: ReactNode;
}) {
  return (
    <section data-reveal className="relative overflow-hidden rounded-[28px] border border-white/8 bg-[linear-gradient(155deg,rgba(8,17,27,0.96),rgba(7,14,22,0.98))] p-6 shadow-[0_28px_70px_-44px_rgba(0,0,0,0.92)]">
      <div className="mb-5 border-b border-white/8 pb-4">
        {rail ? <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{rail}</div> : null}
        <h3 className="mt-1 text-lg font-medium tracking-tight">{title}</h3>
      </div>
      {children}
    </section>
  );
}
