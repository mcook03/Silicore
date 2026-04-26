import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { ScorePill } from "@/components/silicore/Panel";
import { Button } from "@/components/ui/button";
import { Plus, FolderKanban, ArrowRight } from "lucide-react";

export const Route = createFileRoute("/projects")({
  head: () => ({ meta: [{ title: "Projects — Silicore" }] }),
  component: Projects,
});

const projects = [
  { name: "Sentinel Platform", desc: "Industrial power & control modules", boards: 6, avg: 81, critical: 2, updated: "2h ago" },
  { name: "Halo Robotics", desc: "Autonomous sensor stack v3", boards: 9, avg: 74, critical: 5, updated: "yesterday" },
  { name: "Atlas RF", desc: "5G front-end and antenna boards", boards: 4, avg: 68, critical: 7, updated: "3d ago" },
  { name: "Nova MCU Family", desc: "Reference designs for in-house SoC", boards: 11, avg: 88, critical: 0, updated: "5d ago" },
  { name: "Pulse Driver", desc: "High-current motor drive boards", boards: 3, avg: 62, critical: 9, updated: "1w ago" },
  { name: "Glacier Cooling", desc: "Server thermal evaluation kits", boards: 5, avg: 85, critical: 1, updated: "1w ago" },
];

function Projects() {
  return (
    <AppShell title="Projects">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">{projects.length} workspaces · 38 boards under analysis</p>
          <Button size="sm" className="rounded-full"><Plus className="mr-1.5 h-3.5 w-3.5" /> New project</Button>
        </div>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {projects.map((p) => (
            <div key={p.name} className="group rounded-2xl border border-border bg-surface p-6 transition-colors hover:border-primary/30">
              <div className="flex items-start justify-between">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <FolderKanban className="h-5 w-5" />
                </div>
                <ScorePill score={p.avg} />
              </div>
              <h3 className="mt-4 text-lg font-medium">{p.name}</h3>
              <p className="text-sm text-muted-foreground">{p.desc}</p>
              <div className="mt-5 grid grid-cols-3 gap-3 border-t border-border pt-4 text-center">
                <Stat label="boards" value={String(p.boards)} />
                <Stat label="avg score" value={String(p.avg)} />
                <Stat label="critical" value={String(p.critical)} tone={p.critical > 3 ? "danger" : undefined} />
              </div>
              <div className="mt-4 flex items-center justify-between text-xs">
                <span className="font-mono text-muted-foreground">updated {p.updated}</span>
                <span className="flex items-center gap-1 text-primary opacity-0 transition-opacity group-hover:opacity-100">
                  open <ArrowRight className="h-3 w-3" />
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </AppShell>
  );
}

function Stat({ label, value, tone }: { label: string; value: string; tone?: "danger" }) {
  return (
    <div>
      <div className={`text-base font-semibold ${tone === "danger" ? "text-danger" : ""}`}>{value}</div>
      <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
    </div>
  );
}
