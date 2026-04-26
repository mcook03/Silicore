import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { Panel, ScorePill } from "@/components/silicore/Panel";
import { LineChart, Line, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

export const Route = createFileRoute("/history")({
  head: () => ({ meta: [{ title: "History — Silicore" }] }),
  component: History,
});

const series = Array.from({ length: 20 }, (_, i) => ({
  d: `wk${i + 1}`,
  sentinel: 60 + Math.round(i * 1.2 + Math.sin(i / 2) * 4),
  halo: 55 + Math.round(i * 0.8 + Math.cos(i / 3) * 5),
  atlas: 70 - Math.round(i * 0.4 + Math.sin(i) * 3),
}));

const log = [
  { when: "Today · 14:22", board: "Sentinel Power", rev: "rev-c", score: 82, delta: "+9", who: "Elena M." },
  { when: "Today · 11:08", board: "Halo Sensor Array", rev: "rev-a", score: 71, delta: "—", who: "Diego R." },
  { when: "Yesterday · 18:40", board: "Atlas RF Front-end", rev: "rev-b", score: 64, delta: "-3", who: "Elena M." },
  { when: "Yesterday · 09:11", board: "Nova MCU Carrier", rev: "rev-d", score: 91, delta: "+5", who: "Priya S." },
  { when: "2d ago", board: "Pulse Driver Board", rev: "rev-a", score: 58, delta: "—", who: "Diego R." },
  { when: "3d ago", board: "Sentinel Power", rev: "rev-b", score: 73, delta: "+4", who: "Elena M." },
  { when: "4d ago", board: "Glacier Cooling", rev: "rev-a", score: 85, delta: "—", who: "Priya S." },
];

function History() {
  return (
    <AppShell title="History">
      <div className="space-y-6">
        <Panel title="Score progression · last 20 weeks">
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={series}>
              <CartesianGrid stroke="oklch(0.28 0.014 250)" vertical={false} />
              <XAxis dataKey="d" stroke="oklch(0.55 0.018 250)" fontSize={11} tickLine={false} axisLine={false} />
              <YAxis stroke="oklch(0.55 0.018 250)" fontSize={11} tickLine={false} axisLine={false} domain={[40, 100]} />
              <Tooltip contentStyle={{ background: "oklch(0.19 0.014 250)", border: "1px solid oklch(0.28 0.014 250)", borderRadius: 8, fontSize: 12 }} />
              <Line type="monotone" dataKey="sentinel" stroke="oklch(0.85 0.16 195)" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="halo" stroke="oklch(0.78 0.17 150)" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="atlas" stroke="oklch(0.82 0.16 75)" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
          <div className="mt-4 flex flex-wrap gap-4 font-mono text-xs text-muted-foreground">
            <Legend color="oklch(0.85 0.16 195)" label="Sentinel" />
            <Legend color="oklch(0.78 0.17 150)" label="Halo" />
            <Legend color="oklch(0.82 0.16 75)" label="Atlas" />
          </div>
        </Panel>

        <Panel title="Analysis log">
          <div className="-mx-6 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="font-mono text-xs uppercase tracking-wider text-muted-foreground">
                  <th className="px-6 py-3 text-left font-normal">When</th>
                  <th className="px-6 py-3 text-left font-normal">Board</th>
                  <th className="px-6 py-3 text-left font-normal">Revision</th>
                  <th className="px-6 py-3 text-left font-normal">Score</th>
                  <th className="px-6 py-3 text-left font-normal">Δ</th>
                  <th className="px-6 py-3 text-left font-normal">By</th>
                </tr>
              </thead>
              <tbody>
                {log.map((r, i) => (
                  <tr key={i} className="border-t border-border/60 hover:bg-surface/50">
                    <td className="px-6 py-3.5 font-mono text-xs text-muted-foreground">{r.when}</td>
                    <td className="px-6 py-3.5 font-medium">{r.board}</td>
                    <td className="px-6 py-3.5 font-mono text-xs text-muted-foreground">{r.rev}</td>
                    <td className="px-6 py-3.5"><ScorePill score={r.score} /></td>
                    <td className={`px-6 py-3.5 font-mono text-xs ${r.delta.startsWith("+") ? "text-success" : r.delta.startsWith("-") ? "text-danger" : "text-muted-foreground"}`}>{r.delta}</td>
                    <td className="px-6 py-3.5 text-muted-foreground">{r.who}</td>
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

function Legend({ color, label }: { color: string; label: string }) {
  return (
    <span className="flex items-center gap-2">
      <span className="h-2 w-2 rounded-full" style={{ background: color }} /> {label}
    </span>
  );
}
