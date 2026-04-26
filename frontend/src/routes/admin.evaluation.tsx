import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { Panel } from "@/components/silicore/Panel";
import { TrendingUp, Target } from "lucide-react";

export const Route = createFileRoute("/admin/evaluation")({
  head: () => ({ meta: [{ title: "Evaluation — Silicore" }] }),
  component: Evaluation,
});

const suites = [
  { name: "DFM rule pack", precision: 0.94, recall: 0.88, f1: 0.91, runs: 218 },
  { name: "Signal integrity", precision: 0.89, recall: 0.83, f1: 0.86, runs: 174 },
  { name: "Thermal", precision: 0.96, recall: 0.79, f1: 0.87, runs: 142 },
  { name: "EMI / EMC", precision: 0.81, recall: 0.86, f1: 0.83, runs: 96 },
  { name: "BOM sourcing", precision: 0.92, recall: 0.91, f1: 0.91, runs: 203 },
];

function Evaluation() {
  return (
    <AppShell title="Evaluation">
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-medium tracking-tight">Rule-pack quality</h2>
          <p className="mt-1 text-sm text-muted-foreground">Latest evaluation against the labeled benchmark set.</p>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <Stat label="Avg precision" value="0.90" icon={Target} />
          <Stat label="Avg recall" value="0.85" icon={TrendingUp} />
          <Stat label="Avg F1" value="0.88" icon={Target} />
        </div>

        <Panel title="Per rule-pack">
          <div className="overflow-hidden rounded-xl border border-border">
            <table className="w-full text-sm">
              <thead className="bg-background/40 text-left font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th className="px-4 py-3">Rule pack</th>
                  <th className="px-4 py-3">Precision</th>
                  <th className="px-4 py-3">Recall</th>
                  <th className="px-4 py-3">F1</th>
                  <th className="px-4 py-3">Runs</th>
                </tr>
              </thead>
              <tbody>
                {suites.map((s) => (
                  <tr key={s.name} className="border-t border-border hover:bg-background/40">
                    <td className="px-4 py-3">{s.name}</td>
                    <td className="px-4 py-3 font-mono text-xs">{s.precision.toFixed(2)}</td>
                    <td className="px-4 py-3 font-mono text-xs">{s.recall.toFixed(2)}</td>
                    <td className="px-4 py-3 font-mono text-xs">{s.f1.toFixed(2)}</td>
                    <td className="px-4 py-3 font-mono text-xs text-muted-foreground">{s.runs}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      </div>
    </AppShell>
  );
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
