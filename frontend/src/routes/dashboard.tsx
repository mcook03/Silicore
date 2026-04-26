import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { ScoreRing } from "@/components/silicore/ScoreRing";
import { Panel, ScorePill } from "@/components/silicore/Panel";
import { Link } from "@tanstack/react-router";
import {
  LineChart, Line, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid, AreaChart, Area,
} from "recharts";
import { ArrowUpRight, CircuitBoard, TrendingUp, AlertTriangle } from "lucide-react";
import { BoardHeatmap } from "@/components/silicore/BoardHeatmap";
import { SeverityDonut, CategoryBreakdown } from "@/components/silicore/AnalysisCharts";

export const Route = createFileRoute("/dashboard")({
  head: () => ({ meta: [{ title: "Dashboard — Silicore" }] }),
  component: Dashboard,
});

const trend = Array.from({ length: 14 }, (_, i) => ({
  d: `D${i + 1}`,
  score: 60 + Math.round(Math.sin(i / 2) * 8 + i * 1.4),
  issues: 28 - i + (i % 3),
}));

const recent = [
  { name: "Sentinel Power Module", rev: "rev-c", score: 82, delta: "+9", issues: 14, status: "ready" },
  { name: "Halo Sensor Array", rev: "rev-a", score: 71, delta: "—", issues: 22, status: "ready" },
  { name: "Atlas RF Front-end", rev: "rev-b", score: 64, delta: "-3", issues: 31, status: "warn" },
  { name: "Nova MCU Carrier", rev: "rev-d", score: 91, delta: "+5", issues: 6, status: "ready" },
  { name: "Pulse Driver Board", rev: "rev-a", score: 58, delta: "—", issues: 38, status: "warn" },
];

