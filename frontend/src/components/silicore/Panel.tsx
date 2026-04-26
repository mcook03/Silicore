import type { ReactNode } from "react";

export function Panel({
  title,
  subtitle,
  children,
  action,
  className = "",
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <section data-reveal className={`premium-panel rounded-[28px] p-6 sm:p-7 ${className}`}>
      <div className="glow-divider mb-5 flex items-start justify-between gap-4 pb-4">
        <div className="min-w-0">
          <h3 className="text-sm font-medium tracking-tight text-foreground sm:text-[15px]">{title}</h3>
          {subtitle ? <p className="mt-1 text-sm leading-6 text-muted-foreground">{subtitle}</p> : null}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}

export function ScorePill({ score }: { score: number }) {
  const tone = score >= 80 ? "success" : score >= 65 ? "warning" : "danger";
  const cls = {
    success: "border-success/25 bg-success/12 text-success shadow-[0_0_18px_-12px_oklch(0.88_0.15_175_/_0.75)]",
    warning: "border-warning/25 bg-warning/12 text-warning shadow-[0_0_18px_-12px_oklch(0.83_0.13_70_/_0.72)]",
    danger: "border-danger/25 bg-danger/12 text-danger shadow-[0_0_18px_-12px_oklch(0.72_0.17_25_/_0.75)]",
  }[tone];
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-1 font-mono text-[11px] uppercase tracking-[0.16em] ${cls}`}>
      {score}
    </span>
  );
}
