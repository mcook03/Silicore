import { useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { apiPostJson, useApiData } from "@/lib/api";
import {
  Bot,
  BrainCircuit,
  CheckCircle2,
  History as HistoryIcon,
  PlayCircle,
  Send,
  Sparkles,
  User,
  Workflow,
  Wrench,
  Zap,
} from "lucide-react";

export const Route = createFileRoute("/atlas")({
  head: () => ({ meta: [{ title: "Atlas — Silicore" }] }),
  component: Atlas,
});

type SessionPayload = {
  project_options: Array<{ project_id: string; name: string }>;
};

type ThreadMessage = {
  role?: string;
  content?: string;
  prompt?: string;
  answer?: string;
  copy?: string;
};

type AtlasResponse = {
  title?: string;
  answer?: string;
  detail?: string;
  confidence?: number;
  citations?: Array<{ label?: string; components?: string[]; nets?: string[] }>;
  follow_ups?: string[];
  actions?: { components?: string[]; nets?: string[]; net?: string; heat_mode?: string };
  thread_key?: string;
  thread?: ThreadMessage[];
  tool_suggestions?: string[];
  workflow_plan?: Array<{ step?: string; title?: string; action_name?: string; reason?: string }>;
  workflow_results?: Array<{ status?: string; action_name?: string; summary?: string; reason?: string; result?: { summary?: string; status?: string; count?: number } }>;
  agent_trace?: Array<{ step?: number; label?: string; status?: string; summary?: string }>;
};

type AtlasContextPayload = {
  context: Record<string, unknown>;
  selected_project_id?: string;
  selected_run_id?: string;
  board_options?: Array<{ run_id?: string; label?: string; score?: number; risk_count?: number; run_type?: string }>;
  summary?: { title?: string; copy?: string };
  prompt_starters?: string[];
  quick_actions?: string[];
};

type AgentRunsPayload = {
  runs: Array<{ run_id?: string; status?: string; action_name?: string; created_at?: string; duration_ms?: number }>;
};

function Atlas() {
  const session = useApiData<SessionPayload>("/api/frontend/session");
  const [pageType, setPageType] = useState<"board" | "project" | "compare">("project");
  const [projectId, setProjectId] = useState("");
  const [boardName, setBoardName] = useState("");
  const [selectedRunId, setSelectedRunId] = useState("");
  const [prompt, setPrompt] = useState("");
  const [threadKey, setThreadKey] = useState("");
  const [messages, setMessages] = useState<Array<{ who: "user" | "atlas"; text: string }>>([]);
  const [toolSuggestions, setToolSuggestions] = useState<string[]>([]);
  const [workflowPlan, setWorkflowPlan] = useState<Array<{ step?: string; title?: string; action_name?: string; reason?: string }>>([]);
  const [workflowResults, setWorkflowResults] = useState<Array<{ status?: string; action_name?: string; summary?: string; reason?: string; result?: { summary?: string; status?: string; count?: number } }>>([]);
  const [latestAnswer, setLatestAnswer] = useState<AtlasResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const scopeRef = useRef("");

  const resetAtlasThread = () => {
    setThreadKey("");
    setMessages([]);
    setToolSuggestions([]);
    setWorkflowPlan([]);
    setWorkflowResults([]);
    setLatestAnswer(null);
    setError(null);
  };

  const contextUrl = useMemo(() => {
    const params = new URLSearchParams({ page_type: pageType });
    if (projectId) {
      params.set("project_id", projectId);
    }
    if (pageType === "board" && selectedRunId) {
      params.set("run_id", selectedRunId);
    } else if (boardName) {
      params.set("board_name", boardName);
    }
    return `/api/frontend/atlas/context?${params.toString()}`;
  }, [boardName, pageType, projectId, selectedRunId]);

  const atlasContext = useApiData<AtlasContextPayload>(contextUrl);
  const runs = useApiData<AgentRunsPayload>(threadKey ? `/atlas/agent-runs?thread_key=${encodeURIComponent(threadKey)}` : "/atlas/agent-runs");

  useEffect(() => {
    if (!projectId && atlasContext.data?.selected_project_id) {
      setProjectId(atlasContext.data.selected_project_id);
    }
  }, [atlasContext.data?.selected_project_id, projectId]);

  useEffect(() => {
    if (pageType !== "board") {
      return;
    }
    const availableRuns = atlasContext.data?.board_options || [];
    if (!selectedRunId && atlasContext.data?.selected_run_id) {
      setSelectedRunId(atlasContext.data.selected_run_id);
      return;
    }
    if (selectedRunId && !availableRuns.some((option) => option.run_id === selectedRunId) && atlasContext.data?.selected_run_id) {
      setSelectedRunId(atlasContext.data.selected_run_id);
    }
  }, [atlasContext.data?.board_options, atlasContext.data?.selected_run_id, pageType, selectedRunId]);

  const availableBoardOptions = atlasContext.data?.board_options || [];
  const activeRunId = selectedRunId || atlasContext.data?.selected_run_id || availableBoardOptions[0]?.run_id || "";
  const selectedBoardOption = useMemo(
    () => availableBoardOptions.find((option) => option.run_id === activeRunId) || availableBoardOptions[0],
    [activeRunId, availableBoardOptions],
  );

  useEffect(() => {
    if (pageType === "board" && selectedBoardOption?.label) {
      setBoardName(selectedBoardOption.label);
    }
  }, [pageType, selectedBoardOption?.label]);

  const resolvedContext = atlasContext.data?.context || {
    project_id: projectId || session.data?.project_options?.[0]?.project_id || "",
    board_name: boardName || selectedBoardOption?.label || "",
    run_id: selectedRunId,
  };

  const parseThread = (thread: ThreadMessage[] = []) =>
    thread.flatMap((message) => {
      const rows: Array<{ who: "user" | "atlas"; text: string }> = [];
      if (message.prompt) rows.push({ who: "user", text: message.prompt });
      if (message.answer) rows.push({ who: "atlas", text: message.answer });
      if (!message.prompt && !message.answer && (message.content || message.copy)) {
        rows.push({ who: message.role === "user" ? "user" : "atlas", text: stripHtml(message.content || message.copy || "") });
      }
      return rows;
    });

  const contextScope = useMemo(() => {
    if (pageType === "board") {
      return `${pageType}:${selectedRunId || atlasContext.data?.selected_run_id || boardName}`;
    }
    return `${pageType}:${projectId || atlasContext.data?.selected_project_id || ""}`;
  }, [atlasContext.data?.selected_project_id, atlasContext.data?.selected_run_id, boardName, pageType, projectId, selectedRunId]);

  useEffect(() => {
    if (!contextScope) {
      return;
    }
    if (!scopeRef.current) {
      scopeRef.current = contextScope;
      return;
    }
    if (scopeRef.current !== contextScope) {
      scopeRef.current = contextScope;
      resetAtlasThread();
    }
  }, [contextScope]);

  const contextMetrics = useMemo(() => {
    const context = atlasContext.data?.context || {};
    if (pageType === "board") {
      return [
        { label: "Run score", value: formatMetricValue(context.score, "score"), copy: "Board posture from this selected analysis snapshot" },
        { label: "Driver", value: String(context.dominant_domain || "General"), copy: "Primary engineering domain Atlas sees" },
        { label: "Parser trust", value: String(context.parser_confidence || "Mixed"), copy: "How trustworthy the extracted board evidence looks" },
        { label: "Signoff gate", value: String(context.signoff_gate || "Needs review"), copy: "Release-readiness signal for this board" },
      ];
    }
    if (pageType === "compare") {
      return [
        { label: "Score delta", value: formatMetricValue(context.score_diff, "delta"), copy: "Headline revision movement" },
        { label: "Risk delta", value: formatMetricValue(context.risk_diff, "count"), copy: "Change in total risk load" },
        { label: "Direction", value: String(context.direction || "Mixed"), copy: "Overall compare posture" },
        { label: "Next move", value: String(context.next_move || "Inspect changed domains"), copy: "What Atlas recommends next" },
      ];
    }
    return [
      { label: "Health score", value: formatMetricValue(context.health_score, "score"), copy: "Current workspace health blend" },
      { label: "Momentum", value: String(context.momentum || "Stable"), copy: "How recent runs are trending" },
      { label: "Avg confidence", value: formatMetricValue(context.average_confidence, "percent"), copy: "Trust in the workspace evidence base" },
      { label: "Readiness", value: String(context.release_readiness || "Needs review"), copy: "Workspace release posture right now" },
    ];
  }, [atlasContext.data?.context, pageType]);

  const sendPrompt = async (overridePrompt?: string) => {
    const nextPrompt = (overridePrompt ?? prompt).trim();
    if (!nextPrompt) {
      return;
    }
    setError(null);
    try {
      const payload = await apiPostJson<AtlasResponse>("/atlas/query", {
        page_type: pageType,
        prompt: nextPrompt,
        context: resolvedContext,
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
      setLatestAnswer(payload);
      setMessages(parseThread(payload.thread || []));
      setPrompt("");
      await runs.reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Atlas request failed.");
    }
  };

  const runQuickAction = async (actionName: string) => {
    setError(null);
    try {
      const payload = await apiPostJson<{ result?: { summary?: string; status?: string; count?: number }; error?: string; job?: { status?: string; created_at?: string } }>("/atlas/action", {
        action_name: actionName,
        context: resolvedContext,
      });
      if (payload.error) {
        setError(payload.error);
      } else {
        setWorkflowResults((current) => [
          {
            action_name: actionName,
            status: payload.job?.status || payload.result?.status || "completed",
            summary: payload.result?.summary || payload.result?.status || "Atlas action completed.",
            result: payload.result,
          },
          ...current,
        ]);
      }
      await runs.reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Atlas action failed.");
    }
  };

  const visibleQuickActions = toolSuggestions.length ? toolSuggestions : atlasContext.data?.quick_actions || ["compare_latest_runs", "generate_signoff_packet", "open_high_confidence_findings"];
  const starterPrompts = atlasContext.data?.prompt_starters || [];
  const selectedProjectLabel =
    session.data?.project_options?.find((option) => option.project_id === projectId)?.name ||
    session.data?.project_options?.[0]?.name ||
    "Latest project";

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
                Atlas is now grounded in live Silicore context instead of acting like a detached chatbot.
              </h2>
              <p className="mt-4 max-w-2xl text-base leading-8 text-muted-foreground">
                Workspace intelligence, board analysis context, compare posture, workflow actions, and follow-up prompts are now driven by the same backend intelligence layer as the rest of the product.
              </p>
            </div>
            <div className="grid gap-4 sm:grid-cols-3 xl:grid-cols-1">
              <AtlasSignal label="Mode" value={pageType} copy={atlasContext.data?.summary?.title || "Atlas context"} />
              <AtlasSignal label="Thread" value={threadKey ? "Live" : "New"} copy={threadKey || "Start a new Atlas thread"} />
              <AtlasSignal label="Agent runs" value={String(runs.data?.runs.length || 0)} copy="Tracked against this thread" />
            </div>
          </div>
        </section>

        <div className="grid gap-4 lg:grid-cols-[1fr_340px]">
          <div className="space-y-4">
            <AtlasStage title="Context" rail="working context">
              <div className="grid gap-3 md:grid-cols-3">
                <Field label="Page type">
                  <div className="grid grid-cols-3 gap-2">
                    {(["board", "project", "compare"] as const).map((option) => (
                      <button
                        key={option}
                        onClick={() => {
                          setPageType(option);
                          if (option !== "board") {
                            setSelectedRunId("");
                          }
                        }}
                        className={`interactive-lift rounded-2xl border px-3 py-2 text-sm capitalize ${pageType === option ? "border-primary/40 bg-primary/8 text-foreground" : "border-border bg-background/40 text-muted-foreground"}`}
                      >
                        {option}
                      </button>
                    ))}
                  </div>
                </Field>
                {pageType === "board" ? (
                  <>
                    <Field label="Board snapshot">
                      <select value={activeRunId} onChange={(event) => setSelectedRunId(event.target.value)} className="premium-select h-10 w-full rounded-2xl px-3 text-sm text-foreground">
                        {(atlasContext.data?.board_options || []).map((option) => (
                          <option key={option.run_id} value={option.run_id}>
                            {option.label} · score {Math.round(Number(option.score || 0))} · risks {Number(option.risk_count || 0)}
                          </option>
                        ))}
                      </select>
                    </Field>
                    <Field label="Board label">
                      <div className="premium-input flex min-h-10 w-full flex-col items-start justify-center rounded-2xl px-3 py-2 text-sm text-foreground">
                        <div className="truncate font-medium text-foreground">
                          {selectedBoardOption?.label || boardName || "Select a board run"}
                        </div>
                        <div className="mt-0.5 text-xs text-muted-foreground">
                          {activeRunId ? `Run ${activeRunId}` : "Choose a board snapshot to anchor Atlas to a real analysis run"}
                        </div>
                      </div>
                    </Field>
                  </>
                ) : (
                  <>
                    <Field label="Project">
                      <select value={projectId} onChange={(event) => setProjectId(event.target.value)} className="premium-select h-10 w-full rounded-2xl px-3 text-sm text-foreground">
                        <option value="">{selectedProjectLabel}</option>
                        {(session.data?.project_options || []).map((option) => (
                          <option key={option.project_id} value={option.project_id}>{option.name}</option>
                        ))}
                      </select>
                    </Field>
                    <Field label="Context source">
                      <div className="premium-input flex min-h-10 items-center rounded-2xl px-3 text-sm text-foreground">
                        {pageType === "project" ? selectedProjectLabel : "Revision comparison for the selected workspace"}
                      </div>
                    </Field>
                  </>
                )}
              </div>
              <div className="mt-4 rounded-2xl border border-primary/14 bg-primary/8 p-4">
                <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-primary">Atlas brief</div>
                <div className="mt-2 text-lg font-semibold text-foreground">{atlasContext.data?.summary?.title || "Loading context…"}</div>
                <div className="mt-2 text-sm leading-6 text-muted-foreground">
                  {atlasContext.data?.summary?.copy || "Atlas is preparing context from the active page type and selected workspace."}
                </div>
              </div>
              <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                {contextMetrics.map((metric) => (
                  <div key={metric.label} className="overflow-hidden rounded-2xl border border-white/8 bg-background/30 p-4">
                    <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{metric.label}</div>
                    <div className="mt-2 break-words text-2xl font-semibold leading-tight text-foreground">{metric.value}</div>
                    <div className="mt-2 text-xs leading-5 text-muted-foreground">{metric.copy}</div>
                  </div>
                ))}
              </div>
            </AtlasStage>

            <AtlasStage
              title="Ask Atlas"
              rail="copilot input"
              action={
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-7 rounded-full text-xs"
                  onClick={() => {
                    resetAtlasThread();
                    setPrompt("");
                  }}
                >
                  <HistoryIcon className="mr-1.5 h-3 w-3" />
                  New
                </Button>
              }
            >
              <div className="space-y-4">
                <Textarea value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="Ask Atlas what matters, what changed, what blocks signoff, or what to inspect next…" className="premium-textarea min-h-[110px]" />
                <div className="flex flex-wrap gap-1.5">
                  {starterPrompts.map((suggestion) => (
                    <button key={suggestion} onClick={() => void sendPrompt(suggestion)} className="rounded-full border border-border bg-background/40 px-3 py-1 font-mono text-[10px] uppercase tracking-wider text-muted-foreground hover:text-foreground">
                      {suggestion}
                    </button>
                  ))}
                </div>
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="text-xs text-muted-foreground">
                    Atlas is answering from live workspace/board/compare context instead of a generic prompt shell.
                  </div>
                  <Button size="sm" className="rounded-full" onClick={() => void sendPrompt()}><Send className="mr-1.5 h-3.5 w-3.5" /> Send</Button>
                </div>
                {error ? <div className="text-sm text-danger">{error}</div> : null}
              </div>
            </AtlasStage>

            <AtlasStage title="Atlas answer" rail="reasoned output" action={<BrainCircuit className="h-4 w-4 text-primary" />}>
              {latestAnswer ? (
                <div className="space-y-4">
                  <div className="rounded-2xl border border-white/8 bg-background/35 p-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{latestAnswer.title || "Atlas"}</div>
                        <div className="mt-2 text-xl font-semibold text-foreground">{latestAnswer.answer || "No answer returned."}</div>
                      </div>
                      <div className="rounded-full border border-primary/18 bg-primary/10 px-3 py-1.5 text-xs text-primary">
                        Confidence {Math.round((latestAnswer.confidence || 0) * 100)}%
                      </div>
                    </div>
                    {latestAnswer.detail ? <p className="mt-3 text-sm leading-7 text-muted-foreground">{latestAnswer.detail}</p> : null}
                  </div>

                  {latestAnswer.citations?.length ? (
                    <div className="grid gap-3 md:grid-cols-2">
                      {latestAnswer.citations.map((citation, index) => (
                        <div key={`${citation.label}-${index}`} className="rounded-2xl border border-white/8 bg-background/35 p-4">
                          <div className="text-sm font-medium text-foreground">{citation.label || "Evidence item"}</div>
                          <div className="mt-2 text-xs leading-6 text-muted-foreground">
                            Components: {(citation.components || []).join(", ") || "—"}<br />
                            Nets: {(citation.nets || []).join(", ") || "—"}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : null}

                  {latestAnswer.follow_ups?.length ? (
                    <div className="rounded-2xl border border-white/8 bg-background/30 p-4">
                      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Follow-up prompts</div>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {latestAnswer.follow_ups.map((item) => (
                          <button key={item} onClick={() => void sendPrompt(item)} className="rounded-full border border-primary/18 bg-primary/8 px-3 py-1.5 text-xs text-primary hover:bg-primary/12">
                            {item}
                          </button>
                        ))}
                      </div>
                    </div>
                  ) : null}

                  {latestAnswer.agent_trace?.length ? (
                    <div className="space-y-2">
                      {latestAnswer.agent_trace.map((item, index) => (
                        <div key={`${item.label}-${index}`} className="rounded-2xl border border-white/8 bg-background/30 p-4">
                          <div className="flex items-center justify-between gap-3">
                            <div className="text-sm font-medium text-foreground">{item.label || `Step ${index + 1}`}</div>
                            <span className={`font-mono text-[10px] uppercase tracking-[0.16em] ${item.status === "completed" ? "text-success" : item.status === "failed" ? "text-danger" : "text-warning"}`}>{item.status || "ready"}</span>
                          </div>
                          <div className="mt-2 text-sm text-muted-foreground">{item.summary || "Atlas executed this step."}</div>
                        </div>
                      ))}
                    </div>
                  ) : null}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">Ask Atlas a real engineering question and this panel will show the answer, its confidence, cited signals, and suggested follow-ups.</p>
              )}
            </AtlasStage>

            <AtlasStage title="Thread" rail="conversation stream">
              <div className="space-y-3">
                {messages.map((message, index) => (
                  <div key={`${message.who}-${index}`} className={`flex items-start gap-3 rounded-xl border border-border p-4 ${message.who === "user" ? "bg-background/40" : "bg-primary/5"}`}>
                    <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${message.who === "user" ? "bg-muted text-muted-foreground" : "bg-primary/15 text-primary"}`}>
                      {message.who === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                    </div>
                    <div className="flex-1">
                      <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{message.who === "user" ? "You" : "Atlas"}</div>
                      <p className="mt-1 whitespace-pre-wrap text-sm">{message.text}</p>
                    </div>
                  </div>
                ))}
                {!messages.length ? <p className="text-sm text-muted-foreground">Start with one of the suggested prompts above and Atlas will keep the thread anchored to this live context.</p> : null}
              </div>
            </AtlasStage>
          </div>

          <div className="space-y-4">
            <AtlasStage title="Quick actions" rail="action shortcuts" action={<Wrench className="h-4 w-4 text-primary" />}>
              <div className="space-y-2">
                {visibleQuickActions.map((actionName) => (
                  <button key={actionName} onClick={() => void runQuickAction(actionName)} className="flex w-full items-center justify-between rounded-lg border border-border bg-background/40 p-3 text-left text-sm hover:border-primary/30">
                    <span>{actionName.replaceAll("_", " ")}</span>
                    <PlayCircle className="h-4 w-4 text-muted-foreground" />
                  </button>
                ))}
              </div>
            </AtlasStage>

            <AtlasStage title="Workflow plan" rail="planner" action={<Workflow className="h-4 w-4 text-primary" />}>
              <div className="space-y-2">
                {workflowPlan.map((step, index) => (
                  <div key={`${step.action_name || step.title}-${index}`} className="rounded-xl border border-border bg-background/40 p-3">
                    <div className="text-sm text-foreground">{step.title || step.action_name || step.step || `Step ${index + 1}`}</div>
                    {step.reason ? <div className="mt-1 text-xs text-muted-foreground">{step.reason}</div> : null}
                  </div>
                ))}
                {!workflowPlan.length ? <p className="text-sm text-muted-foreground">Atlas will surface a workflow plan here whenever your prompt implies a concrete engineering action path.</p> : null}
              </div>
            </AtlasStage>

            <AtlasStage title="Workflow results" rail="execution output" action={<CheckCircle2 className="h-4 w-4 text-primary" />}>
              <div className="space-y-2">
                {workflowResults.map((result, index) => (
                  <div key={`${result.action_name}-${index}`} className="rounded-xl border border-border bg-background/40 p-3">
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-sm text-foreground">{(result.action_name || "workflow").replaceAll("_", " ")}</div>
                      <span className={`font-mono text-[10px] uppercase tracking-wider ${result.status === "completed" ? "text-success" : result.status === "failed" ? "text-danger" : "text-warning"}`}>{result.status || "ready"}</span>
                    </div>
                    <div className="mt-1 text-sm text-muted-foreground">{result.summary || result.result?.summary || result.result?.status || result.reason || "Atlas recorded a workflow event."}</div>
                  </div>
                ))}
                {!workflowResults.length ? <p className="text-sm text-muted-foreground">When Atlas executes or suggests actions, their outputs will show up here instead of getting lost in the thread.</p> : null}
              </div>
            </AtlasStage>

            <AtlasStage title="Agent runs" rail="execution history" action={<Zap className="h-4 w-4 text-primary" />}>
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
            </AtlasStage>
          </div>
        </div>
      </div>
    </AppShell>
  );
}

function stripHtml(value: string) {
  return String(value || "").replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
}

function formatMetricValue(value: unknown, mode: "score" | "percent" | "delta" | "count") {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "—";
  }
  if (mode === "percent") {
    const normalized = number <= 1 ? number * 100 : number;
    return `${Math.round(normalized)}%`;
  }
  if (mode === "delta") {
    const rounded = Math.round(number);
    return `${rounded > 0 ? "+" : ""}${rounded}`;
  }
  return `${Math.round(number)}`;
}

function AtlasSignal({ label, value, copy }: { label: string; value: string; copy: string }) {
  return (
    <div className="border-l border-white/10 pl-4">
      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{label}</div>
      <div className="mt-1 text-3xl font-semibold capitalize text-foreground">{value}</div>
      <div className="mt-1 text-sm text-muted-foreground">{copy}</div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="space-y-1.5">
      <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
      {children}
    </div>
  );
}

function AtlasStage({
  title,
  rail,
  action,
  children,
}: {
  title: string;
  rail?: string;
  action?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section data-reveal className="relative overflow-hidden rounded-[28px] border border-white/8 bg-[linear-gradient(155deg,rgba(8,17,27,0.96),rgba(7,14,22,0.98))] p-6 shadow-[0_28px_70px_-44px_rgba(0,0,0,0.92)]">
      <div className="mb-5 flex items-start justify-between gap-4 border-b border-white/8 pb-4">
        <div>
          {rail ? <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{rail}</div> : null}
          <h3 className="mt-1 text-lg font-medium tracking-tight">{title}</h3>
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}
