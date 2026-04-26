import { useEffect, useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import type { ReactNode } from "react";
import { AppShell } from "@/components/silicore/AppShell";
import { ScorePill } from "@/components/silicore/Panel";
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
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useApiData } from "@/lib/api";

const transparentCursor = { fill: "transparent", stroke: "transparent" };

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
  summary?: string | null;
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

  const compareReadyRuns = useMemo(
    () =>
      runs.filter((run) => {
        const hasScore = run.score != null;
        const hasIssues = Number(run.risk_count || 0) > 0;
        const hasCritical = Number(run.critical_count || 0) > 0;
        const looksLikeAnalysis = run.run_type === "single" || Boolean(run.summary);
        return hasScore || hasIssues || hasCritical || looksLikeAnalysis;
      }),
    [runs],
  );

  const selectableRuns = compareReadyRuns.length >= 2 ? compareReadyRuns : runs;

  useEffect(() => {
    if (!selectableRuns.length) {
      return;
    }
    setRunBId((current) => {
      if (current && selectableRuns.some((run) => run.run_id === current)) {
        return current;
      }
      return selectableRuns[0]?.run_id || "";
    });
    setRunAId((current) => {
      if (current && selectableRuns.some((run) => run.run_id === current) && current !== (selectableRuns[0]?.run_id || "")) {
        return current;
      }
      return selectableRuns[1]?.run_id || selectableRuns[0]?.run_id || "";
    });
  }, [selectableRuns]);

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
  const selectedRunA = selectableRuns.find((run) => run.run_id === runAId);
  const selectedRunB = selectableRuns.find((run) => run.run_id === runBId);
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
  const trendData = useMemo(
    () =>
      [...selectableRuns]
        .slice(0, 6)
        .reverse()
        .map((run, index) => ({
          label: run.name?.slice(0, 14) || `R${index + 1}`,
          fullLabel: run.name || run.run_id,
          score: normalizeScore(run.score),
          issues: Number(run.risk_count || 0),
          critical: Number(run.critical_count || 0),
        })),
    [selectableRuns],
  );
  const categoryHeatmap = useMemo(
    () =>
      (compare.data?.categories || []).map((item) => ({
        category: item.name,
        baseline: item.before,
        candidate: item.after,
        delta: item.delta,
        intensity: Math.max(Math.abs(item.delta), item.before, item.after),
      })),
    [compare.data?.categories],
  );
  const changeMix = useMemo(
    () => [
      { name: "Resolved", value: improvements, fill: "oklch(0.76 0.16 160)" },
      { name: "Regressed", value: regressions, fill: "oklch(0.68 0.2 24)" },
      { name: "New", value: neutralChanges, fill: "oklch(0.8 0.14 82)" },
    ],
    [improvements, regressions, neutralChanges],
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
          <CompareStage
            title="Comparison setup"
            rail="selection rail"
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
                    {selectableRuns.map((run) => (
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
                    {selectableRuns.map((run) => (
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
                    Compare now prioritizes runs that actually contain analyzable score/risk data so the page doesn’t silently land on empty batch shells.
                  </span>
                </div>
              </div>
            </div>
          </CompareStage>

          <CompareStage title="Run library" rail="workspace runs" action={<Sparkles className="h-4 w-4 text-primary" />}>
            {selectableRuns.length < 2 ? (
              <EmptyPanel copy="This workspace needs at least two comparable analysis runs before Silicore can produce a meaningful revision comparison." />
            ) : (
            <div className="grid gap-3 sm:grid-cols-2">
              {selectableRuns.map((run) => {
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
            )}
          </CompareStage>
        </section>

        <section className="grid gap-6 xl:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)]">
          <CompareStage title="Revision trendline" rail="time motion" action={<span className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Last 6 runs</span>}>
            {trendData.length ? (
              <div className="space-y-4">
                <div className="h-[280px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={trendData} margin={{ top: 10, right: 10, left: -18, bottom: 0 }}>
                      <CartesianGrid stroke="rgba(148, 163, 184, 0.14)" vertical={false} />
                      <XAxis dataKey="label" tickLine={false} axisLine={false} fontSize={11} stroke="rgba(148, 163, 184, 0.8)" />
                      <YAxis yAxisId="score" domain={[0, 100]} tickLine={false} axisLine={false} fontSize={11} stroke="rgba(148, 163, 184, 0.8)" />
                      <YAxis yAxisId="issues" orientation="right" tickLine={false} axisLine={false} fontSize={11} stroke="rgba(148, 163, 184, 0.45)" />
                      <Tooltip cursor={transparentCursor} content={<TrendTooltip />} />
                      <Line yAxisId="score" type="monotone" dataKey="score" stroke="oklch(0.84 0.15 205)" strokeWidth={3} dot={{ r: 3, fill: "oklch(0.84 0.15 205)" }} activeDot={{ r: 5 }} />
                      <Line yAxisId="issues" type="monotone" dataKey="issues" stroke="oklch(0.76 0.15 76)" strokeWidth={2} dot={{ r: 0 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
                <div className="grid gap-3 sm:grid-cols-3">
                  <MiniStat label="Latest score" value={String(trendData[trendData.length - 1]?.score ?? 0)} />
                  <MiniStat label="Latest issues" value={String(trendData[trendData.length - 1]?.issues ?? 0)} />
                  <MiniStat label="Latest critical" value={String(trendData[trendData.length - 1]?.critical ?? 0)} />
                </div>
              </div>
            ) : (
              <EmptyPanel copy="There are not enough runs in this workspace yet to render a score and findings trendline." />
            )}
          </CompareStage>

          <CompareStage title="Change mix and issue pressure" rail="pressure model">
            <div className="grid gap-4 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
              <div className="rounded-[22px] border border-border bg-background/25 p-4">
                <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Outcome mix</div>
                <div className="mt-4 h-[240px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={changeMix} margin={{ top: 10, right: 10, left: -18, bottom: 0 }}>
                      <CartesianGrid stroke="rgba(148, 163, 184, 0.12)" vertical={false} />
                      <XAxis dataKey="name" tickLine={false} axisLine={false} fontSize={11} stroke="rgba(148, 163, 184, 0.8)" />
                      <YAxis tickLine={false} axisLine={false} fontSize={11} stroke="rgba(148, 163, 184, 0.8)" allowDecimals={false} />
                      <Tooltip cursor={transparentCursor} content={<MixTooltip />} />
                      <Bar dataKey="value" radius={[8, 8, 0, 0]} activeBar={{ stroke: "rgba(255,255,255,0.72)", strokeWidth: 1.4, fillOpacity: 1, filter: "drop-shadow(0 0 10px rgba(86,211,240,0.3))" }}>
                        {changeMix.map((entry) => (
                          <Cell key={entry.name} fill={entry.fill} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="rounded-[22px] border border-border bg-background/25 p-4">
                <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Run pressure snapshot</div>
                <div className="mt-4 space-y-3">
                  <PressureMeter
                    label="Baseline pressure"
                    value={compare.data?.run_a.issues || 0}
                    max={Math.max(compare.data?.run_a.issues || 0, compare.data?.run_b.issues || 0, 1)}
                    tone="baseline"
                  />
                  <PressureMeter
                    label="Candidate pressure"
                    value={compare.data?.run_b.issues || 0}
                    max={Math.max(compare.data?.run_a.issues || 0, compare.data?.run_b.issues || 0, 1)}
                    tone="candidate"
                  />
                  <PressureMeter
                    label="Risk shift"
                    value={Math.abs(issueDelta)}
                    max={Math.max(Math.abs(issueDelta), 1)}
                    tone={issueDelta <= 0 ? "candidate" : "danger"}
                    suffix={issueDelta === 0 ? "stable" : issueDelta < 0 ? "improved" : "higher"}
                  />
                </div>
              </div>
            </div>
          </CompareStage>
        </section>

        {compare.error ? (
          <div className="rounded-2xl border border-danger/20 bg-danger/10 px-4 py-3 text-sm text-danger">{compare.error}</div>
        ) : null}

        <section className="grid gap-6 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
          <CompareStage title={`Category movement · ${compare.data?.project.name || selectedProjectLabel}`} rail="delta surface">
            {(compare.data?.categories || []).length ? (
              <div className="space-y-5">
                <CategoryHeatmap rows={categoryHeatmap} scale={categoryScale} />
                <div className="space-y-4">
                  {(compare.data?.categories || []).map((item) => (
                    <CategoryRow key={item.name} item={item} scale={categoryScale} />
                  ))}
                </div>
              </div>
            ) : (
              <EmptyPanel copy="These runs do not currently expose category deltas. Compare two richer analysis runs to see domain-level movement here." />
            )}
          </CompareStage>

          <CompareStage title="Difference digest" rail="decision digest">
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
          </CompareStage>
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

function CompareStage({
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
    <section data-reveal className="relative overflow-hidden rounded-[30px] border border-white/8 bg-[linear-gradient(160deg,rgba(8,16,26,0.96),rgba(7,14,22,0.98))] p-6 shadow-[0_28px_72px_-46px_rgba(0,0,0,0.9)]">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/60 to-transparent" />
      <div className="relative">
        <div className="mb-5 flex items-start justify-between gap-4">
          <div>
            {rail ? <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{rail}</div> : null}
            <h3 className="mt-1 text-lg font-medium tracking-tight">{title}</h3>
          </div>
          {action}
        </div>
        {children}
      </div>
    </section>
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

function CategoryHeatmap({
  rows,
  scale,
}: {
  rows: Array<{ category: string; baseline: number; candidate: number; delta: number; intensity: number }>;
  scale: number;
}) {
  return (
    <div className="rounded-[22px] border border-border bg-background/20 p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Delta heat map</div>
          <div className="mt-1 text-sm text-muted-foreground">Each row shows baseline, candidate, and delta intensity for a category.</div>
        </div>
        <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
          <span>cool</span>
          <div className="h-2 w-24 rounded-full bg-[linear-gradient(90deg,oklch(0.76_0.16_160),oklch(0.82_0.15_205),oklch(0.74_0.18_80),oklch(0.68_0.2_24))]" />
          <span>hot</span>
        </div>
      </div>
      <div className="mt-4 space-y-2">
        {rows.map((row) => (
          <div key={row.category} className="grid grid-cols-[minmax(0,1.2fr)_72px_72px_72px] items-center gap-2">
            <div className="truncate pr-2 text-sm">{row.category}</div>
            <HeatCell label="Base" value={row.baseline} fill={heatColor(row.baseline, scale, "baseline")} />
            <HeatCell label="Cand" value={row.candidate} fill={heatColor(row.candidate, scale, "candidate")} />
            <HeatCell label="Delta" value={row.delta} fill={heatColor(Math.abs(row.delta), scale, row.delta < 0 ? "danger" : "delta")} prefix={row.delta > 0 ? "+" : ""} />
          </div>
        ))}
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

function TrendTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: { fullLabel: string; score: number; issues: number; critical: number } }> }) {
  if (!active || !payload?.length) {
    return null;
  }
  const point = payload[0]?.payload;
  return (
    <div className="rounded-xl border border-border bg-background/95 px-3 py-2 text-xs shadow-xl">
      <div className="max-w-[220px] break-words font-medium">{point.fullLabel}</div>
      <div className="mt-2 space-y-1 text-muted-foreground">
        <div>Score: <span className="text-foreground">{point.score}</span></div>
        <div>Issues: <span className="text-foreground">{point.issues}</span></div>
        <div>Critical: <span className="text-foreground">{point.critical}</span></div>
      </div>
    </div>
  );
}

function MixTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: { name: string; value: number } }> }) {
  if (!active || !payload?.length) {
    return null;
  }
  const point = payload[0]?.payload;
  return (
    <div className="rounded-xl border border-border bg-background/95 px-3 py-2 text-xs shadow-xl">
      <div className="font-medium">{point.name}</div>
      <div className="mt-1 text-muted-foreground">Count: <span className="text-foreground">{point.value}</span></div>
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

function HeatCell({
  label,
  value,
  fill,
  prefix = "",
}: {
  label: string;
  value: number;
  fill: string;
  prefix?: string;
}) {
  return (
    <div
      className="rounded-xl border border-white/8 px-2 py-2 text-center"
      style={{ background: fill }}
      title={`${label}: ${prefix}${value}`}
    >
      <div className="font-mono text-[9px] uppercase tracking-[0.16em] text-black/65">{label}</div>
      <div className="mt-1 text-sm font-semibold text-slate-950">
        {prefix}
        {value}
      </div>
    </div>
  );
}

function PressureMeter({
  label,
  value,
  max,
  tone,
  suffix,
}: {
  label: string;
  value: number;
  max: number;
  tone: "baseline" | "candidate" | "danger";
  suffix?: string;
}) {
  const width = `${Math.max(8, (value / Math.max(max, 1)) * 100)}%`;
  const fill =
    tone === "baseline"
      ? "linear-gradient(90deg, rgba(148,163,184,0.65), rgba(203,213,225,0.9))"
      : tone === "candidate"
        ? "linear-gradient(90deg, rgba(86,211,240,0.72), rgba(90,160,255,0.96))"
        : "linear-gradient(90deg, rgba(248,113,113,0.72), rgba(239,68,68,0.96))";
  return (
    <div className="rounded-[18px] border border-border bg-background/30 p-3">
      <div className="flex items-center justify-between gap-3">
        <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{label}</div>
        <div className="text-sm font-semibold">
          {value}
          {suffix ? <span className="ml-1 text-xs font-normal text-muted-foreground">{suffix}</span> : null}
        </div>
      </div>
      <div className="mt-3 h-3 rounded-full bg-muted/70">
        <div className="h-3 rounded-full" style={{ width, background: fill }} />
      </div>
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

function heatColor(value: number, scale: number, mode: "baseline" | "candidate" | "delta" | "danger") {
  const normalized = Math.max(0, Math.min(1, value / Math.max(scale, 1)));
  if (mode === "baseline") {
    return `oklch(${0.34 + normalized * 0.32} ${0.04 + normalized * 0.08} 245 / 0.92)`;
  }
  if (mode === "candidate") {
    return `oklch(${0.48 + normalized * 0.32} ${0.08 + normalized * 0.12} 202 / 0.96)`;
  }
  if (mode === "danger") {
    return `oklch(${0.64 + normalized * 0.1} ${0.14 + normalized * 0.08} 28 / 0.96)`;
  }
  return `oklch(${0.66 + normalized * 0.12} ${0.12 + normalized * 0.06} 88 / 0.96)`;
}
