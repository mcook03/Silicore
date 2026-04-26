import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { Panel } from "@/components/silicore/Panel";
import { BoardHeatmap } from "@/components/silicore/BoardHeatmap";
import { ScoreRing } from "@/components/silicore/ScoreRing";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Download, FileText } from "lucide-react";
import { useApiData } from "@/lib/api";

export const Route = createFileRoute("/history/$runDir")({
  head: () => ({ meta: [{ title: "Run detail — Silicore" }] }),
  component: RunDetail,
});

type RunDetailPayload = {
  run_dir?: string;
  name?: string;
  result?: { score?: number; health_summary?: string | { title?: string; summary?: string } };
  files?: Array<{ filename: string; kind: string; run_dir: string }>;
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

function RunDetail() {
  const { runDir } = Route.useParams();
  const { data, error } = useApiData<RunDetailPayload>(`/api/frontend/history/${runDir}`);
  const healthSummaryText = typeof data?.result?.health_summary === "string"
    ? data.result.health_summary
    : data?.result?.health_summary?.summary || data?.result?.health_summary?.title || "Run loaded.";
  return (
    <AppShell title="Run detail">
      <div className="space-y-6">
        <Link to="/history" className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-3 w-3" /> All runs
        </Link>

        {error ? <div className="rounded-xl border border-danger/20 bg-danger/10 px-4 py-3 text-sm text-danger">{error}</div> : null}

        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="font-mono text-xs uppercase tracking-wider text-muted-foreground">run · {runDir}</div>
            <h2 className="mt-1 text-2xl font-medium tracking-tight">{data?.name || runDir}</h2>
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-[320px_1fr]">
          <div className="rounded-2xl border border-border bg-surface p-6">
            <div className="flex flex-col items-center">
              <ScoreRing score={Math.round(Number(data?.result?.score || 0))} size={160} />
              <div className="mt-4 text-sm">{healthSummaryText}</div>
            </div>
          </div>

          <Panel title="Run artifacts" action={<FileText className="h-4 w-4 text-muted-foreground" />}>
            <div className="space-y-2">
              {(data?.files ?? []).map((file) => (
                <div key={file.filename} className="flex items-center justify-between rounded-xl border border-border bg-background/40 p-3.5">
                  <div className="flex items-center gap-3">
                    <FileText className="h-4 w-4 text-primary" />
                    <span className="font-mono text-sm">{file.filename}</span>
                  </div>
                  <Button asChild size="sm" variant="ghost" className="h-7 rounded-full text-xs">
                    <a href={`/download/${runDir}/${file.filename}`}><Download className="h-3 w-3" /></a>
                  </Button>
                </div>
              ))}
            </div>
          </Panel>
        </div>

        <div className="grid gap-4 xl:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)]">
          <BoardHeatmap
            title="Run hotspot map"
            boardView={data?.board_view}
            emptyCopy="This saved run does not include enough board geometry to render a spatial hotspot map."
          />
          <Panel title="Spatial readout">
            <div className="space-y-4">
              <div className="rounded-2xl border border-border bg-background/40 p-4 text-sm leading-6 text-muted-foreground">
                This view adds a spatial lens to the saved run so you can quickly scan where thermal pressure, density, or findings intensity would likely surface before downloading artifacts or opening the original deliverables.
              </div>
              <div className="grid gap-3 sm:grid-cols-3">
                <RunStat label="Score" value={String(Math.round(Number(data?.result?.score || 0)))} />
                <RunStat label="Artifacts" value={String((data?.files ?? []).length)} />
                <RunStat label="Run id" value={runDir.slice(0, 8)} />
              </div>
            </div>
          </Panel>
        </div>
      </div>
    </AppShell>
  );
}

function RunStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-background/40 p-4">
      <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className="mt-2 text-xl font-semibold">{value}</div>
    </div>
  );
}
