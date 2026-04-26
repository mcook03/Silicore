import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { Panel } from "@/components/silicore/Panel";
import { CheckCircle2, Server, Database, Cpu, Cloud } from "lucide-react";

export const Route = createFileRoute("/health")({
  head: () => ({ meta: [{ title: "System health — Silicore" }] }),
  component: Health,
});

const services = [
  { name: "Web · /health/live", status: "ok", latency: "12 ms", icon: Server },
  { name: "Web · /health/ready", status: "ok", latency: "18 ms", icon: Server },
  { name: "Database · silicore.db", status: "ok", latency: "3 ms", icon: Database },
  { name: "Worker · queue", status: "ok", latency: "—", icon: Cpu },
  { name: "Atlas gateway", status: "ok", latency: "104 ms", icon: Cloud },
];

function Health() {
  return (
    <AppShell title="System health">
      <div className="space-y-6">
        <div className="rounded-2xl border border-success/20 bg-success/5 p-6">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="h-5 w-5 text-success" />
            <div>
              <div className="text-sm font-medium">All systems operational</div>
              <div className="font-mono text-xs text-muted-foreground">Last checked just now · uptime 99.98% (30d)</div>
            </div>
          </div>
        </div>

        <Panel title="Services">
          <div className="space-y-2">
            {services.map((s) => (
              <div key={s.name} className="flex items-center justify-between rounded-xl border border-border bg-background/40 p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <s.icon className="h-4 w-4" />
                  </div>
                  <div>
                    <div className="text-sm">{s.name}</div>
                    <div className="font-mono text-[11px] text-muted-foreground">latency {s.latency}</div>
                  </div>
                </div>
                <span className="inline-flex items-center gap-1 rounded-md border border-success/20 bg-success/10 px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider text-success">
                  <CheckCircle2 className="h-3 w-3" /> {s.status}
                </span>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Runtime">
          <div className="grid gap-3 md:grid-cols-3">
            <Meta label="Version" value="silicore 1.4.2" />
            <Meta label="Region" value="us-east-1" />
            <Meta label="Build" value="b3f2c19 · 2026-04-24" />
            <Meta label="Python" value="3.12.1" />
            <Meta label="Worker pool" value="2 / 4" />
            <Meta label="Storage" value="42% of 100 GB" />
          </div>
        </Panel>
      </div>
    </AppShell>
  );
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-background/40 p-4">
      <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className="mt-1 font-mono text-sm">{value}</div>
    </div>
  );
}
