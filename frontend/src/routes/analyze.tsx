import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { ScoreRing } from "@/components/silicore/ScoreRing";
import { Panel } from "@/components/silicore/Panel";
import { Button } from "@/components/ui/button";
import { Upload, FileUp, Sparkles, AlertTriangle, AlertCircle, Info, CheckCircle2, ChevronRight, Download } from "lucide-react";
import { BoardHeatmap } from "@/components/silicore/BoardHeatmap";
import { SeverityDonut, CategoryBreakdown } from "@/components/silicore/AnalysisCharts";
import { apiPostForm, useApiData } from "@/lib/api";

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
};

type AnalysisResultPayload = {
  result: {
    filename?: string;
    score?: number;
    health_summary?: string;
    risks?: Risk[];
    grouped_risks?: Array<{ title?: string; count?: number }>;
    downloads?: Record<string, string>;
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
  const risks = result?.risks ?? [];
  const severityData = [
    { name: "critical", value: risks.filter((item) => (item.severity || "").toLowerCase() === "critical").length },
    { name: "medium", value: risks.filter((item) => (item.severity || "").toLowerCase() === "medium").length },
    { name: "low", value: risks.filter((item) => !["critical", "medium"].includes((item.severity || "").toLowerCase())).length },
  ].filter((item) => item.value > 0);
  const categoryData = (result?.grouped_risks ?? []).map((item) => ({
    category: item.title || "General",
    critical: 0,
    medium: 0,
    low: Number(item.count || 0),
  }));

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
        <form onSubmit={onSubmit} className="relative overflow-hidden rounded-2xl border border-dashed border-border bg-surface p-8">
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
                  className="h-10 w-full rounded-md border border-input bg-transparent px-3 text-sm"
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
                  className="h-10 w-full rounded-md border border-input bg-transparent px-3 text-sm"
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
                  className="h-10 w-full rounded-md border border-input bg-transparent px-3 text-sm"
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
                    <div className="text-sm">{result.health_summary || "Analysis complete."}</div>
                  </div>
                </div>
                <div className="mt-6 grid grid-cols-3 gap-2 border-t border-border pt-4 text-center">
                  <Tally tone="danger" label="critical" n={severityData.find((item) => item.name === "critical")?.value ?? 0} />
                  <Tally tone="warning" label="medium" n={severityData.find((item) => item.name === "medium")?.value ?? 0} />
                  <Tally tone="muted" label="low" n={severityData.find((item) => item.name === "low")?.value ?? 0} />
                </div>
                <div className="mt-6 flex flex-wrap gap-2">
                  {Object.entries(result.downloads || {}).map(([label, href]) => (
                    <a key={label} href={href} className="inline-flex items-center gap-1 rounded-full border border-border px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground">
                      <Download className="h-3 w-3" /> {label}
                    </a>
                  ))}
                </div>
              </div>

              <Panel title="Category summary">
                <div className="space-y-4">
                  {(result.grouped_risks ?? []).map((item) => (
                    <div key={item.title}>
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

            <div className="grid gap-4 lg:grid-cols-[1fr_360px]">
              <BoardHeatmap title={`Board heatmap · ${result.filename || "board"}`} />
              <Panel title="Severity mix">
                <SeverityDonut data={severityData} />
              </Panel>
            </div>

            <Panel title="Findings by category">
              <CategoryBreakdown data={categoryData} />
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
