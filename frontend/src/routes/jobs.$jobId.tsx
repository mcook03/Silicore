import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { Panel } from "@/components/silicore/Panel";
import { ArrowLeft, Terminal } from "lucide-react";
import { useApiData } from "@/lib/api";

export const Route = createFileRoute("/jobs/$jobId")({
  head: () => ({ meta: [{ title: "Job detail — Silicore" }] }),
  component: JobDetail,
});

type JobDetailPayload = {
  job_id: string;
  job_type?: string;
  status?: string;
  created_at?: string;
  started_at?: string;
  completed_at?: string;
  payload?: Record<string, unknown>;
  result?: Record<string, unknown>;
  error?: string;
  logs?: string[];
};

function JobDetail() {
  const { jobId } = Route.useParams();
  const { data, error } = useApiData<JobDetailPayload>(`/api/frontend/jobs/${encodeURIComponent(jobId)}`);
  const details = [
    { label: "Job type", value: data?.job_type || "—" },
    { label: "Queued at", value: data?.created_at || "—" },
    { label: "Started", value: data?.started_at || "—" },
    { label: "Finished", value: data?.completed_at || "—" },
  ];
  const logLines = Array.isArray(data?.logs) && data?.logs.length
    ? data.logs
    : Object.entries(data?.result || {}).map(([key, value]) => `${key}: ${typeof value === "object" ? JSON.stringify(value) : String(value)}`);

  return (
    <AppShell title="Job detail">
      <div className="space-y-6">
        <Link to="/jobs" className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-3 w-3" /> All jobs
        </Link>

        {error ? <div className="rounded-xl border border-danger/20 bg-danger/10 px-4 py-3 text-sm text-danger">{error}</div> : null}

        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="font-mono text-xs uppercase tracking-wider text-muted-foreground">job · {data?.job_id || jobId}</div>
            <h2 className="mt-1 text-2xl font-medium tracking-tight">{data?.job_type || "Background job"}</h2>
          </div>
          <span className={`font-mono text-xs ${data?.status === "completed" ? "text-success" : data?.status === "failed" ? "text-danger" : "text-warning"}`}>● {data?.status || "unknown"}</span>
        </div>

        <div className="grid gap-4 md:grid-cols-4">
          {details.map((detail) => <Stat key={detail.label} label={detail.label} value={detail.value} />)}
        </div>

        <Panel title="Payload">
          <pre className="overflow-x-auto rounded-lg border border-border bg-background/60 p-4 font-mono text-[12px] leading-relaxed text-muted-foreground">
{JSON.stringify(data?.payload || {}, null, 2)}
          </pre>
        </Panel>

        <Panel title="Logs / result" action={<Terminal className="h-4 w-4 text-muted-foreground" />}>
          <pre className="overflow-x-auto rounded-lg border border-border bg-background/60 p-4 font-mono text-[12px] leading-relaxed text-muted-foreground">
{logLines.length ? logLines.join("\n") : data?.error || "No logs were recorded for this job."}
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
      <div className="mt-1 break-words font-mono text-sm">{value}</div>
    </div>
  );
}
