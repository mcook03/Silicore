import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { PageHero } from "@/components/silicore/PageHero";
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
        <PageHero
          eyebrow={<><FolderKanban className="h-3.5 w-3.5" /> Workspace system</>}
          title="Organize boards into durable workspaces that stay ready for review, comparison, and release."
          description="Projects now act like a polished control layer over Silicore’s backend workflows, giving each workspace clearer identity, state, and action hierarchy."
          metrics={[
            { label: "Workspaces", value: String(data?.summary.total_projects ?? 0), copy: "Visible in your current view" },
            { label: "Linked runs", value: String(data?.summary.total_runs ?? 0), copy: "Attached to project history" },
            { label: "Create flow", value: creating ? "Busy" : "Ready", copy: "Launch a new workspace instantly" },
          ]}
          actions={
            <Button size="sm" onClick={onCreate} disabled={creating}>
              <Plus className="mr-1.5 h-3.5 w-3.5" /> New project
            </Button>
          }
        />
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
