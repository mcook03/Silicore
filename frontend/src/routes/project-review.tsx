import { useState } from "react";
import type { ReactNode } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { BoardHeatmap } from "@/components/silicore/BoardHeatmap";
import { ScoreTrend } from "@/components/silicore/AnalysisCharts";
import { Button } from "@/components/ui/button";
import { Upload, Layers, Sparkles } from "lucide-react";
import { apiPostForm, useApiData } from "@/lib/api";
import { CartesianGrid, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from "recharts";

const transparentCursor = { fill: "transparent", stroke: "transparent" };

export const Route = createFileRoute("/project-review")({
  head: () => ({ meta: [{ title: "Project review — Silicore" }] }),
  component: ProjectReview,
});

type ReviewOptions = {
  analysis_modes: {
    profiles: Array<{ value: string; label: string }>;
    board_types: Array<{ value: string; label: string }>;
  };
  project_options: Array<{ project_id: string; name: string }>;
};

type ProjectReviewResult = {
  project_result: {
    boards?: Array<{ filename?: string; score?: number; risks?: Array<{ severity?: string }> }>;
    summary?: { total_boards?: number; average_score?: number; best_score?: number; worst_score?: number };
  };
  comparison: {
    best_board?: { filename?: string; score?: number };
    worst_board?: { filename?: string; score?: number };
    score_spread?: number;
  };
  project_intelligence_review?: {
    category_heatmap?: Array<{
      category: string;
      total?: number;
      cells: Array<{ board?: string; value: number; tone: "none" | "light" | "medium" | "strong" }>;
    }>;
  };
};

function ProjectReview() {
  const { data: options } = useApiData<ReviewOptions>("/api/frontend/analyze/options");
  const [files, setFiles] = useState<File[]>([]);
  const [projectId, setProjectId] = useState("");
  const [profile, setProfile] = useState("balanced");
  const [boardType, setBoardType] = useState("general");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ProjectReviewResult | null>(null);

  const onSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!files.length) {
      setError("Upload at least one board file.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const formData = new FormData();
      files.forEach((file) => formData.append("project_files", file));
      formData.append("project_id", projectId);
      formData.append("analysis_profile", profile);
      formData.append("analysis_board_type", boardType);
      const payload = await apiPostForm<ProjectReviewResult>("/api/frontend/analyze/project", formData);
      setResult(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Project analysis failed.");
    } finally {
      setSubmitting(false);
    }
  };

  const boards = result?.project_result.boards ?? [];
  const summary = result?.project_result.summary ?? {};
  const boardTrend = boards.map((board, index) => ({
    label: `B${index + 1}`,
    score: normalizeScore(board.score),
  }));
  const boardVariance = boards.map((board) => ({
    name: board.filename || "Board",
    score: normalizeScore(board.score),
    risks: (board.risks || []).length,
  }));

  return (
    <AppShell title="Project review">
      <div className="mx-auto max-w-5xl space-y-6">
        <div>
          <h2 className="text-xl font-medium tracking-tight">Submit a multi-board project for review</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Upload a real set of board files and Silicore will compare the boards together inside the new UI.
          </p>
        </div>

        <form onSubmit={onSubmit} className="space-y-6">
          <ReviewStage title="Review setup" rail="project intake">
            <div className="grid gap-4 md:grid-cols-3">
              <Field label="Workspace">
                <select value={projectId} onChange={(event) => setProjectId(event.target.value)} className="h-10 w-full rounded-md border border-input bg-transparent px-3 text-sm">
                  <option value="">No workspace</option>
                  {(options?.project_options ?? []).map((option) => (
                    <option key={option.project_id} value={option.project_id}>{option.name}</option>
                  ))}
                </select>
              </Field>
              <Field label="Profile">
                <select value={profile} onChange={(event) => setProfile(event.target.value)} className="h-10 w-full rounded-md border border-input bg-transparent px-3 text-sm">
                  {(options?.analysis_modes.profiles ?? []).map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </Field>
              <Field label="Board type">
                <select value={boardType} onChange={(event) => setBoardType(event.target.value)} className="h-10 w-full rounded-md border border-input bg-transparent px-3 text-sm">
                  {(options?.analysis_modes.board_types ?? []).map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </Field>
            </div>
          </ReviewStage>

          <ReviewStage title="Boards in this review" rail="board queue" action={<span className="font-mono text-xs text-muted-foreground">{files.length} selected</span>}>
            <div className="space-y-2">
              {files.map((file) => (
                <div key={file.name} className="flex items-center justify-between rounded-xl border border-border bg-background/40 p-3.5">
                  <div className="flex items-center gap-3">
                    <Layers className="h-4 w-4 text-primary" />
                    <span className="text-sm">{file.name}</span>
                  </div>
                  <span className="font-mono text-xs text-muted-foreground">queued</span>
                </div>
              ))}
              <label className="block cursor-pointer rounded-xl border border-dashed border-border bg-background/40 p-6 text-center">
                <Upload className="mx-auto h-5 w-5 text-primary" />
                <div className="mt-2 text-sm">Drop board files here or click to select</div>
                <div className="font-mono text-[11px] text-muted-foreground">.zip · .brd · .kicad_pcb · .kicad_sch · .sch · .pro · .kicad_mod · .odb</div>
                <input
                  type="file"
                  multiple
                  className="hidden"
                  accept=".zip,.odb,.brd,.kicad_pcb,.kicad_sch,.sch,.pro,.kicad_mod,.pcbdocascii,.gbr,.gko,.ger,.gtl,.gbl,.gto,.gbo,.gts,.gbs,.gm1,.pho,.art,.outline,.drl,.xln,.txt"
                  onChange={(event) => setFiles(Array.from(event.target.files ?? []))}
                />
              </label>
              {error && <div className="rounded-lg border border-danger/20 bg-danger/10 px-3 py-2 text-sm text-danger">{error}</div>}
            </div>
          </ReviewStage>

          <div className="flex justify-end gap-2">
            <Button type="submit" size="sm" className="rounded-full" disabled={submitting}>
              <Sparkles className="mr-1.5 h-3.5 w-3.5" />
              {submitting ? "Analyzing…" : "Submit review"}
            </Button>
          </div>
        </form>

        {result && (
          <>
            <div className="grid gap-4 md:grid-cols-4">
              <SummaryStat label="Boards" value={String(summary.total_boards || 0)} />
              <SummaryStat label="Average score" value={String(normalizeScore(summary.average_score))} />
              <SummaryStat label="Best score" value={String(normalizeScore(summary.best_score))} />
              <SummaryStat label="Worst score" value={String(normalizeScore(summary.worst_score))} />
            </div>

            <div className="grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
              <BoardHeatmap
                title="Project hotspot map"
                matrixRows={result.project_intelligence_review?.category_heatmap}
                emptyCopy="This review needs categorized board findings before it can render a real project heat map."
              />
              <ReviewStage title="Review signal" rail="portfolio readout">
                <div className="space-y-4">
                  <div className="rounded-2xl border border-border bg-background/40 p-4 text-sm leading-6 text-muted-foreground">
                    Use this map as a quick scan for where board pressure would likely cluster across the reviewed set. Switch modes to read thermal, density, or findings emphasis before drilling into individual board results.
                  </div>
                  <div className="grid gap-3 sm:grid-cols-3">
                    <SummaryStat label="Boards loaded" value={String(boards.length)} />
                    <SummaryStat label="Best board" value={String(normalizeScore(result.comparison.best_board?.score))} />
                    <SummaryStat label="Spread" value={String(normalizeScore(result.comparison.score_spread))} />
                  </div>
                </div>
              </ReviewStage>
            </div>

            <ReviewStage title="Board score spread" rail="score spread">
              {boardTrend.length ? (
                <ScoreTrend data={boardTrend} />
              ) : (
                <p className="text-sm text-muted-foreground">Board-to-board score trend appears after a project review completes.</p>
              )}
            </ReviewStage>

            <ReviewStage title="Board-to-board variance" rail="variance field">
              {boardVariance.length ? (
                <ResponsiveContainer width="100%" height={300}>
                  <ScatterChart margin={{ top: 8, right: 18, bottom: 10, left: 0 }}>
                    <CartesianGrid stroke="oklch(0.28 0.014 250)" />
                    <XAxis type="number" dataKey="score" name="Score" tickLine={false} axisLine={false} stroke="oklch(0.55 0.018 250)" fontSize={11} domain={[0, 100]} />
                    <YAxis type="number" dataKey="risks" name="Findings" tickLine={false} axisLine={false} stroke="oklch(0.55 0.018 250)" fontSize={11} allowDecimals={false} />
                    <Tooltip cursor={transparentCursor} contentStyle={{ background: "oklch(0.19 0.014 250)", border: "1px solid oklch(0.28 0.014 250)", borderRadius: 8, fontSize: 12 }} formatter={(value, name) => [value, name === "score" ? "Score" : "Findings"]} labelFormatter={() => ""} />
                    <Scatter data={boardVariance} fill="oklch(0.84 0.15 205)" />
                  </ScatterChart>
                </ResponsiveContainer>
              ) : (
                <p className="text-sm text-muted-foreground">Variance plotting appears after Silicore has multiple boards to compare.</p>
              )}
            </ReviewStage>

            <ReviewStage title="Board comparison" rail="board ladder" action={<span className="font-mono text-xs text-muted-foreground">spread {result.comparison.score_spread || 0}</span>}>
              <div className="space-y-2">
                {boards.map((board) => {
                  const criticals = (board.risks ?? []).filter((risk) => (risk.severity || "").toLowerCase() === "critical").length;
                  return (
                    <div key={board.filename} className="flex items-center justify-between rounded-xl border border-border bg-background/40 p-4">
                      <div>
                        <div className="text-sm">{board.filename}</div>
                        <div className="font-mono text-[11px] text-muted-foreground">{criticals} critical findings</div>
                      </div>
                      <div className="text-lg font-semibold">{normalizeScore(board.score)}</div>
                    </div>
                  );
                })}
              </div>
            </ReviewStage>
          </>
        )}
      </div>
    </AppShell>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
      {children}
    </div>
  );
}

function SummaryStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-border bg-surface p-5">
      <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
    </div>
  );
}

function normalizeScore(value?: number) {
  const numeric = Number(value || 0);
  if (!Number.isFinite(numeric)) {
    return 0;
  }
  return Math.round(numeric <= 10 ? numeric * 10 : numeric);
}

function ReviewStage({
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
    <section data-reveal className="relative overflow-hidden rounded-[28px] border border-white/8 bg-[linear-gradient(155deg,rgba(8,17,27,0.96),rgba(7,14,22,0.98))] p-6 shadow-[0_28px_70px_-44px_rgba(0,0,0,0.92)]">
      <div className="mb-5 flex items-start justify-between gap-4 border-b border-white/8 pb-4">
        <div>
          {rail ? <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{rail}</div> : null}
          <h3 className="mt-1 text-lg font-medium tracking-tight">{title}</h3>
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}
