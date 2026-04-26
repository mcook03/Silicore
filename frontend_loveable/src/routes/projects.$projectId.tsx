import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { Panel, ScorePill } from "@/components/silicore/Panel";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  ArrowLeft, Users, MessageSquare, ShieldCheck, GitBranch, CheckCircle2,
  CircleDot, Clock, Plus, FileCheck2, AlertTriangle,
} from "lucide-react";
import { BoardHeatmap } from "@/components/silicore/BoardHeatmap";
import { SeverityDonut, ScoreTrend, CategoryBreakdown } from "@/components/silicore/AnalysisCharts";

export const Route = createFileRoute("/projects/$projectId")({
  head: () => ({ meta: [{ title: "Project detail — Silicore" }] }),
  component: ProjectDetail,
});

const boards = [
  { name: "sentinel-power.brd", score: 82, status: "review", critical: 3 },
  { name: "sentinel-mcu.kicad_pcb", score: 91, status: "approved", critical: 0 },
  { name: "sentinel-rf-frontend.brd", score: 68, status: "blocked", critical: 7 },
  { name: "sentinel-io-bridge.kicad_pcb", score: 77, status: "review", critical: 2 },
];

const members = [
  { name: "Elena Morris", role: "Owner", initials: "EM" },
  { name: "Tomás Reyes", role: "Reviewer", initials: "TR" },
  { name: "Priya Shah", role: "Engineer", initials: "PS" },
  { name: "Kenji Watanabe", role: "Engineer", initials: "KW" },
];

const gates = [
  { name: "DFM sign-off", status: "passed", approvals: "3 / 3" },
  { name: "Signal integrity", status: "passed", approvals: "2 / 2" },
  { name: "Thermal review", status: "pending", approvals: "1 / 2" },
  { name: "Compliance", status: "blocked", approvals: "0 / 2" },
];

const notes = [
  { who: "Tomás Reyes", when: "2h ago", text: "Power plane split looks fine after rev-c. Moving DFM to passed." },
  { who: "Priya Shah", when: "yesterday", text: "Need confirmation on FCC pre-scan before compliance gate." },
];

