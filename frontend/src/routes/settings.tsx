import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { Panel } from "@/components/silicore/Panel";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export const Route = createFileRoute("/settings")({
  head: () => ({ meta: [{ title: "Settings — Silicore" }] }),
  component: Settings,
});

const rules = [
  { name: "Minimum trace clearance", desc: "Flag traces with < value clearance.", value: "0.20mm", on: true },
  { name: "Differential pair length match", desc: "Allowed mismatch on diff pairs.", value: "5 mil", on: true },
  { name: "Via-in-pad tenting required", desc: "Untented vias on pads raise an issue.", value: "—", on: true },
  { name: "Thermal pad stitching", desc: "Require stitching vias under thermal pads.", value: "≥ 4 vias", on: true },
  { name: "Silkscreen on pads", desc: "Block silkscreen overlap with copper pads.", value: "—", on: false },
  { name: "BOM single-source warning", desc: "Warn on parts with only one supplier.", value: "—", on: true },
];

function Settings() {
  return (
    <AppShell title="Settings">
      <div className="grid gap-6 lg:grid-cols-[260px_1fr]">
        <nav className="space-y-1 text-sm">
          {["Workspace", "Scoring weights", "Design rules", "Integrations", "Members", "Billing"].map((s, i) => (
            <button key={s} className={`flex w-full items-center justify-between rounded-md px-3 py-2 text-left transition-colors ${i === 1 ? "bg-surface text-foreground" : "text-muted-foreground hover:bg-surface/60 hover:text-foreground"}`}>
              {s}
            </button>
          ))}
        </nav>

        <div className="space-y-6">
          <Panel title="Scoring weights">
            <p className="mb-6 text-sm text-muted-foreground">Adjust how each category contributes to the overall risk score. Weights are normalized.</p>
            <div className="space-y-6">
              {[
                { name: "Design for Manufacturing", v: 30 },
                { name: "Signal Integrity", v: 25 },
                { name: "Thermal", v: 15 },
                { name: "EMI / EMC", v: 20 },
                { name: "BOM & Sourcing", v: 10 },
              ].map((w) => (
                <div key={w.name}>
                  <div className="mb-2 flex items-center justify-between text-sm">
                    <span>{w.name}</span>
                    <span className="font-mono text-xs text-muted-foreground">{w.v}%</span>
                  </div>
                  <Slider defaultValue={[w.v]} max={100} step={5} />
                </div>
              ))}
            </div>
            <div className="mt-6 flex justify-end gap-2">
              <Button variant="ghost" size="sm">Reset</Button>
              <Button size="sm" className="rounded-full">Save weights</Button>
            </div>
          </Panel>

          <Panel title="Design rules">
            <div className="divide-y divide-border">
              {rules.map((r) => (
                <div key={r.name} className="flex items-center justify-between py-4 first:pt-0 last:pb-0">
                  <div>
                    <div className="text-sm font-medium">{r.name}</div>
                    <div className="text-xs text-muted-foreground">{r.desc}</div>
                  </div>
                  <div className="flex items-center gap-4">
                    {r.value !== "—" && (
                      <Input defaultValue={r.value} className="h-8 w-24 font-mono text-xs" />
                    )}
                    <Switch defaultChecked={r.on} />
                  </div>
                </div>
              ))}
            </div>
          </Panel>

          <Panel title="Workspace">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label className="mb-2 block">Workspace name</Label>
                <Input defaultValue="Astrabit Labs" />
              </div>
              <div>
                <Label className="mb-2 block">Default unit</Label>
                <Input defaultValue="millimeter (mm)" />
              </div>
            </div>
          </Panel>
        </div>
      </div>
    </AppShell>
  );
}
