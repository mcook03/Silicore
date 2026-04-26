import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { Panel } from "@/components/silicore/Panel";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { apiPostForm, apiPostJson, useApiData } from "@/lib/api";
import { Plug, ShieldCheck, Upload } from "lucide-react";

export const Route = createFileRoute("/nexus-ops")({
  head: () => ({ meta: [{ title: "Nexus Ops — Silicore" }] }),
  component: NexusOps,
});

type OperationsSnapshot = {
  worker: { running: boolean; thread_name?: string | null };
  jobs: Array<{ job_id: string; job_type_label?: string; status?: string; created_at?: string }>;
  reviews: Array<{ status?: string; created_at?: string; summary?: string }>;
  audit_events: Array<{ event_type?: string; created_at?: string; message?: string }>;
  evaluations: Array<{ evaluation_id?: string; scope?: string; created_at?: string; summary?: Record<string, unknown> }>;
  fixture_evaluations: Array<Record<string, unknown>>;
  external_evaluations: Array<Record<string, unknown>>;
  integrations: Array<{ integration_id?: string; label?: string; integration_type?: string; status?: string; config?: Record<string, unknown> }>;
  summary: {
    queued_jobs: number;
    failed_jobs: number;
    completed_jobs: number;
    latest_job_label: string;
    latest_review_status: string;
    latest_evaluation_label: string;
    external_validation_label: string;
    worker_label: string;
  };
};

type OpsPayload = { operations_snapshot: OperationsSnapshot };

