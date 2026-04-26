import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { Panel } from "@/components/silicore/Panel";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Plug, ShieldCheck, ExternalLink, CheckCircle2, AlertCircle, Plus } from "lucide-react";

export const Route = createFileRoute("/nexus-ops")({
  head: () => ({ meta: [{ title: "Nexus Ops — Silicore" }] }),
  component: NexusOps,
});

const integrations = [
  { name: "Altium 365", status: "connected", desc: "Sync workspaces, projects and reviews", last: "synced 4 min ago" },
  { name: "JIRA", status: "connected", desc: "Auto-file findings as issues", last: "synced 12 min ago" },
  { name: "Slack", status: "connected", desc: "Notify channels on new criticals", last: "active" },
  { name: "GitHub", status: "disconnected", desc: "Mirror release-gate status to PRs", last: "—" },
  { name: "PLM (Arena)", status: "error", desc: "Push BOMs and rev metadata", last: "auth failed 1h ago" },
];

const validations = [
  { vendor: "JLCPCB DFM", board: "sentinel-power.brd", status: "passed", at: "1h ago" },
  { vendor: "PCBWay manufacturability", board: "halo-sensor.kicad_pcb", status: "warnings", at: "3h ago" },
  { vendor: "Sierra signal integrity", board: "atlas-rf-fe.brd", status: "failed", at: "yesterday" },
];

function NexusOps() {
  return (
    <AppShell title="Nexus Ops">
      <div className="space-y-6">
        <div className="flex items-end justify-between">
          <div>
            <h2 className="text-xl font-medium tracking-tight">Operations & external validation</h2>
            <p className="mt-1 text-sm text-muted-foreground">Manage integrations and forward boards to external validators.</p>
          </div>
          <Button size="sm" className="rounded-full"><Plus className="mr-1.5 h-3.5 w-3.5" /> Add integration</Button>
        </div>

        <Panel title="Integrations">
          <div className="grid gap-3 md:grid-cols-2">
            {integrations.map((i) => (
              <div key={i.name} className="flex items-start justify-between rounded-xl border border-border bg-background/40 p-4">
                <div className="flex items-start gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <Plug className="h-4 w-4" />
                  </div>
                  <div>
                    <div className="text-sm">{i.name}</div>
                    <div className="text-xs text-muted-foreground">{i.desc}</div>
                    <div className="mt-1 font-mono text-[11px] text-muted-foreground">{i.last}</div>
                  </div>
                </div>
                <StatusBadge status={i.status} />
              </div>
            ))}
          </div>
        </Panel>

        <div className="grid gap-4 lg:grid-cols-[1fr_360px]">
          <Panel title="External validation runs" action={<ExternalLink className="h-4 w-4 text-muted-foreground" />}>
            <div className="space-y-2">
              {validations.map((v, i) => (
                <div key={i} className="flex items-center justify-between rounded-xl border border-border bg-background/40 p-4">
                  <div>
                    <div className="text-sm">{v.board}</div>
                    <div className="font-mono text-[11px] text-muted-foreground">{v.vendor} · {v.at}</div>
                  </div>
                  <StatusBadge status={v.status} />
                </div>
              ))}
            </div>
          </Panel>

          <Panel title="Send for external validation" action={<ShieldCheck className="h-4 w-4 text-muted-foreground" />}>
            <div className="space-y-3">
              <Field label="Board"><Input placeholder="sentinel-power.brd" /></Field>
              <Field label="Vendor"><Input placeholder="JLCPCB · DFM scan" /></Field>
              <Field label="Notes"><Input placeholder="Optional context for the vendor" /></Field>
              <Button className="w-full rounded-full">Submit run</Button>
            </div>
          </Panel>
        </div>
      </div>
    </AppShell>
  );
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { cls: string; Icon: typeof CheckCircle2; label: string }> = {
    connected: { cls: "text-success bg-success/10 border-success/20", Icon: CheckCircle2, label: "Connected" },
    passed: { cls: "text-success bg-success/10 border-success/20", Icon: CheckCircle2, label: "Passed" },
    warnings: { cls: "text-warning bg-warning/10 border-warning/20", Icon: AlertCircle, label: "Warnings" },
    failed: { cls: "text-danger bg-danger/10 border-danger/20", Icon: AlertCircle, label: "Failed" },
    error: { cls: "text-danger bg-danger/10 border-danger/20", Icon: AlertCircle, label: "Error" },
    disconnected: { cls: "text-muted-foreground bg-muted/40 border-border", Icon: AlertCircle, label: "Disconnected" },
  };
  const m = map[status] ?? map.disconnected;
  return (
    <span className={`inline-flex items-center gap-1 rounded-md border px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider ${m.cls}`}>
      <m.Icon className="h-3 w-3" /> {m.label}
    </span>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
      {children}
    </div>
  );
}
