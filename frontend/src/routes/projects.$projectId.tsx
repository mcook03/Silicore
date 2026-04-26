import { useState } from "react";
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { BoardHeatmap } from "@/components/silicore/BoardHeatmap";
import { ScoreTrend } from "@/components/silicore/AnalysisCharts";
import { Panel, ScorePill } from "@/components/silicore/Panel";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  ArrowLeft, Users, MessageSquare, ShieldCheck, GitBranch, CheckCircle2,
  CircleDot, Clock, FileCheck2, AlertTriangle, Trash2,
} from "lucide-react";
import { apiDelete, apiPostJson, useApiData } from "@/lib/api";

export const Route = createFileRoute("/projects/$projectId")({
  head: () => ({ meta: [{ title: "Project detail — Silicore" }] }),
  component: ProjectDetail,
});

type ProjectDetailPayload = {
  project: {
    project_id: string;
    name: string;
    description: string;
    latest_score: number;
    runs: Array<{ run_id: string; name?: string; score?: number; critical_count?: number }>;
    owner_name?: string;
    team_members?: Array<{ name?: string; member_role?: string }>;
    release_gates?: Array<{ gate_id: string; title?: string; status?: string; approval_count?: number; required_approvals?: number }>;
  };
  review_feed: Array<{ review_id?: string; actor_name?: string; created_at?: string; summary?: string; status_label?: string }>;
  risk_heatmap?: Array<{
    category: string;
    total?: number;
    cells: Array<{ label?: string; value: number; tone: "none" | "light" | "medium" | "strong" }>;
  }>;
};