function ProjectDetail() {
  const { projectId } = Route.useParams();

  return (
    <AppShell title="Sentinel Platform">
      <div className="space-y-6">
        <Link to="/projects" className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-3 w-3" /> All projects
        </Link>

        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="font-mono text-xs uppercase tracking-wider text-muted-foreground">project · {projectId}</div>
            <h2 className="mt-1 text-2xl font-medium tracking-tight">Sentinel Platform</h2>
            <p className="mt-1 text-sm text-muted-foreground">Industrial power & control modules · 4 boards in review</p>
          </div>
          <div className="flex items-center gap-2">
            <ScorePill score={81} />
            <Button size="sm" variant="ghost" className="rounded-full">Status: active</Button>
            <Button size="sm" className="rounded-full"><Plus className="mr-1.5 h-3.5 w-3.5" /> Add board</Button>
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          <Stat label="Boards" value="4" icon={GitBranch} />
          <Stat label="Open critical" value="12" tone="danger" icon={AlertTriangle} />
          <Stat label="Pending approvals" value="3" tone="warning" icon={Clock} />
        </div>

        <div className="grid gap-4 lg:grid-cols-[1fr_360px]">
          <Panel title="Boards">
            <div className="space-y-2">
              {boards.map((b) => (
                <div key={b.name} className="flex items-center justify-between rounded-xl border border-border bg-background/40 p-4">
                  <div>
                    <div className="text-sm">{b.name}</div>
                    <div className="font-mono text-[11px] text-muted-foreground">
                      {b.critical} critical · status {b.status}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <StatusDot status={b.status} />
                    <ScorePill score={b.score} />
                  </div>
                </div>
              ))}
            </div>
          </Panel>

          <Panel title="Members" action={<Button size="sm" variant="ghost" className="h-7 rounded-full text-xs"><Users className="mr-1.5 h-3 w-3" /> Invite</Button>}>
            <div className="space-y-3">
              {members.map((m) => (
                <div key={m.name} className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/15 font-mono text-xs text-primary">{m.initials}</div>
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm">{m.name}</div>
                    <div className="truncate font-mono text-[11px] text-muted-foreground">{m.role}</div>
                  </div>
                </div>
              ))}
            </div>
          </Panel>
        </div>

        <div className="grid gap-4 lg:grid-cols-[1fr_360px]">
          <BoardHeatmap title="Project hotspot map" cols={20} rows={10} />
          <Panel title="Severity mix">
            <SeverityDonut
              data={[
                { name: "critical", value: 12 },
                { name: "medium", value: 18 },
                { name: "low", value: 27 },
              ]}
            />
          </Panel>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <Panel title="Score trend · last 8 revs">
            <ScoreTrend
              data={[
                { label: "rev-a", score: 62 },
                { label: "rev-b", score: 65 },
                { label: "rev-c", score: 70 },
                { label: "rev-d", score: 68 },
                { label: "rev-e", score: 74 },
                { label: "rev-f", score: 78 },
                { label: "rev-g", score: 80 },
                { label: "rev-h", score: 81 },
              ]}
            />
          </Panel>
          <Panel title="Findings by category">
            <CategoryBreakdown
              data={[
                { category: "DFM", critical: 3, medium: 5, low: 8 },
                { category: "Signal", critical: 4, medium: 6, low: 7 },
                { category: "Thermal", critical: 2, medium: 3, low: 4 },
                { category: "EMI / EMC", critical: 3, medium: 2, low: 5 },
                { category: "BOM", critical: 0, medium: 2, low: 3 },
              ]}
            />
          </Panel>
        </div>

        <Panel title="Release gates" action={<span className="font-mono text-xs text-muted-foreground">{gates.length} gates</span>}>
          <div className="grid gap-3 md:grid-cols-2">
            {gates.map((g) => (
              <div key={g.name} className="flex items-center justify-between rounded-xl border border-border bg-background/40 p-4">
                <div className="flex items-center gap-3">
                  <span className={`flex h-8 w-8 items-center justify-center rounded-md border ${
                    g.status === "passed" ? "border-success/30 bg-success/10 text-success" :
                    g.status === "blocked" ? "border-danger/30 bg-danger/10 text-danger" :
                    "border-warning/30 bg-warning/10 text-warning"
                  }`}>
                    {g.status === "passed" ? <CheckCircle2 className="h-4 w-4" /> :
                     g.status === "blocked" ? <AlertTriangle className="h-4 w-4" /> :
                     <CircleDot className="h-4 w-4" />}
                  </span>
                  <div>
                    <div className="text-sm">{g.name}</div>
                    <div className="font-mono text-[11px] text-muted-foreground">{g.approvals} approvals</div>
                  </div>
                </div>
                <Button size="sm" variant="ghost" className="rounded-full text-xs"><ShieldCheck className="mr-1.5 h-3 w-3" /> Review</Button>
              </div>
            ))}
          </div>
        </Panel>

        <div className="grid gap-4 lg:grid-cols-2">
          <Panel title="Notes & activity" action={<MessageSquare className="h-4 w-4 text-muted-foreground" />}>
            <div className="space-y-3">
              {notes.map((n, i) => (
                <div key={i} className="rounded-xl border border-border bg-background/40 p-4">
                  <div className="flex items-center justify-between">
                    <div className="text-sm">{n.who}</div>
                    <div className="font-mono text-[11px] text-muted-foreground">{n.when}</div>
                  </div>
                  <p className="mt-1.5 text-sm text-muted-foreground">{n.text}</p>
                </div>
              ))}
              <div className="space-y-2 pt-2">
                <Textarea placeholder="Add a note for the team…" className="min-h-[80px]" />
                <div className="flex justify-end">
                  <Button size="sm" className="rounded-full">Post note</Button>
                </div>
              </div>
            </div>
          </Panel>

          <Panel title="Submit a review" action={<FileCheck2 className="h-4 w-4 text-muted-foreground" />}>
            <div className="space-y-3">
              <div className="space-y-1.5">
                <label className="text-xs uppercase tracking-wider text-muted-foreground">Reviewer</label>
                <Input placeholder="Tomás Reyes" />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs uppercase tracking-wider text-muted-foreground">Verdict</label>
                <div className="flex gap-2">
                  <Button size="sm" variant="ghost" className="flex-1 rounded-full border border-border">Approve</Button>
                  <Button size="sm" variant="ghost" className="flex-1 rounded-full border border-border">Request changes</Button>
                  <Button size="sm" variant="ghost" className="flex-1 rounded-full border border-border">Block</Button>
                </div>
              </div>
              <div className="space-y-1.5">
                <label className="text-xs uppercase tracking-wider text-muted-foreground">Summary</label>
                <Textarea placeholder="Findings, follow-ups, blockers…" className="min-h-[100px]" />
              </div>
              <Button className="w-full rounded-full">Submit review</Button>
            </div>
          </Panel>
        </div>
      </div>
    </AppShell>
  );
}

function Stat({ label, value, tone, icon: Icon }: { label: string; value: string; tone?: "danger" | "warning"; icon: typeof Users }) {
  const c = tone === "danger" ? "text-danger" : tone === "warning" ? "text-warning" : "text-foreground";
  return (
    <div className="rounded-2xl border border-border bg-surface p-5">
      <div className="flex items-center justify-between">
        <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</span>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </div>
      <div className={`mt-2 text-2xl font-semibold ${c}`}>{value}</div>
    </div>
  );
}

function StatusDot({ status }: { status: string }) {
  const tone = status === "approved" ? "bg-success" : status === "blocked" ? "bg-danger" : "bg-warning";
  return <span className={`h-2 w-2 rounded-full ${tone}`} />;
}
