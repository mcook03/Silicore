import type { ReactNode } from "react";

type HeroMetric = {
  label: string;
  value: string;
  copy?: string;
};

export function PageHero({
  eyebrow,
  title,
  description,
  metrics = [],
  actions,
}: {
  eyebrow: ReactNode;
  title: ReactNode;
  description: ReactNode;
  metrics?: HeroMetric[];
  actions?: ReactNode;
}) {
  return (
    <section data-reveal className="premium-hero rounded-[32px] px-6 py-7 sm:px-8 sm:py-8">
      <div className="relative grid gap-6 xl:grid-cols-[minmax(0,1.25fr)_minmax(0,0.75fr)]">
        <div className="min-w-0">
          <div className="section-eyebrow">{eyebrow}</div>
          <h2 className="mt-5 max-w-3xl text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            {title}
          </h2>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">
            {description}
          </p>
          {actions ? <div className="mt-5 flex flex-wrap items-center gap-3">{actions}</div> : null}
        </div>

        {!!metrics.length && (
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
            {metrics.map((metric) => (
              <div key={metric.label} className="metric-tile">
                <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
                  {metric.label}
                </div>
                <div className="mt-2 text-xl font-semibold text-foreground">{metric.value}</div>
                {metric.copy ? <div className="mt-1 text-xs text-muted-foreground">{metric.copy}</div> : null}
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
