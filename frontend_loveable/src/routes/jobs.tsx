import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { Panel } from "@/components/silicore/Panel";
import { Button } from "@/components/ui/button";
import { Play, RefreshCcw, Cpu, ChevronRight } from "lucide-react";

export const Route = createFileRoute("/jobs")({
  head: () => ({ meta: [{ title: "Jobs — Silicore" }] }),
  component: Jobs,
});

const jobs = [
  { id: "job_8af21c", kind: "board.analyze", target: "sentinel-power.brd", status: "running", queued: "12s ago", duration: "11s" },
  { id: "job_e03b77", kind: "project.compare", target: "Sentinel rev-c↔rev-b", status: "queued", queued: "30s ago", duration: "—" },
  { id: "job_2cd901", kind: "board.analyze", target: "halo-sensor.kicad_pcb", status: "complete", queued: "5m ago", duration: "27s" },
  { id: "job_44e8a2", kind: "external.validate", target: "atlas-rf-fe.brd → JLCPCB", status: "failed", queued: "12m ago", duration: "8s" },
  { id: "job_9b1afe", kind: "report.generate", target: "Sentinel weekly", status: "complete", queued: "1h ago", duration: "1m 14s" },
];

function Jobs() {
  return (
    <AppShell title="Jobs">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">{jobs.length} jobs · 1 running · 1 queued</p>
          <div className="flex gap-2">
            <Button size="sm" variant="ghost" className="rounded-full"><RefreshCcw className="mr-1.5 h-3.5 w-3.5" /> Refresh</Button>
            <Button size="sm" className="rounded-full"><Play className="mr-1.5 h-3.5 w-3.5" /> Process queue</Button>
          </div>
        </div>

        <Panel title="Queue">
          <div className="overflow-hidden rounded-xl border border-border">
            <table className="w-full text-sm">
              <thead className="bg-background/40 text-left font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th className="px-4 py-3">Job ID</th>
                  <th className="px-4 py-3">Kind</th>
                  <th className="px-4 py-3">Target</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Duration</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((j) => (
                  <tr key={j.id} className="border-t border-border hover:bg-background/40">
                    <td className="px-4 py-3 font-mono text-xs">{j.id}</td>
                    <td className="px-4 py-3"><span className="rounded border border-border px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{j.kind}</span></td>
                    <td className="px-4 py-3 text-muted-foreground">{j.target}</td>
                    <td className="px-4 py-3"><JobStatus status={j.status} /></td>
                    <td className="px-4 py-3 font-mono text-xs text-muted-foreground">{j.duration}</td>
                    <td className="px-4 py-3 text-right">
                      <Link to="/jobs/$jobId" params={{ jobId: j.id }} className="inline-flex items-center gap-1 text-xs text-primary hover:underline">
                        details <ChevronRight className="h-3 w-3" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel title="Worker" action={<Cpu className="h-4 w-4 text-primary" />}>
          <div className="grid gap-3 md:grid-cols-3">
            <Stat label="Status" value="running" tone="success" />
            <Stat label="Throughput" value="14 / hr" />
            <Stat label="Avg latency" value="22 s" />
          </div>
          <div className="mt-4 flex gap-2">
            <Button size="sm" variant="ghost" className="rounded-full">Stop worker</Button>
            <Button size="sm" className="rounded-full">Start worker</Button>
          </div>
        </Panel>
      </div>
    </AppShell>
  );
}

function JobStatus({ status }: { status: string }) {
  const c =
    status === "running" ? "text-warning" :
    status === "complete" ? "text-success" :
    status === "failed" ? "text-danger" :
    "text-muted-foreground";
  return <span className={`font-mono text-xs ${c}`}>● {status}</span>;
}

function Stat({ label, value, tone }: { label: string; value: string; tone?: "success" }) {
  return (
    <div className="rounded-xl border border-border bg-background/40 p-4">
      <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className={`mt-1 text-lg font-semibold ${tone === "success" ? "text-success" : ""}`}>{value}</div>
    </div>
  );
}
