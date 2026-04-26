import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { Panel } from "@/components/silicore/Panel";
import { Button } from "@/components/ui/button";
import { Upload, Layers, Sparkles } from "lucide-react";
import { apiPostForm, useApiData } from "@/lib/api";

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
          <Panel title="Review setup">
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
          </Panel>

          <Panel title="Boards in this review" action={<span className="font-mono text-xs text-muted-foreground">{files.length} selected</span>}>
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
                <div className="font-mono text-[11px] text-muted-foreground">.zip · .brd · .kicad_pcb · .odb</div>
                <input
                  type="file"
                  multiple
                  className="hidden"
                  accept=".zip,.odb,.brd,.kicad_pcb,.pcbdocascii,.gbr,.gko,.ger,.gtl,.gbl,.gto,.gbo,.gts,.gbs,.gm1,.pho,.art,.outline,.drl,.xln,.txt"
                  onChange={(event) => setFiles(Array.from(event.target.files ?? []))}
                />
              </label>
              {error && <div className="rounded-lg border border-danger/20 bg-danger/10 px-3 py-2 text-sm text-danger">{error}</div>}
            </div>
          </Panel>

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

            <Panel title="Board comparison" action={<span className="font-mono text-xs text-muted-foreground">spread {result.comparison.score_spread || 0}</span>}>
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
            </Panel>
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
