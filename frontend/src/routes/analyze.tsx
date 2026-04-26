import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { ScoreRing } from "@/components/silicore/ScoreRing";
import { Panel } from "@/components/silicore/Panel";
import { Button } from "@/components/ui/button";
import { Upload, FileUp, Sparkles, AlertTriangle, AlertCircle, Info, CheckCircle2, ChevronRight } from "lucide-react";
import { BoardHeatmap } from "@/components/silicore/BoardHeatmap";
import { SeverityDonut, CategoryBreakdown } from "@/components/silicore/AnalysisCharts";

export const Route = createFileRoute("/analyze")({
  head: () => ({ meta: [{ title: "Board analysis — Silicore" }] }),
  component: Analyze,
});

const categories = [
  { name: "Design for Manufacturing", score: 88, issues: 4 },
  { name: "Signal Integrity", score: 76, issues: 6 },
  { name: "Thermal", score: 91, issues: 1 },
  { name: "EMI / EMC", score: 72, issues: 3 },
  { name: "BOM & Sourcing", score: 84, issues: 2 },
];

const findings = [
  { sev: "critical", title: "Insufficient clearance: VBUS ↔ GND on L2", loc: "L2 · net VBUS · 0.12mm", cat: "DFM", fix: "Increase trace clearance to ≥ 0.20mm or move VBUS to L3." },
  { sev: "critical", title: "Differential pair length mismatch on USB_DP/DM", loc: "U3 → J1 · Δ 7.4mil", cat: "Signal integrity", fix: "Add serpentine to USB_DM to match length within 5mil." },
  { sev: "critical", title: "No decoupling capacitor near U7 power pins", loc: "U7.4 · VCC", cat: "EMI", fix: "Place 100nF 0402 within 2mm of pin 4." },
  { sev: "medium", title: "Via-in-pad on U7 not tented", loc: "U7.3", cat: "DFM", fix: "Tent or fill vias to prevent solder wicking." },
  { sev: "medium", title: "Thermal pad on Q2 lacks stitching vias", loc: "Q2", cat: "Thermal", fix: "Add 4× 0.3mm vias under thermal pad." },
  { sev: "low", title: "Silkscreen overlap on R12 pad", loc: "R12", cat: "DFM", fix: "Move designator 0.4mm north." },
];

