import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { Panel } from "@/components/silicore/Panel";
import { PageHero } from "@/components/silicore/PageHero";
import { Button } from "@/components/ui/button";
import { Play, RefreshCcw, Cpu, ChevronRight } from "lucide-react";
import { apiPostJson, useApiData } from "@/lib/api";

export const Route = createFileRoute("/jobs")({
  head: () => ({ meta: [{ title: "Jobs — Silicore" }] }),
  component: Jobs,
});

type Job = {
  job_id: string;
  job_type: string;
  status: string;
  payload?: Record<string, unknown>;
  started_at?: string | null;
  completed_at?: string | null;
};

type JobsPayload = {
  jobs: Job[];
  worker: { running: boolean; thread_name?: string | null };
};

function Jobs() {
  const { data, error, reload } = useApiData<JobsPayload>("/api/frontend/jobs");
  const accessBlocked = Boolean(error && /access is required/i.test(error));

  const processQueue = async () => {
    await apiPostJson("/api/frontend/jobs/process", {});
    await reload();
  };

  const toggleWorker = async () => {
    if (data?.worker.running) {
      await apiPostJson("/api/frontend/worker/stop", {});
    } else {
      await apiPostJson("/api/frontend/worker/start", {});
    }
    await reload();
  };

  const jobs = data?.jobs ?? [];

  return (
    <AppShell title="Jobs">
      <div className="space-y-6">
        <PageHero
          eyebrow={<><Cpu className="h-3.5 w-3.5" /> Queue control</>}
          title="Manage background work with a cleaner operations surface for queue health, worker state, and job flow."
          description="This page now reads like an operational console instead of a raw table, while keeping the job controls explicit and fast."
          metrics={[
            { label: "Jobs", value: String(jobs.length), copy: "Visible in the active queue snapshot" },
            { label: "Worker", value: data?.worker.running ? "Running" : "Stopped", copy: data?.worker.thread_name || "No worker thread attached" },
          ]}
          actions={
            <>
              <Button size="sm" variant="ghost" onClick={() => void reload()}><RefreshCcw className="mr-1.5 h-3.5 w-3.5" /> Refresh</Button>
              <Button size="sm" onClick={() => void processQueue()}><Play className="mr-1.5 h-3.5 w-3.5" /> Process queue</Button>
            </>
          }
        />

        {error ? <div className="rounded-xl border border-danger/20 bg-danger/10 px-4 py-3 text-sm text-danger">{error}</div> : null}
        {accessBlocked ? (
          <Panel title="Lead access required">
            <p className="text-sm text-muted-foreground">Job controls are reserved for lead and admin roles because they can process queued work and manage the background worker.</p>
          </Panel>
        ) : null}

        <Panel title="Queue">
          <div className="overflow-hidden rounded-xl border border-border">
            <table className="premium-table w-full text-sm">
              <thead className="bg-background/40 text-left font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th className="px-4 py-3">Job ID</th>
                  <th className="px-4 py-3">Kind</th>
                  <th className="px-4 py-3">Target</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((job) => (
                  <tr key={job.job_id} className="border-t border-border hover:bg-background/40">
                    <td className="px-4 py-3 font-mono text-xs">{job.job_id}</td>
                    <td className="px-4 py-3"><span className="rounded border border-border px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{job.job_type}</span></td>
                    <td className="px-4 py-3 text-muted-foreground">{String(job.payload?.filename || job.payload?.label || job.payload?.path || "—")}</td>
                    <td className="px-4 py-3"><JobStatus status={job.status} /></td>
                    <td className="px-4 py-3 text-right">
                      <Link to="/jobs/$jobId" params={{ jobId: job.job_id }} className="inline-flex items-center gap-1 text-xs text-primary hover:underline">
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
          <div className="grid gap-3 md:grid-cols-2">
            <Stat label="Status" value={data?.worker.running ? "running" : "stopped"} tone={data?.worker.running ? "success" : undefined} />
            <Stat label="Thread" value={data?.worker.thread_name || "—"} />
          </div>
          <div className="mt-4 flex gap-2">
            <Button size="sm" className="rounded-full" onClick={() => void toggleWorker()}>
              {data?.worker.running ? "Stop worker" : "Start worker"}
            </Button>
          </div>
        </Panel>
      </div>
    </AppShell>
  );
}

function JobStatus({ status }: { status: string }) {
  const c =
    status === "running" ? "text-warning" :
    status === "completed" ? "text-success" :
    status === "failed" ? "text-danger" :
    "text-muted-foreground";
  return <span className={`font-mono text-xs ${c}`}>● {status}</span>;
}

function Stat({ label, value, tone }: { label: string; value: string; tone?: "success" }) {
  return (
    <div data-reveal className="premium-subtle rounded-2xl p-4">
      <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className={`mt-1 text-lg font-semibold ${tone === "success" ? "text-success" : ""}`}>{value}</div>
    </div>
  );
}
