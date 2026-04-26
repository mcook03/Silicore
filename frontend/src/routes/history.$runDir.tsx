import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { Panel } from "@/components/silicore/Panel";
import { ScoreRing } from "@/components/silicore/ScoreRing";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Download, Printer, FileText } from "lucide-react";

export const Route = createFileRoute("/history/$runDir")({
  head: () => ({ meta: [{ title: "Run detail — Silicore" }] }),
  component: RunDetail,
});

const files = [
  { name: "analysis.json", size: "84 KB" },
  { name: "report.html", size: "212 KB" },
  { name: "report.md", size: "31 KB" },
  { name: "findings.csv", size: "12 KB" },
  { name: "source.kicad_pcb", size: "1.4 MB" },
];

function RunDetail() {
  const { runDir } = Route.useParams();
  return (
    <AppShell title="Run detail">
      <div className="space-y-6">
        <Link to="/history" className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-3 w-3" /> All runs
        </Link>

        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="font-mono text-xs uppercase tracking-wider text-muted-foreground">run · {runDir}</div>
            <h2 className="mt-1 text-2xl font-medium tracking-tight">sentinel-power.brd</h2>
            <p className="mt-1 text-sm text-muted-foreground">Analyzed 2026-04-25 · 13 findings · 3 critical</p>
          </div>
          <div className="flex gap-2">
            <Button size="sm" variant="ghost" className="rounded-full"><Printer className="mr-1.5 h-3.5 w-3.5" /> Print</Button>
            <Button size="sm" className="rounded-full"><Download className="mr-1.5 h-3.5 w-3.5" /> Download bundle</Button>
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-[320px_1fr]">
          <div className="rounded-2xl border border-border bg-surface p-6">
            <div className="flex flex-col items-center">
              <ScoreRing score={82} size={160} />
              <div className="mt-4 text-sm">Healthy with 3 critical fixes.</div>
            </div>
          </div>

          <Panel title="Run artifacts" action={<FileText className="h-4 w-4 text-muted-foreground" />}>
            <div className="space-y-2">
              {files.map((f) => (
                <div key={f.name} className="flex items-center justify-between rounded-xl border border-border bg-background/40 p-3.5">
                  <div className="flex items-center gap-3">
                    <FileText className="h-4 w-4 text-primary" />
                    <span className="font-mono text-sm">{f.name}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-xs text-muted-foreground">{f.size}</span>
                    <Button size="sm" variant="ghost" className="h-7 rounded-full text-xs"><Download className="h-3 w-3" /></Button>
                  </div>
                </div>
              ))}
            </div>
          </Panel>
        </div>
      </div>
    </AppShell>
  );
}
