import { useEffect, useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { Panel } from "@/components/silicore/Panel";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { apiGet, apiPostJson, useApiData } from "@/lib/api";
import { Sparkles, Send, Bot, User, Zap, History as HistoryIcon, PlayCircle } from "lucide-react";

export const Route = createFileRoute("/atlas")({
  head: () => ({ meta: [{ title: "Atlas — Silicore" }] }),
  component: Atlas,
});

type SessionPayload = {
  project_options: Array<{ value: string; label: string }>;
};

type ThreadMessage = {
  role?: string;
  content?: string;
  prompt?: string;
  answer?: string;
  created_at?: string;
};

type AtlasResponse = {
  answer?: string;
  summary?: string;
  thread_key?: string;
  thread?: ThreadMessage[];
  tool_suggestions?: string[];
  workflow_plan?: Array<{ step?: string; title?: string }>;
  workflow_results?: Array<{ status?: string; action_name?: string; summary?: string }>;
};

type AgentRunsPayload = {
  runs: Array<{ run_id?: string; status?: string; action_name?: string; created_at?: string; duration_ms?: number }>;
};

function Atlas() {
  const session = useApiData<SessionPayload>("/api/frontend/session");
  const [pageType, setPageType] = useState<"board" | "project" | "compare">("project");
  const [projectId, setProjectId] = useState("");
  const [boardName, setBoardName] = useState("");
  const [prompt, setPrompt] = useState("");
  const [threadKey, setThreadKey] = useState("");
  const [messages, setMessages] = useState<Array<{ who: "user" | "atlas"; text: string }>>([]);
  const [toolSuggestions, setToolSuggestions] = useState<string[]>([]);
  const [workflowPlan, setWorkflowPlan] = useState<Array<{ step?: string; title?: string }>>([]);
  const [workflowResults, setWorkflowResults] = useState<Array<{ status?: string; action_name?: string; summary?: string }>>([]);
  const [error, setError] = useState<string | null>(null);
  const runs = useApiData<AgentRunsPayload>(threadKey ? `/atlas/agent-runs?thread_key=${encodeURIComponent(threadKey)}` : "/atlas/agent-runs");

  const context = useMemo(() => ({
    project_id: projectId || session.data?.project_options?.[0]?.value || "",
    board_name: boardName,
  }), [projectId, boardName, session.data]);

  useEffect(() => {
    if (!threadKey) {
      return;
    }
    void apiGet<{ messages: ThreadMessage[] }>(`/atlas/thread?thread_key=${encodeURIComponent(threadKey)}`).then((payload) => {
      const nextMessages = payload.messages.flatMap((message) => {
        const rows: Array<{ who: "user" | "atlas"; text: string }> = [];
        if (message.prompt) rows.push({ who: "user", text: message.prompt });
        if (message.answer) rows.push({ who: "atlas", text: message.answer });
        if (!message.prompt && !message.answer && message.content) {
          rows.push({ who: message.role === "user" ? "user" : "atlas", text: message.content });
        }
        return rows;
      });
      if (nextMessages.length) {
        setMessages(nextMessages);
      }
    }).catch(() => undefined);
  }, [threadKey]);

  const sendPrompt = async () => {
    if (!prompt.trim()) {
      return;
    }
    setError(null);
    try {
      const payload = await apiPostJson<AtlasResponse>("/atlas/query", {
        page_type: pageType,
        prompt,
        context,
        thread_key: threadKey || undefined,
        history: messages.map((message) => ({
          role: message.who === "user" ? "user" : "assistant",
          content: message.text,
        })),
      });
      setThreadKey(payload.thread_key || "");
      setToolSuggestions(payload.tool_suggestions || []);
      setWorkflowPlan(payload.workflow_plan || []);
      setWorkflowResults(payload.workflow_results || []);
      setMessages(payload.thread?.flatMap((message) => {
        const rows: Array<{ who: "user" | "atlas"; text: string }> = [];
        if (message.prompt) rows.push({ who: "user", text: message.prompt });
        if (message.answer) rows.push({ who: "atlas", text: message.answer });
        if (!message.prompt && !message.answer && message.content) {
          rows.push({ who: message.role === "user" ? "user" : "atlas", text: message.content });
        }
        return rows;
      }) || []);
      setPrompt("");
      await runs.reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Atlas request failed.");
    }
  };

  const runQuickAction = async (actionName: string) => {
    setError(null);
    try {
      await apiPostJson("/atlas/action", {
        action_name: actionName,
        context,
      });
      await runs.reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Atlas action failed.");
    }
  };

  return (
    <AppShell title="Atlas — AI copilot">
      <div className="space-y-6">
        <section
          data-reveal
          className="relative overflow-hidden rounded-[34px] border border-border/80 bg-[radial-gradient(circle_at_78%_20%,rgba(86,211,240,0.16),transparent_18%),linear-gradient(135deg,rgba(8,16,26,0.98),rgba(9,17,28,0.96)_48%,rgba(15,18,30,0.96))] px-6 py-7 sm:px-8 sm:py-8"
        >
          <div className="absolute inset-y-0 left-[58%] w-px bg-gradient-to-b from-transparent via-white/8 to-transparent max-xl:hidden" />
          <div className="relative grid gap-7 xl:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)]">
            <div>
              <div className="section-eyebrow">
                <Sparkles className="h-3.5 w-3.5" />
                Copilot interface
              </div>
              <h2 className="mt-5 max-w-3xl text-4xl font-semibold tracking-tight text-foreground sm:text-[3.15rem] sm:leading-[1.02]">
                Atlas should feel like a live copilot station, not a chatbot dropped into a dashboard.
              </h2>
              <p className="mt-4 max-w-2xl text-base leading-8 text-muted-foreground">
                Context, thread state, quick actions, and agent runs should support the conversation instead of competing with it. This layout is moving toward that more intentional flow.
              </p>
            </div>
            <div className="grid gap-4 sm:grid-cols-3 xl:grid-cols-1">
              <AtlasSignal label="Thread" value={threadKey ? "Live" : "New"} copy={threadKey || "Start a new Atlas thread"} />
              <AtlasSignal label="Messages" value={String(messages.length)} copy="Conversation items in memory" />
              <AtlasSignal label="Agent runs" value={String(runs.data?.runs.length || 0)} copy="Tracked against this thread" />
            </div>
          </div>
        </section>

        <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
        <div className="space-y-4">
          <Panel title="Context">
            <div className="grid gap-3 md:grid-cols-3">
              <Field label="Page type">
                <div className="grid grid-cols-3 gap-2">
                  {(["board", "project", "compare"] as const).map((option) => (
                    <button key={option} onClick={() => setPageType(option)} className={`interactive-lift rounded-2xl border px-3 py-2 text-sm capitalize ${pageType === option ? "border-primary/40 bg-primary/8 text-foreground" : "border-border bg-background/40 text-muted-foreground"}`}>
                      {option}
                    </button>
                  ))}
                </div>
              </Field>
              <Field label="Project">
                <select value={projectId} onChange={(event) => setProjectId(event.target.value)} className="premium-select h-10 rounded-2xl px-3 text-sm">
                  <option value="">Latest project</option>
                  {(session.data?.project_options || []).map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </Field>
              <Field label="Board name">
                <Input value={boardName} onChange={(event) => setBoardName(event.target.value)} placeholder="sentinel-power.kicad_pcb" className="premium-input" />
              </Field>
            </div>
          </Panel>

          <Panel title="Thread" action={<Button size="sm" variant="ghost" className="h-7 rounded-full text-xs" onClick={() => { setThreadKey(""); setMessages([]); setToolSuggestions([]); setWorkflowPlan([]); setWorkflowResults([]); }}><HistoryIcon className="mr-1.5 h-3 w-3" /> New</Button>}>
            <div className="space-y-3">
              {messages.map((message, index) => (
                <div key={`${message.who}-${index}`} className={`flex items-start gap-3 rounded-xl border border-border p-4 ${message.who === "user" ? "bg-background/40" : "bg-primary/5"}`}>
                  <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${message.who === "user" ? "bg-muted text-muted-foreground" : "bg-primary/15 text-primary"}`}>
                    {message.who === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                  </div>
                  <div className="flex-1">
                    <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{message.who === "user" ? "You" : "Atlas"}</div>
                    <p className="mt-1 text-sm whitespace-pre-wrap">{message.text}</p>
                  </div>
                </div>
              ))}
              {!messages.length ? <p className="text-sm text-muted-foreground">Ask Atlas about a board, project, or comparison and Silicore will answer against the live backend context.</p> : null}
            </div>
          </Panel>

          <Panel title="Ask Atlas">
            <div className="space-y-3">
              <Textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="Ask about a board, request a fix, or trigger an action…" className="premium-textarea min-h-[100px]" />
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex flex-wrap gap-1.5">
                  {["compare_latest_runs", "generate_signoff_packet", "open_high_confidence_findings", "run_fixture_evaluation"].map((suggestion) => (
                    <button key={suggestion} onClick={() => setPrompt(`Run ${suggestion.replaceAll("_", " ")} for the current context.`)} className="rounded-full border border-border bg-background/40 px-3 py-1 font-mono text-[10px] uppercase tracking-wider text-muted-foreground hover:text-foreground">
                      {suggestion.replaceAll("_", " ")}
                    </button>
                  ))}
                </div>
                <Button size="sm" className="rounded-full" onClick={() => void sendPrompt()}><Send className="mr-1.5 h-3.5 w-3.5" /> Send</Button>
              </div>
              {error ? <div className="text-sm text-danger">{error}</div> : null}
            </div>
          </Panel>
        </div>

        <div className="space-y-4">
          <Panel title="Agent runs" action={<Sparkles className="h-4 w-4 text-primary" />}>
            <div className="space-y-2">
              {(runs.data?.runs || []).map((run, index) => (
                <div key={`${run.run_id || run.action_name}-${index}`} className="rounded-xl border border-border bg-background/40 p-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">{run.action_name || run.run_id || "Atlas run"}</span>
                    <span className={`font-mono text-[10px] uppercase tracking-wider ${run.status === "completed" ? "text-success" : run.status === "failed" ? "text-danger" : "text-warning"}`}>{run.status || "unknown"}</span>
                  </div>
                  <div className="mt-1 font-mono text-[11px] text-muted-foreground">{run.created_at || "now"} {run.duration_ms ? `· ${run.duration_ms} ms` : ""}</div>
                </div>
              ))}
              {!runs.data?.runs.length ? <p className="text-sm text-muted-foreground">No Atlas runs recorded for this thread yet.</p> : null}
            </div>
          </Panel>

          <Panel title="Workflow plan">
            <div className="space-y-2">
              {workflowPlan.map((step, index) => (
                <div key={`${step.step || step.title}-${index}`} className="rounded-xl border border-border bg-background/40 p-3">
                  <div className="text-sm">{step.title || step.step || `Step ${index + 1}`}</div>
                </div>
              ))}
              {!workflowPlan.length ? <p className="text-sm text-muted-foreground">Atlas will surface its workflow plan here after a request.</p> : null}
            </div>
          </Panel>

          <Panel title="Quick actions" action={<Zap className="h-4 w-4 text-primary" />}>
            <div className="space-y-2">
              {(toolSuggestions.length ? toolSuggestions : ["compare_latest_runs", "generate_signoff_packet", "open_high_confidence_findings"]).map((actionName) => (
                <button key={actionName} onClick={() => void runQuickAction(actionName)} className="flex w-full items-center justify-between rounded-lg border border-border bg-background/40 p-3 text-left text-sm hover:border-primary/30">
                  <span>{actionName.replaceAll("_", " ")}</span>
                  <PlayCircle className="h-4 w-4 text-muted-foreground" />
                </button>
              ))}
            </div>
            {workflowResults.length ? (
              <div className="mt-4 space-y-2 border-t border-border pt-4">
                {workflowResults.map((result, index) => (
                  <div key={`${result.action_name}-${index}`} className="rounded-lg border border-border bg-background/40 p-3">
                    <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{result.action_name || "workflow"}</div>
                    <div className="mt-1 text-sm">{result.summary || result.status || "completed"}</div>
                  </div>
                ))}
              </div>
            ) : null}
          </Panel>
        </div>
      </div>
      </div>
    </AppShell>
  );
}

function AtlasSignal({ label, value, copy }: { label: string; value: string; copy: string }) {
  return (
    <div className="border-l border-white/10 pl-4">
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{label}</div>
      <div className="mt-1 text-3xl font-semibold text-foreground">{value}</div>
      <div className="mt-1 text-sm text-muted-foreground">{copy}</div>
    </div>
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
