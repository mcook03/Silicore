import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { Panel } from "@/components/silicore/Panel";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Download, Filter } from "lucide-react";

export const Route = createFileRoute("/admin/audit")({
  head: () => ({ meta: [{ title: "Audit log — Silicore" }] }),
  component: Audit,
});

const events = [
  { at: "12:04:12", actor: "elena@astrabit.io", action: "board.analyze", target: "sentinel-power.brd", ip: "10.4.1.22" },
  { at: "12:01:47", actor: "tomas@astrabit.io", action: "review.approve", target: "sentinel-mcu.kicad_pcb", ip: "10.4.1.18" },
  { at: "11:58:02", actor: "priya@astrabit.io", action: "project.create", target: "Halo Robotics", ip: "10.4.1.31" },
  { at: "11:42:15", actor: "system", action: "worker.start", target: "worker-01", ip: "internal" },
  { at: "11:30:09", actor: "kenji@astrabit.io", action: "settings.update", target: "thermal.thresholds", ip: "10.4.1.27" },
  { at: "11:15:41", actor: "elena@astrabit.io", action: "release-gate.approve", target: "DFM sign-off", ip: "10.4.1.22" },
];

function Audit() {
  return (
    <AppShell title="Audit log">
      <div className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm text-muted-foreground">All workspace activity, retained 365 days.</p>
          <div className="flex gap-2">
            <div className="relative">
              <Input placeholder="Search actor, action, target…" className="w-72 pl-8" />
              <Filter className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
            </div>
            <Button size="sm" variant="ghost" className="rounded-full"><Download className="mr-1.5 h-3.5 w-3.5" /> Export</Button>
          </div>
        </div>

        <Panel title="Events">
          <div className="overflow-hidden rounded-xl border border-border">
            <table className="w-full text-sm">
              <thead className="bg-background/40 text-left font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th className="px-4 py-3">Time</th>
                  <th className="px-4 py-3">Actor</th>
                  <th className="px-4 py-3">Action</th>
                  <th className="px-4 py-3">Target</th>
                  <th className="px-4 py-3">IP</th>
                </tr>
              </thead>
              <tbody>
                {events.map((e, i) => (
                  <tr key={i} className="border-t border-border hover:bg-background/40">
                    <td className="px-4 py-3 font-mono text-xs">{e.at}</td>
                    <td className="px-4 py-3">{e.actor}</td>
                    <td className="px-4 py-3"><span className="rounded border border-border px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{e.action}</span></td>
                    <td className="px-4 py-3 text-muted-foreground">{e.target}</td>
                    <td className="px-4 py-3 font-mono text-xs text-muted-foreground">{e.ip}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      </div>
    </AppShell>
  );
}