function Dashboard() {
  return (
    <AppShell title="Dashboard">
      <div className="space-y-6">
        <div className="grid gap-4 lg:grid-cols-3">
          <div className="rounded-2xl border border-border bg-surface p-6 lg:row-span-2">
            <div className="flex items-start justify-between">
              <div>
                <div className="font-mono text-xs uppercase tracking-wider text-muted-foreground">Overall risk score</div>
                <div className="mt-1 text-sm text-muted-foreground">Across 12 active boards</div>
              </div>
              <span className="rounded-full border border-success/30 bg-success/10 px-2 py-0.5 font-mono text-xs text-success">+4.2</span>
            </div>
            <div className="mt-8 flex flex-col items-center">
              <ScoreRing score={78} size={180} />
              <div className="mt-4 text-center text-sm text-muted-foreground">
                Healthy. <span className="text-foreground">3 boards</span> need attention.
              </div>
            </div>
            <div className="mt-8 grid grid-cols-3 gap-4 border-t border-border pt-6 text-center">
              <Mini label="Critical" value="7" tone="danger" />
              <Mini label="Medium" value="24" tone="warning" />
              <Mini label="Low" value="61" tone="muted" />
            </div>
          </div>

          <KpiCard label="Boards analyzed" value="148" trend="+12 this week" icon={CircuitBoard} />
          <KpiCard label="Avg score 30d" value="74.6" trend="+3.1 vs prior" icon={TrendingUp} />
          <KpiCard label="Open critical issues" value="7" trend="-2 since Mon" icon={AlertTriangle} tone="danger" />
          <KpiCard label="Time saved est." value="42h" trend="vs manual review" icon={ArrowUpRight} />
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <Panel title="Score trend · 14 days">
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={trend}>
                <defs>
                  <linearGradient id="g1" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="oklch(0.85 0.16 195)" stopOpacity={0.45} />
                    <stop offset="100%" stopColor="oklch(0.85 0.16 195)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="oklch(0.28 0.014 250)" vertical={false} />
                <XAxis dataKey="d" stroke="oklch(0.55 0.018 250)" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="oklch(0.55 0.018 250)" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ background: "oklch(0.19 0.014 250)", border: "1px solid oklch(0.28 0.014 250)", borderRadius: 8, fontSize: 12 }} />
                <Area type="monotone" dataKey="score" stroke="oklch(0.85 0.16 195)" strokeWidth={2} fill="url(#g1)" />
              </AreaChart>
            </ResponsiveContainer>
          </Panel>
          <Panel title="Issues over time">
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={trend}>
                <CartesianGrid stroke="oklch(0.28 0.014 250)" vertical={false} />
                <XAxis dataKey="d" stroke="oklch(0.55 0.018 250)" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="oklch(0.55 0.018 250)" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ background: "oklch(0.19 0.014 250)", border: "1px solid oklch(0.28 0.014 250)", borderRadius: 8, fontSize: 12 }} />
                <Line type="monotone" dataKey="issues" stroke="oklch(0.82 0.16 75)" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </Panel>
        </div>

        <div className="grid gap-4 lg:grid-cols-[1fr_360px]">
          <BoardHeatmap title="Fleet hotspot map" cols={22} rows={10} />
          <Panel title="Severity mix · all boards">
            <SeverityDonut
              data={[
                { name: "critical", value: 7 },
                { name: "medium", value: 24 },
                { name: "low", value: 61 },
              ]}
            />
          </Panel>
        </div>

        <Panel title="Findings by category">
          <CategoryBreakdown
            data={[
              { category: "DFM", critical: 2, medium: 8, low: 18 },
              { category: "Signal", critical: 2, medium: 7, low: 14 },
              { category: "Thermal", critical: 1, medium: 4, low: 12 },
              { category: "EMI / EMC", critical: 2, medium: 3, low: 9 },
              { category: "BOM", critical: 0, medium: 2, low: 8 },
            ]}
          />
        </Panel>

        <Panel title="Recent analyses" action={<Link to="/history" className="font-mono text-xs text-primary hover:underline">view all →</Link>}>
          <div className="-mx-6 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
                  <th className="px-6 py-3 text-left font-normal">Board</th>
                  <th className="px-6 py-3 text-left font-normal">Revision</th>
                  <th className="px-6 py-3 text-left font-normal">Score</th>
                  <th className="px-6 py-3 text-left font-normal">Δ</th>
                  <th className="px-6 py-3 text-left font-normal">Issues</th>
                  <th className="px-6 py-3 text-left font-normal">Status</th>
                </tr>
              </thead>
              <tbody>
                {recent.map((r) => (
                  <tr key={r.name} className="border-t border-border/60 hover:bg-surface/50">
                    <td className="px-6 py-3.5 font-medium">{r.name}</td>
                    <td className="px-6 py-3.5 font-mono text-xs text-muted-foreground">{r.rev}</td>
                    <td className="px-6 py-3.5"><ScorePill score={r.score} /></td>
                    <td className={`px-6 py-3.5 font-mono text-xs ${r.delta.startsWith("+") ? "text-success" : r.delta.startsWith("-") ? "text-danger" : "text-muted-foreground"}`}>{r.delta}</td>
                    <td className="px-6 py-3.5 text-muted-foreground">{r.issues}</td>
                    <td className="px-6 py-3.5">
                      <span className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 font-mono text-[11px] ${r.status === "ready" ? "bg-success/10 text-success" : "bg-warning/10 text-warning"}`}>
                        <span className={`h-1.5 w-1.5 rounded-full ${r.status === "ready" ? "bg-success" : "bg-warning"}`} />
                        {r.status}
                      </span>
                    </td>
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

function KpiCard({ label, value, trend, icon: Icon, tone }: { label: string; value: string; trend: string; icon: React.ComponentType<{ className?: string }>; tone?: "danger" }) {
  return (
    <div className="rounded-2xl border border-border bg-surface p-6">
      <div className="flex items-center justify-between">
        <span className="font-mono text-xs uppercase tracking-wider text-muted-foreground">{label}</span>
        <Icon className={`h-4 w-4 ${tone === "danger" ? "text-danger" : "text-primary"}`} />
      </div>
      <div className="mt-4 text-3xl font-semibold">{value}</div>
      <div className="mt-1 text-xs text-muted-foreground">{trend}</div>
    </div>
  );
}

function Mini({ label, value, tone }: { label: string; value: string; tone: "danger" | "warning" | "muted" }) {
  const c = { danger: "text-danger", warning: "text-warning", muted: "text-muted-foreground" }[tone];
  return (
    <div>
      <div className={`text-xl font-semibold ${c}`}>{value}</div>
      <div className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground">{label}</div>
    </div>
  );
}

