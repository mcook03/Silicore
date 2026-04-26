import type { ReactNode } from "react";
import { ArrowRight, LoaderCircle, Sparkles } from "lucide-react";
import { Link } from "@tanstack/react-router";

export function LoadingSurface({
  title = "Loading surface",
  copy = "Silicore is assembling the latest engineering view.",
  lines = 3,
}: {
  title?: string;
  copy?: string;
  lines?: number;
}) {
  return (
    <div className="rounded-[28px] border border-white/8 bg-[linear-gradient(155deg,rgba(8,17,27,0.94),rgba(7,14,22,0.98))] p-6 shadow-[0_24px_68px_-44px_rgba(0,0,0,0.9)]">
      <div className="flex items-center gap-3">
        <span className="flex h-10 w-10 items-center justify-center rounded-2xl border border-primary/20 bg-primary/10 text-primary">
          <LoaderCircle className="h-4 w-4 animate-spin" />
        </span>
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Live loading</div>
          <div className="mt-1 text-lg font-medium tracking-tight text-foreground">{title}</div>
        </div>
      </div>
      <p className="mt-4 text-sm leading-7 text-muted-foreground">{copy}</p>
      <div className="mt-5 space-y-3">
        {Array.from({ length: lines }).map((_, index) => (
          <div
            key={index}
            className="h-3 rounded-full bg-[linear-gradient(90deg,rgba(255,255,255,0.05),rgba(86,211,240,0.16),rgba(255,255,255,0.05))] animate-[shimmer_1.8s_linear_infinite]"
            style={{ width: `${100 - index * 12}%` }}
          />
        ))}
      </div>
    </div>
  );
}

export function EmptySurface({
  eyebrow = "Empty state",
  title,
  copy,
  action,
}: {
  eyebrow?: string;
  title: string;
  copy: string;
  action?: ReactNode;
}) {
  return (
    <div className="rounded-[28px] border border-dashed border-white/12 bg-[linear-gradient(160deg,rgba(8,16,26,0.72),rgba(7,14,22,0.9))] p-6">
      <div className="flex items-start gap-4">
        <span className="mt-0.5 flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-primary/20 bg-primary/10 text-primary">
          <Sparkles className="h-4 w-4" />
        </span>
        <div className="min-w-0">
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{eyebrow}</div>
          <div className="mt-1 text-lg font-medium tracking-tight text-foreground">{title}</div>
          <p className="mt-2 max-w-2xl text-sm leading-7 text-muted-foreground">{copy}</p>
          {action ? <div className="mt-4">{action}</div> : null}
        </div>
      </div>
    </div>
  );
}

export function FilterPills<T extends string>({
  options,
  active,
  onChange,
}: {
  options: Array<{ value: T; label: string; count?: number }>;
  active: T;
  onChange: (value: T) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((option) => {
        const selected = option.value === active;
        return (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs transition-all ${
              selected
                ? "border-primary/35 bg-primary/12 text-primary shadow-[0_0_0_1px_rgba(86,211,240,0.08)]"
                : "border-white/10 bg-white/4 text-muted-foreground hover:border-primary/20 hover:text-foreground"
            }`}
          >
            <span className="font-mono uppercase tracking-[0.16em]">{option.label}</span>
            {typeof option.count === "number" ? (
              <span className="rounded-full bg-background/45 px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
                {option.count}
              </span>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}

export function DecisionStrip({
  eyebrow = "Decision strip",
  title,
  copy,
  metrics,
}: {
  eyebrow?: string;
  title: string;
  copy: string;
  metrics: Array<{ label: string; value: string; tone?: "default" | "success" | "warning" | "danger" }>;
}) {
  return (
    <div className="decision-strip rounded-[28px] px-5 py-5">
      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)] xl:items-end">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{eyebrow}</div>
          <div className="mt-1 text-xl font-semibold tracking-tight text-foreground">{title}</div>
          <p className="mt-2 max-w-2xl text-sm leading-7 text-muted-foreground">{copy}</p>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {metrics.map((metric) => (
            <div key={metric.label} className="rounded-2xl border border-white/8 bg-black/10 px-4 py-3">
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{metric.label}</div>
              <div className={`mt-2 text-2xl font-semibold ${toneClass(metric.tone)}`}>{metric.value}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function WorkflowAction({
  to,
  label,
  copy,
}: {
  to: string;
  label: string;
  copy: string;
}) {
  return (
    <Link
      to={to}
      className="group flex items-center justify-between gap-4 rounded-2xl border border-white/8 bg-white/3 px-4 py-3 transition-colors hover:border-primary/20 hover:bg-primary/6"
    >
      <div>
        <div className="text-sm font-medium text-foreground">{label}</div>
        <div className="mt-1 text-xs text-muted-foreground">{copy}</div>
      </div>
      <ArrowRight className="h-4 w-4 text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:text-primary" />
    </Link>
  );
}

function toneClass(tone?: "default" | "success" | "warning" | "danger") {
  if (tone === "success") return "text-success";
  if (tone === "warning") return "text-warning";
  if (tone === "danger") return "text-danger";
  return "text-foreground";
}
