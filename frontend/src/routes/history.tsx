import { createFileRoute, Link } from "@tanstack/react-router";
import type { ReactNode } from "react";
import { AppShell } from "@/components/silicore/AppShell";
import { ScorePill } from "@/components/silicore/Panel";
import { useApiData } from "@/lib/api";
import { History as HistoryIcon } from "lucide-react";

export const Route = createFileRoute("/history")({
  head: () => ({ meta: [{ title: "History — Silicore" }] }),
  component: History,
});

type HistoryRun = {
  name: string;
  created_at?: string;
  result?: { score?: number };
  risk_count?: number;
  critical_count?: number;
  preview?: string;
};

type HistoryPayload = {
  runs: HistoryRun[];
  summary: { total_runs: number; total_files: number };
};

function History() {
  const { data, error } = useApiData<HistoryPayload>("/api/frontend/history");
  return (
    <AppShell title="History">
      <div className="space-y-6">
        <section
          data-reveal
          className="relative overflow-hidden rounded-[30px] border border-border/80 bg-[linear-gradient(180deg,rgba(7,15,24,0.98),rgba(8,17,27,0.94))] px-6 py-7 sm:px-8 sm:py-8"
        >
          <div className="pointer-events-none absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-primary/8 to-transparent" />
          <div className="relative flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
            <div className="max-w-3xl">
              <div className="section-eyebrow">
                <HistoryIcon className="h-3.5 w-3.5" />
                Analysis archive
              </div>
              <h2 className="mt-5 text-4xl font-semibold tracking-tight text-foreground sm:text-[3.2rem] sm:leading-[1.02]">
                Revisit prior analyses like a clean engineering ledger, not a leftover file table.
              </h2>
              <p className="mt-4 text-base leading-8 text-muted-foreground">
                History should help you scan outcomes, compare moments in time, and jump back into detail without the page feeling like an admin afterthought.
              </p>
            </div>
            <div className="flex flex-wrap gap-x-8 gap-y-3 border-t border-white/8 pt-4 xl:border-t-0 xl:pt-0">
              <HistoryMetric label="Runs" value={String(data?.summary.total_runs ?? 0)} />
              <HistoryMetric label="Files" value={String(data?.summary.total_files ?? 0)} />
            </div>
          </div>
        </section>

        <HistoryStage title="Analysis log" rail="run archive" subtitle="Every recorded run, sorted into a cleaner review-friendly table.">
          {error ? (
            <p className="text-sm text-danger">{error}</p>
          ) : (
            <div className="-mx-6 overflow-x-auto">
              <table className="premium-table w-full text-sm">
                <thead>
                  <tr className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
                    <th className="px-6 py-3 text-left font-normal">Run</th>
                    <th className="px-6 py-3 text-left font-normal">Created</th>
                    <th className="px-6 py-3 text-left font-normal">Score</th>
                    <th className="px-6 py-3 text-left font-normal">Risks</th>
                    <th className="px-6 py-3 text-left font-normal">Critical</th>
                    <th className="px-6 py-3 text-left font-normal"></th>
                  </tr>
                </thead>
                <tbody>
                  {(data?.runs ?? []).map((run) => (
                    <tr key={run.name} className="border-t border-border/60 hover:bg-surface/50">
                      <td className="px-6 py-3.5 font-medium">{run.name}</td>
                      <td className="px-6 py-3.5 font-mono text-xs text-muted-foreground">{run.created_at || "—"}</td>
                      <td className="px-6 py-3.5"><ScorePill score={Math.round(Number(run.result?.score || 0))} /></td>
                      <td className="px-6 py-3.5 text-muted-foreground">{run.risk_count || 0}</td>
                      <td className="px-6 py-3.5 text-muted-foreground">{run.critical_count || 0}</td>
                      <td className="px-6 py-3.5 text-right">
                        <Link to="/history/$runDir" params={{ runDir: run.name }} className="text-xs text-primary hover:underline">open</Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </HistoryStage>
      </div>
    </AppShell>
  );
}

function HistoryMetric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{label}</div>
      <div className="mt-1 text-3xl font-semibold text-foreground">{value}</div>
    </div>
  );
}

function HistoryStage({
  title,
  rail,
  subtitle,
  children,
}: {
  title: string;
  rail?: string;
  subtitle?: string;
  children: ReactNode;
}) {
  return (
    <section data-reveal className="relative overflow-hidden rounded-[28px] border border-white/8 bg-[linear-gradient(150deg,rgba(8,17,27,0.96),rgba(7,14,22,0.98))] p-6 shadow-[0_28px_70px_-44px_rgba(0,0,0,0.92)]">
      <div className="mb-5 border-b border-white/8 pb-4">
        {rail ? <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{rail}</div> : null}
        <h3 className="mt-1 text-lg font-medium tracking-tight">{title}</h3>
        {subtitle ? <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p> : null}
      </div>
      {children}
    </section>
  );
}
