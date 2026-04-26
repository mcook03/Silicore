import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { ScorePill } from "@/components/silicore/Panel";
import { Button } from "@/components/ui/button";
import { Plus, FolderKanban, ArrowRight, Trash2 } from "lucide-react";
import { apiPostJson, useApiData } from "@/lib/api";

export const Route = createFileRoute("/projects")({
  head: () => ({ meta: [{ title: "Projects — Silicore" }] }),
  component: Projects,
});

type ProjectItem = {
  project_id: string;
  name: string;
  description: string;
  average_score: number;
  latest_score: number;
  open_assignment_count: number;
  open_release_gate_count: number;
  runs: Array<unknown>;
};

type ProjectsPayload = {
  projects: ProjectItem[];
  summary: { total_projects: number; total_runs: number };
};

function Projects() {
  const { data, loading, error, reload } = useApiData<ProjectsPayload>("/api/frontend/projects");
  const [creating, setCreating] = useState(false);

  const onCreate = async () => {
    const name = window.prompt("Project name");
    if (!name) return;
    setCreating(true);
    try {
      await apiPostJson("/api/frontend/projects", { name, description: "" });
      await reload();
    } finally {
      setCreating(false);
    }
  };

  return (
    <AppShell title="Projects">
      <div className="space-y-6">
        <section
          data-reveal
          className="relative overflow-hidden rounded-[34px] border border-border/80 bg-[linear-gradient(135deg,rgba(7,16,26,0.97),rgba(9,18,28,0.94)_58%,rgba(11,23,33,0.97))] px-6 py-7 sm:px-8 sm:py-8"
        >
          <div className="absolute inset-y-0 left-[34%] w-px bg-gradient-to-b from-transparent via-white/8 to-transparent max-xl:hidden" />
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_0%_0%,rgba(86,211,240,0.12),transparent_24%),radial-gradient(circle_at_100%_100%,rgba(125,178,255,0.12),transparent_28%)]" />
          <div className="relative grid gap-8 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
            <div className="min-w-0">
              <div className="section-eyebrow">
                <FolderKanban className="h-3.5 w-3.5" />
                Workspace system
              </div>
              <h2 className="mt-6 max-w-3xl text-4xl font-semibold tracking-tight text-foreground sm:text-[3.4rem] sm:leading-[0.98]">
                Organize boards into workspaces that feel active, owned, and ready for engineering review.
              </h2>
              <p className="mt-4 max-w-2xl text-base leading-8 text-muted-foreground">
                Instead of a generic project index, this page is shifting toward a workspace overview with state, ownership, and quick motion into the right board context.
              </p>
              <div className="mt-7 flex flex-wrap items-center gap-3">
                <Button size="sm" onClick={onCreate} disabled={creating}>
                  <Plus className="mr-1.5 h-3.5 w-3.5" /> New project
                </Button>
                <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                  {data?.summary.total_projects ?? 0} workspaces · {data?.summary.total_runs ?? 0} linked runs
                </span>
              </div>
            </div>

            <div className="grid content-start gap-4">
              <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
                <ProjectSignal label="Workspaces" value={String(data?.summary.total_projects ?? 0)} copy="Visible in your current view" />
                <ProjectSignal label="Linked runs" value={String(data?.summary.total_runs ?? 0)} copy="Attached to workspace history" />
                <ProjectSignal label="Create flow" value={creating ? "Busy" : "Ready"} copy="Launch new workspace instantly" />
              </div>
            </div>
          </div>
        </section>
        {error ? (
          <div className="rounded-xl border border-danger/20 bg-danger/10 px-4 py-3 text-sm text-danger">{error}</div>
        ) : null}
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {(data?.projects ?? []).map((project) => (
            <div key={project.project_id} data-reveal className="premium-card group rounded-[26px] p-6">
              <div className="flex items-start justify-between gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <FolderKanban className="h-5 w-5" />
                </div>
                <ScorePill score={Math.round(project.latest_score || project.average_score || 0)} />
              </div>
              <a href={`/projects/${project.project_id}`} className="block">
                <h3 className="mt-4 text-lg font-medium">{project.name}</h3>
                <p className="text-sm text-muted-foreground">{project.description || "No description yet."}</p>
              </a>
              <div className="mt-5 grid grid-cols-3 gap-3 border-t border-border pt-4 text-center">
                <Stat label="runs" value={String(project.runs.length)} />
                <Stat label="avg score" value={String(Math.round(project.average_score || 0))} />
                <Stat label="open items" value={String((project.open_assignment_count || 0) + (project.open_release_gate_count || 0))} />
              </div>
              <div className="mt-4 flex items-center justify-between gap-3 text-xs">
                <span className="font-mono text-muted-foreground">{loading ? "Loading…" : project.project_id}</span>
                <div className="flex items-center gap-2">
                  <form
                    method="post"
                    action={`/projects/${project.project_id}/delete`}
                    onSubmit={(event) => {
                      if (!window.confirm(`Delete project "${project.name}"? This cannot be undone.`)) {
                        event.preventDefault();
                      }
                    }}
                  >
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-8 rounded-full border border-danger/25 bg-danger/10 px-3 text-danger hover:bg-danger/15 hover:text-danger"
                      type="submit"
                    >
                      <Trash2 className="mr-1.5 h-3.5 w-3.5" />
                      Delete
                    </Button>
                  </form>
                  <Button
                    asChild
                    size="sm"
                    variant="ghost"
                    className="h-8 rounded-full border border-primary/20 bg-primary/10 px-3 text-primary hover:bg-primary/15 hover:text-primary"
                  >
                    <a href={`/projects/${project.project_id}`}>
                      Open <ArrowRight className="h-3.5 w-3.5" />
                    </a>
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </AppShell>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-base font-semibold">{value}</div>
      <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
    </div>
  );
}

function ProjectSignal({ label, value, copy }: { label: string; value: string; copy: string }) {
  return (
    <div className="border-l border-white/10 pl-4">
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{label}</div>
      <div className="mt-1 text-3xl font-semibold text-foreground">{value}</div>
      <div className="mt-1 text-sm text-muted-foreground">{copy}</div>
    </div>
  );
}
