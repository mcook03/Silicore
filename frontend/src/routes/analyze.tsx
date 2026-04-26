import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { ScoreRing } from "@/components/silicore/ScoreRing";
import { Panel } from "@/components/silicore/Panel";
import { BoardHeatmap } from "@/components/silicore/BoardHeatmap";
import { CategoryBreakdown, SeverityDonut } from "@/components/silicore/AnalysisCharts";
import { Button } from "@/components/ui/button";
import { Upload, FileUp, Sparkles, AlertTriangle, AlertCircle, Info, CheckCircle2, ChevronRight, Download } from "lucide-react";
import { apiPostForm, useApiData } from "@/lib/api";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const transparentCursor = { fill: "transparent", stroke: "transparent" };

export const Route = createFileRoute("/analyze")({
  head: () => ({ meta: [{ title: "Board analysis — Silicore" }] }),
  component: Analyze,
});

type AnalysisOptions = {
  analysis_modes: {
    profiles: Array<{ value: string; label: string }>;
    board_types: Array<{ value: string; label: string }>;
  };
  project_options: Array<{ project_id: string; name: string }>;
};

type Risk = {
  severity?: string;
  message?: string;
  category?: string;
  recommendation?: string;
  components?: string[];
  nets?: string[];
  transparency_view?: {
    confidence_score?: number;
    confidence_band?: string;
    traceability_score?: number;
  };
};

type GroupedRisk = {
  title?: string;
  count?: number;
  severity_counts?: {
    critical?: number;
    high?: number;
    medium?: number;
    low?: number;
  };
};

type DownloadItem = {
  label?: string;
  url?: string;
};

type AnalysisResultPayload = {
  result: {
    filename?: string;
    score?: number;
    health_summary?: string | { title?: string; summary?: string };
    risks?: Risk[];
    grouped_risks?: GroupedRisk[];
    downloads?: DownloadItem[] | Record<string, string>;
    analysis_context_view?: {
      score_breakdown?: {
        category_rows?: Array<{ label?: string; penalty?: number }>;
      };
    };
    board_view?: {
      has_data?: boolean;
      width?: number;
      height?: number;
      base_view_box?: string;
      outline_segments?: Array<{ x1: number; y1: number; x2: number; y2: number }>;
      hotspots?: Array<{ x: number; y: number; radius: number; tone: "safe" | "low" | "medium" | "high" | "critical" }>;
      summary_stats?: Array<{ label: string; value: number }>;
    };
  };
};

