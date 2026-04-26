import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { Panel } from "@/components/silicore/Panel";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Sparkles, Send, Bot, User, Zap, History as HistoryIcon, PlayCircle } from "lucide-react";

export const Route = createFileRoute("/atlas")({
  head: () => ({ meta: [{ title: "Atlas — Silicore" }] }),
  component: Atlas,
});

const thread = [
  { who: "user", text: "Why did sentinel-power score drop on rev-c?" },
  { who: "atlas", text: "Three new findings appeared: a clearance violation on VBUS, missing decoupling near U7, and a thermal pad without stitching vias on Q2. The dominant impact is the EMI category (-11)." },
  { who: "user", text: "Open a fix-up task for the decoupling cap." },
  { who: "atlas", text: "Created task SEN-412 in the Sentinel project, assigned to Priya. I attached the schematic snippet and recommended a 100nF 0402 within 2mm of U7.4." },
];

const runs = [
  { name: "diff-against-rev-b", status: "complete", duration: "8s", at: "2 min ago" },
  { name: "summarize-findings", status: "complete", duration: "3s", at: "5 min ago" },
  { name: "create-jira-task", status: "complete", duration: "12s", at: "5 min ago" },
  { name: "audit-bom-sourcing", status: "running", duration: "—", at: "now" },
];

function Atlas() {
  return (
    <AppShell title="Atlas — AI copilot">
      <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
        <div className="space-y-4">
          <Panel title="Thread" action={<Button size="sm" variant="ghost" className="h-7 rounded-full text-xs"><HistoryIcon className="mr-1.5 h-3 w-3" /> New</Button>}>
            <div className="space-y-3">
              {thread.map((m, i) => (
                <div key={i} className={`flex items-start gap-3 rounded-xl border border-border p-4 ${
                  m.who === "user" ? "bg-background/40" : "bg-primary/5"
                }`}>
                  <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                    m.who === "user" ? "bg-muted text-muted-foreground" : "bg-primary/15 text-primary"
                  }`}>
                    {m.who === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                  </div>
                  <div className="flex-1">
                    <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                      {m.who === "user" ? "You" : "Atlas"}
                    </div>
                    <p className="mt-1 text-sm">{m.text}</p>
                  </div>
                </div>
              ))}
            </div>
          </Panel>

          <Panel title="Ask Atlas">
            <div className="space-y-3">
              <Textarea placeholder="Ask about a board, request a fix, or trigger an action…" className="min-h-[100px]" />
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex flex-wrap gap-1.5">
                  {["Diff vs last rev", "Summarize criticals", "Open JIRA task", "Suggest stackup"].map((s) => (
                    <button key={s} className="rounded-full border border-border bg-background/40 px-3 py-1 font-mono text-[10px] uppercase tracking-wider text-muted-foreground hover:text-foreground">
                      {s}
                    </button>
                  ))}
                </div>
                <Button size="sm" className="rounded-full"><Send className="mr-1.5 h-3.5 w-3.5" /> Send</Button>
              </div>
            </div>
          </Panel>
        </div>

        <div className="space-y-4">
          <Panel title="Agent runs" action={<Sparkles className="h-4 w-4 text-primary" />}>
            <div className="space-y-2">
              {runs.map((r) => (
                <div key={r.name} className="rounded-xl border border-border bg-background/40 p-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">{r.name}</span>
                    <span className={`font-mono text-[10px] uppercase tracking-wider ${
                      r.status === "running" ? "text-warning" : "text-success"
                    }`}>{r.status}</span>
                  </div>
                  <div className="mt-1 font-mono text-[11px] text-muted-foreground">{r.duration} · {r.at}</div>
                </div>
              ))}
            </div>
          </Panel>

          <Panel title="Quick actions" action={<Zap className="h-4 w-4 text-primary" />}>
            <div className="space-y-2">
              {["Re-run analysis", "Generate fix report", "Notify reviewers", "Export findings to CSV"].map((a) => (
                <button key={a} className="flex w-full items-center justify-between rounded-lg border border-border bg-background/40 p-3 text-left text-sm hover:border-primary/30">
                  <span>{a}</span>
                  <PlayCircle className="h-4 w-4 text-muted-foreground" />
                </button>
              ))}
            </div>
          </Panel>
        </div>
      </div>
    </AppShell>
  );
}
