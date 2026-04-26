import { useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { Panel, ScorePill } from "@/components/silicore/Panel";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ArrowRight, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { useApiData } from "@/lib/api";

export const Route = createFileRoute("/compare")({
  head: () => ({ meta: [{ title: "Compare revisions — Silicore" }] }),
  component: Compare,
});

type SessionPayload = {
  project_options: Array<{ value: string; label: string }>;
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
  const activeProjectId = projectId || defaultProject;
  const compare = useApiData<ComparePayload>(activeProjectId ? `/api/frontend/compare?project_id=${encodeURIComponent(activeProjectId)}` : "/api/frontend/compare");

  const selectedLabel = useMemo(
    () => session.data?.project_options.find((option) => option.value === activeProjectId)?.label || "Select project",
    [session.data, activeProjectId],
  );

  return (
    <AppShell title="Compare revisions">
      <div className="space-y-6">
        <Panel title="Comparison target" action={<Button size="sm" variant="ghost" className="rounded-full" onClick={() => void compare.reload()}>Refresh</Button>}>
          <div className="grid gap-3 md:grid-cols-[1fr_180px]">
            <div>
              <div className="mb-2 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">Project</div>
              <div className="grid gap-2 sm:grid-cols-2">
                {(session.data?.project_options || []).map((option) => (
                  <button key={option.value} onClick={() => setProjectId(option.value)} className={`rounded-xl border px-4 py-3 text-left text-sm ${activeProjectId === option.value ? "border-primary/40 bg-primary/5" : "border-border bg-background/40"}`}>
                    {option.label}
                  </button>
                ))}
                {!session.data?.project_options?.length ? <Input value={selectedLabel} readOnly /> : null}
              </div>
            </div>
          </div>
        </Panel>

        {compare.error ? <div className="rounded-xl border border-danger/20 bg-danger/10 px-4 py-3 text-sm text-danger">{compare.error}</div> : null}

        {compare.data ? (
          <>
            <div className="grid items-center gap-4 lg:grid-cols-[1fr_auto_1fr]">
              <RevCard rev={compare.data.run_a} />
              <div className="hidden h-12 w-12 items-center justify-center rounded-full border border-border bg-surface lg:flex">
                <ArrowRight className="h-5 w-5 text-primary" />
              </div>
              <RevCard rev={compare.data.run_b} highlight />
            </div>

            <Panel title={`Category changes · ${compare.data.project.name}`}>
              <div className="space-y-5">
                {compare.data.categories.map((item) => (
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
                    <div className="relative h-1.5 overflow-hidden rounded-full bg-muted">
                      <div className="absolute inset-y-0 left-0 rounded-full bg-muted-foreground/40" style={{ width: `${item.before}%` }} />
                      <div className="absolute inset-y-0 left-0 rounded-full bg-primary" style={{ width: `${item.after}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </Panel>

            <Panel title="What changed and why it matters">
              <div className="space-y-2">
                {compare.data.changes.map((change) => <ChangeRow key={`${change.kind}-${change.title}`} {...change} />)}
                {!compare.data.changes.length ? <p className="text-sm text-muted-foreground">No distinct change items were generated for the selected runs.</p> : null}
              </div>
            </Panel>
          </>
        ) : null}
      </div>
    </AppShell>
  );
}

function RevCard({ rev, highlight }: { rev: ComparePayload["run_a"]; highlight?: boolean }) {
  return (
    <div className={`rounded-2xl border bg-surface p-6 ${highlight ? "border-primary/40 shadow-[0_0_0_1px_oklch(0.85_0.16_195_/_0.2)]" : "border-border"}`}>
      <div className="flex items-center justify-between">
        <div>
          <div className="font-mono text-xs uppercase tracking-wider text-muted-foreground">run</div>
          <div className="mt-1 text-2xl font-semibold">{rev.name}</div>
        </div>
        <ScorePill score={rev.score} />
      </div>
      <div className="mt-6 flex items-center gap-6 text-sm">
        <div>
          <div className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground">issues</div>
          <div className="text-xl font-medium">{rev.issues}</div>
        </div>
        <div>
          <div className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground">score</div>
          <div className="text-xl font-medium">{rev.score}</div>
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
    <div className="flex items-start gap-4 rounded-xl border border-border bg-background/40 p-4">
      <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-md border ${cls}`}><Icon className="h-4 w-4" /></span>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded border border-border px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</span>
          <span className="text-sm font-medium">{title}</span>
        </div>
        <div className="mt-1 text-xs text-muted-foreground">{why}</div>
      </div>
      <span className="shrink-0 font-mono text-xs text-muted-foreground">{impact}</span>
    </div>
  );
}
