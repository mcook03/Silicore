import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { apiPostJson, useApiData } from "@/lib/api";
import { SlidersHorizontal, ShieldCheck, Zap, Waves, Thermometer, ChevronDown } from "lucide-react";

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

type ConfigRecord = Record<string, unknown>;

function Settings() {
  const { data, error, reload } = useApiData<SettingsPayload>("/api/frontend/settings");
  const [draftConfig, setDraftConfig] = useState<ConfigRecord | null>(null);
  const [editorValue, setEditorValue] = useState("");
  const [saveState, setSaveState] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [advancedOpen, setAdvancedOpen] = useState(false);

  useEffect(() => {
    if (data?.config) {
      setDraftConfig(data.config);
      setEditorValue(JSON.stringify(data.config, null, 2));
    }
  }, [data]);

  const saveConfig = async (nextConfig?: ConfigRecord | null) => {
    const configToSave = nextConfig || draftConfig;
    if (!configToSave) {
      return;
    }
    setSaving(true);
    setSaveState(null);
    try {
      await apiPostJson("/api/frontend/settings", { config: configToSave });
      setSaveState("Settings saved.");
      await reload();
    } catch (err) {
      setSaveState(err instanceof Error ? err.message : "Unable to save settings.");
    } finally {
      setSaving(false);
    }
  };

  const updateConfig = (updater: (current: ConfigRecord) => ConfigRecord) => {
    setDraftConfig((current) => {
      const base = (current || data?.config || {}) as ConfigRecord;
      const next = updater(base);
      setEditorValue(JSON.stringify(next, null, 2));
      return next;
    });
  };

  const profileOptions = asStringArray(getNested(draftConfig, ["analysis", "available_profiles"])).map((value) => ({
    value,
    label: humanize(value),
  }));
  const boardTypeOptions = asStringArray(getNested(draftConfig, ["analysis", "available_board_types"])).map((value) => ({
    value,
    label: humanize(value),
  }));
  const categoryToggles = (getNested(draftConfig, ["analysis", "category_toggles"]) as Record<string, boolean> | undefined) || {};

  const summaryCards = useMemo(() => [
    {
      label: "Current profile",
      value: String(getNested(draftConfig, ["analysis", "profile"]) || "balanced"),
      subtext: "Default review posture",
    },
    {
      label: "Board mode",
      value: String(getNested(draftConfig, ["analysis", "board_type"]) || "general"),
      subtext: "Primary board context",
    },
    {
      label: "Editable controls",
      value: String(data?.settings_view.total_controls ?? 0),
      subtext: "Exposed in this workspace",
    },
    {
      label: "Advanced capabilities",
      value: String(data?.settings_view.advanced_capability_count ?? 0),
      subtext: "Physics and rule tuning",
    },
  ], [draftConfig, data]);

  return (
    <AppShell title="Settings">
      <div className="space-y-6">
        {error ? <div className="rounded-xl border border-danger/20 bg-danger/10 px-4 py-3 text-sm text-danger">{error}</div> : null}

        <section
          data-reveal
          className="relative overflow-hidden rounded-[34px] border border-border/80 bg-[radial-gradient(circle_at_100%_0%,rgba(86,211,240,0.14),transparent_22%),linear-gradient(135deg,rgba(8,17,27,0.98),rgba(8,15,24,0.96)_58%,rgba(11,20,32,0.98))] px-6 py-7 sm:px-8 sm:py-8"
        >
          <div className="absolute inset-y-0 right-[32%] w-px bg-gradient-to-b from-transparent via-white/8 to-transparent max-xl:hidden" />
          <div className="relative grid gap-8 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
            <div>
              <div className="section-eyebrow">
                <SlidersHorizontal className="h-3.5 w-3.5" />
                Control board
              </div>
              <h2 className="mt-5 max-w-3xl text-4xl font-semibold tracking-tight text-foreground sm:text-[3.15rem] sm:leading-[1.02]">
                Tune how Silicore thinks about spacing, score pressure, power realism, and review strictness.
              </h2>
              <p className="mt-4 max-w-2xl text-base leading-8 text-muted-foreground">
                Settings should feel like a control instrument, not a banner sitting above more cards. This page is moving toward a more intentional configuration workspace with daily controls front and center.
              </p>
            </div>
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-1">
              {summaryCards.map((card) => (
                <div key={card.label} className="border-l border-white/10 pl-4">
                  <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{card.label}</div>
                  <div className="mt-1 text-2xl font-semibold text-foreground">{humanize(card.value)}</div>
                  <div className="mt-1 text-sm text-muted-foreground">{card.subtext}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <div className="grid gap-6 xl:grid-cols-[320px_1fr]">
          <SettingsZone title="Workspace posture" rail="config snapshot">
            <div className="space-y-3">
              {data?.settings_architecture.profile_cards.map((card) => (
                <div key={card.title} className="rounded-xl border border-border bg-background/40 p-4">
                  <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{card.title}</div>
                  <div className="mt-1 text-lg font-semibold">{card.value}</div>
                  <div className="mt-2 text-xs text-muted-foreground">{card.copy}</div>
                </div>
              )) ?? null}
              <div className="rounded-xl border border-primary/20 bg-primary/5 p-4 text-sm">
                <div className="font-medium">Controls exposed</div>
                <div className="mt-1 font-mono text-xs text-muted-foreground">{data?.settings_view.total_controls ?? 0} editable controls across {Object.keys(data?.settings_view.section_counts || {}).length} sections.</div>
              </div>
            </div>
          </SettingsZone>

          <div className="space-y-6">
            <SettingsZone title="Analysis defaults" rail="default routing" action={<Zap className="h-4 w-4 text-primary" />}>
              <div className="grid gap-5 lg:grid-cols-2">
                <Field label="Default profile">
                  <select
                    value={String(getNested(draftConfig, ["analysis", "profile"]) || "balanced")}
                    onChange={(event) => updateConfig((current) => setNested(current, ["analysis", "profile"], event.target.value))}
                    className="premium-select h-11 w-full px-3 text-sm"
                  >
                    {profileOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                  </select>
                </Field>
                <Field label="Board type">
                  <select
                    value={String(getNested(draftConfig, ["analysis", "board_type"]) || "general")}
                    onChange={(event) => updateConfig((current) => setNested(current, ["analysis", "board_type"], event.target.value))}
                    className="premium-select h-11 w-full px-3 text-sm"
                  >
                    {boardTypeOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                  </select>
                </Field>
              </div>

              <div className="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {Object.entries(categoryToggles).map(([key, value]) => (
                  <ToggleCard
                    key={key}
                    label={humanize(key)}
                    description="Enable or disable this domain during analysis."
                    checked={Boolean(value)}
                    onCheckedChange={(checked) => updateConfig((current) => setNested(current, ["analysis", "category_toggles", key], checked))}
                  />
                ))}
              </div>
            </SettingsZone>

            <div className="grid gap-6 lg:grid-cols-2">
              <SettingsZone title="Score penalties" rail="scoring pressure" action={<ShieldCheck className="h-4 w-4 text-primary" />}>
                <div className="space-y-6">
                  <SliderField
                    label="Critical penalty"
                    value={asNumber(getNested(draftConfig, ["score", "penalty_critical"]), 1.2)}
                    min={0}
                    max={2}
                    step={0.05}
                    copy="How much a critical finding drags the score."
                    onValueChange={(value) => updateConfig((current) => setNested(current, ["score", "penalty_critical"], value))}
                  />
                  <SliderField
                    label="High penalty"
                    value={asNumber(getNested(draftConfig, ["score", "penalty_high"]), 0.6)}
                    min={0}
                    max={1.5}
                    step={0.05}
                    copy="Pressure applied to high-severity findings."
                    onValueChange={(value) => updateConfig((current) => setNested(current, ["score", "penalty_high"], value))}
                  />
                  <SliderField
                    label="Medium penalty"
                    value={asNumber(getNested(draftConfig, ["score", "penalty_medium"]), 0.4)}
                    min={0}
                    max={1}
                    step={0.05}
                    copy="Penalty weight for medium findings."
                    onValueChange={(value) => updateConfig((current) => setNested(current, ["score", "penalty_medium"], value))}
                  />
                  <SliderField
                    label="Low penalty"
                    value={asNumber(getNested(draftConfig, ["score", "penalty_low"]), 0.2)}
                    min={0}
                    max={0.8}
                    step={0.05}
                    copy="Penalty weight for low findings."
                    onValueChange={(value) => updateConfig((current) => setNested(current, ["score", "penalty_low"], value))}
                  />
                </div>
              </SettingsZone>

              <SettingsZone title="Layout and routing" rail="physical layout" action={<Waves className="h-4 w-4 text-primary" />}>
                <div className="space-y-6">
                  <SliderField
                    label="Minimum component spacing"
                    value={asNumber(getNested(draftConfig, ["layout", "min_component_spacing"]), 3)}
                    min={0.5}
                    max={10}
                    step={0.1}
                    copy="Clearance target between nearby components."
                    onValueChange={(value) => updateConfig((current) => setNested(current, ["layout", "min_component_spacing"], value))}
                  />
                  <SliderField
                    label="Density threshold"
                    value={asNumber(getNested(draftConfig, ["layout", "density_threshold"]), 6)}
                    min={1}
                    max={20}
                    step={1}
                    copy="How dense a region can get before layout pressure is flagged."
                    onValueChange={(value) => updateConfig((current) => setNested(current, ["layout", "density_threshold"], value))}
                  />
                  <SliderField
                    label="Density region size"
                    value={asNumber(getNested(draftConfig, ["layout", "density_region_size"]), 25)}
                    min={5}
                    max={60}
                    step={1}
                    copy="The analysis window size used for density evaluation."
                    onValueChange={(value) => updateConfig((current) => setNested(current, ["layout", "density_region_size"], value))}
                  />
                  <SliderField
                    label="Signal trace width floor"
                    value={asNumber(getNested(draftConfig, ["signal", "min_general_trace_width"]), 0.15)}
                    min={0.05}
                    max={1}
                    step={0.01}
                    copy="Minimum general-purpose routed width."
                    onValueChange={(value) => updateConfig((current) => setNested(current, ["signal", "min_general_trace_width"], value))}
                  />
                </div>
              </SettingsZone>
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
              <SettingsZone title="Power and manufacturability" rail="power model" action={<Zap className="h-4 w-4 text-primary" />}>
                <div className="space-y-6">
                  <SliderField
                    label="Power trace width floor"
                    value={asNumber(getNested(draftConfig, ["power", "min_trace_width"]), 0.5)}
                    min={0.1}
                    max={2}
                    step={0.05}
                    copy="Minimum width expected on power rails."
                    onValueChange={(value) => updateConfig((current) => setNested(current, ["power", "min_trace_width"], value))}
                  />
                  <SliderField
                    label="Max power via count"
                    value={asNumber(getNested(draftConfig, ["power", "max_via_count"]), 5)}
                    min={1}
                    max={12}
                    step={1}
                    copy="Upper bound before power transitions are considered excessive."
                    onValueChange={(value) => updateConfig((current) => setNested(current, ["power", "max_via_count"], value))}
                  />
                  <SliderField
                    label="Diff pair mismatch threshold"
                    value={asNumber(getNested(draftConfig, ["rules", "differential_pair_length_mismatch_threshold"]), 5)}
                    min={1}
                    max={20}
                    step={0.5}
                    copy="Allowed differential pair skew before Silicore flags it."
                    onValueChange={(value) => updateConfig((current) => setNested(current, ["rules", "differential_pair_length_mismatch_threshold"], value))}
                  />
                  <SliderField
                    label="Minimum fiducials"
                    value={asNumber(getNested(draftConfig, ["rules", "assembly_testability_min_fiducials"]), 2)}
                    min={0}
                    max={6}
                    step={1}
                    copy="Required global fiducials for assembly confidence."
                    onValueChange={(value) => updateConfig((current) => setNested(current, ["rules", "assembly_testability_min_fiducials"], value))}
                  />
                </div>
              </SettingsZone>

              <SettingsZone title="Safety and thermal" rail="risk policy" action={<Thermometer className="h-4 w-4 text-primary" />}>
                <div className="space-y-6">
                  <SliderField
                    label="High-voltage clearance"
                    value={asNumber(getNested(draftConfig, ["rules", "safety_high_voltage_min_clearance"]), 2.5)}
                    min={0.5}
                    max={10}
                    step={0.1}
                    copy="Clearance threshold for elevated-voltage checks."
                    onValueChange={(value) => updateConfig((current) => setNested(current, ["rules", "safety_high_voltage_min_clearance"], value))}
                  />
                  <SliderField
                    label="High-voltage creepage"
                    value={asNumber(getNested(draftConfig, ["rules", "safety_high_voltage_min_creepage"]), 5)}
                    min={1}
                    max={15}
                    step={0.1}
                    copy="Creepage target used during safety review."
                    onValueChange={(value) => updateConfig((current) => setNested(current, ["rules", "safety_high_voltage_min_creepage"], value))}
                  />
                  <SliderField
                    label="Thermal hotspot distance"
                    value={asNumber(getNested(draftConfig, ["thermal", "hotspot_distance_threshold"]), 4)}
                    min={1}
                    max={20}
                    step={0.5}
                    copy="Radius used to classify hotspot proximity."
                    onValueChange={(value) => updateConfig((current) => setNested(current, ["thermal", "hotspot_distance_threshold"], value))}
                  />
                  <ToggleCard
                    label="Require ground reference"
                    description="Force EMI checks to expect explicit ground reference behavior."
                    checked={Boolean(getNested(draftConfig, ["emi", "require_ground_reference"]))}
                    onCheckedChange={(checked) => updateConfig((current) => setNested(current, ["emi", "require_ground_reference"], checked))}
                  />
                </div>
              </SettingsZone>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-border bg-surface p-4">
              <div>
                <div className="text-sm font-medium">Save tuned settings</div>
                <div className="text-xs text-muted-foreground">These controls write back into the same Silicore config the backend uses for analysis.</div>
              </div>
              <Button className="rounded-full" onClick={() => void saveConfig()} disabled={saving}>
                {saving ? "Saving…" : "Save tuned config"}
              </Button>
            </div>
          </div>
        </div>

        <SettingsZone title="Architecture notes" rail="system notes">
          <div className="grid gap-3 md:grid-cols-3">
            {data?.settings_architecture.domain_pillars.map((pillar) => (
              <div key={pillar.title} className="rounded-xl border border-border bg-background/40 p-4">
                <div className="text-sm font-medium">{pillar.title}</div>
                <div className="mt-2 text-xs text-muted-foreground">{pillar.copy}</div>
              </div>
            )) ?? null}
          </div>
        </SettingsZone>

        <SettingsZone
          title="Advanced JSON"
          rail="power user editor"
          action={
            <Button type="button" size="sm" variant="ghost" className="rounded-full" onClick={() => setAdvancedOpen((value) => !value)}>
              <ChevronDown className={`mr-1.5 h-3.5 w-3.5 transition-transform ${advancedOpen ? "rotate-180" : ""}`} />
              {advancedOpen ? "Hide" : "Show"}
            </Button>
          }
        >
          {advancedOpen ? (
            <>
              <p className="mb-4 text-sm text-muted-foreground">Use the advanced editor when you need direct access to the full config object.</p>
              <div className="mb-3 flex gap-2">
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  className="rounded-full"
                  onClick={() => {
                    try {
                      const parsed = JSON.parse(editorValue) as ConfigRecord;
                      setDraftConfig(parsed);
                      setEditorValue(JSON.stringify(parsed, null, 2));
                      setSaveState("JSON formatted.");
                    } catch (err) {
                      setSaveState(err instanceof Error ? err.message : "JSON formatting failed.");
                    }
                  }}
                >
                  Format JSON
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  className="rounded-full"
                  onClick={() => {
                    try {
                      const parsed = JSON.parse(editorValue) as ConfigRecord;
                      setDraftConfig(parsed);
                      setSaveState("Draft synced from JSON.");
                    } catch (err) {
                      setSaveState(err instanceof Error ? err.message : "Draft sync failed.");
                    }
                  }}
                >
                  Sync to controls
                </Button>
              </div>
              <Textarea value={editorValue} onChange={(event) => setEditorValue(event.target.value)} className="min-h-[420px] font-mono text-xs" />
            </>
          ) : (
            <p className="text-sm text-muted-foreground">The raw JSON editor is tucked away by default now, but it’s still here for power users and edge-case tuning.</p>
          )}
          {saveState ? <div className={`mt-3 text-sm ${/saved|formatted|synced/i.test(saveState) ? "text-success" : "text-danger"}`}>{saveState}</div> : null}
        </SettingsZone>
      </div>
    </AppShell>
  );
}

function SettingsZone({
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
    <section data-reveal className="relative overflow-hidden rounded-[28px] border border-white/8 bg-[linear-gradient(145deg,rgba(8,17,27,0.96),rgba(7,14,22,0.98))] p-6 shadow-[0_28px_70px_-44px_rgba(0,0,0,0.92)]">
      <div className="pointer-events-none absolute inset-y-0 right-0 w-px bg-gradient-to-b from-transparent via-primary/50 to-transparent" />
      <div className="relative">
        <div className="mb-5 flex items-start justify-between gap-4">
          <div>
            {rail ? <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{rail}</div> : null}
            <h3 className="mt-1 text-lg font-medium tracking-tight">{title}</h3>
          </div>
          {action}
        </div>
        {children}
      </div>
    </section>
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

function ToggleCard({
  label,
  description,
  checked,
  onCheckedChange,
}: {
  label: string;
  description: string;
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-2xl border border-border bg-background/40 p-4">
      <div>
        <div className="text-sm font-medium">{label}</div>
        <div className="mt-1 text-xs text-muted-foreground">{description}</div>
      </div>
      <Switch checked={checked} onCheckedChange={onCheckedChange} />
    </div>
  );
}

function SliderField({
  label,
  value,
  min,
  max,
  step,
  copy,
  onValueChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  copy: string;
  onValueChange: (value: number) => void;
}) {
  return (
    <div className="rounded-2xl border border-border bg-background/40 p-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <div className="text-sm font-medium">{label}</div>
          <div className="mt-1 text-xs text-muted-foreground">{copy}</div>
        </div>
        <Input
          type="number"
          value={String(value)}
          onChange={(event) => onValueChange(Number(event.target.value))}
          className="h-9 w-24 font-mono text-xs"
        />
      </div>
      <div className="mt-4">
        <Slider value={[value]} min={min} max={max} step={step} onValueChange={(next) => onValueChange(next[0] || min)} />
        <div className="mt-2 flex items-center justify-between font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
          <span>{min}</span>
          <span>{max}</span>
        </div>
      </div>
    </div>
  );
}

function getNested(source: unknown, path: string[]) {
  return path.reduce<unknown>((current, key) => {
    if (!current || typeof current !== "object") {
      return undefined;
    }
    return (current as Record<string, unknown>)[key];
  }, source);
}

function setNested(source: ConfigRecord, path: string[], value: unknown): ConfigRecord {
  const clone: ConfigRecord = JSON.parse(JSON.stringify(source));
  let cursor: ConfigRecord = clone;
  for (let index = 0; index < path.length - 1; index += 1) {
    const key = path[index];
    const next = cursor[key];
    if (!next || typeof next !== "object" || Array.isArray(next)) {
      cursor[key] = {};
    }
    cursor = cursor[key] as ConfigRecord;
  }
  cursor[path[path.length - 1]] = value;
  return clone;
}

function asStringArray(value: unknown) {
  return Array.isArray(value) ? value.map((item) => String(item)) : [];
}

function asNumber(value: unknown, fallback: number) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : fallback;
}

function humanize(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase());
}
