import { useEffect, useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { Panel, ScorePill } from "@/components/silicore/Panel";
import { Button } from "@/components/ui/button";
import {
  ArrowLeftRight,
  ArrowRight,
  GitCompareArrows,
  Minus,
  RefreshCcw,
  Sparkles,
  TrendingDown,
  TrendingUp,
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

  const selectedProjectLabel = session.data?.project_options?.find((option) => option.value === activeProjectId)?.label || "Select project";
  const selectedRunA = runs.find((run) => run.run_id === runAId);
  const selectedRunB = runs.find((run) => run.run_id === runBId);
  const scoreDelta = (compare.data?.run_b.score || 0) - (compare.data?.run_a.score || 0);
  const issueDelta = (compare.data?.run_b.issues || 0) - (compare.data?.run_a.issues || 0);
  const strongestCategoryShift = [...(compare.data?.categories || [])].sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))[0];

  const swapRuns = () => {
    setRunAId(runBId);
    setRunBId(runAId);
  };

  return (
    <AppShell title="Compare revisions">
      <div className="space-y-6">
        <section className="relative overflow-hidden rounded-[28px] border border-border bg-[radial-gradient(circle_at_top_left,_rgba(86,211,240,0.16),_transparent_34%),linear-gradient(180deg,_rgba(12,20,31,0.98),_rgba(11,17,26,0.96))] p-8">
          <div className="absolute inset-y-0 right-0 hidden w-1/3 bg-[linear-gradient(180deg,transparent,rgba(86,211,240,0.04),transparent)] lg:block" />
          <div className="relative grid gap-8 lg:grid-cols-[1.25fr_0.75fr]">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-3 py-1 font-mono text-[10px] uppercase tracking-[0.22em] text-primary">
                <GitCompareArrows className="h-3.5 w-3.5" />
                Revision intelligence
              </div>
              <h2 className="mt-5 max-w-2xl text-4xl font-semibold tracking-tight text-foreground">Compare two Silicore runs side by side and see what actually moved.</h2>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">
                Pick a workspace, choose a baseline and a candidate run, and Silicore will summarize score shifts, issue movement, and the most meaningful engineering differences.
              </p>

              <div className="mt-8 grid gap-3 sm:grid-cols-3">
                <HeroStat label="Selected workspace" value={selectedProjectLabel} />
                <HeroStat label="Score delta" value={`${scoreDelta > 0 ? "+" : ""}${scoreDelta.toFixed(1)}`} tone={scoreDelta > 0 ? "success" : scoreDelta < 0 ? "danger" : "muted"} />
                <HeroStat label="Issue delta" value={`${issueDelta > 0 ? "+" : ""}${issueDelta}`} tone={issueDelta < 0 ? "success" : issueDelta > 0 ? "danger" : "muted"} />
              </div>
            </div>

            <div className="rounded-[24px] border border-white/10 bg-black/20 p-5 backdrop-blur-sm">
              <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-muted-foreground">Quick read</div>
              <div className="mt-4 space-y-3">
                <InsightRow
                  label="Better score"
                  value={scoreDelta > 0 ? compare.data?.run_b.name || "Candidate" : scoreDelta < 0 ? compare.data?.run_a.name || "Baseline" : "No change"}
                />
                <InsightRow
                  label="Cleaner issue count"
                  value={issueDelta < 0 ? compare.data?.run_b.name || "Candidate" : issueDelta > 0 ? compare.data?.run_a.name || "Baseline" : "No change"}
                />
                <InsightRow
                  label="Biggest category shift"
                  value={strongestCategoryShift ? `${strongestCategoryShift.name} (${strongestCategoryShift.delta > 0 ? "+" : ""}${strongestCategoryShift.delta})` : "Not enough run data yet"}
                />
              </div>
            </div>
          </div>
        </section>

        <div className="grid gap-6 xl:grid-cols-[360px_1fr]">
          <Panel title="Comparison setup" action={<Button size="sm" variant="ghost" className="rounded-full" onClick={() => void compare.reload()}><RefreshCcw className="mr-1.5 h-3.5 w-3.5" /> Refresh</Button>}>
            <div className="space-y-5">
              <Field label="Workspace">
                <select value={activeProjectId} onChange={(event) => { setProjectId(event.target.value); setRunAId(""); setRunBId(""); }} className="h-11 w-full rounded-xl border border-input bg-transparent px-3 text-sm">
                  {(session.data?.project_options || []).map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </Field>

              <Field label="Baseline run">
                <select value={runAId} onChange={(event) => setRunAId(event.target.value)} className="h-11 w-full rounded-xl border border-input bg-transparent px-3 text-sm">
                  {runs.map((run) => (
                    <option key={run.run_id} value={run.run_id}>{run.name || run.run_id}</option>
                  ))}
                </select>
              </Field>

              <div className="flex justify-center">
                <Button type="button" variant="ghost" className="rounded-full" onClick={swapRuns}>
                  <ArrowLeftRight className="mr-1.5 h-3.5 w-3.5" /> Swap runs
                </Button>
              </div>

              <Field label="Candidate run">
                <select value={runBId} onChange={(event) => setRunBId(event.target.value)} className="h-11 w-full rounded-xl border border-input bg-transparent px-3 text-sm">
                  {runs.map((run) => (
                    <option key={run.run_id} value={run.run_id}>{run.name || run.run_id}</option>
                  ))}
                </select>
              </Field>

              <div className="rounded-2xl border border-border bg-background/40 p-4 text-sm text-muted-foreground">
                Choose two runs from the same workspace. Silicore compares the earlier snapshot as the baseline and the later one as the candidate.
              </div>
            </div>
          </Panel>

          <div className="space-y-6">
            {compare.error ? <div className="rounded-xl border border-danger/20 bg-danger/10 px-4 py-3 text-sm text-danger">{compare.error}</div> : null}

            <div className="grid gap-4 lg:grid-cols-[1fr_auto_1fr]">
              <RevisionCard title="Baseline" run={selectedRunA} compareRun={compare.data?.run_a} />
              <div className="hidden h-12 w-12 items-center justify-center rounded-full border border-border bg-surface lg:flex">
                <ArrowRight className="h-5 w-5 text-primary" />
              </div>
              <RevisionCard title="Candidate" run={selectedRunB} compareRun={compare.data?.run_b} highlight />
            </div>

            <Panel title="Run selector">
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {runs.map((run) => {
                  const state = run.run_id === runAId ? "baseline" : run.run_id === runBId ? "candidate" : "idle";
                  return (
                    <button
                      key={run.run_id}
                      onClick={() => {
                        if (!runAId || run.run_id === runBId) {
                          setRunAId(run.run_id);
                          return;
                        }
                        setRunBId(run.run_id);
                      }}
                      className={`rounded-2xl border p-4 text-left transition-colors ${
                        state === "baseline"
                          ? "border-primary/40 bg-primary/8"
                          : state === "candidate"
                            ? "border-success/30 bg-success/8"
                            : "border-border bg-background/40 hover:border-primary/25"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{state === "idle" ? run.run_type || "run" : state}</div>
                        <ScorePill score={normalizeScore(run.score)} />
                      </div>
                      <div className="mt-3 line-clamp-2 text-sm font-medium">{run.name || run.run_id}</div>
                      <div className="mt-2 flex flex-wrap gap-3 font-mono text-[11px] text-muted-foreground">
                        <span>{run.critical_count || 0} critical</span>
                        <span>{run.risk_count || 0} issues</span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </Panel>

            <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
              <Panel title={`Category movement · ${compare.data?.project.name || selectedProjectLabel}`}>
                {(compare.data?.categories || []).length ? (
                  <div className="space-y-5">
                    {(compare.data?.categories || []).map((item) => (
                      <div key={item.name}>
                        <div className="mb-1.5 flex items-center justify-between text-sm">
                          <span>{item.name}</span>
                          <div className="flex items-center gap-3 font-mono text-xs">
                            <span className="text-muted-foreground">{item.before}</span>
                            <ArrowRight className="h-3 w-3 text-muted-foreground" />
                            <span className="text-foreground">{item.after}</span>
                            <span className={`w-10 text-right ${item.delta > 0 ? "text-success" : item.delta < 0 ? "text-danger" : "text-muted-foreground"}`}>
                              {item.delta > 0 ? "+" : ""}{item.delta}
                            </span>
                          </div>
                        </div>
                        <div className="relative h-2 overflow-hidden rounded-full bg-muted">
                          <div className="absolute inset-y-0 left-0 rounded-full bg-white/20" style={{ width: `${Math.max(item.before, 3)}%` }} />
                          <div className={`absolute inset-y-0 left-0 rounded-full ${item.delta >= 0 ? "bg-primary" : "bg-danger"}`} style={{ width: `${Math.max(item.after, 3)}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <EmptyPanel copy="These runs do not currently expose category deltas. Compare two richer analysis runs to see domain-level movement here." />
                )}
              </Panel>

              <Panel title="Decision pulse" action={<Sparkles className="h-4 w-4 text-primary" />}>
                <div className="space-y-3">
                  <DecisionCard
                    label="Score movement"
                    value={`${scoreDelta > 0 ? "+" : ""}${scoreDelta.toFixed(1)}`}
                    tone={scoreDelta > 0 ? "success" : scoreDelta < 0 ? "danger" : "muted"}
                    copy={scoreDelta > 0 ? "Candidate run improved the engineering score." : scoreDelta < 0 ? "Candidate run regressed versus baseline." : "No score change between selected runs."}
                  />
                  <DecisionCard
                    label="Issue movement"
                    value={`${issueDelta > 0 ? "+" : ""}${issueDelta}`}
                    tone={issueDelta < 0 ? "success" : issueDelta > 0 ? "danger" : "muted"}
                    copy={issueDelta < 0 ? "Candidate run resolved issues overall." : issueDelta > 0 ? "Candidate run added net-new issue pressure." : "No issue-count change between selected runs."}
                  />
                </div>
              </Panel>
            </div>

            <Panel title="What changed and why it matters">
              <div className="space-y-2">
                {(compare.data?.changes || []).map((change) => <ChangeRow key={`${change.kind}-${change.title}`} {...change} />)}
                {!compare.data?.changes?.length ? (
                  <EmptyPanel copy="Silicore didn’t generate a distinct change list for these runs yet. Try choosing runs with richer risk snapshots or more different analysis outcomes." />
                ) : null}
              </div>
            </Panel>
          </div>
        </div>
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
    <div className={`rounded-[24px] border bg-surface p-6 ${highlight ? "border-primary/40 shadow-[0_0_0_1px_oklch(0.85_0.16_195_/_0.2)]" : "border-border"}`}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground">{title}</div>
          <div className="mt-2 text-xl font-semibold leading-tight">{compareRun?.name || run?.name || "Select a run"}</div>
          <div className="mt-2 font-mono text-[11px] text-muted-foreground">{run?.created_at || "No timestamp"}</div>
        </div>
        <ScorePill score={score} />
      </div>

      <div className="mt-6 grid grid-cols-3 gap-3">
        <MiniStat label="Score" value={String(score)} />
        <MiniStat label="Issues" value={String(compareRun?.issues ?? run?.risk_count ?? 0)} />
        <MiniStat label="Critical" value={String(run?.critical_count ?? 0)} />
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
    <div className="flex items-start gap-4 rounded-2xl border border-border bg-background/40 p-4">
      <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border ${cls}`}><Icon className="h-4 w-4" /></span>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded border border-border px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</span>
          <span className="text-sm font-medium">{title}</span>
        </div>
        <div className="mt-1 text-xs text-muted-foreground">{why}</div>
      </div>
      <span className="shrink-0 rounded-full border border-border px-2 py-1 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{impact}</span>
    </div>
  );
}

function HeroStat({ label, value, tone }: { label: string; value: string; tone?: "success" | "danger" | "muted" }) {
  const toneClass = tone === "success" ? "text-success" : tone === "danger" ? "text-danger" : "text-foreground";
  return (
    <div className="rounded-2xl border border-white/10 bg-black/20 p-4 backdrop-blur-sm">
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{label}</div>
      <div className={`mt-2 line-clamp-2 text-lg font-semibold ${toneClass}`}>{value}</div>
    </div>
  );
}

function InsightRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-border/60 bg-background/30 p-3">
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{label}</div>
      <div className="mt-1 text-sm">{value}</div>
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

function DecisionCard({ label, value, copy, tone }: { label: string; value: string; copy: string; tone: "success" | "danger" | "muted" }) {
  const toneClass = tone === "success" ? "text-success" : tone === "danger" ? "text-danger" : "text-foreground";
  return (
    <div className="rounded-2xl border border-border bg-background/40 p-4">
      <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className={`mt-2 text-3xl font-semibold ${toneClass}`}>{value}</div>
      <div className="mt-2 text-sm text-muted-foreground">{copy}</div>
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-background/40 p-3">
      <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className="mt-1 text-lg font-semibold">{value}</div>
    </div>
  );
}

function EmptyPanel({ copy }: { copy: string }) {
  return <p className="rounded-2xl border border-dashed border-border bg-background/30 p-5 text-sm text-muted-foreground">{copy}</p>;
}

function normalizeScore(value?: number | null) {
  const numeric = Number(value || 0);
  if (!Number.isFinite(numeric)) {
    return 0;
  }
  return Math.round(numeric <= 10 ? numeric * 10 : numeric);
}
