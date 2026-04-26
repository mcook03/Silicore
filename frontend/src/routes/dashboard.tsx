import { createFileRoute, Link } from "@tanstack/react-router";
import { BoardHeatmap } from "@/components/silicore/BoardHeatmap";
import { ScoreRing } from "@/components/silicore/ScoreRing";
import { Panel, ScorePill } from "@/components/silicore/Panel";
import {
  LineChart, Line, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid, AreaChart, Area,
} from "recharts";
import { ArrowUpRight, CircuitBoard, TrendingUp, AlertTriangle } from "lucide-react";
import { AppShell } from "@/components/silicore/AppShell";
import { useApiData } from "@/lib/api";

const transparentCursor = { fill: "transparent", stroke: "transparent" };

export const Route = createFileRoute("/dashboard")({
  head: () => ({ meta: [{ title: "Dashboard — Silicore" }] }),
  component: Dashboard,
});

type DashboardPayload = {
  stats: {
    overall_score: number;
    score_change: number;
    critical_total: number;
    medium_total: number;
    low_total: number;
    boards_analyzed: number;
    avg_score_30d: number;
    open_critical_issues: number;
    issue_change: number;
  };
  trend: Array<{ label: string; score: number; issues: number; name: string; critical?: number; high?: number; medium?: number; low?: number }>;
  recent: Array<{ name: string; rev: string; score: number; delta: number | null; issues: number; status: string; run_dir: string }>;
  risk_heatmap?: Array<{
    category: string;
    total?: number;
    cells: Array<{ label?: string; value: number; tone: "none" | "light" | "medium" | "strong" }>;
  }>;
};

