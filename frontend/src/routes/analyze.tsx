import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { ScoreRing } from "@/components/silicore/ScoreRing";
import { BoardHeatmap } from "@/components/silicore/BoardHeatmap";
import { CategoryBreakdown, SeverityDonut } from "@/components/silicore/AnalysisCharts";
import { Button } from "@/components/ui/button";
import { Upload, FileUp, Sparkles, AlertTriangle, AlertCircle, Info, CheckCircle2, ChevronRight, Download } from "lucide-react";
import { apiPostForm, useApiData } from "@/lib/api";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { DecisionStrip, EmptySurface, FilterPills, LoadingSurface, WorkflowAction } from "@/components/silicore/UXPrimitives";
import { usePersistentState } from "@/lib/uiState";

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
  const [projectId, setProjectId] = usePersistentState("silicore:analyze:projectId", "");
  const [profile, setProfile] = useState("balanced");
  const [boardType, setBoardType] = useState("general");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResultPayload | null>(null);
  const [severityFilter, setSeverityFilter] = usePersistentState<"all" | "critical" | "high" | "medium" | "low">("silicore:analyze:severityFilter", "all");
  const [categoryFilter, setCategoryFilter] = usePersistentState("silicore:analyze:categoryFilter", "all");
  const [selectedFindingKey, setSelectedFindingKey] = useState<string | null>(null);
  const [justCompleted, setJustCompleted] = useState(false);

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
  const severityCounts = {
    all: risks.length,
    critical: risks.filter((item) => (item.severity || "").toLowerCase() === "critical").length,
    high: risks.filter((item) => (item.severity || "").toLowerCase() === "high").length,
    medium: risks.filter((item) => (item.severity || "").toLowerCase() === "medium").length,
    low: risks.filter((item) => !["critical", "high", "medium"].includes((item.severity || "").toLowerCase())).length,
  };
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
  const categoryOptions = useMemo(
    () => ["all", ...new Set(groupedRisks.map((item) => item.title || "General"))],
    [groupedRisks],
  );
  const filteredRisks = useMemo(
    () =>
      risks.filter((risk) => {
        const severity = (risk.severity || "low").toLowerCase();
        const category = risk.category || "General";
        const severityMatch = severityFilter === "all" ? true : severity === severityFilter;
        const categoryMatch = categoryFilter === "all" ? true : category === categoryFilter;
        return severityMatch && categoryMatch;
      }),
    [risks, severityFilter, categoryFilter],
  );
  const selectedFinding =
    filteredRisks.find((risk) => findingKey(risk) === selectedFindingKey)
    || risks.find((risk) => findingKey(risk) === selectedFindingKey)
    || filteredRisks[0]
    || risks[0]
    || null;
  useEffect(() => {
    if (!flashTimerNeeded(justCompleted)) return;
    const timer = window.setTimeout(() => setJustCompleted(false), 2600);
    return () => window.clearTimeout(timer);
  }, [justCompleted]);
  const topCategory = [...groupedRisks].sort((a, b) => Number(b.count || 0) - Number(a.count || 0))[0];
  const lowestConfidenceBucket = confidenceData.find((item) => item.label === "Low")?.value || 0;
  const highestComponent = componentLeaderboard[0];
  const highestNet = netLeaderboard[0];
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
      setSeverityFilter("all");
      setCategoryFilter("all");
      const nextRisks = Array.isArray(payload.result?.risks) ? payload.result.risks : [];
      setSelectedFindingKey(nextRisks[0] ? findingKey(nextRisks[0]) : null);
      setJustCompleted(true);
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
          className="editorial-surface instrument-grid rounded-[38px] px-6 py-7 sm:px-8 sm:py-8"
        >
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
                This should read like an instrument bay: intake on one side, live tuning on the other, then results unfolding as a dense engineering workspace instead of stacked forms and cards.
              </p>
            </div>
            <div className="command-strip rounded-[28px] p-5">
              <div className="grid gap-4 sm:grid-cols-3 xl:grid-cols-1">
                <AnalyzeSignal label="Profiles" value={String(options?.analysis_modes.profiles.length ?? 0)} copy="Analysis presets available" />
                <AnalyzeSignal label="Board types" value={String(options?.analysis_modes.board_types.length ?? 0)} copy="Context modes for the run" />
                <AnalyzeSignal label="Workspaces" value={String(options?.project_options.length ?? 0)} copy="Projects available for linking" />
              </div>
            </div>
          </div>
        </section>

        <form onSubmit={onSubmit} className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_380px]">
          <section className="editorial-surface instrument-grid rounded-[34px] p-8">
            <div className="relative flex h-full flex-col justify-between gap-8">
              <div className="max-w-2xl">
                <div className="section-eyebrow">
                  <Upload className="h-3.5 w-3.5" />
                  Intake surface
                </div>
                <h3 className="mt-5 text-3xl font-semibold tracking-tight text-foreground sm:text-[2.65rem] sm:leading-[1.02]">
                  Drop a board into the workspace and turn analysis settings without leaving the canvas.
                </h3>
                <p className="mt-4 text-base leading-8 text-muted-foreground">
                  Intake, file signal, and action controls stay together here so the run starts feeling like a workstation action instead of a generic upload form.
                </p>
              </div>

              <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_260px]">
                <div className="command-strip flex min-h-[320px] flex-col justify-between rounded-[30px] p-6">
                  <div>
                    <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-border bg-background/55">
                      <Upload className="h-5 w-5 text-primary" />
                    </div>
                    <h4 className="mt-5 text-xl font-medium tracking-tight">Board intake</h4>
                    <p className="mt-2 max-w-lg text-sm leading-7 text-muted-foreground">
                      Drop in a Gerber zip, ODB++, Altium export, or KiCad board file and route it into the right analysis profile immediately.
                    </p>
                  </div>

                  <div>
                    <div className="rounded-[24px] border border-dashed border-primary/25 bg-primary/6 px-5 py-8 text-center lg:text-left">
                      <div className="text-sm text-foreground">{selectedFile ? selectedFile.name : "No file selected yet"}</div>
                      <div className="mt-2 font-mono text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                        .zip · .odb · .brd · .kicad_pcb
                      </div>
                    </div>

                    <div className="mt-5 flex flex-wrap items-center gap-3">
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
                  </div>
                </div>

                <div className="grid gap-4">
                  <div className="signal-rail">
                    <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Flight readout</div>
                    <div className="mt-2 text-sm leading-7 text-muted-foreground">
                      Tune routing and scoring context before launch. These controls shape how the board gets interpreted and linked back into your workspace history.
                    </div>
                  </div>
                  <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
                    <AnalyzeSignal label="Project links" value={projectId ? "Live" : "Open"} copy="Attach results to a workspace" />
                    <AnalyzeSignal label="Profile" value={profile} copy="Preset analysis posture" />
                    <AnalyzeSignal label="Board type" value={boardType} copy="Physical context mode" />
                  </div>
                </div>
              </div>
            </div>
          </section>

          <aside className="command-strip rounded-[34px] p-5">
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Tuning rail</div>
            <div className="mt-2 text-sm leading-7 text-muted-foreground">
              Route this analysis into the right workspace and scoring posture before launch.
            </div>

            <div className="mt-5 grid gap-3">
              <label className="space-y-1.5">
                <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">Project</span>
                <select
                  value={projectId}
                  onChange={(event) => setProjectId(event.target.value)}
                  className="premium-select h-11 w-full px-3 text-sm"
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
                  className="premium-select h-11 w-full px-3 text-sm"
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
                  className="premium-select h-11 w-full px-3 text-sm"
                >
                  {(options?.analysis_modes.board_types ?? []).map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </label>
              {error && <div className="rounded-lg border border-danger/20 bg-danger/10 px-3 py-2 text-sm text-danger">{error}</div>}
            </div>
          </aside>
        </form>

        {submitting ? (
          <LoadingSurface
            title="Running board analysis"
            copy="Silicore is parsing the board, scoring the risk field, and assembling exports for this workspace."
            lines={4}
          />
        ) : null}

        {result ? (
          <>
            {justCompleted ? (
              <DecisionStrip
                eyebrow="Analysis complete"
                title="Silicore finished the run and the workstation is now centered on the newest result."
                copy="Use the trust surface and focused finding panel below to move from score into exact evidence without losing the broader result context."
                metrics={[
                  { label: "Result state", value: "Ready", tone: "success" },
                  { label: "Score", value: String(Math.round(Number(result.score || 0))), tone: Number(result.score || 0) >= 80 ? "success" : "warning" },
                  { label: "Findings", value: String(risks.length), tone: risks.length > 10 ? "danger" : "default" },
                  { label: "Exports", value: String(downloadItems.length), tone: "default" },
                ]}
              />
            ) : null}

            <DecisionStrip
              eyebrow="Run decision"
              title={
                Number(result.score || 0) >= 85
                  ? "This board looks healthy enough for focused final review."
                  : Number(result.score || 0) >= 65
                    ? "The board is analyzable, but there are still concentrated risk pockets to work through."
                    : "This board needs another engineering pass before it should move toward signoff."
              }
              copy={`Silicore sees ${risks.length} findings across ${groupedRisks.length} grouped domains. ${topCategory ? `${topCategory.title || "General"} is the heaviest drag area right now.` : "Use the grouped findings and score drag charts below to decide where to start."}`}
              metrics={[
                { label: "Run score", value: String(Math.round(Number(result.score || 0))), tone: Number(result.score || 0) >= 80 ? "success" : Number(result.score || 0) >= 60 ? "warning" : "danger" },
                { label: "Top drag", value: topCategory?.title || "—", tone: "warning" },
                { label: "Low confidence", value: String(lowestConfidenceBucket), tone: lowestConfidenceBucket > 0 ? "danger" : "success" },
                { label: "Artifacts", value: String(downloadItems.length), tone: "default" },
              ]}
            />

            <div className="grid gap-5 xl:grid-cols-[320px_minmax(0,1fr)]">
              <div className="command-strip rounded-[30px] p-6">
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
                <div className="mt-6 grid gap-3">
                  <WorkflowAction to="/history" label="Open history ledger" copy="Check how this run compares to the recent analysis archive." />
                  <WorkflowAction to="/compare" label="Move into compare" copy="Pair this run against another revision to arbitrate the delta." />
                </div>
              </div>

              <div className="editorial-surface rounded-[30px] p-6">
                <div className="mb-5 flex items-center justify-between gap-3">
                  <div>
                    <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Category summary</div>
                    <h3 className="mt-1 text-xl font-medium tracking-tight text-foreground">Grouped findings and board surface context</h3>
                  </div>
                </div>
                <div className="grid gap-6 xl:grid-cols-[minmax(0,0.72fr)_minmax(0,1.28fr)]">
                  <div className="space-y-4">
                    {groupedRisks.map((item, index) => (
                      <button
                        type="button"
                        key={`${item.title}-${index}`}
                        onClick={() => setCategoryFilter((item.title || "General") === categoryFilter ? "all" : (item.title || "General"))}
                        className={`block w-full rounded-2xl px-2 py-2 text-left transition-colors ${categoryFilter === (item.title || "General") ? "bg-primary/8" : "hover:bg-white/4"}`}
                      >
                        <div className="mb-1.5 flex items-center justify-between text-sm">
                          <span>{item.title || "General"}</span>
                          <span className="font-mono text-xs text-muted-foreground">{item.count || 0} findings</span>
                        </div>
                        <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                          <div className="h-full rounded-full bg-primary" style={{ width: `${Math.min(Number(item.count || 0) * 8, 100)}%` }} />
                        </div>
                      </button>
                    ))}
                  </div>
                  <BoardHeatmap
                    title="Board hotspot map"
                    boardView={result.board_view}
                    focusSummary={selectedFinding ? {
                      title: "Linked issue focus",
                      detail: `Selected finding: ${selectedFinding.message || "Unnamed issue"} · ${(selectedFinding.components || []).length || 0} components · ${(selectedFinding.nets || []).length || 0} nets`,
                    } : null}
                    linkedFinding={selectedFinding ? {
                      message: selectedFinding.message,
                      components: selectedFinding.components || [],
                      nets: selectedFinding.nets || [],
                    } : null}
                  />
                </div>
              </div>
            </div>

            <div className="grid gap-4 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
              <AnalysisSurface title="Severity mix" rail="signal profile">
                {severityData.length ? (
                  <div className="space-y-4">
                    <SeverityDonut
                      data={severityData}
                      activeKey={severityFilter === "all" ? undefined : severityFilter}
                      onSelect={(value) => setSeverityFilter(value === severityFilter ? "all" : value as typeof severityFilter)}
                    />
                    <FilterPills
                      active={severityFilter}
                      onChange={setSeverityFilter}
                      options={[
                        { value: "all", label: "All", count: severityCounts.all },
                        { value: "critical", label: "Critical", count: severityCounts.critical },
                        { value: "high", label: "High", count: severityCounts.high },
                        { value: "medium", label: "Medium", count: severityCounts.medium },
                        { value: "low", label: "Low", count: severityCounts.low },
                      ]}
                    />
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No severity breakdown is available for this run yet.</p>
                )}
              </AnalysisSurface>

              <AnalysisSurface title="Category distribution" rail="domain stack">
                {categoryChartData.length ? (
                  <div className="space-y-4">
                    <CategoryBreakdown data={categoryChartData} activeCategory={categoryFilter === "all" ? undefined : categoryFilter} onSelect={(value) => setCategoryFilter(value === categoryFilter ? "all" : value)} />
                    <FilterPills
                      active={categoryFilter}
                      onChange={setCategoryFilter}
                      options={categoryOptions.map((value) => ({
                        value,
                        label: value === "all" ? "All categories" : value,
                        count: value === "all" ? groupedRisks.length : groupedRisks.find((item) => (item.title || "General") === value)?.count ?? 0,
                      }))}
                    />
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">Category-level distribution appears after Silicore groups findings for the uploaded board.</p>
                )}
              </AnalysisSurface>
            </div>

            <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
              <AnalysisSurface title="Board signal" rail="readout">
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
              </AnalysisSurface>
              <AnalysisSurface title="Run posture" rail="analysis metadata">
                <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
                  <SignalStat label="Filtered findings" value={String(filteredRisks.length)} />
                  <SignalStat label="Top component" value={highestComponent?.label || "—"} />
                  <SignalStat label="Top net" value={highestNet?.label || "—"} />
                </div>
                <div className="mt-4 rounded-2xl border border-border bg-background/40 p-4 text-sm leading-7 text-muted-foreground">
                  The result view now lets you narrow the risk field by severity and category before you commit to a fix path, so charts act like controls instead of static decoration.
                </div>
              </AnalysisSurface>
            </div>

            <div className="grid gap-4 xl:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)]">
              <AnalysisSurface title="Focused finding" rail="issue drill-down" action={<span className="font-mono text-xs text-muted-foreground">{selectedFinding ? "selected" : "idle"}</span>}>
                {selectedFinding ? (
                  <FocusedFindingCard risk={selectedFinding} />
                ) : (
                  <EmptySurface
                    eyebrow="Focused finding"
                    title="Pick a finding to inspect its evidence."
                    copy="The selected issue here becomes the drill-down context for confidence, traceability, and remediation planning."
                  />
                )}
              </AnalysisSurface>

              <AnalysisSurface title="Trust & explainability" rail="why Silicore said this">
                <TrustSurface
                  score={Math.round(Number(result.score || 0))}
                  totalFindings={risks.length}
                  topCategory={topCategory?.title || "General"}
                  lowConfidenceCount={lowestConfidenceBucket}
                  selectedFinding={selectedFinding}
                />
              </AnalysisSurface>
            </div>

            <div className="grid gap-4 xl:grid-cols-2">
              <AnalysisSurface title="Penalty contribution" rail="score drag">
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
              </AnalysisSurface>

              <AnalysisSurface title="Confidence distribution" rail="evidence confidence">
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
              </AnalysisSurface>
            </div>

            <div className="grid gap-4 xl:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)]">
              <AnalysisSurface title="Component hotspot leaderboard" rail="component pressure">
                {componentLeaderboard.length ? (
                  <Leaderboard items={componentLeaderboard} accent="oklch(0.84 0.15 205)" />
                ) : (
                  <p className="text-sm text-muted-foreground">No component-linked findings were preserved for this run.</p>
                )}
              </AnalysisSurface>

              <AnalysisSurface title="Net hotspot leaderboard" rail="net pressure">
                {netLeaderboard.length ? (
                  <Leaderboard items={netLeaderboard} accent="oklch(0.82 0.16 75)" />
                ) : (
                  <p className="text-sm text-muted-foreground">No net-linked findings were preserved for this run.</p>
                )}
              </AnalysisSurface>
            </div>

            <AnalysisSurface title="Traceability completeness" rail="audit readiness">
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
            </AnalysisSurface>

            <AnalysisSurface title="Artifacts" rail="exports">
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
            </AnalysisSurface>

            <AnalysisSurface title="Findings & recommendations" rail="action list" action={<span className="font-mono text-xs text-muted-foreground">{filteredRisks.length} visible</span>}>
              <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                <p className="max-w-2xl text-sm text-muted-foreground">
                  Use the severity donut, category stack, or grouped findings rail to focus this list on the exact issue cluster you want to work.
                </p>
                <FilterPills
                  active={severityFilter}
                  onChange={setSeverityFilter}
                  options={[
                    { value: "all", label: "All severities", count: severityCounts.all },
                    { value: "critical", label: "Critical", count: severityCounts.critical },
                    { value: "high", label: "High", count: severityCounts.high },
                    { value: "medium", label: "Medium", count: severityCounts.medium },
                    { value: "low", label: "Low", count: severityCounts.low },
                  ]}
                />
              </div>
              <div className="space-y-2">
                {filteredRisks.length ? (
                  filteredRisks.map((finding, index) => (
                    <FindingRow
                      key={`${finding.message}-${index}`}
                      risk={finding}
                      selected={findingKey(finding) === findingKey(selectedFinding)}
                      onSelect={() => setSelectedFindingKey(findingKey(finding))}
                    />
                  ))
                ) : (
                  <EmptySurface
                    eyebrow="Filtered view"
                    title="No findings match the current filters."
                    copy="Clear the severity or category filter and Silicore will bring the broader finding set back into view."
                  />
                )}
              </div>
            </AnalysisSurface>
          </>
        ) : (
          <EmptySurface
            eyebrow="Analysis ready"
            title="The analysis workstation is ready for a board."
            copy="Drop a board into the intake surface above and Silicore will populate score, grouped findings, traceability, and exports here in one continuous engineering workspace."
          />
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

function AnalysisSurface({
  title,
  rail,
  action,
  children,
}: {
  title: string;
  rail?: string;
  action?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section data-reveal className="relative overflow-hidden rounded-[28px] border border-white/8 bg-[linear-gradient(135deg,rgba(8,17,27,0.96),rgba(7,14,22,0.98))] p-6 shadow-[0_28px_72px_-44px_rgba(0,0,0,0.9)]">
      <div className="pointer-events-none absolute inset-y-0 left-0 w-px bg-gradient-to-b from-transparent via-primary/50 to-transparent" />
      <div className="relative">
        <div className="mb-5 flex items-start justify-between gap-4">
          <div className="min-w-0">
            {rail ? <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{rail}</div> : null}
            <h3 className="mt-1 text-lg font-medium tracking-tight">{title}</h3>
          </div>
          {action}
        </div>
        {children}
      </div>
    </section>
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

function FindingRow({
  risk,
  selected,
  onSelect,
}: {
  risk: Risk;
  selected?: boolean;
  onSelect?: () => void;
}) {
  const severity = (risk.severity || "low").toLowerCase();
  const map = {
    critical: { Icon: AlertCircle, cls: "text-danger bg-danger/10 border-danger/20" },
    medium: { Icon: AlertTriangle, cls: "text-warning bg-warning/10 border-warning/20" },
    low: { Icon: Info, cls: "text-primary bg-primary/10 border-primary/20" },
    high: { Icon: AlertTriangle, cls: "text-warning bg-warning/10 border-warning/20" },
  } as const;
  const { Icon, cls } = map[severity as keyof typeof map] ?? map.low;
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`group flex w-full items-start gap-4 rounded-xl border bg-background/40 p-4 text-left transition-colors hover:border-primary/30 ${
        selected ? "border-primary/35 bg-primary/8" : "border-border"
      }`}
    >
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
    </button>
  );
}

function findingKey(risk?: Risk | null) {
  return `${risk?.message || "issue"}|${risk?.category || "General"}|${risk?.recommendation || ""}`;
}

function flashTimerNeeded(value: boolean) {
  return typeof window !== "undefined" && value;
}

function SignalStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-background/40 p-4">
      <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
    </div>
  );
}

function FocusedFindingCard({ risk }: { risk: Risk }) {
  const confidence = Number(risk.transparency_view?.confidence_score || 0);
  const traceability = Number(risk.transparency_view?.traceability_score || 0);
  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-white/8 bg-background/35 p-5">
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-full border border-border px-2 py-1 font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
            {(risk.severity || "low").toUpperCase()}
          </span>
          <span className="rounded-full border border-border px-2 py-1 font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
            {risk.category || "General"}
          </span>
        </div>
        <h4 className="mt-4 text-xl font-semibold tracking-tight text-foreground">{risk.message || "Unnamed issue"}</h4>
        <p className="mt-3 text-sm leading-7 text-muted-foreground">{risk.recommendation || "Review this issue directly in layout and confirm the design intent."}</p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <SignalStat label="Confidence" value={String(confidence || 0)} />
        <SignalStat label="Traceability" value={String(traceability || 0)} />
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <TagBucket label="Components" values={risk.components || []} empty="No component references were preserved." />
        <TagBucket label="Nets" values={risk.nets || []} empty="No net references were preserved." />
      </div>
    </div>
  );
}

