import { useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { ScorePill } from "@/components/silicore/Panel";
import { Button } from "@/components/ui/button";
import { Plus, FolderKanban, ArrowRight, Trash2 } from "lucide-react";
import { apiDelete, apiPostJson, useApiData } from "@/lib/api";

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
  const [deletingId, setDeletingId] = useState("");

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

  const onDelete = async (projectId: string, name: string) => {
    if (!window.confirm(`Delete project "${name}"? This cannot be undone.`)) {
      return;
    }
    setDeletingId(projectId);
    try {
      await apiDelete(`/api/frontend/projects/${projectId}`);
      await reload();
    } finally {
      setDeletingId("");
    }
  };

  return (
    <AppShell title="Projects">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            {data?.summary.total_projects ?? 0} workspaces · {data?.summary.total_runs ?? 0} linked runs
          </p>
          <Button size="sm" className="rounded-full" onClick={onCreate} disabled={creating}>
            <Plus className="mr-1.5 h-3.5 w-3.5" /> New project
          </Button>
        </div>
        {error ? (
          <div className="rounded-xl border border-danger/20 bg-danger/10 px-4 py-3 text-sm text-danger">{error}</div>
        ) : null}
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {(data?.projects ?? []).map((project) => (
            <div key={project.project_id} className="group rounded-2xl border border-border bg-surface p-6 transition-colors hover:border-primary/30">
              <div className="flex items-start justify-between gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <FolderKanban className="h-5 w-5" />
                </div>
                <ScorePill score={Math.round(project.latest_score || project.average_score || 0)} />
              </div>
              <Link to="/projects/$projectId" params={{ projectId: project.project_id }} className="block">
                <h3 className="mt-4 text-lg font-medium">{project.name}</h3>
                <p className="text-sm text-muted-foreground">{project.description || "No description yet."}</p>
              </Link>
              <div className="mt-5 grid grid-cols-3 gap-3 border-t border-border pt-4 text-center">
                <Stat label="runs" value={String(project.runs.length)} />
                <Stat label="avg score" value={String(Math.round(project.average_score || 0))} />
                <Stat label="open items" value={String((project.open_assignment_count || 0) + (project.open_release_gate_count || 0))} />
              </div>
              <div className="mt-4 flex items-center justify-between gap-3 text-xs">
                <span className="font-mono text-muted-foreground">{loading ? "Loading…" : project.project_id}</span>
                <div className="flex items-center gap-2">
                  <Link
                    to="/projects/$projectId"
                    params={{ projectId: project.project_id }}
                    className="flex items-center gap-1 text-primary opacity-0 transition-opacity group-hover:opacity-100"
                  >
                    open <ArrowRight className="h-3 w-3" />
                  </Link>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-8 rounded-full border border-danger/25 bg-danger/10 px-3 text-danger hover:bg-danger/15 hover:text-danger"
                    disabled={deletingId === project.project_id}
                    onClick={() => void onDelete(project.project_id, project.name)}
                  >
                    <Trash2 className="mr-1.5 h-3.5 w-3.5" />
                    {deletingId === project.project_id ? "Deleting…" : "Delete"}
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
