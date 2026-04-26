import { useEffect, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { Panel } from "@/components/silicore/Panel";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { apiPostJson, useApiData } from "@/lib/api";

export const Route = createFileRoute("/settings")({
  head: () => ({ meta: [{ title: "Settings — Silicore" }] }),
  component: Settings,
});

type SettingsPayload = {
  config: Record<string, unknown>;
  editable_config: Record<string, unknown>;
  settings_view: {
    section_counts: Record<string, number>;
    total_controls: number;
    advanced_capability_count: number;
  };
  settings_architecture: {
    profile_cards: Array<{ title: string; value: string | number; copy: string }>;
    domain_pillars: Array<{ title: string; copy: string }>;
  };
};

function Settings() {
  const { data, error, reload } = useApiData<SettingsPayload>("/api/frontend/settings");
  const [editorValue, setEditorValue] = useState("");
  const [saveState, setSaveState] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (data?.config) {
      setEditorValue(JSON.stringify(data.config, null, 2));
    }
  }, [data]);

  const saveConfig = async () => {
    setSaving(true);
    setSaveState(null);
    try {
      const parsed = JSON.parse(editorValue) as Record<string, unknown>;
      await apiPostJson("/api/frontend/settings", { config: parsed });
      setSaveState("Settings saved.");
      await reload();
    } catch (err) {
      setSaveState(err instanceof Error ? err.message : "Unable to save settings.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <AppShell title="Settings">
      <div className="space-y-6">
        {error ? <div className="rounded-xl border border-danger/20 bg-danger/10 px-4 py-3 text-sm text-danger">{error}</div> : null}

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {data?.settings_architecture.profile_cards.map((card) => (
            <div key={card.title} className="rounded-2xl border border-border bg-surface p-5">
              <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{card.title}</div>
              <div className="mt-2 text-2xl font-semibold">{card.value}</div>
              <div className="mt-2 text-xs text-muted-foreground">{card.copy}</div>
            </div>
          )) ?? null}
        </div>

        <div className="grid gap-6 xl:grid-cols-[320px_1fr]">
          <Panel title="Control surface">
            <div className="space-y-3">
              {Object.entries(data?.settings_view.section_counts || {}).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between rounded-lg border border-border bg-background/40 px-3 py-2">
                  <span className="text-sm capitalize">{key}</span>
                  <span className="font-mono text-xs text-muted-foreground">{value}</span>
                </div>
              ))}
              <div className="rounded-lg border border-primary/20 bg-primary/5 px-3 py-2 text-sm">
                <div className="font-medium">Total editable controls</div>
                <div className="font-mono text-xs text-muted-foreground">{data?.settings_view.total_controls ?? 0} active controls</div>
              </div>
            </div>
          </Panel>

          <Panel title="Configuration editor" action={<Button size="sm" className="rounded-full" onClick={() => void saveConfig()} disabled={saving}>{saving ? "Saving…" : "Save config"}</Button>}>
            <p className="mb-4 text-sm text-muted-foreground">This editor writes the full Silicore config that powers upload analysis, scoring, and rule behavior in the new UI.</p>
            <div className="mb-3 flex gap-2">
              <Button
                type="button"
                size="sm"
                variant="ghost"
                className="rounded-full"
                onClick={() => {
                  try {
                    const parsed = JSON.parse(editorValue) as Record<string, unknown>;
                    setEditorValue(JSON.stringify(parsed, null, 2));
                    setSaveState("JSON formatted.");
                  } catch (err) {
                    setSaveState(err instanceof Error ? err.message : "JSON formatting failed.");
                  }
                }}
              >
                Format JSON
              </Button>
            </div>
            <Textarea value={editorValue} onChange={(event) => setEditorValue(event.target.value)} className="min-h-[520px] font-mono text-xs" />
            {saveState ? <div className={`mt-3 text-sm ${saveState === "Settings saved." || saveState === "JSON formatted." ? "text-success" : "text-danger"}`}>{saveState}</div> : null}
          </Panel>
        </div>

        <Panel title="Architecture notes">
          <div className="grid gap-3 md:grid-cols-3">
            {data?.settings_architecture.domain_pillars.map((pillar) => (
              <div key={pillar.title} className="rounded-xl border border-border bg-background/40 p-4">
                <div className="text-sm font-medium">{pillar.title}</div>
                <div className="mt-2 text-xs text-muted-foreground">{pillar.copy}</div>
              </div>
            )) ?? null}
          </div>
        </Panel>
      </div>
    </AppShell>
  );
}