function Analyze() {
  const { data: options, loading: optionsLoading } = useApiData<AnalysisOptions>("/api/frontend/analyze/options");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [projectId, setProjectId] = useState("");
  const [profile, setProfile] = useState("balanced");
  const [boardType, setBoardType] = useState("general");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResultPayload | null>(null);

  const result = analysis?.result;
  const risks = Array.isArray(result?.risks) ? result.risks : [];
  const groupedRisks = Array.isArray(result?.grouped_risks) ? result.grouped_risks : [];
  const downloadItems: DownloadItem[] = Array.isArray(result?.downloads)
    ? result.downloads
    : Object.entries(result?.downloads || {}).map(([label, url]) => ({ label, url }));
  const healthSummaryText = typeof result?.health_summary === "string"
    ? result.health_summary
    : result?.health_summary?.summary || result?.health_summary?.title || "Analysis complete.";
  const severityData = [
    { name: "critical", value: risks.filter((item) => (item.severity || "").toLowerCase() === "critical").length },
    { name: "high", value: risks.filter((item) => (item.severity || "").toLowerCase() === "high").length },
    { name: "medium", value: risks.filter((item) => (item.severity || "").toLowerCase() === "medium").length },
    { name: "low", value: risks.filter((item) => !["critical", "high", "medium"].includes((item.severity || "").toLowerCase())).length },
  ].filter((item) => item.value > 0);
  const categoryChartData = groupedRisks.map((item) => ({
    category: item.title || "General",
    critical: Number(item.severity_counts?.critical || 0),
    medium: Number(item.severity_counts?.medium || 0) + Number(item.severity_counts?.high || 0),
    low: Number(item.severity_counts?.low || 0),
  }));
  const penaltyRows = (result?.analysis_context_view?.score_breakdown?.category_rows || [])
    .map((item) => ({ label: item.label || "General", penalty: Number(item.penalty || 0) }))
    .filter((item) => item.penalty > 0)
    .sort((a, b) => b.penalty - a.penalty)
    .slice(0, 8);
  const confidenceBuckets = risks.reduce(
    (acc, risk) => {
      const score = Number(risk.transparency_view?.confidence_score || 0);
      if (score >= 80) acc.high += 1;
      else if (score >= 60) acc.medium += 1;
      else acc.low += 1;
      return acc;
    },
    { high: 0, medium: 0, low: 0 },
  );
  const confidenceData = [
    { label: "High", value: confidenceBuckets.high, fill: "oklch(0.76 0.16 160)" },
    { label: "Medium", value: confidenceBuckets.medium, fill: "oklch(0.82 0.16 75)" },
    { label: "Low", value: confidenceBuckets.low, fill: "oklch(0.68 0.2 24)" },
  ];
  const traceabilityData = risks.reduce(
    (acc, risk) => {
      const score = Number(risk.transparency_view?.traceability_score || 0);
      if (score >= 85) acc.auditReady += 1;
      else if (score >= 60) acc.moderate += 1;
      else acc.weak += 1;
      return acc;
    },
    { auditReady: 0, moderate: 0, weak: 0 },
  );
  const traceabilityChart = [
    { label: "Audit-ready", value: traceabilityData.auditReady, fill: "oklch(0.76 0.16 160)" },
    { label: "Moderate", value: traceabilityData.moderate, fill: "oklch(0.84 0.15 205)" },
    { label: "Weak", value: traceabilityData.weak, fill: "oklch(0.68 0.2 24)" },
  ];
  const componentLeaderboard = Array.from(
    risks.reduce((map, risk) => {
      for (const ref of risk.components || []) {
        map.set(ref, (map.get(ref) || 0) + 1);
      }
      return map;
    }, new Map<string, number>()),
  )
    .map(([label, value]) => ({ label, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 6);
  const netLeaderboard = Array.from(
    risks.reduce((map, risk) => {
      for (const net of risk.nets || []) {
        map.set(net, (map.get(net) || 0) + 1);
      }
      return map;
    }, new Map<string, number>()),
  )
    .map(([label, value]) => ({ label, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 6);
  const onSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedFile) {
      setError("Choose a board file before starting analysis.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("board_file", selectedFile);
      formData.append("project_id", projectId);
      formData.append("analysis_profile", profile);
      formData.append("analysis_board_type", boardType);
      const payload = await apiPostForm<AnalysisResultPayload>("/api/frontend/analyze/single", formData);
      setAnalysis(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AppShell title="Board analysis">
      <div className="space-y-6">
        <section
          data-reveal
          className="relative overflow-hidden rounded-[34px] border border-border/80 bg-[radial-gradient(circle_at_82%_22%,rgba(96,240,198,0.14),transparent_18%),linear-gradient(135deg,rgba(7,16,26,0.98),rgba(8,18,28,0.95)_55%,rgba(10,17,28,0.98))] px-6 py-7 sm:px-8 sm:py-8"
        >
          <div className="absolute inset-y-0 left-[62%] w-px bg-gradient-to-b from-transparent via-white/8 to-transparent max-xl:hidden" />
          <div className="relative grid gap-8 xl:grid-cols-[minmax(0,1.08fr)_minmax(0,0.92fr)]">
            <div>
              <div className="section-eyebrow">
                <Sparkles className="h-3.5 w-3.5" />
                Analysis studio
              </div>
              <h2 className="mt-5 max-w-3xl text-4xl font-semibold tracking-tight text-foreground sm:text-[3.2rem] sm:leading-[1.02]">
                Upload a board into a workspace that feels like a live analysis instrument, not a file form.
              </h2>
              <p className="mt-4 max-w-2xl text-base leading-8 text-muted-foreground">
                The top of this page should set the tone for the full flow: upload, tune, run, and inspect without looking like another generic hero stacked over content.
              </p>
            </div>
            <div className="grid gap-4 sm:grid-cols-3 xl:grid-cols-1">
              <AnalyzeSignal label="Profiles" value={String(options?.analysis_modes.profiles.length ?? 0)} copy="Analysis presets available" />
              <AnalyzeSignal label="Board types" value={String(options?.analysis_modes.board_types.length ?? 0)} copy="Context modes for the run" />
              <AnalyzeSignal label="Workspaces" value={String(options?.project_options.length ?? 0)} copy="Projects available for linking" />
            </div>
          </div>
        </section>

        <form onSubmit={onSubmit} className="premium-hero relative overflow-hidden rounded-[30px] p-8">
          <div className="bg-hero-glow pointer-events-none absolute inset-0 opacity-40" />
          <div className="relative grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
            <div className="text-center lg:text-left">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl border border-border bg-background lg:mx-0">
                <Upload className="h-5 w-5 text-primary" />
              </div>
              <h3 className="mt-4 text-lg font-medium">Upload a PCB file</h3>
              <p className="mt-1 max-w-xl text-sm text-muted-foreground">
                Drop a Gerber zip, ODB++, `.brd` or `.kicad_pcb` file to run a real Silicore analysis in the new UI.
              </p>
              <div className="mt-4 text-sm text-foreground">
                {selectedFile ? selectedFile.name : "No file selected yet"}
              </div>
              <div className="mt-5 flex flex-wrap items-center justify-center gap-2 lg:justify-start">
                <label className="inline-flex cursor-pointer items-center justify-center rounded-full bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90">
                  <FileUp className="mr-1.5 h-3.5 w-3.5" />
                  Choose file
                  <input
                    type="file"
                    className="hidden"
                    accept=".zip,.odb,.brd,.kicad_pcb,.pcbdocascii,.gbr,.gko,.ger,.gtl,.gbl,.gto,.gbo,.gts,.gbs,.gm1,.pho,.art,.outline,.drl,.xln,.txt"
                    onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
                  />
                </label>
                <Button type="submit" size="sm" className="rounded-full" disabled={submitting || optionsLoading}>
                  <Sparkles className="mr-1.5 h-3.5 w-3.5" />
                  {submitting ? "Analyzing…" : "Run analysis"}
                </Button>
              </div>
              <div className="mt-4 font-mono text-xs text-muted-foreground">.zip · .odb · .brd · .kicad_pcb</div>
            </div>

            <div className="grid gap-3 rounded-2xl border border-border bg-background/40 p-4">
              <label className="space-y-1.5">
                <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">Project</span>
                <select
                  value={projectId}
                  onChange={(event) => setProjectId(event.target.value)}
                  className="premium-select h-10 w-full px-3 text-sm"
                >
                  <option value="">No workspace</option>
                  {(options?.project_options ?? []).map((option) => (
                    <option key={option.project_id} value={option.project_id}>{option.name}</option>
                  ))}
                </select>
              </label>
              <label className="space-y-1.5">
                <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">Profile</span>
                <select
                  value={profile}
                  onChange={(event) => setProfile(event.target.value)}
                  className="premium-select h-10 w-full px-3 text-sm"
                >
                  {(options?.analysis_modes.profiles ?? []).map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </label>
              <label className="space-y-1.5">
                <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">Board type</span>
                <select
                  value={boardType}
                  onChange={(event) => setBoardType(event.target.value)}
                  className="premium-select h-10 w-full px-3 text-sm"
                >
                  {(options?.analysis_modes.board_types ?? []).map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </label>
              {error && <div className="rounded-lg border border-danger/20 bg-danger/10 px-3 py-2 text-sm text-danger">{error}</div>}
            </div>
          </div>
        </form>

        {result ? (
          <>
            <div className="grid gap-4 lg:grid-cols-[320px_1fr]">
              <div className="rounded-2xl border border-border bg-surface p-6">
                <div className="mb-2 font-mono text-xs uppercase tracking-wider text-muted-foreground">{result.filename}</div>
                <div className="mb-6 text-sm text-muted-foreground">Latest analysis result</div>
                <div className="flex flex-col items-center">
                  <ScoreRing score={Math.round(Number(result.score || 0))} size={160} />
                  <div className="mt-4 text-center">
                    <div className="text-sm">{healthSummaryText}</div>
                  </div>
                </div>
                <div className="mt-6 grid grid-cols-3 gap-2 border-t border-border pt-4 text-center">
                  <Tally tone="danger" label="critical" n={severityData.find((item) => item.name === "critical")?.value ?? 0} />
                  <Tally tone="warning" label="medium" n={severityData.find((item) => item.name === "medium")?.value ?? 0} />
                  <Tally tone="muted" label="low" n={severityData.find((item) => item.name === "low")?.value ?? 0} />
                </div>
                <div className="mt-6 flex flex-wrap gap-2">
                  {downloadItems.map((item, index) => (
                    <a key={`${item.label}-${index}`} href={item.url || "#"} className="inline-flex items-center gap-1 rounded-full border border-border px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground">
                      <Download className="h-3 w-3" /> {item.label || "Download artifact"}
                    </a>
                  ))}
                </div>
              </div>

              <Panel title="Category summary">
                <div className="space-y-4">
                  {groupedRisks.map((item, index) => (
                    <div key={`${item.title}-${index}`}>
                      <div className="mb-1.5 flex items-center justify-between text-sm">
                        <span>{item.title || "General"}</span>
                        <span className="font-mono text-xs text-muted-foreground">{item.count || 0} findings</span>
                      </div>
                      <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                        <div className="h-full rounded-full bg-primary" style={{ width: `${Math.min(Number(item.count || 0) * 8, 100)}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </Panel>
            </div>

            <div className="grid gap-4 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
              <Panel title="Severity mix">
                {severityData.length ? (
                  <SeverityDonut data={severityData} />
                ) : (
                  <p className="text-sm text-muted-foreground">No severity breakdown is available for this run yet.</p>
                )}
              </Panel>

              <Panel title="Category distribution">
                {categoryChartData.length ? (
                  <CategoryBreakdown data={categoryChartData} />
                ) : (
                  <p className="text-sm text-muted-foreground">Category-level distribution appears after Silicore groups findings for the uploaded board.</p>
                )}
              </Panel>
            </div>

            <div className="grid gap-4 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
              <BoardHeatmap
                title="Board hotspot map"
                boardView={result.board_view}
                emptyCopy="This run does not include enough board geometry to render a spatial hotspot map yet."
              />
              <Panel title="Board signal">
                <div className="space-y-4">
                  <div className="rounded-2xl border border-border bg-background/40 p-4">
                    <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">Interpretation</div>
                    <p className="mt-2 text-sm leading-6 text-muted-foreground">
                      Use the hotspot map to scan where thermal concentration, routing density, or findings pressure would likely cluster across the board surface while you review the grouped findings below.
                    </p>
                  </div>
                  <div className="grid gap-3 sm:grid-cols-3">
                    <SignalStat label="Findings" value={String(risks.length)} />
                    <SignalStat label="Groups" value={String(groupedRisks.length)} />
                    <SignalStat label="Artifacts" value={String(downloadItems.length)} />
                  </div>
                  <div className="rounded-2xl border border-border bg-background/40 p-4 text-sm text-muted-foreground">
                    When we expose coordinate-aware backend data, this panel can upgrade from an analysis heat overlay to a true board-geometry map without changing the page structure.
                  </div>
                </div>
              </Panel>
            </div>

            <div className="grid gap-4 xl:grid-cols-2">
              <Panel title="Penalty contribution">
                {penaltyRows.length ? (
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={penaltyRows} layout="vertical" margin={{ left: 10, right: 18 }}>
                      <CartesianGrid stroke="oklch(0.28 0.014 250)" horizontal={false} />
                      <XAxis type="number" tickLine={false} axisLine={false} stroke="oklch(0.55 0.018 250)" fontSize={11} />
                      <YAxis type="category" dataKey="label" width={118} tickLine={false} axisLine={false} stroke="oklch(0.55 0.018 250)" fontSize={11} />
                      <Tooltip cursor={transparentCursor} contentStyle={{ background: "oklch(0.19 0.014 250)", border: "1px solid oklch(0.28 0.014 250)", borderRadius: 8, fontSize: 12 }} />
                      <Bar dataKey="penalty" fill="oklch(0.84 0.15 205)" radius={[0, 8, 8, 0]} activeBar={{ stroke: "rgba(255,255,255,0.72)", strokeWidth: 1.4, fillOpacity: 1, filter: "drop-shadow(0 0 10px rgba(86,211,240,0.32))" }} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-sm text-muted-foreground">Penalty contribution will appear when score explanation detail is available for the run.</p>
                )}
              </Panel>

              <Panel title="Confidence distribution">
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={confidenceData} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
                    <CartesianGrid stroke="oklch(0.28 0.014 250)" vertical={false} />
                    <XAxis dataKey="label" tickLine={false} axisLine={false} stroke="oklch(0.55 0.018 250)" fontSize={11} />
                    <YAxis tickLine={false} axisLine={false} stroke="oklch(0.55 0.018 250)" fontSize={11} allowDecimals={false} />
                    <Tooltip cursor={transparentCursor} contentStyle={{ background: "oklch(0.19 0.014 250)", border: "1px solid oklch(0.28 0.014 250)", borderRadius: 8, fontSize: 12 }} />
                    <Bar dataKey="value" radius={[8, 8, 0, 0]} activeBar={{ stroke: "rgba(255,255,255,0.72)", strokeWidth: 1.4, fillOpacity: 1, filter: "drop-shadow(0 0 10px rgba(86,211,240,0.3))" }}>
                      {confidenceData.map((item) => <Cell key={item.label} fill={item.fill} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </Panel>
            </div>

            <div className="grid gap-4 xl:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)]">
              <Panel title="Component hotspot leaderboard">
                {componentLeaderboard.length ? (
                  <Leaderboard items={componentLeaderboard} accent="oklch(0.84 0.15 205)" />
                ) : (
                  <p className="text-sm text-muted-foreground">No component-linked findings were preserved for this run.</p>
                )}
              </Panel>

              <Panel title="Net hotspot leaderboard">
                {netLeaderboard.length ? (
                  <Leaderboard items={netLeaderboard} accent="oklch(0.82 0.16 75)" />
                ) : (
                  <p className="text-sm text-muted-foreground">No net-linked findings were preserved for this run.</p>
                )}
              </Panel>
            </div>

            <Panel title="Traceability completeness">
              <div className="grid gap-4 xl:grid-cols-[minmax(0,0.8fr)_minmax(0,1.2fr)]">
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={traceabilityChart} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
                    <CartesianGrid stroke="oklch(0.28 0.014 250)" vertical={false} />
                    <XAxis dataKey="label" tickLine={false} axisLine={false} stroke="oklch(0.55 0.018 250)" fontSize={11} />
                    <YAxis tickLine={false} axisLine={false} stroke="oklch(0.55 0.018 250)" fontSize={11} allowDecimals={false} />
                    <Tooltip cursor={transparentCursor} contentStyle={{ background: "oklch(0.19 0.014 250)", border: "1px solid oklch(0.28 0.014 250)", borderRadius: 8, fontSize: 12 }} />
                    <Bar dataKey="value" radius={[8, 8, 0, 0]} activeBar={{ stroke: "rgba(255,255,255,0.72)", strokeWidth: 1.4, fillOpacity: 1, filter: "drop-shadow(0 0 10px rgba(86,211,240,0.3))" }}>
                      {traceabilityChart.map((item) => <Cell key={item.label} fill={item.fill} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
                <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
                  <SignalStat label="Audit-ready" value={String(traceabilityData.auditReady)} />
                  <SignalStat label="Moderate evidence" value={String(traceabilityData.moderate)} />
                  <SignalStat label="Weak evidence" value={String(traceabilityData.weak)} />
                </div>
              </div>
            </Panel>

            <Panel title="Artifacts">
              <div className="grid gap-3 md:grid-cols-2">
                {downloadItems.map((item, index) => (
                  <a
                    key={`artifact-${index}`}
                    href={item.url || "#"}
                    className="flex items-center justify-between rounded-xl border border-border bg-background/40 p-4 text-sm hover:border-primary/30"
                  >
                    <span>{item.label || "Download artifact"}</span>
                    <Download className="h-4 w-4 text-muted-foreground" />
                  </a>
                ))}
              </div>
            </Panel>

            <Panel title="Findings & recommendations" action={<span className="font-mono text-xs text-muted-foreground">{risks.length} total</span>}>
              <div className="space-y-2">
                {risks.map((finding, index) => <FindingRow key={`${finding.message}-${index}`} risk={finding} />)}
              </div>
            </Panel>
          </>
        ) : (
          <Panel title="Ready to analyze">
            <p className="text-sm text-muted-foreground">
              Run a board through the uploader above and Silicore will populate live findings, score breakdowns, and downloads here.
            </p>
          </Panel>
        )}
      </div>
    </AppShell>
  );
}

function AnalyzeSignal({ label, value, copy }: { label: string; value: string; copy: string }) {
  return (
    <div className="border-l border-white/10 pl-4">
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{label}</div>
      <div className="mt-1 text-3xl font-semibold text-foreground">{value}</div>
      <div className="mt-1 text-sm text-muted-foreground">{copy}</div>
    </div>
  );
}

function Tally({ tone, label, n }: { tone: "danger" | "warning" | "muted"; label: string; n: number }) {
  const c = { danger: "text-danger", warning: "text-warning", muted: "text-muted-foreground" }[tone];
  return (
    <div>
      <div className={`text-lg font-semibold ${c}`}>{n}</div>
      <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
    </div>
  );
}

function FindingRow({ risk }: { risk: Risk }) {
  const severity = (risk.severity || "low").toLowerCase();
  const map = {
    critical: { Icon: AlertCircle, cls: "text-danger bg-danger/10 border-danger/20" },
    medium: { Icon: AlertTriangle, cls: "text-warning bg-warning/10 border-warning/20" },
    low: { Icon: Info, cls: "text-primary bg-primary/10 border-primary/20" },
    high: { Icon: AlertTriangle, cls: "text-warning bg-warning/10 border-warning/20" },
  } as const;
  const { Icon, cls } = map[severity as keyof typeof map] ?? map.low;
  return (
    <div className="group flex items-start gap-4 rounded-xl border border-border bg-background/40 p-4 transition-colors hover:border-primary/30">
      <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-md border ${cls}`}><Icon className="h-4 w-4" /></span>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-medium">{risk.message || "Unnamed issue"}</span>
          <span className="rounded border border-border px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{risk.category || "General"}</span>
        </div>
        <div className="mt-2 flex items-start gap-2 rounded-md bg-surface px-3 py-2 text-xs text-muted-foreground">
          <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
          <span><span className="text-foreground">Fix · </span>{risk.recommendation || "Review this issue in layout."}</span>
        </div>
      </div>
      <ChevronRight className="mt-2 h-4 w-4 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:text-foreground" />
    </div>
  );
}

function SignalStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-background/40 p-4">
      <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
    </div>
  );
}

function Leaderboard({ items, accent }: { items: Array<{ label: string; value: number }>; accent: string }) {
  const maxValue = Math.max(...items.map((item) => item.value), 1);
  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div key={item.label} className="rounded-xl border border-border bg-background/40 p-4">
          <div className="flex items-center justify-between gap-3">
            <div className="text-sm font-medium">{item.label}</div>
            <div className="font-mono text-xs text-muted-foreground">{item.value}</div>
          </div>
          <div className="mt-3 h-2 rounded-full bg-muted/70">
            <div className="h-2 rounded-full" style={{ width: `${Math.max((item.value / maxValue) * 100, 8)}%`, background: accent }} />
          </div>
        </div>
      ))}
    </div>
  );
}