function ProjectDetail() {
  const { projectId } = Route.useParams();
  const navigate = useNavigate();
  const { data, error, reload } = useApiData<ProjectDetailPayload>(`/api/frontend/projects/${projectId}`);
  const [note, setNote] = useState("");
  const [reviewSummary, setReviewSummary] = useState("");
  const [reviewStatus, setReviewStatus] = useState("approved");
  const [deleting, setDeleting] = useState(false);

  const submitNote = async () => {
    if (!note.trim()) return;
    await apiPostJson(`/api/frontend/projects/${projectId}/notes`, { author: "Silicore UI", body: note });
    setNote("");
    await reload();
  };

  const submitReview = async () => {
    if (!reviewSummary.trim()) return;
    await apiPostJson(`/api/frontend/projects/${projectId}/reviews`, { status: reviewStatus, summary: reviewSummary });
    setReviewSummary("");
    await reload();
  };

  const removeProject = async () => {
    if (!project || !window.confirm(`Delete project "${project.name}"? This cannot be undone.`)) {
      return;
    }
    setDeleting(true);
    try {
      await apiDelete(`/api/frontend/projects/${projectId}`);
      await navigate({ to: "/projects" });
    } finally {
      setDeleting(false);
    }
  };

  const project = data?.project;
  const reviewFeed = data?.review_feed ?? [];
  const runTrend = (project?.runs || []).slice(0, 6).reverse().map((run, index) => ({
    label: `R${index + 1}`,
    score: normalizeRunScore(run.score),
  }));

  return (
    <AppShell title={project?.name || "Project detail"}>
      <div className="space-y-6">
        <Link to="/projects" className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-3 w-3" /> All projects
        </Link>

        {error ? (
          <div className="rounded-xl border border-danger/20 bg-danger/10 px-4 py-3 text-sm text-danger">{error}</div>
        ) : null}

        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="font-mono text-xs uppercase tracking-wider text-muted-foreground">project · {projectId}</div>
            <h2 className="mt-1 text-2xl font-medium tracking-tight">{project?.name || "Loading…"}</h2>
            <p className="mt-1 text-sm text-muted-foreground">{project?.description || "No description yet."}</p>
          </div>
          <div className="flex items-center gap-2">
            <ScorePill score={Math.round(project?.latest_score || 0)} />
            <Button size="sm" variant="ghost" className="rounded-full">Owner: {project?.owner_name || "Unassigned"}</Button>
            <Button
              size="sm"
              variant="ghost"
              className="rounded-full border border-danger/25 bg-danger/10 text-danger hover:bg-danger/15 hover:text-danger"
              disabled={deleting}
              onClick={() => void removeProject()}
            >
              <Trash2 className="mr-1.5 h-3.5 w-3.5" />
              {deleting ? "Deleting…" : "Delete project"}
            </Button>
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          <Stat label="Runs" value={String(project?.runs.length || 0)} icon={GitBranch} />
          <Stat label="Open critical" value={String((project?.runs || []).reduce((sum, run) => sum + Number(run.critical_count || 0), 0))} tone="danger" icon={AlertTriangle} />
          <Stat label="Pending approvals" value={String((project?.release_gates || []).filter((gate) => !["approved", "rejected"].includes((gate.status || "").toLowerCase())).length)} tone="warning" icon={Clock} />
        </div>

        <div className="grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
          <BoardHeatmap
            title="Project hotspot overview"
            matrixRows={data?.risk_heatmap}
            emptyCopy="This project needs linked run findings before a real heat map can be shown."
          />
          <Panel title="Project signal">
            <div className="space-y-4">
              <div className="rounded-2xl border border-border bg-background/40 p-4 text-sm leading-6 text-muted-foreground">
                This view adds a spatial overview for the current project so you can scan likely risk concentration before diving into release gates, notes, or individual runs.
              </div>
              <div className="grid gap-3 sm:grid-cols-3">
                <QuickStat label="Latest score" value={String(Math.round(project?.latest_score || 0))} />
                <QuickStat label="Team size" value={String((project?.team_members || []).length)} />
                <QuickStat label="Gates" value={String((project?.release_gates || []).length)} />
              </div>
            </div>
          </Panel>
        </div>

        <Panel title="Run score trend">
          {runTrend.length ? (
            <ScoreTrend data={runTrend} />
          ) : (
            <p className="text-sm text-muted-foreground">Run trend data appears here as soon as this project has recorded analyses.</p>
          )}
        </Panel>

        <div className="grid gap-4 lg:grid-cols-[1fr_360px]">
          <Panel title="Runs">
            <div className="space-y-2">
              {(project?.runs || []).map((run) => (
                <div key={run.run_id} className="flex items-center justify-between rounded-xl border border-border bg-background/40 p-4">
                  <div>
                    <div className="text-sm">{run.name || run.run_id}</div>
                    <div className="font-mono text-[11px] text-muted-foreground">{run.critical_count || 0} critical findings</div>
                  </div>
                  <ScorePill score={normalizeRunScore(run.score)} />
                </div>
              ))}
            </div>
          </Panel>

          <Panel title="Members" action={<Users className="h-4 w-4 text-muted-foreground" />}>
            <div className="space-y-3">
              {(project?.team_members || []).map((member, index) => (
                <div key={`${member.name}-${index}`} className="rounded-xl border border-border bg-background/40 p-3">
                  <div className="text-sm">{member.name || "Member"}</div>
                  <div className="font-mono text-[11px] text-muted-foreground">{member.member_role || "viewer"}</div>
                </div>
              ))}
            </div>
          </Panel>
        </div>

        <Panel title="Release gates" action={<ShieldCheck className="h-4 w-4 text-muted-foreground" />}>
          <div className="grid gap-3 md:grid-cols-2">
            {(project?.release_gates || []).map((gate) => (
              <div key={gate.gate_id} className="flex items-center justify-between rounded-xl border border-border bg-background/40 p-4">
                <div className="flex items-center gap-3">
                  <span className={`flex h-8 w-8 items-center justify-center rounded-md border ${
                    (gate.status || "").toLowerCase() === "approved" ? "border-success/30 bg-success/10 text-success" :
                    (gate.status || "").toLowerCase() === "blocked" ? "border-danger/30 bg-danger/10 text-danger" :
                    "border-warning/30 bg-warning/10 text-warning"
                  }`}>
                    {(gate.status || "").toLowerCase() === "approved" ? <CheckCircle2 className="h-4 w-4" /> :
                      (gate.status || "").toLowerCase() === "blocked" ? <AlertTriangle className="h-4 w-4" /> :
                      <CircleDot className="h-4 w-4" />}
                  </span>
                  <div>
                    <div className="text-sm">{gate.title || "Release gate"}</div>
                    <div className="font-mono text-[11px] text-muted-foreground">{gate.approval_count || 0} / {gate.required_approvals || 0} approvals</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Panel>

        <div className="grid gap-4 lg:grid-cols-2">
          <Panel title="Notes & activity" action={<MessageSquare className="h-4 w-4 text-muted-foreground" />}>
            <div className="space-y-3">
              {reviewFeed.map((item, index) => (
                <div key={`${item.review_id || "review"}-${index}`} className="rounded-xl border border-border bg-background/40 p-4">
                  <div className="flex items-center justify-between">
                    <div className="text-sm">{item.actor_name || "Reviewer"}</div>
                    <div className="font-mono text-[11px] text-muted-foreground">{item.created_at || "recent"}</div>
                  </div>
                  <p className="mt-1.5 text-sm text-muted-foreground">{item.summary || item.status_label || "Review update"}</p>
                </div>
              ))}
              <div className="space-y-2 pt-2">
                <Textarea value={note} onChange={(event) => setNote(event.target.value)} placeholder="Add a note for the team…" className="min-h-[80px]" />
                <div className="flex justify-end">
                  <Button size="sm" className="rounded-full" onClick={() => void submitNote()}>Post note</Button>
                </div>
              </div>
            </div>
          </Panel>

          <Panel title="Submit a review" action={<FileCheck2 className="h-4 w-4 text-muted-foreground" />}>
            <div className="space-y-3">
              <div className="space-y-1.5">
                <label className="text-xs uppercase tracking-wider text-muted-foreground">Verdict</label>
                <select value={reviewStatus} onChange={(event) => setReviewStatus(event.target.value)} className="h-10 w-full rounded-md border border-input bg-transparent px-3 text-sm">
                  <option value="approved">Approve</option>
                  <option value="changes_requested">Request changes</option>
                  <option value="blocked">Block</option>
                </select>
              </div>
              <div className="space-y-1.5">
                <label className="text-xs uppercase tracking-wider text-muted-foreground">Summary</label>
                <Textarea value={reviewSummary} onChange={(event) => setReviewSummary(event.target.value)} placeholder="Findings, follow-ups, blockers…" className="min-h-[100px]" />
              </div>
              <Button className="w-full rounded-full" onClick={() => void submitReview()}>Submit review</Button>
            </div>
          </Panel>
        </div>
      </div>
    </AppShell>
  );
}

function Stat({ label, value, tone, icon: Icon }: { label: string; value: string; tone?: "danger" | "warning"; icon: typeof Users }) {
  const c = tone === "danger" ? "text-danger" : tone === "warning" ? "text-warning" : "text-foreground";
  return (
    <div className="rounded-2xl border border-border bg-surface p-5">
      <div className="flex items-center justify-between">
        <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</span>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </div>
      <div className={`mt-2 text-2xl font-semibold ${c}`}>{value}</div>
    </div>
  );
}

function normalizeRunScore(value?: number) {
  const numeric = Number(value || 0);
  if (!Number.isFinite(numeric)) {
    return 0;
  }
  return Math.round(numeric <= 10 ? numeric * 10 : numeric);
}

function QuickStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-background/40 p-4">
      <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className="mt-2 text-xl font-semibold">{value}</div>
    </div>
  );
}