function Dashboard() {
  const { data, loading, error } = useApiData<DashboardPayload>("/api/frontend/dashboard");
  const trend = data?.trend ?? [];
  const recent = data?.recent ?? [];
  const stats = data?.stats;

  return (
    <AppShell title="Dashboard">
      {error ? (
        <Panel title="Dashboard unavailable">
          <p className="text-sm text-danger">{error}</p>
        </Panel>
      ) : (
        <div className="space-y-6">
          <section
            data-reveal
            className="relative overflow-hidden rounded-[36px] border border-border/80 bg-[radial-gradient(circle_at_18%_12%,rgba(96,240,198,0.14),transparent_18%),radial-gradient(circle_at_82%_14%,rgba(125,178,255,0.16),transparent_22%),linear-gradient(180deg,rgba(7,15,24,0.96),rgba(8,16,26,0.98))] px-6 py-7 sm:px-8 sm:py-9"
          >
            <div className="pointer-events-none absolute inset-0 opacity-60 [background-image:linear-gradient(to_right,rgba(255,255,255,0.035)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.025)_1px,transparent_1px)] [background-size:76px_76px]" />
            <div className="relative grid gap-8 xl:grid-cols-[minmax(0,1.25fr)_320px]">
              <div className="min-w-0">
                <div className="section-eyebrow">
                  <TrendingUp className="h-3.5 w-3.5" />
                  Mission control
                </div>
                <h2 className="mt-6 max-w-4xl text-4xl font-semibold tracking-tight text-foreground sm:text-5xl sm:leading-[1.02]">
                  Track design health, hotspot movement, and risk momentum without digging through raw runs.
                </h2>
                <p className="mt-5 max-w-3xl text-base leading-8 text-muted-foreground">
                  The dashboard should feel like a live engineering surface, not a stack of cards. This composition keeps the score center-stage while surfacing fleet pressure and recent activity in one glance.
                </p>

                <div className="mt-8 flex flex-wrap items-center gap-x-8 gap-y-4 border-t border-white/8 pt-5">
                  <HeroMetric label="Boards analyzed" value={String(stats?.boards_analyzed ?? 0)} />
                  <HeroMetric label="Overall score" value={String(Math.round(stats?.overall_score ?? 0))} />
                  <HeroMetric label="Open critical" value={String(stats?.open_critical_issues ?? 0)} tone="danger" />
                  <HeroMetric label="Average score" value={String(stats?.avg_score_30d ?? 0)} />
                </div>
              </div>

              <div className="relative flex min-h-[340px] items-center justify-center">
                <div className="absolute inset-x-12 top-4 h-24 rounded-full bg-primary/10 blur-3xl" />
                <div className="absolute left-0 top-10 h-px w-24 bg-gradient-to-r from-transparent via-primary/60 to-transparent" />
                <div className="absolute right-0 bottom-12 h-px w-28 bg-gradient-to-r from-transparent via-success/60 to-transparent" />
                <div className="relative">
                  <div className="absolute inset-[-20px] rounded-full border border-primary/14" />
                  <div className="absolute inset-[-44px] rounded-full border border-white/5" />
                  <div className="premium-subtle relative rounded-full p-6 shadow-[0_28px_70px_-36px_rgba(0,0,0,0.85)]">
                    <ScoreRing score={Math.round(stats?.overall_score || 0)} size={210} />
                  </div>
                </div>
                <div className="absolute bottom-4 left-0 right-0 flex items-center justify-between text-[11px]">
                  <div className="font-mono uppercase tracking-[0.18em] text-muted-foreground">critical {stats?.critical_total ?? 0}</div>
                  <div className="font-mono uppercase tracking-[0.18em] text-success">
                    {stats ? `${stats.score_change >= 0 ? "+" : ""}${stats.score_change} delta` : "0 delta"}
                  </div>
                </div>
              </div>
            </div>
          </section>

          <div className="grid gap-4 lg:grid-cols-3">
            <div data-reveal className="premium-panel rounded-[28px] p-6 lg:row-span-2">
              <div className="flex items-start justify-between">
                <div>
                  <div className="font-mono text-xs uppercase tracking-wider text-muted-foreground">Overall risk score</div>
                  <div className="mt-1 text-sm text-muted-foreground">Across recent analyses</div>
                </div>
                <span className="rounded-full border border-success/30 bg-success/10 px-2 py-0.5 font-mono text-xs text-success">
                  {stats ? `${stats.score_change >= 0 ? "+" : ""}${stats.score_change}` : "…"}
                </span>
              </div>
              <div className="mt-8 flex flex-col items-center">
                <ScoreRing score={Math.round(stats?.overall_score || 0)} size={180} />
                <div className="mt-4 text-center text-sm text-muted-foreground">
                  {loading ? "Loading…" : `${stats?.boards_analyzed || 0} runs summarized.`}
                </div>
              </div>
              <div className="mt-8 grid grid-cols-3 gap-4 border-t border-border pt-6 text-center">
                <Mini label="Critical" value={String(stats?.critical_total ?? 0)} tone="danger" />
                <Mini label="Medium" value={String(stats?.medium_total ?? 0)} tone="warning" />
                <Mini label="Low" value={String(stats?.low_total ?? 0)} tone="muted" />
              </div>
            </div>

            <KpiCard label="Boards analyzed" value={String(stats?.boards_analyzed ?? 0)} trend="Recent runs" icon={CircuitBoard} />
            <KpiCard label="Avg score" value={String(stats?.avg_score_30d ?? 0)} trend="Across recent runs" icon={TrendingUp} />
            <KpiCard label="Open critical issues" value={String(stats?.open_critical_issues ?? 0)} trend={`${stats?.issue_change ?? 0} vs oldest sample`} icon={AlertTriangle} tone="danger" />
            <KpiCard label="Latest change" value={`${stats?.score_change ?? 0}`} trend="Newest vs oldest score" icon={ArrowUpRight} />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <Panel title="Score trend">
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={trend}>
                  <defs>
                    <linearGradient id="g1" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="oklch(0.85 0.16 195)" stopOpacity={0.45} />
                      <stop offset="100%" stopColor="oklch(0.85 0.16 195)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="oklch(0.28 0.014 250)" vertical={false} />
                  <XAxis dataKey="label" stroke="oklch(0.55 0.018 250)" fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis stroke="oklch(0.55 0.018 250)" fontSize={11} tickLine={false} axisLine={false} />
                  <Tooltip cursor={transparentCursor} contentStyle={{ background: "oklch(0.19 0.014 250)", border: "1px solid oklch(0.28 0.014 250)", borderRadius: 8, fontSize: 12 }} />
                  <Area type="monotone" dataKey="score" stroke="oklch(0.85 0.16 195)" strokeWidth={2} fill="url(#g1)" />
                </AreaChart>
              </ResponsiveContainer>
            </Panel>
            <Panel title="Issues over time">
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={trend}>
                  <CartesianGrid stroke="oklch(0.28 0.014 250)" vertical={false} />
                  <XAxis dataKey="label" stroke="oklch(0.55 0.018 250)" fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis stroke="oklch(0.55 0.018 250)" fontSize={11} tickLine={false} axisLine={false} />
                  <Tooltip cursor={transparentCursor} contentStyle={{ background: "oklch(0.19 0.014 250)", border: "1px solid oklch(0.28 0.014 250)", borderRadius: 8, fontSize: 12 }} />
                  <Line type="monotone" dataKey="issues" stroke="oklch(0.82 0.16 75)" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </Panel>
          </div>

          <Panel title="Severity over time">
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={trend}>
                <defs>
                  <linearGradient id="sevCritical" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="oklch(0.68 0.2 24)" stopOpacity={0.9} />
                    <stop offset="100%" stopColor="oklch(0.68 0.2 24)" stopOpacity={0.22} />
                  </linearGradient>
                  <linearGradient id="sevHigh" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="oklch(0.77 0.18 52)" stopOpacity={0.85} />
                    <stop offset="100%" stopColor="oklch(0.77 0.18 52)" stopOpacity={0.2} />
                  </linearGradient>
                  <linearGradient id="sevMedium" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="oklch(0.82 0.16 75)" stopOpacity={0.8} />
                    <stop offset="100%" stopColor="oklch(0.82 0.16 75)" stopOpacity={0.18} />
                  </linearGradient>
                  <linearGradient id="sevLow" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="oklch(0.84 0.15 205)" stopOpacity={0.75} />
                    <stop offset="100%" stopColor="oklch(0.84 0.15 205)" stopOpacity={0.15} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="oklch(0.28 0.014 250)" vertical={false} />
                <XAxis dataKey="label" stroke="oklch(0.55 0.018 250)" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis stroke="oklch(0.55 0.018 250)" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip cursor={transparentCursor} contentStyle={{ background: "oklch(0.19 0.014 250)", border: "1px solid oklch(0.28 0.014 250)", borderRadius: 8, fontSize: 12 }} />
                <Area type="monotone" dataKey="critical" stackId="1" stroke="oklch(0.68 0.2 24)" fill="url(#sevCritical)" />
                <Area type="monotone" dataKey="high" stackId="1" stroke="oklch(0.77 0.18 52)" fill="url(#sevHigh)" />
                <Area type="monotone" dataKey="medium" stackId="1" stroke="oklch(0.82 0.16 75)" fill="url(#sevMedium)" />
                <Area type="monotone" dataKey="low" stackId="1" stroke="oklch(0.84 0.15 205)" fill="url(#sevLow)" />
              </AreaChart>
            </ResponsiveContainer>
          </Panel>

          <div className="grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
            <BoardHeatmap
              title="Fleet hotspot overview"
              matrixRows={data?.risk_heatmap}
              emptyCopy="Recent runs do not expose enough categorized findings yet to render a workspace heat map."
            />
            <Panel title="Hotspot reading guide">
              <div className="space-y-4">
                <div className="rounded-2xl border border-border bg-background/40 p-4 text-sm leading-6 text-muted-foreground">
                  This overview gives the dashboard a spatial read on where board pressure typically concentrates across recent analyses. Switch between thermal, density, and findings modes to change the lens.
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <MetricCard label="Recent runs" value={String(recent.length)} copy="Included in the latest dashboard sample" />
                  <MetricCard label="Trend points" value={String(trend.length)} copy="Used to shape the score and issue curves" />
                  <MetricCard label="Critical findings" value={String(stats?.critical_total ?? 0)} copy="Open critical issues across recent analyses" />
                  <MetricCard label="Boards analyzed" value={String(stats?.boards_analyzed ?? 0)} copy="Total runs represented in this dashboard view" />
                </div>
              </div>
            </Panel>
          </div>

          <Panel title="Recent analyses" action={<Link to="/history" className="font-mono text-xs text-primary hover:underline">view all →</Link>}>
            <div className="-mx-6 overflow-x-auto">
              <table className="premium-table w-full text-sm">
                <thead>
                  <tr className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
                    <th className="px-6 py-3 text-left font-normal">Board</th>
                    <th className="px-6 py-3 text-left font-normal">Run</th>
                    <th className="px-6 py-3 text-left font-normal">Score</th>
                    <th className="px-6 py-3 text-left font-normal">Δ</th>
                    <th className="px-6 py-3 text-left font-normal">Issues</th>
                    <th className="px-6 py-3 text-left font-normal">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {recent.map((item) => (
                    <tr key={item.run_dir} className="border-t border-border/60 hover:bg-surface/50">
                      <td className="px-6 py-3.5 font-medium">{item.name}</td>
                      <td className="px-6 py-3.5 font-mono text-xs text-muted-foreground">{item.rev}</td>
                      <td className="px-6 py-3.5"><ScorePill score={item.score} /></td>
                      <td className={`px-6 py-3.5 font-mono text-xs ${item.delta && item.delta > 0 ? "text-success" : item.delta && item.delta < 0 ? "text-danger" : "text-muted-foreground"}`}>
                        {item.delta == null ? "—" : `${item.delta > 0 ? "+" : ""}${item.delta}`}
                      </td>
                      <td className="px-6 py-3.5 text-muted-foreground">{item.issues}</td>
                      <td className="px-6 py-3.5">
                        <span className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 font-mono text-[11px] ${item.status === "ready" ? "bg-success/10 text-success" : "bg-warning/10 text-warning"}`}>
                          <span className={`h-1.5 w-1.5 rounded-full ${item.status === "ready" ? "bg-success" : "bg-warning"}`} />
                          {item.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Panel>
        </div>
      )}
    </AppShell>
  );
}

function KpiCard({ label, value, trend, icon: Icon, tone }: { label: string; value: string; trend: string; icon: React.ComponentType<{ className?: string }>; tone?: "danger" }) {
  return (
    <div data-reveal className="premium-card rounded-[26px] p-6">
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

function MetricCard({ label, value, copy }: { label: string; value: string; copy: string }) {
  return (
    <div className="rounded-xl border border-border bg-background/40 p-4">
      <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
      <div className="mt-1 text-xs text-muted-foreground">{copy}</div>
    </div>
  );
}

function HeroMetric({ label, value, tone }: { label: string; value: string; tone?: "danger" }) {
  return (
    <div className="min-w-[132px]">
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{label}</div>
      <div className={`mt-1 text-2xl font-semibold ${tone === "danger" ? "text-danger" : "text-foreground"}`}>{value}</div>
    </div>
  );
}
