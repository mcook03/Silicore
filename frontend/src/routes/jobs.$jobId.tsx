import { createFileRoute, Link } from "@tanstack/react-router";
import type { ReactNode } from "react";
import { AppShell } from "@/components/silicore/AppShell";
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

        <JobStage title="Payload" rail="input payload">
          <pre className="overflow-x-auto rounded-lg border border-border bg-background/60 p-4 font-mono text-[12px] leading-relaxed text-muted-foreground">
{JSON.stringify(data?.payload || {}, null, 2)}
          </pre>
        </JobStage>

        <JobStage title="Logs / result" rail="execution output" action={<Terminal className="h-4 w-4 text-muted-foreground" />}>
          <pre className="overflow-x-auto rounded-lg border border-border bg-background/60 p-4 font-mono text-[12px] leading-relaxed text-muted-foreground">
{logLines.length ? logLines.join("\n") : data?.error || "No logs were recorded for this job."}
          </pre>
        </JobStage>
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

function JobStage({
  title,
  rail,
  action,
  children,
}: {
  title: string;
  rail?: string;
  action?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section data-reveal className="relative overflow-hidden rounded-[28px] border border-white/8 bg-[linear-gradient(155deg,rgba(8,17,27,0.96),rgba(7,14,22,0.98))] p-6 shadow-[0_28px_70px_-44px_rgba(0,0,0,0.92)]">
      <div className="mb-5 flex items-start justify-between gap-4 border-b border-white/8 pb-4">
        <div>
          {rail ? <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{rail}</div> : null}
          <h3 className="mt-1 text-lg font-medium tracking-tight">{title}</h3>
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}
