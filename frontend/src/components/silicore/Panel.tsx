import type { ReactNode } from "react";

export function Panel({
  title,
  children,
  action,
}: {
  title: string;
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-border bg-surface p-6">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-medium">{title}</h3>
        {action}
      </div>
      {children}
    </div>
  );
}

export function ScorePill({ score }: { score: number }) {
  const tone = score >= 80 ? "success" : score >= 65 ? "warning" : "danger";
  const cls = {
    success: "text-success bg-success/10",
    warning: "text-warning bg-warning/10",
    danger: "text-danger bg-danger/10",
  }[tone];
  return (
    <span className={`inline-flex items-center rounded-md px-2 py-0.5 font-mono text-xs ${cls}`}>
      {score}
    </span>
  );
}