function Analyze() {
  return (
    <AppShell title="Board analysis">
      <div className="space-y-6">
        <Dropzone />

        <div className="grid gap-4 lg:grid-cols-[320px_1fr]">
          <div className="rounded-2xl border border-border bg-surface p-6">
            <div className="mb-2 font-mono text-xs uppercase tracking-wider text-muted-foreground">sentinel-power.brd</div>
            <div className="mb-6 text-sm text-muted-foreground">Last analyzed 2 min ago</div>
            <div className="flex flex-col items-center">
              <ScoreRing score={82} size={160} />
              <div className="mt-4 text-center">
                <div className="text-sm">Healthy with 3 critical fixes.</div>
                <div className="mt-1 font-mono text-xs text-success">+9 vs rev-b</div>
              </div>
            </div>
            <div className="mt-6 grid grid-cols-3 gap-2 border-t border-border pt-4 text-center">
              <Tally tone="danger" label="critical" n={3} />
              <Tally tone="warning" label="medium" n={6} />
              <Tally tone="muted" label="low" n={5} />
            </div>
            <Button className="mt-6 w-full rounded-full" size="sm"><Sparkles className="mr-1.5 h-3.5 w-3.5" /> Generate fix report</Button>
          </div>

          <Panel title="Categories">
            <div className="space-y-5">
              {categories.map((c) => (
                <div key={c.name}>
                  <div className="mb-1.5 flex items-center justify-between text-sm">
                    <span>{c.name}</span>
                    <span className="font-mono text-xs text-muted-foreground">{c.issues} issue{c.issues !== 1 && "s"} · <span className="text-foreground">{c.score}</span></span>
                  </div>
                  <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full rounded-full"
                      style={{ width: `${c.score}%`, background: c.score >= 80 ? "oklch(0.78 0.17 150)" : c.score >= 65 ? "oklch(0.82 0.16 75)" : "oklch(0.68 0.22 25)" }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </Panel>
        </div>

        <div className="grid gap-4 lg:grid-cols-[1fr_360px]">
          <BoardHeatmap title="Board heatmap · sentinel-power.brd" />
          <Panel title="Severity mix">
            <SeverityDonut
              data={[
                { name: "critical", value: 3 },
                { name: "medium", value: 6 },
                { name: "low", value: 5 },
              ]}
            />
          </Panel>
        </div>

        <Panel title="Findings by category">
          <CategoryBreakdown
            data={[
              { category: "DFM", critical: 1, medium: 2, low: 1 },
              { category: "Signal", critical: 1, medium: 4, low: 1 },
              { category: "Thermal", critical: 0, medium: 0, low: 1 },
              { category: "EMI / EMC", critical: 1, medium: 0, low: 2 },
              { category: "BOM", critical: 0, medium: 0, low: 0 },
            ]}
          />
        </Panel>

        <Panel title="Findings & recommendations" action={<span className="font-mono text-xs text-muted-foreground">{findings.length} total</span>}>
          <div className="space-y-2">
            {findings.map((f) => <FindingRow key={f.title} {...f} />)}
          </div>
        </Panel>
      </div>
    </AppShell>
  );
}

function Dropzone() {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-dashed border-border bg-surface p-10 text-center">
      <div className="bg-hero-glow pointer-events-none absolute inset-0 opacity-50" />
      <div className="relative">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl border border-border bg-background">
          <Upload className="h-5 w-5 text-primary" />
        </div>
        <h3 className="mt-4 text-lg font-medium">Upload a PCB file</h3>
        <p className="mx-auto mt-1 max-w-sm text-sm text-muted-foreground">
          Drop a Gerber zip, ODB++, .brd or .kicad_pcb. Analysis usually takes under 30 seconds.
        </p>
        <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
          <Button size="sm" className="rounded-full"><FileUp className="mr-1.5 h-3.5 w-3.5" /> Choose file</Button>
          <Button size="sm" variant="ghost" className="rounded-full text-muted-foreground">Or paste URL</Button>
        </div>
        <div className="mt-4 font-mono text-xs text-muted-foreground">.zip · .odb · .brd · .kicad_pcb · max 50 MB</div>
      </div>
    </div>
  );
}

function Tally({ tone, label, n }: { tone: "danger" | "warning" | "muted"; label: string; n: number }) {
  const c = { danger: "text-danger", warning: "text-warning", muted: "text-muted-foreground" }[tone];
  return (
    <div>
      <div className={`text-lg font-semibold ${c}`}>{n}</div>
      <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
    </div>
  );
}

function FindingRow({ sev, title, loc, cat, fix }: { sev: string; title: string; loc: string; cat: string; fix: string }) {
  const map = {
    critical: { Icon: AlertCircle, cls: "text-danger bg-danger/10 border-danger/20" },
    medium: { Icon: AlertTriangle, cls: "text-warning bg-warning/10 border-warning/20" },
    low: { Icon: Info, cls: "text-primary bg-primary/10 border-primary/20" },
  } as const;
  const { Icon, cls } = map[sev as keyof typeof map];
  return (
    <div className="group flex items-start gap-4 rounded-xl border border-border bg-background/40 p-4 transition-colors hover:border-primary/30">
      <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-md border ${cls}`}><Icon className="h-4 w-4" /></span>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-medium">{title}</span>
          <span className="rounded border border-border px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{cat}</span>
        </div>
        <div className="mt-0.5 font-mono text-[11px] text-muted-foreground">{loc}</div>
        <div className="mt-2 flex items-start gap-2 rounded-md bg-surface px-3 py-2 text-xs text-muted-foreground">
          <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
          <span><span className="text-foreground">Fix · </span>{fix}</span>
        </div>
      </div>
      <ChevronRight className="mt-2 h-4 w-4 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:text-foreground" />
    </div>
  );
}
