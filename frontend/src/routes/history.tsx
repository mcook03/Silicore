import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { PageHero } from "@/components/silicore/PageHero";
import { Panel, ScorePill } from "@/components/silicore/Panel";
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
        <PageHero
          eyebrow={<><HistoryIcon className="h-3.5 w-3.5" /> Analysis archive</>}
          title="Review the full run trail with enough clarity to revisit old decisions without losing context."
          description="History now feels like an audit-grade ledger instead of a simple file list, keeping score, risk, and critical counts visible at a glance."
          metrics={[
            { label: "Runs", value: String(data?.summary.total_runs ?? 0), copy: "Recorded analyses in the archive" },
            { label: "Files", value: String(data?.summary.total_files ?? 0), copy: "Artifacts tracked alongside runs" },
          ]}
        />

        <Panel title="Analysis log" subtitle="Every recorded run, sorted into a cleaner review-friendly table.">
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
        </Panel>
      </div>
    </AppShell>
  );
}