function NexusOps() {
  const { data, error, reload } = useApiData<OpsPayload>("/api/frontend/ops");
  const accessBlocked = Boolean(error && /access is required/i.test(error));
  const [integrationType, setIntegrationType] = useState("");
  const [integrationLabel, setIntegrationLabel] = useState("");
  const [integrationStatus, setIntegrationStatus] = useState("configured");
  const [integrationEndpoint, setIntegrationEndpoint] = useState("");
  const [validationLabel, setValidationLabel] = useState("");
  const [validationFiles, setValidationFiles] = useState<FileList | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const addIntegration = async () => {
    setMessage(null);
    try {
      await apiPostJson("/api/frontend/ops/integrations", {
        integration_type: integrationType,
        label: integrationLabel,
        status: integrationStatus,
        endpoint: integrationEndpoint,
      });
      setMessage("Integration saved.");
      setIntegrationType("");
      setIntegrationLabel("");
      setIntegrationEndpoint("");
      await reload();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Unable to save integration.");
    }
  };

  const submitValidation = async () => {
    setMessage(null);
    try {
      const formData = new FormData();
      formData.append("label", validationLabel || "External validation");
      Array.from(validationFiles || []).forEach((file) => formData.append("validation_files", file));
      await apiPostForm("/api/frontend/ops/external-validation", formData);
      setMessage("External validation run queued.");
      setValidationFiles(null);
      setValidationLabel("");
      await reload();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Unable to submit validation package.");
    }
  };

  const snapshot = data?.operations_snapshot;

  return (
    <AppShell title="Nexus Ops">
      <div className="space-y-6">
        <section
          data-reveal
          className="relative overflow-hidden rounded-[34px] border border-border/80 bg-[linear-gradient(115deg,rgba(7,15,24,0.98),rgba(8,18,28,0.95)_52%,rgba(11,21,31,0.97))] px-6 py-7 sm:px-8 sm:py-8"
        >
          <div className="pointer-events-none absolute inset-x-0 top-0 h-28 bg-gradient-to-b from-primary/8 to-transparent" />
          <div className="relative grid gap-8 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
            <div>
              <div className="section-eyebrow">
                <Plug className="h-3.5 w-3.5" />
                Operations fabric
              </div>
              <h2 className="mt-5 max-w-3xl text-4xl font-semibold tracking-tight text-foreground sm:text-[3.1rem] sm:leading-[1.02]">
                Run integrations, validation, and telemetry from an ops surface that feels deliberate.
              </h2>
              <p className="mt-4 max-w-2xl text-base leading-8 text-muted-foreground">
                Nexus Ops should read like a mission rail for high-trust internal workflows, with state and action aligned before you drop into the detailed panels below.
              </p>
            </div>
            <div className="grid gap-4 sm:grid-cols-3 xl:grid-cols-1">
              <OpsSignal label="Queued jobs" value={String(snapshot?.summary.queued_jobs ?? 0)} copy="Waiting in the pipeline" />
              <OpsSignal label="Completed" value={String(snapshot?.summary.completed_jobs ?? 0)} copy="Finished in this snapshot" />
              <OpsSignal label="Worker" value={snapshot?.summary.worker_label || "Unknown"} copy="Current execution posture" />
            </div>
          </div>
        </section>

        {error ? <div className="rounded-xl border border-danger/20 bg-danger/10 px-4 py-3 text-sm text-danger">{error}</div> : null}
        {accessBlocked ? (
          <Panel title="Lead access required">
            <p className="text-sm text-muted-foreground">Nexus Ops is reserved for lead and admin roles because it exposes integrations, external validation uploads, and operational telemetry.</p>
          </Panel>
        ) : null}
        {message ? <div className="rounded-xl border border-primary/20 bg-primary/5 px-4 py-3 text-sm">{message}</div> : null}

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <StatCard label="Queued jobs" value={String(snapshot?.summary.queued_jobs ?? 0)} />
          <StatCard label="Failed jobs" value={String(snapshot?.summary.failed_jobs ?? 0)} />
          <StatCard label="Completed jobs" value={String(snapshot?.summary.completed_jobs ?? 0)} />
          <StatCard label="Worker" value={snapshot?.summary.worker_label || "unknown"} />
        </div>

        <Panel title="Integrations" action={<Plug className="h-4 w-4 text-primary" />}>
          <div className="grid gap-3 md:grid-cols-2">
            {(snapshot?.integrations || []).map((integration) => (
              <div key={integration.integration_id || integration.label} className="rounded-xl border border-border bg-background/40 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-sm">{integration.label || integration.integration_type}</div>
                    <div className="font-mono text-[11px] text-muted-foreground">{integration.integration_type}</div>
                  </div>
                  <span className="rounded border border-border px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{integration.status || "configured"}</span>
                </div>
                {integration.config?.endpoint ? <div className="mt-2 break-all font-mono text-[11px] text-muted-foreground">{String(integration.config.endpoint)}</div> : null}
              </div>
            ))}
            {!snapshot?.integrations.length ? <p className="text-sm text-muted-foreground">No integrations configured yet.</p> : null}
          </div>
        </Panel>

        <div className="grid gap-6 xl:grid-cols-[1fr_360px]">
          <Panel title="Recent operations">
            <div className="space-y-2">
              {(snapshot?.jobs || []).slice(0, 8).map((job) => (
                <div key={job.job_id} className="rounded-xl border border-border bg-background/40 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div className="text-sm">{job.job_type_label || job.job_id}</div>
                    <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{job.status || "unknown"}</span>
                  </div>
                  <div className="mt-1 font-mono text-[11px] text-muted-foreground">{job.created_at || "no timestamp"}</div>
                </div>
              ))}
              {!snapshot?.jobs.length ? <p className="text-sm text-muted-foreground">No recent jobs were reported.</p> : null}
            </div>
          </Panel>

          <Panel title="Add integration">
            <div className="space-y-3">
              <Field label="Type"><Input className="premium-input" value={integrationType} onChange={(event) => setIntegrationType(event.target.value)} placeholder="github" /></Field>
              <Field label="Label"><Input className="premium-input" value={integrationLabel} onChange={(event) => setIntegrationLabel(event.target.value)} placeholder="GitHub" /></Field>
              <Field label="Status"><Input className="premium-input" value={integrationStatus} onChange={(event) => setIntegrationStatus(event.target.value)} placeholder="configured" /></Field>
              <Field label="Endpoint"><Input className="premium-input" value={integrationEndpoint} onChange={(event) => setIntegrationEndpoint(event.target.value)} placeholder="https://api.example.com" /></Field>
              <Button className="w-full rounded-full" onClick={() => void addIntegration()}>Save integration</Button>
            </div>
          </Panel>
        </div>

        <div className="grid gap-6 xl:grid-cols-[1fr_360px]">
          <Panel title="Evaluation history" action={<ShieldCheck className="h-4 w-4 text-primary" />}>
            <div className="space-y-2">
              {(snapshot?.evaluations || []).map((evaluation) => (
                <div key={evaluation.evaluation_id} className="rounded-xl border border-border bg-background/40 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div className="text-sm">{evaluation.evaluation_id || "evaluation"}</div>
                    <span className="rounded border border-border px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{evaluation.scope || "scope"}</span>
                  </div>
                  <div className="mt-1 font-mono text-[11px] text-muted-foreground">{evaluation.created_at || "no timestamp"}</div>
                </div>
              ))}
              {!snapshot?.evaluations.length ? <p className="text-sm text-muted-foreground">No evaluation history is available.</p> : null}
            </div>
          </Panel>

          <Panel title="External validation upload" action={<Upload className="h-4 w-4 text-muted-foreground" />}>
            <div className="space-y-3">
              <Field label="Run label"><Input className="premium-input" value={validationLabel} onChange={(event) => setValidationLabel(event.target.value)} placeholder="Vendor CAM package" /></Field>
              <Field label="Files"><Input className="premium-input" type="file" multiple onChange={(event) => setValidationFiles(event.target.files)} /></Field>
              <Button className="w-full rounded-full" onClick={() => void submitValidation()}>Submit validation package</Button>
            </div>
          </Panel>
        </div>
      </div>
    </AppShell>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div data-reveal className="premium-card rounded-[24px] p-5">
      <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
    </div>
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

function OpsSignal({ label, value, copy }: { label: string; value: string; copy: string }) {
  return (
    <div className="border-l border-white/10 pl-4">
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{label}</div>
      <div className="mt-1 text-3xl font-semibold text-foreground">{value}</div>
      <div className="mt-1 text-sm text-muted-foreground">{copy}</div>
    </div>
  );
}
