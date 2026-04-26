import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { Panel } from "@/components/silicore/Panel";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Upload, Layers, Sparkles } from "lucide-react";

export const Route = createFileRoute("/project-review")({
  head: () => ({ meta: [{ title: "Project review — Silicore" }] }),
  component: ProjectReview,
});

function ProjectReview() {
  return (
    <AppShell title="Project review">
      <div className="mx-auto max-w-4xl space-y-6">
        <div>
          <h2 className="text-xl font-medium tracking-tight">Submit a multi-board project for review</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Bundle related boards into a single review so reviewers can compare scores, gates and findings together.
          </p>
        </div>

        <Panel title="Project metadata">
          <div className="grid gap-4 md:grid-cols-2">
            <Field label="Project name"><Input placeholder="Sentinel Platform — rev D" /></Field>
            <Field label="Workspace"><Input placeholder="Astrabit Labs" /></Field>
            <Field label="Lead reviewer"><Input placeholder="elena@astrabit.io" /></Field>
            <Field label="Target ship date"><Input type="date" /></Field>
          </div>
          <div className="mt-4">
            <Field label="Scope summary">
              <Textarea placeholder="What changed since the last review, what to focus on…" className="min-h-[110px]" />
            </Field>
          </div>
        </Panel>

        <Panel title="Boards in this review" action={<span className="font-mono text-xs text-muted-foreground">3 attached</span>}>
          <div className="space-y-2">
            {["sentinel-power.brd", "sentinel-mcu.kicad_pcb", "sentinel-rf-frontend.brd"].map((f) => (
              <div key={f} className="flex items-center justify-between rounded-xl border border-border bg-background/40 p-3.5">
                <div className="flex items-center gap-3">
                  <Layers className="h-4 w-4 text-primary" />
                  <span className="text-sm">{f}</span>
                </div>
                <span className="font-mono text-xs text-muted-foreground">queued</span>
              </div>
            ))}
            <div className="rounded-xl border border-dashed border-border bg-background/40 p-6 text-center">
              <Upload className="mx-auto h-5 w-5 text-primary" />
              <div className="mt-2 text-sm">Drop more board files here</div>
              <div className="font-mono text-[11px] text-muted-foreground">.zip · .brd · .kicad_pcb · .odb</div>
            </div>
          </div>
        </Panel>

        <div className="flex justify-end gap-2">
          <Button size="sm" variant="ghost" className="rounded-full">Save as draft</Button>
          <Button size="sm" className="rounded-full"><Sparkles className="mr-1.5 h-3.5 w-3.5" /> Submit review</Button>
        </div>
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
