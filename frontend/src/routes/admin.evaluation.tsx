import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { Panel } from "@/components/silicore/Panel";
import { TrendingUp, Target } from "lucide-react";
import { useApiData } from "@/lib/api";

export const Route = createFileRoute("/admin/evaluation")({
  head: () => ({ meta: [{ title: "Evaluation — Silicore" }] }),
  component: Evaluation,
});

type EvaluationBoard = {
  board_name?: string;
  precision?: number;
  recall?: number;
  f1?: number;
  fixture_count?: number;
  score?: number;
};

type EvaluationPayload = {
  scope?: string;
  fixture_count?: number;
  boards?: EvaluationBoard[];
  history_summary?: {
    total_runs?: number;
    fixture_runs?: number;
    external_runs?: number;
  };
};

function Evaluation() {
  const [scope, setScope] = useState<"fixtures" | "external">("fixtures");
  const { data, error, reload } = useApiData<EvaluationPayload>(`/api/frontend/admin/evaluation?scope=${scope}`);
  const boards = data?.boards || [];
  const averages = averageMetrics(boards);

  return (
    <AppShell title="Evaluation">
      <div className="space-y-6">
        <div className="flex items-end justify-between gap-3">
          <div>
            <h2 className="text-xl font-medium tracking-tight">Rule-pack quality</h2>
            <p className="mt-1 text-sm text-muted-foreground">Live evaluation data from Silicore fixture and external validation suites.</p>
          </div>
          <div className="flex gap-2">
            <button className={`rounded-full border px-3 py-1.5 text-sm ${scope === "fixtures" ? "border-primary/40 bg-primary/5" : "border-border"}`} onClick={() => setScope("fixtures")}>Fixtures</button>
            <button className={`rounded-full border px-3 py-1.5 text-sm ${scope === "external" ? "border-primary/40 bg-primary/5" : "border-border"}`} onClick={() => setScope("external")}>External</button>
            <button className="rounded-full border border-border px-3 py-1.5 text-sm" onClick={() => void reload()}>Refresh</button>
          </div>
        </div>

        {error ? <div className="rounded-xl border border-danger/20 bg-danger/10 px-4 py-3 text-sm text-danger">{error}</div> : null}

        <div className="grid gap-4 md:grid-cols-3">
          <Stat label="Avg precision" value={averages.precision.toFixed(2)} icon={Target} />
          <Stat label="Avg recall" value={averages.recall.toFixed(2)} icon={TrendingUp} />
          <Stat label="Avg F1" value={averages.f1.toFixed(2)} icon={Target} />
        </div>

        <Panel title="History summary">
          <div className="grid gap-3 md:grid-cols-3">
            <Meta label="Total runs" value={String(data?.history_summary?.total_runs ?? 0)} />
            <Meta label="Fixture runs" value={String(data?.history_summary?.fixture_runs ?? 0)} />
            <Meta label="External runs" value={String(data?.history_summary?.external_runs ?? 0)} />
          </div>
        </Panel>

        <Panel title="Per board / suite">
          <div className="overflow-hidden rounded-xl border border-border">
            <table className="w-full text-sm">
              <thead className="bg-background/40 text-left font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th className="px-4 py-3">Board</th>
                  <th className="px-4 py-3">Precision</th>
                  <th className="px-4 py-3">Recall</th>
                  <th className="px-4 py-3">F1</th>
                  <th className="px-4 py-3">Fixtures</th>
                </tr>
              </thead>
              <tbody>
                {boards.map((board, index) => (
                  <tr key={`${board.board_name}-${index}`} className="border-t border-border hover:bg-background/40">
                    <td className="px-4 py-3">{board.board_name || `Board ${index + 1}`}</td>
                    <td className="px-4 py-3 font-mono text-xs">{formatMetric(board.precision)}</td>
                    <td className="px-4 py-3 font-mono text-xs">{formatMetric(board.recall)}</td>
                    <td className="px-4 py-3 font-mono text-xs">{formatMetric(board.f1)}</td>
                    <td className="px-4 py-3 font-mono text-xs text-muted-foreground">{board.fixture_count ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!boards.length ? <div className="px-4 py-6 text-sm text-muted-foreground">No evaluation board rows are available for this scope.</div> : null}
          </div>
        </Panel>
      </div>
    </AppShell>
  );
}

function averageMetrics(boards: EvaluationBoard[]) {
  if (!boards.length) {
    return { precision: 0, recall: 0, f1: 0 };
  }
  const totals = boards.reduce(
    (acc, board) => ({
      precision: acc.precision + Number(board.precision || 0),
      recall: acc.recall + Number(board.recall || 0),
      f1: acc.f1 + Number(board.f1 || 0),
    }),
    { precision: 0, recall: 0, f1: 0 },
  );
  return {
    precision: totals.precision / boards.length,
    recall: totals.recall / boards.length,
    f1: totals.f1 / boards.length,
  };
}

function formatMetric(value?: number) {
  return typeof value === "number" ? value.toFixed(2) : "—";
}

function Stat({ label, value, icon: Icon }: { label: string; value: string; icon: typeof Target }) {
  return (
    <div className="rounded-2xl border border-border bg-surface p-5">
      <div className="flex items-center justify-between">
        <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</span>
        <Icon className="h-4 w-4 text-primary" />
      </div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
    </div>
  );
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-background/40 p-4">
      <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className="mt-1 font-mono text-sm">{value}</div>
    </div>
  );
}