function TrustSurface({
  score,
  totalFindings,
  topCategory,
  lowConfidenceCount,
  selectedFinding,
}: {
  score: number;
  totalFindings: number;
  topCategory: string;
  lowConfidenceCount: number;
  selectedFinding: Risk | null;
}) {
  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-border bg-background/35 p-5 text-sm leading-7 text-muted-foreground">
        Silicore’s score is being dragged most by <span className="text-foreground">{topCategory}</span>, across <span className="text-foreground">{totalFindings}</span> findings. {lowConfidenceCount > 0 ? `${lowConfidenceCount} findings still sit in the lower-confidence band, so review those before treating the run as signoff-ready.` : "The run does not currently show any low-confidence findings, which makes the recommendation set easier to trust."}
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        <SignalStat label="Run score" value={String(score)} />
        <SignalStat label="Top drag" value={topCategory} />
        <SignalStat label="Low confidence" value={String(lowConfidenceCount)} />
      </div>
      <div className="rounded-2xl border border-border bg-background/35 p-5">
        <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">Selected issue rationale</div>
        <p className="mt-3 text-sm leading-7 text-muted-foreground">
          {selectedFinding
            ? `Silicore flagged "${selectedFinding.message || "this issue"}" under ${selectedFinding.category || "General"} with a confidence score of ${Number(selectedFinding.transparency_view?.confidence_score || 0)} and traceability score of ${Number(selectedFinding.transparency_view?.traceability_score || 0)}.`
            : "Select a finding from the action list and this panel will explain why it is in the result set and how trustworthy the evidence looks."}
        </p>
      </div>
    </div>
  );
}

function TagBucket({ label, values, empty }: { label: string; values: string[]; empty: string }) {
  return (
    <div className="rounded-xl border border-border bg-background/35 p-4">
      <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className="mt-3 flex flex-wrap gap-2">
        {values.length ? values.map((item) => (
          <span key={item} className="rounded-full border border-border px-2 py-1 text-xs text-muted-foreground">{item}</span>
        )) : <span className="text-sm text-muted-foreground">{empty}</span>}
      </div>
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
