import { createFileRoute, Link } from "@tanstack/react-router";
import { BoardHeatmap } from "@/components/silicore/BoardHeatmap";
import { ScoreRing } from "@/components/silicore/ScoreRing";
import { ScorePill } from "@/components/silicore/Panel";
import {
  LineChart, Line, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid, AreaChart, Area,
} from "recharts";
import { TrendingUp, AlertTriangle } from "lucide-react";
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
        <section data-reveal className="rounded-[30px] border border-danger/20 bg-danger/10 p-6">
          <p className="text-sm text-danger">{error}</p>
        </section>
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

          <section data-reveal className="grid gap-6 xl:grid-cols-[220px_minmax(0,1fr)_320px]">
            <div className="relative overflow-hidden rounded-[30px] border border-white/8 bg-[linear-gradient(180deg,rgba(9,17,27,0.96),rgba(7,14,22,0.98))] p-5">
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Telemetry rail</div>
              <div className="mt-5 space-y-6">
                <RailMetric label="Boards analyzed" value={String(stats?.boards_analyzed ?? 0)} />
                <RailMetric label="Average score" value={String(stats?.avg_score_30d ?? 0)} />
                <RailMetric label="Critical open" value={String(stats?.open_critical_issues ?? 0)} tone="danger" />
                <RailMetric label="Issue change" value={String(stats?.issue_change ?? 0)} tone={(stats?.issue_change || 0) > 0 ? "danger" : undefined} />
              </div>
            </div>

            <div className="relative overflow-hidden rounded-[34px] border border-white/8 bg-[linear-gradient(180deg,rgba(8,17,28,0.95),rgba(6,13,21,0.98))] px-6 py-6 shadow-[0_32px_80px_-46px_rgba(0,0,0,0.95)]">
              <div className="pointer-events-none absolute inset-0 opacity-45 [background-image:linear-gradient(to_right,rgba(255,255,255,0.04)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.02)_1px,transparent_1px)] [background-size:64px_64px]" />
              <div className="relative">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div className="max-w-xl">
                    <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Central score field</div>
                    <h3 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">Live design pressure across recent analyses</h3>
                    <p className="mt-2 text-sm leading-7 text-muted-foreground">This canvas pulls score, risk, and severity movement into one field instead of scattering them into stacked blocks.</p>
                  </div>
                  <div className="relative shrink-0">
                    <div className="absolute inset-[-20px] rounded-full bg-primary/10 blur-2xl" />
                    <div className="relative rounded-full border border-white/8 bg-background/50 p-4">
                      <ScoreRing score={Math.round(stats?.overall_score || 0)} size={168} />
                    </div>
                  </div>
                </div>

                <div className="mt-6 h-[280px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={trend}>
                      <defs>
                        <linearGradient id="dashboardScore" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="oklch(0.85 0.16 195)" stopOpacity={0.48} />
                          <stop offset="100%" stopColor="oklch(0.85 0.16 195)" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="dashboardCritical" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="oklch(0.68 0.2 24)" stopOpacity={0.3} />
                          <stop offset="100%" stopColor="oklch(0.68 0.2 24)" stopOpacity={0.02} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid stroke="rgba(148,163,184,0.15)" vertical={false} />
                      <XAxis dataKey="label" tickLine={false} axisLine={false} stroke="rgba(148,163,184,0.78)" fontSize={11} />
                      <YAxis yAxisId="score" domain={[0, 100]} tickLine={false} axisLine={false} stroke="rgba(148,163,184,0.78)" fontSize={11} />
                      <YAxis yAxisId="critical" orientation="right" tickLine={false} axisLine={false} stroke="rgba(248,113,113,0.45)" fontSize={11} />
                      <Tooltip cursor={transparentCursor} contentStyle={{ background: "oklch(0.19 0.014 250)", border: "1px solid oklch(0.28 0.014 250)", borderRadius: 12, fontSize: 12 }} />
                      <Area yAxisId="critical" type="monotone" dataKey="critical" stroke="oklch(0.68 0.2 24)" strokeWidth={1.5} fill="url(#dashboardCritical)" />
                      <Area yAxisId="score" type="monotone" dataKey="score" stroke="oklch(0.85 0.16 195)" strokeWidth={3} fill="url(#dashboardScore)" />
                      <Line yAxisId="score" type="monotone" dataKey="issues" stroke="oklch(0.82 0.16 75)" strokeWidth={2} dot={false} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>

                <div className="mt-5 grid gap-4 md:grid-cols-3">
                  <InlineSignal label="Critical" value={String(stats?.critical_total ?? 0)} tone="danger" />
                  <InlineSignal label="Medium" value={String(stats?.medium_total ?? 0)} tone="warning" />
                  <InlineSignal label="Low" value={String(stats?.low_total ?? 0)} />
                </div>
              </div>
            </div>

            <div className="relative overflow-hidden rounded-[30px] border border-white/8 bg-[linear-gradient(180deg,rgba(9,17,27,0.96),rgba(7,14,22,0.98))] p-5">
              <div className="mb-4 flex items-center justify-between gap-3">
                <div>
                  <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Activity strip</div>
                  <h3 className="mt-1 text-lg font-medium tracking-tight">Recent analyses</h3>
                </div>
                <Link to="/history" className="font-mono text-[10px] uppercase tracking-[0.18em] text-primary hover:underline">View all</Link>
              </div>
              <div className="space-y-3">
                {recent.slice(0, 5).map((item) => (
                  <div key={item.run_dir} className="border-l border-white/10 pl-4">
                    <div className="flex items-center justify-between gap-3">
                      <div className="min-w-0">
                        <div className="truncate text-sm font-medium text-foreground">{item.name}</div>
                        <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{item.rev}</div>
                      </div>
                      <ScorePill score={item.score} />
                    </div>
                    <div className="mt-2 flex items-center gap-3 text-xs text-muted-foreground">
                      <span>{item.issues} issues</span>
                      <span className={item.delta && item.delta > 0 ? "text-success" : item.delta && item.delta < 0 ? "text-danger" : ""}>
                        {item.delta == null ? "stable" : `${item.delta > 0 ? "+" : ""}${item.delta}`}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section data-reveal className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
            <div className="relative overflow-hidden rounded-[32px] border border-white/8 bg-[linear-gradient(170deg,rgba(8,17,27,0.96),rgba(7,14,22,0.98))] p-6 shadow-[0_30px_76px_-44px_rgba(0,0,0,0.95)]">
              <div className="mb-5 flex items-start justify-between gap-4">
                <div>
                  <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Spatial context</div>
                  <h3 className="mt-1 text-xl font-medium tracking-tight">Fleet hotspot overview</h3>
                </div>
                <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{recent.length} recent runs</div>
              </div>
              <BoardHeatmap
                title="Fleet hotspot overview"
                matrixRows={data?.risk_heatmap}
                emptyCopy="Recent runs do not expose enough categorized findings yet to render a workspace heat map."
              />
            </div>

            <div className="grid gap-6">
              <div className="relative overflow-hidden rounded-[30px] border border-white/8 bg-[linear-gradient(180deg,rgba(9,18,28,0.95),rgba(7,14,22,0.98))] p-6">
                <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Severity stack</div>
                <h3 className="mt-1 text-lg font-medium tracking-tight">Severity over time</h3>
                <div className="mt-4 h-[220px]">
                  <ResponsiveContainer width="100%" height="100%">
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
                      <Tooltip cursor={transparentCursor} contentStyle={{ background: "oklch(0.19 0.014 250)", border: "1px solid oklch(0.28 0.014 250)", borderRadius: 12, fontSize: 12 }} />
                      <Area type="monotone" dataKey="critical" stackId="1" stroke="oklch(0.68 0.2 24)" fill="url(#sevCritical)" />
                      <Area type="monotone" dataKey="high" stackId="1" stroke="oklch(0.77 0.18 52)" fill="url(#sevHigh)" />
                      <Area type="monotone" dataKey="medium" stackId="1" stroke="oklch(0.82 0.16 75)" fill="url(#sevMedium)" />
                      <Area type="monotone" dataKey="low" stackId="1" stroke="oklch(0.84 0.15 205)" fill="url(#sevLow)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="relative overflow-hidden rounded-[30px] border border-white/8 bg-[linear-gradient(180deg,rgba(9,18,28,0.95),rgba(7,14,22,0.98))] p-6">
                <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Reading guide</div>
                <h3 className="mt-1 text-lg font-medium tracking-tight">How to interpret the field</h3>
                <div className="mt-4 space-y-4 text-sm leading-7 text-muted-foreground">
                  <p>The central canvas prioritizes score movement first, then critical pressure and issue drift, so you can see whether the fleet is improving or just reshuffling lower-severity noise.</p>
                  <p>The hotspot map reads spatial pressure across recent runs, while the activity strip keeps the latest boards close at hand without dropping you into a table-first layout.</p>
                </div>
              </div>
            </div>
          </section>

          <section data-reveal className="relative overflow-hidden rounded-[30px] border border-white/8 bg-[linear-gradient(180deg,rgba(9,18,28,0.95),rgba(7,14,22,0.98))] p-6">
            <div className="mb-5 flex items-start justify-between gap-4">
              <div>
                <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Run ledger</div>
                <h3 className="mt-1 text-xl font-medium tracking-tight">Extended recent analyses</h3>
              </div>
              <Link to="/history" className="font-mono text-[10px] uppercase tracking-[0.18em] text-primary hover:underline">Go to archive</Link>
            </div>
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
          </section>
        </div>
      )}
    </AppShell>
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

function RailMetric({ label, value, tone }: { label: string; value: string; tone?: "danger" }) {
  return (
    <div className="border-l border-white/10 pl-4">
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{label}</div>
      <div className={`mt-1 text-3xl font-semibold ${tone === "danger" ? "text-danger" : "text-foreground"}`}>{value}</div>
    </div>
  );
}

function InlineSignal({ label, value, tone }: { label: string; value: string; tone?: "danger" | "warning" }) {
  const toneClass = tone === "danger" ? "text-danger" : tone === "warning" ? "text-warning" : "text-foreground";
  return (
    <div className="border-t border-white/8 pt-3">
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{label}</div>
      <div className={`mt-1 text-2xl font-semibold ${toneClass}`}>{value}</div>
    </div>
  );
}
