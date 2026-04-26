import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { Panel, ScorePill } from "@/components/silicore/Panel";
import { ArrowRight, TrendingUp, TrendingDown, Minus } from "lucide-react";

export const Route = createFileRoute("/compare")({
  head: () => ({ meta: [{ title: "Compare revisions — Silicore" }] }),
  component: Compare,
});

const A = { name: "sentinel-power", rev: "rev-b", score: 73, issues: 23, cats: { DFM: 80, "Signal integrity": 68, Thermal: 85, EMI: 65, BOM: 80 } };
const B = { name: "sentinel-power", rev: "rev-c", score: 82, issues: 14, cats: { DFM: 88, "Signal integrity": 76, Thermal: 91, EMI: 72, BOM: 84 } };

const changes = [
  { kind: "fixed", title: "Differential pair USB_DP/DM length matched", impact: "+4 SI", why: "Improves USB 2.0 eye-diagram margin." },
  { kind: "fixed", title: "Thermal stitching added under Q2", impact: "+6 Thermal", why: "Lowers junction temp by ~12°C at full load." },
  { kind: "new", title: "Insufficient clearance VBUS↔GND on L2", impact: "-3 DFM", why: "New routing on L2 narrowed the gap below 0.20mm." },
  { kind: "fixed", title: "Decoupling caps on U2 power rails", impact: "+5 EMI", why: "Reduces switching noise on 3V3 rail." },
  { kind: "regressed", title: "Silkscreen overlaps on connectors", impact: "-1 DFM", why: "New silkscreen layer pushed designators into pads." },
];

function Compare() {
  return (
    <AppShell title="Compare revisions">
      <div className="space-y-6">
        <div className="grid items-center gap-4 lg:grid-cols-[1fr_auto_1fr]">
          <RevCard rev={A} />
          <div className="hidden h-12 w-12 items-center justify-center rounded-full border border-border bg-surface lg:flex">
            <ArrowRight className="h-5 w-5 text-primary" />
          </div>
          <RevCard rev={B} highlight />
        </div>

        <Panel title="Score change · by category">
          <div className="space-y-5">
            {Object.keys(A.cats).map((k) => {
              const a = A.cats[k as keyof typeof A.cats];
              const b = B.cats[k as keyof typeof B.cats];
              const delta = b - a;
              return (
                <div key={k}>
                  <div className="mb-1.5 flex items-center justify-between text-sm">
                    <span>{k}</span>
                    <div className="flex items-center gap-3 font-mono text-xs">
                      <span className="text-muted-foreground">{a}</span>
                      <ArrowRight className="h-3 w-3 text-muted-foreground" />
                      <span className="text-foreground">{b}</span>
                      <span className={`w-10 text-right ${delta > 0 ? "text-success" : delta < 0 ? "text-danger" : "text-muted-foreground"}`}>
                        {delta > 0 ? "+" : ""}{delta}
                      </span>
                    </div>
                  </div>
                  <div className="relative h-1.5 overflow-hidden rounded-full bg-muted">
                    <div className="absolute inset-y-0 left-0 rounded-full bg-muted-foreground/40" style={{ width: `${a}%` }} />
                    <div className="absolute inset-y-0 left-0 rounded-full bg-primary" style={{ width: `${b}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </Panel>

        <Panel title="What changed and why it matters">
          <div className="space-y-2">
            {changes.map((c) => <ChangeRow key={c.title} {...c} />)}
          </div>
        </Panel>
      </div>
    </AppShell>
  );
}

function RevCard({ rev, highlight }: { rev: typeof A; highlight?: boolean }) {
  return (
    <div className={`rounded-2xl border bg-surface p-6 ${highlight ? "border-primary/40 shadow-[0_0_0_1px_oklch(0.85_0.16_195_/_0.2)]" : "border-border"}`}>
      <div className="flex items-center justify-between">
        <div>
          <div className="font-mono text-xs uppercase tracking-wider text-muted-foreground">{rev.name}</div>
          <div className="mt-1 text-2xl font-semibold">{rev.rev}</div>
        </div>
        <ScorePill score={rev.score} />
      </div>
      <div className="mt-6 flex items-center gap-6 text-sm">
        <div>
          <div className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground">issues</div>
          <div className="text-xl font-medium">{rev.issues}</div>
        </div>
        <div>
          <div className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground">score</div>
          <div className="text-xl font-medium">{rev.score}</div>
        </div>
      </div>
    </div>
  );
}

function ChangeRow({ kind, title, impact, why }: { kind: string; title: string; impact: string; why: string }) {
  const map = {
    fixed: { Icon: TrendingUp, cls: "text-success bg-success/10 border-success/20", label: "Fixed" },
    regressed: { Icon: TrendingDown, cls: "text-danger bg-danger/10 border-danger/20", label: "Regressed" },
    new: { Icon: Minus, cls: "text-warning bg-warning/10 border-warning/20", label: "New" },
  } as const;
  const { Icon, cls, label } = map[kind as keyof typeof map];
  return (
    <div className="flex items-start gap-4 rounded-xl border border-border bg-background/40 p-4">
      <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-md border ${cls}`}><Icon className="h-4 w-4" /></span>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded border border-border px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</span>
          <span className="text-sm font-medium">{title}</span>
        </div>
        <div className="mt-1 text-xs text-muted-foreground">{why}</div>
      </div>
      <span className={`shrink-0 font-mono text-xs ${impact.startsWith("+") ? "text-success" : "text-danger"}`}>{impact}</span>
    </div>
  );
}
