import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { Panel } from "@/components/silicore/Panel";
import { ArrowLeft, Terminal } from "lucide-react";

export const Route = createFileRoute("/jobs/$jobId")({
  head: () => ({ meta: [{ title: "Job detail — Silicore" }] }),
  component: JobDetail,
});

const logs = [
  "[12:04:01] queued job board.analyze sentinel-power.brd",
  "[12:04:02] worker.claim worker-01 → job_8af21c",
  "[12:04:02] parsing kicad_pcb",
  "[12:04:04] running rule pack: dfm.v3",
  "[12:04:07] running rule pack: signal-integrity.v2",
  "[12:04:09] running rule pack: thermal.v1",
  "[12:04:11] 13 findings · 3 critical",
  "[12:04:11] persisting analysis run_2026_04_25_1204",
  "[12:04:12] done · score 82",
];

function JobDetail() {
  const { jobId } = Route.useParams();
  return (
    <AppShell title="Job detail">
      <div className="space-y-6">
        <Link to="/jobs" className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-3 w-3" /> All jobs
        </Link>

        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="font-mono text-xs uppercase tracking-wider text-muted-foreground">job · {jobId}</div>
            <h2 className="mt-1 text-2xl font-medium tracking-tight">board.analyze · sentinel-power.brd</h2>
          </div>
          <span className="font-mono text-xs text-success">● complete · 12 s</span>
        </div>

        <div className="grid gap-4 md:grid-cols-4">
          <Stat label="Worker" value="worker-01" />
          <Stat label="Queued at" value="12:04:01" />
          <Stat label="Started" value="12:04:02" />
          <Stat label="Finished" value="12:04:12" />
        </div>

        <Panel title="Logs" action={<Terminal className="h-4 w-4 text-muted-foreground" />}>
          <pre className="overflow-x-auto rounded-lg border border-border bg-background/60 p-4 font-mono text-[12px] leading-relaxed text-muted-foreground">
{logs.join("\n")}
          </pre>
        </Panel>
      </div>
    </AppShell>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-4">
      <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className="mt-1 font-mono text-sm">{value}</div>
    </div>
  );
}
