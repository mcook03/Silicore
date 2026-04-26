import { useEffect, useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import type { ReactNode } from "react";
import { AppShell } from "@/components/silicore/AppShell";
import { Panel, ScorePill } from "@/components/silicore/Panel";
import { Button } from "@/components/ui/button";
import {
  ArrowLeftRight,
  ArrowRight,
  CheckCircle2,
  Dot,
  GitCompareArrows,
  Minus,
  RefreshCcw,
  Sparkles,
  TrendingDown,
  TrendingUp,
  TriangleAlert,
} from "lucide-react";
import { useApiData } from "@/lib/api";

export const Route = createFileRoute("/compare")({
  head: () => ({ meta: [{ title: "Compare revisions — Silicore" }] }),
  component: Compare,
});

type SessionPayload = {
  project_options: Array<{ value: string; label: string }>;
};

type ProjectRun = {
  run_id: string;
  name?: string;
  created_at?: string;
  score?: number | null;
  risk_count?: number;
  critical_count?: number;
  run_type?: string;
};

type ProjectDetailPayload = {
  project: {
    project_id: string;
    name: string;
    description?: string;
    runs: ProjectRun[];
  };
};

type ComparePayload = {
  project: { project_id: string; name: string };
  run_a: { run_id?: string; name: string; score: number; issues: number };
  run_b: { run_id?: string; name: string; score: number; issues: number };
  categories: Array<{ name: string; before: number; after: number; delta: number }>;
  changes: Array<{ kind: "fixed" | "new" | "regressed"; title: string; impact: string; why: string }>;
};

function Compare() {
  const session = useApiData<SessionPayload>("/api/frontend/session");
  const defaultProject = session.data?.project_options?.[0]?.value || "";
  const [projectId, setProjectId] = useState("");
  const [runAId, setRunAId] = useState("");
  const [runBId, setRunBId] = useState("");
  const activeProjectId = projectId || defaultProject;

  const projectDetail = useApiData<ProjectDetailPayload>(
    activeProjectId ? `/api/frontend/projects/${encodeURIComponent(activeProjectId)}` : "/api/frontend/projects/missing",
  );

  const runs = useMemo(() => {
    const source = projectDetail.data?.project?.runs || [];
    return [...source]
      .filter((run) => run.run_id)
      .sort((a, b) => String(b.created_at || "").localeCompare(String(a.created_at || "")));
  }, [projectDetail.data]);

  useEffect(() => {
    if (!runs.length) {
      return;
    }
    setRunBId((current) => current || runs[0]?.run_id || "");
    setRunAId((current) => current || runs[1]?.run_id || runs[0]?.run_id || "");
  }, [runs]);

  const compareUrl = useMemo(() => {
    if (!activeProjectId) {
      return "/api/frontend/compare";
    }
    const params = new URLSearchParams({ project_id: activeProjectId });
    if (runAId) params.set("run_a", runAId);
    if (runBId) params.set("run_b", runBId);
    return `/api/frontend/compare?${params.toString()}`;
  }, [activeProjectId, runAId, runBId]);

  const compare = useApiData<ComparePayload>(compareUrl);

  const selectedProjectLabel =
    session.data?.project_options?.find((option) => option.value === activeProjectId)?.label || "Select project";
  const selectedRunA = runs.find((run) => run.run_id === runAId);
  const selectedRunB = runs.find((run) => run.run_id === runBId);
  const scoreDelta = (compare.data?.run_b.score || 0) - (compare.data?.run_a.score || 0);
  const issueDelta = (compare.data?.run_b.issues || 0) - (compare.data?.run_a.issues || 0);
  const strongestCategoryShift = [...(compare.data?.categories || [])].sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))[0];
  const improvements = (compare.data?.changes || []).filter((change) => change.kind === "fixed").length;
  const regressions = (compare.data?.changes || []).filter((change) => change.kind === "regressed").length;
  const neutralChanges = (compare.data?.changes || []).filter((change) => change.kind === "new").length;
  const categoryScale = Math.max(
    1,
    ...(compare.data?.categories || []).map((item) => Math.max(item.before, item.after, Math.abs(item.delta))),
  );

  const swapRuns = () => {
    setRunAId(runBId);
    setRunBId(runAId);
  };

  const pickRun = (runId: string) => {
    if (!runAId || runId === runBId) {
      setRunAId(runId);
      return;
    }
    if (!runBId || runId === runAId) {
      setRunBId(runId);
      return;
    }
    setRunBId(runId);
  };

  return (
    <AppShell title="Compare revisions">
      <div className="space-y-6">
        <section className="relative overflow-hidden rounded-[32px] border border-border bg-[radial-gradient(circle_at_top_left,_rgba(86,211,240,0.18),_transparent_28%),radial-gradient(circle_at_bottom_right,_rgba(61,144,255,0.14),_transparent_36%),linear-gradient(180deg,_rgba(8,16,26,0.98),_rgba(10,17,27,0.97))] px-6 py-7 sm:px-8 sm:py-8">
          <div className="absolute inset-0 bg-[linear-gradient(120deg,transparent,rgba(255,255,255,0.03),transparent)]" />
          <div className="relative space-y-7">
            <div className="grid gap-6 xl:grid-cols-[minmax(0,1.35fr)_minmax(0,0.65fr)]">
              <div className="min-w-0">
                <div className="inline-flex items-center gap-2 rounded-full border border-primary/25 bg-primary/10 px-3 py-1 font-mono text-[10px] uppercase tracking-[0.24em] text-primary">
                  <GitCompareArrows className="h-3.5 w-3.5" />
                  Revision cockpit
                </div>
                <h2 className="mt-5 max-w-3xl text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
                  Put two board analysis revisions in one view and make the delta obvious.
                </h2>
                <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">
                  This layout keeps the comparison readable without side-scrolling. Pick a workspace, choose a baseline and candidate,
                  and Silicore will surface the score shift, risk movement, and the differences worth engineering attention.
                </p>
              </div>

              <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
                <HeroCallout
                  label="Workspace"
                  value={selectedProjectLabel}
                  copy="Active comparison context"
                />
                <HeroCallout
                  label="Best score position"
                  value={
                    scoreDelta > 0
                      ? compare.data?.run_b.name || "Candidate"
                      : scoreDelta < 0
                        ? compare.data?.run_a.name || "Baseline"
                        : "Tie"
                  }
                  copy={scoreDelta === 0 ? "No change in score" : `${scoreDelta > 0 ? "+" : ""}${scoreDelta.toFixed(1)} score movement`}
                />
                <HeroCallout
                  label="Largest shift"
                  value={strongestCategoryShift?.name || "Not available"}
                  copy={
                    strongestCategoryShift
                      ? `${strongestCategoryShift.delta > 0 ? "+" : ""}${strongestCategoryShift.delta} movement`
                      : "Choose richer runs to expose category deltas"
                  }
                />
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <HeroStat label="Score delta" value={`${scoreDelta > 0 ? "+" : ""}${scoreDelta.toFixed(1)}`} tone={scoreDelta > 0 ? "success" : scoreDelta < 0 ? "danger" : "muted"} />
              <HeroStat label="Issue delta" value={`${issueDelta > 0 ? "+" : ""}${issueDelta}`} tone={issueDelta < 0 ? "success" : issueDelta > 0 ? "danger" : "muted"} />
              <HeroStat label="Resolved findings" value={String(improvements)} tone="success" />
              <HeroStat label="Regressions" value={String(regressions)} tone={regressions > 0 ? "danger" : "muted"} />
            </div>
          </div>
        </section>

        <section className="grid gap-6 2xl:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
          <Panel
            title="Comparison setup"
            action={
              <Button size="sm" variant="ghost" className="rounded-full" onClick={() => void compare.reload()}>
                <RefreshCcw className="mr-1.5 h-3.5 w-3.5" />
                Refresh
              </Button>
            }
          >
            <div className="space-y-5">
              <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto_minmax(0,1fr)]">
                <Field label="Workspace">
                  <select
                    value={activeProjectId}
                    onChange={(event) => {
                      setProjectId(event.target.value);
                      setRunAId("");
                      setRunBId("");
                    }}
                    className="h-11 w-full rounded-2xl border border-input bg-background/50 px-3 text-sm"
                  >
                    {(session.data?.project_options || []).map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </Field>

                <Field label="Baseline run">
                  <select
                    value={runAId}
                    onChange={(event) => setRunAId(event.target.value)}
                    className="h-11 w-full rounded-2xl border border-input bg-background/50 px-3 text-sm"
                  >
                    {runs.map((run) => (
                      <option key={run.run_id} value={run.run_id}>
                        {run.name || run.run_id}
                      </option>
                    ))}
                  </select>
                </Field>

                <div className="flex items-end justify-center">
                  <Button type="button" variant="ghost" className="h-11 rounded-2xl px-4" onClick={swapRuns}>
                    <ArrowLeftRight className="h-4 w-4" />
                  </Button>
                </div>

                <Field label="Candidate run">
                  <select
                    value={runBId}
                    onChange={(event) => setRunBId(event.target.value)}
                    className="h-11 w-full rounded-2xl border border-input bg-background/50 px-3 text-sm"
                  >
                    {runs.map((run) => (
                      <option key={run.run_id} value={run.run_id}>
                        {run.name || run.run_id}
                      </option>
                    ))}
                  </select>
                </Field>
              </div>

              <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_minmax(0,0.8fr)]">
                <RevisionCard title="Baseline" run={selectedRunA} compareRun={compare.data?.run_a} />
                <RevisionCard title="Candidate" run={selectedRunB} compareRun={compare.data?.run_b} highlight />
                <DecisionBoard
                  scoreDelta={scoreDelta}
                  issueDelta={issueDelta}
                  strongestCategoryShift={strongestCategoryShift}
                />
              </div>

              <div className="rounded-[24px] border border-border bg-background/35 p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded-full border border-primary/20 bg-primary/10 px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.18em] text-primary">
                    Selection logic
                  </span>
                  <span className="text-sm text-muted-foreground">
                    Tap any run below to reassign the candidate. Tapping the current candidate moves it into the baseline slot.
                  </span>
                </div>
              </div>
            </div>
          </Panel>

          <Panel title="Run library" action={<Sparkles className="h-4 w-4 text-primary" />}>
            <div className="grid gap-3 sm:grid-cols-2">
              {runs.map((run) => {
                const state = run.run_id === runAId ? "baseline" : run.run_id === runBId ? "candidate" : "idle";
                return (
                  <button
                    key={run.run_id}
                    onClick={() => pickRun(run.run_id)}
                    className={`min-w-0 rounded-[24px] border p-4 text-left transition-all ${
                      state === "baseline"
                        ? "border-primary/40 bg-primary/8 shadow-[0_0_0_1px_rgba(86,211,240,0.08)]"
                        : state === "candidate"
                          ? "border-success/30 bg-success/8 shadow-[0_0_0_1px_rgba(38,201,135,0.08)]"
                          : "border-border bg-background/40 hover:border-primary/20 hover:bg-background/55"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
                          {state === "idle" ? run.run_type || "run" : state}
                        </div>
                        <div className="mt-2 break-words text-sm font-medium leading-5">
                          {run.name || run.run_id}
                        </div>
                      </div>
                      <ScorePill score={normalizeScore(run.score)} />
                    </div>

                    <div className="mt-3 flex flex-wrap gap-2 text-xs text-muted-foreground">
                      <span className="rounded-full border border-border px-2 py-1">{run.critical_count || 0} critical</span>
                      <span className="rounded-full border border-border px-2 py-1">{run.risk_count || 0} issues</span>
                    </div>

                    <div className="mt-3 break-all font-mono text-[11px] text-muted-foreground">
                      {run.created_at || run.run_id}
                    </div>
                  </button>
                );
              })}
            </div>
          </Panel>
        </section>

        {compare.error ? (
          <div className="rounded-2xl border border-danger/20 bg-danger/10 px-4 py-3 text-sm text-danger">{compare.error}</div>
        ) : null}

        <section className="grid gap-6 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
          <Panel title={`Category movement · ${compare.data?.project.name || selectedProjectLabel}`}>
            {(compare.data?.categories || []).length ? (
              <div className="space-y-4">
                {(compare.data?.categories || []).map((item) => (
                  <CategoryRow key={item.name} item={item} scale={categoryScale} />
                ))}
              </div>
            ) : (
              <EmptyPanel copy="These runs do not currently expose category deltas. Compare two richer analysis runs to see domain-level movement here." />
            )}
          </Panel>

          <Panel title="Difference digest">
            <div className="grid gap-3 sm:grid-cols-3">
              <DigestCard
                icon={<CheckCircle2 className="h-4 w-4" />}
                label="Resolved"
                value={String(improvements)}
                tone="success"
              />
              <DigestCard
                icon={<TriangleAlert className="h-4 w-4" />}
                label="Regressed"
                value={String(regressions)}
                tone={regressions > 0 ? "danger" : "muted"}
              />
              <DigestCard
                icon={<Minus className="h-4 w-4" />}
                label="New findings"
                value={String(neutralChanges)}
                tone="muted"
              />
            </div>

            <div className="mt-4 space-y-3">
              {(compare.data?.changes || []).length ? (
                (compare.data?.changes || []).map((change) => <ChangeRow key={`${change.kind}-${change.title}`} {...change} />)
              ) : (
                <EmptyPanel copy="Silicore didn’t generate a distinct change list for these runs yet. Try choosing runs with richer risk snapshots or more different analysis outcomes." />
              )}
            </div>
          </Panel>
        </section>
      </div>
    </AppShell>
  );
}

function RevisionCard({
  title,
  run,
  compareRun,
  highlight,
}: {
  title: string;
  run?: ProjectRun;
  compareRun?: ComparePayload["run_a"];
  highlight?: boolean;
}) {
  const score = compareRun?.score ?? normalizeScore(run?.score);
  return (
    <div
      className={`min-w-0 rounded-[24px] border bg-surface p-5 ${
        highlight ? "border-primary/40 shadow-[0_0_0_1px_oklch(0.85_0.16_195_/_0.2)]" : "border-border"
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground">{title}</div>
          <div className="mt-2 break-words text-xl font-semibold leading-tight">
            {compareRun?.name || run?.name || "Select a run"}
          </div>
          <div className="mt-2 break-all font-mono text-[11px] text-muted-foreground">
            {run?.created_at || run?.run_id || "No timestamp"}
          </div>
        </div>
        <ScorePill score={score} />
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-3">
        <MiniStat label="Score" value={String(score)} />
        <MiniStat label="Issues" value={String(compareRun?.issues ?? run?.risk_count ?? 0)} />
        <MiniStat label="Critical" value={String(run?.critical_count ?? 0)} />
      </div>
    </div>
  );
}

function DecisionBoard({
  scoreDelta,
  issueDelta,
  strongestCategoryShift,
}: {
  scoreDelta: number;
  issueDelta: number;
  strongestCategoryShift?: ComparePayload["categories"][number];
}) {
  const recommendation =
    scoreDelta > 0 && issueDelta <= 0
      ? "Candidate is the stronger revision."
      : scoreDelta < 0 && issueDelta >= 0
        ? "Baseline is safer to keep."
        : "Review the detailed deltas before deciding.";

  return (
    <div className="rounded-[24px] border border-border bg-[linear-gradient(180deg,rgba(16,24,37,0.96),rgba(12,18,29,0.9))] p-5">
      <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-primary">Decision pulse</div>
      <div className="mt-3 text-lg font-semibold">{recommendation}</div>
      <div className="mt-4 space-y-3">
        <DecisionLine
          label="Score movement"
          value={`${scoreDelta > 0 ? "+" : ""}${scoreDelta.toFixed(1)}`}
          tone={scoreDelta > 0 ? "success" : scoreDelta < 0 ? "danger" : "muted"}
        />
        <DecisionLine
          label="Issue movement"
          value={`${issueDelta > 0 ? "+" : ""}${issueDelta}`}
          tone={issueDelta < 0 ? "success" : issueDelta > 0 ? "danger" : "muted"}
        />
        <DecisionLine
          label="Biggest category move"
          value={
            strongestCategoryShift
              ? `${strongestCategoryShift.name} ${strongestCategoryShift.delta > 0 ? "+" : ""}${strongestCategoryShift.delta}`
              : "Not enough data"
          }
          tone="muted"
        />
      </div>
    </div>
  );
}

function CategoryRow({
  item,
  scale,
}: {
  item: ComparePayload["categories"][number];
  scale: number;
}) {
  const beforeWidth = `${Math.max(8, (item.before / scale) * 100)}%`;
  const afterWidth = `${Math.max(8, (item.after / scale) * 100)}%`;
  const deltaTone =
    item.delta > 0 ? "text-success" : item.delta < 0 ? "text-danger" : "text-muted-foreground";

  return (
    <div className="rounded-[22px] border border-border bg-background/30 p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0">
          <div className="text-sm font-medium">{item.name}</div>
          <div className="mt-1 flex flex-wrap items-center gap-1 text-xs text-muted-foreground">
            <span>Baseline {item.before}</span>
            <Dot className="h-3.5 w-3.5" />
            <span>Candidate {item.after}</span>
          </div>
        </div>
        <div className={`rounded-full border border-border px-2.5 py-1 font-mono text-[11px] ${deltaTone}`}>
          {item.delta > 0 ? "+" : ""}
          {item.delta}
        </div>
      </div>

      <div className="mt-4 space-y-2">
        <div>
          <div className="mb-1 flex items-center justify-between text-[11px] text-muted-foreground">
            <span>Baseline</span>
            <span>{item.before}</span>
          </div>
          <div className="h-2.5 rounded-full bg-muted/80">
            <div className="h-2.5 rounded-full bg-white/25" style={{ width: beforeWidth }} />
          </div>
        </div>

        <div>
          <div className="mb-1 flex items-center justify-between text-[11px] text-muted-foreground">
            <span>Candidate</span>
            <span>{item.after}</span>
          </div>
          <div className="h-2.5 rounded-full bg-muted/80">
            <div
              className={`h-2.5 rounded-full ${item.delta >= 0 ? "bg-primary" : "bg-danger"}`}
              style={{ width: afterWidth }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

function ChangeRow({ kind, title, impact, why }: { kind: string; title: string; impact: string; why: string }) {
  const map = {
    fixed: { Icon: TrendingUp, cls: "text-success bg-success/10 border-success/20", label: "Fixed" },
    regressed: { Icon: TrendingDown, cls: "text-danger bg-danger/10 border-danger/20", label: "Regressed" },
    new: { Icon: Minus, cls: "text-warning bg-warning/10 border-warning/20", label: "New" },
  } as const;
  const { Icon, cls, label } = map[kind as keyof typeof map] || map.new;
  return (
    <div className="rounded-[22px] border border-border bg-background/35 p-4">
      <div className="flex flex-wrap items-start gap-3">
        <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border ${cls}`}>
          <Icon className="h-4 w-4" />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full border border-border px-2 py-1 font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
              {label}
            </span>
            <span className="break-words text-sm font-medium">{title}</span>
          </div>
          <div className="mt-2 text-sm leading-6 text-muted-foreground">{why}</div>
        </div>
        <span className="rounded-full border border-border px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
          {impact}
        </span>
      </div>
    </div>
  );
}

function HeroStat({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: "success" | "danger" | "muted";
}) {
  const toneClass = tone === "success" ? "text-success" : tone === "danger" ? "text-danger" : "text-foreground";
  return (
    <div className="rounded-[22px] border border-white/10 bg-black/25 p-4 backdrop-blur-sm">
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{label}</div>
      <div className={`mt-2 text-2xl font-semibold ${toneClass}`}>{value}</div>
    </div>
  );
}

function HeroCallout({ label, value, copy }: { label: string; value: string; copy: string }) {
  return (
    <div className="rounded-[22px] border border-white/10 bg-black/20 p-4 backdrop-blur-sm">
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{label}</div>
      <div className="mt-2 break-words text-base font-semibold">{value}</div>
      <div className="mt-1 text-xs text-muted-foreground">{copy}</div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="space-y-1.5">
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{label}</div>
      {children}
    </div>
  );
}

function DecisionLine({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: "success" | "danger" | "muted";
}) {
  const toneClass = tone === "success" ? "text-success" : tone === "danger" ? "text-danger" : "text-foreground";
  return (
    <div className="rounded-2xl border border-border bg-background/35 p-3">
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{label}</div>
      <div className={`mt-1 text-sm font-semibold ${toneClass}`}>{value}</div>
    </div>
  );
}

function DigestCard({
  icon,
  label,
  value,
  tone,
}: {
  icon: ReactNode;
  label: string;
  value: string;
  tone: "success" | "danger" | "muted";
}) {
  const toneClass = tone === "success" ? "text-success" : tone === "danger" ? "text-danger" : "text-foreground";
  return (
    <div className="rounded-[20px] border border-border bg-background/30 p-4">
      <div className="flex items-center gap-2 text-muted-foreground">
        {icon}
        <span className="font-mono text-[10px] uppercase tracking-[0.18em]">{label}</span>
      </div>
      <div className={`mt-2 text-2xl font-semibold ${toneClass}`}>{value}</div>
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[18px] border border-border bg-background/35 p-3">
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{label}</div>
      <div className="mt-1 text-lg font-semibold">{value}</div>
    </div>
  );
}

function EmptyPanel({ copy }: { copy: string }) {
  return (
    <p className="rounded-[22px] border border-dashed border-border bg-background/25 p-5 text-sm leading-6 text-muted-foreground">
      {copy}
    </p>
  );
}

function normalizeScore(value?: number | null) {
  const numeric = Number(value || 0);
  if (!Number.isFinite(numeric)) {
    return 0;
  }
  return Math.round(numeric <= 10 ? numeric * 10 : numeric);
}
