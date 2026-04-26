import { useState } from "react";
import { createFileRoute, Link, Outlet, useLocation } from "@tanstack/react-router";
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
  const location = useLocation();
  const { data, error, reload } = useApiData<ProjectsPayload>("/api/frontend/projects");
  const [creating, setCreating] = useState(false);

  if (location.pathname !== "/projects") {
    return <Outlet />;
  }

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
          className="editorial-surface instrument-grid rounded-[38px] px-6 py-7 sm:px-8 sm:py-8"
        >
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
                This should feel closer to a workspace switchboard than a list of boxes: active programs, review pressure, and quick motion into the right engineering context.
              </p>
              <div className="mt-7 flex flex-wrap items-center gap-3">
                <Button size="sm" className="rounded-full" onClick={onCreate} disabled={creating}>
                  <Plus className="mr-1.5 h-3.5 w-3.5" /> New project
                </Button>
                <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                  {data?.summary.total_projects ?? 0} workspaces · {data?.summary.total_runs ?? 0} linked runs
                </span>
              </div>
            </div>

            <div className="grid content-start gap-4">
              <div className="command-strip rounded-[28px] p-5">
                <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Workspace telemetry</div>
                <div className="mt-5 grid gap-5 sm:grid-cols-3 xl:grid-cols-1">
                  <ProjectSignal label="Workspaces" value={String(data?.summary.total_projects ?? 0)} copy="Visible in your current view" />
                  <ProjectSignal label="Linked runs" value={String(data?.summary.total_runs ?? 0)} copy="Attached to workspace history" />
                  <ProjectSignal label="Create flow" value={creating ? "Busy" : "Ready"} copy="Launch new workspace instantly" />
                </div>
              </div>
            </div>
          </div>
        </section>
        {error ? (
          <div className="rounded-xl border border-danger/20 bg-danger/10 px-4 py-3 text-sm text-danger">{error}</div>
        ) : null}
        <div className="space-y-4">
          {(data?.projects ?? []).map((project) => (
            <article key={project.project_id} data-reveal className="workspace-ribbon overflow-hidden p-5 sm:p-6">
              <div className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)]">
                <div className="min-w-0">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-4">
                      <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-primary/18 bg-primary/10 text-primary">
                        <FolderKanban className="h-5 w-5" />
                      </div>
                      <div className="min-w-0">
                        <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{project.project_id}</div>
                        <a href={`/projects/${project.project_id}`} className="mt-1 block text-2xl font-medium tracking-tight text-foreground hover:text-primary">
                          {project.name}
                        </a>
                      </div>
                    </div>
                    <ScorePill score={Math.round(project.latest_score || project.average_score || 0)} />
                  </div>

                  <p className="mt-4 max-w-3xl text-sm leading-7 text-muted-foreground">
                    {project.description || "No description yet. Add context so this workspace reads like an active engineering program instead of a blank container."}
                  </p>

                  <div className="mt-5 grid gap-4 sm:grid-cols-3">
                    <WorkspaceMetric label="Runs" value={String(project.runs.length)} copy="Linked to this workspace timeline" />
                    <WorkspaceMetric label="Average score" value={String(Math.round(project.average_score || 0))} copy="Blended across connected revisions" />
                    <WorkspaceMetric label="Open items" value={String((project.open_assignment_count || 0) + (project.open_release_gate_count || 0))} copy="Assignments and release gates still active" />
                  </div>
                </div>

                <div className="command-strip grid gap-4 rounded-[28px] p-5">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Action rail</div>
                      <div className="mt-1 text-lg font-medium tracking-tight text-foreground">Open the workspace or retire it</div>
                    </div>
                    <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
                      {project.latest_score ? `latest ${Math.round(project.latest_score)}` : "new"}
                    </div>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2">
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
                        className="h-11 w-full rounded-2xl border border-danger/25 bg-danger/10 px-4 text-danger hover:bg-danger/15 hover:text-danger"
                        type="submit"
                      >
                        <Trash2 className="mr-1.5 h-3.5 w-3.5" />
                        Delete workspace
                      </Button>
                    </form>
                    <Link
                      to="/projects/$projectId"
                      params={{ projectId: project.project_id }}
                      className="inline-flex h-11 items-center justify-center gap-2 rounded-2xl border border-primary/20 bg-primary/10 px-4 text-sm font-medium text-primary transition-colors hover:bg-primary/15 hover:text-primary"
                    >
                      Open workspace <ArrowRight className="h-3.5 w-3.5" />
                    </Link>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2">
                    <WorkspacePulse label="Assignments" value={String(project.open_assignment_count || 0)} />
                    <WorkspacePulse label="Release gates" value={String(project.open_release_gate_count || 0)} />
                  </div>
                </div>
              </div>
            </article>
          ))}
        </div>
      </div>
    </AppShell>
  );
}

function WorkspaceMetric({ label, value, copy }: { label: string; value: string; copy: string }) {
  return (
    <div className="signal-rail">
      <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className="mt-1 text-2xl font-semibold text-foreground">{value}</div>
      <div className="mt-1 text-sm text-muted-foreground">{copy}</div>
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

function WorkspacePulse({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/7 bg-white/3 px-4 py-3">
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{label}</div>
      <div className="mt-2 text-xl font-semibold text-foreground">{value}</div>
    </div>
  );
}
