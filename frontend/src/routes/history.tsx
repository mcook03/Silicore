import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { Panel, ScorePill } from "@/components/silicore/Panel";
import { useApiData } from "@/lib/api";

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
        <Panel title="Analysis log">
          {error ? (
            <p className="text-sm text-danger">{error}</p>
          ) : (
            <div className="-mx-6 overflow-x-auto">
              <table className="w-full text-sm">
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
