import { createFileRoute, Link } from "@tanstack/react-router";
import { SiteHeader } from "@/components/silicore/SiteHeader";
import { Logo } from "@/components/silicore/Logo";
import { Reveal, RevealWords } from "@/components/silicore/Reveal";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Silicore — Hardware Design Intelligence" },
      {
        name: "description",
        content:
          "Silicore is engineering intelligence for hardware teams. Identify risks, understand design weaknesses, and improve performance before production.",
      },
      { property: "og:title", content: "Silicore — Hardware Design Intelligence" },
      {
        property: "og:description",
        content: "Deep engineering intelligence for PCB design and hardware teams.",
      },
    ],
  }),
  component: Landing,
});

function Landing() {
  return (
    <div id="top" className="relative min-h-screen overflow-hidden bg-background">
      {/* App-wide background atmosphere — subtle grid + layered glows */}
      <div className="bg-grid pointer-events-none absolute inset-0 opacity-30 [mask-image:radial-gradient(ellipse_70%_50%_at_50%_0%,#000_30%,transparent_85%)]" />
      <div className="bg-hero-glow pointer-events-none absolute inset-0" />

      <SiteHeader />
      <Hero />
      <System />
      <WhatItDoes />
      <Lifecycle />
      <CTA />
      <Footer />
    </div>
  );
}

/* ---------------------------------------------------------------- */
/* SHARED — pill button styles + section dot label                   */
/* ---------------------------------------------------------------- */

function PrimaryPill({
  children,
  to,
  href,
  className = "",
}: {
  children: React.ReactNode;
  to?: string;
  href?: string;
  className?: string;
}) {
  const cls =
    "inline-flex items-center justify-center rounded-full px-7 py-3 text-[15px] font-medium text-primary-foreground transition-transform hover:scale-[1.03] " +
    className;
  const style: React.CSSProperties = {
    background: "linear-gradient(180deg, oklch(0.92 0.1 215), oklch(0.78 0.13 255))",
    boxShadow:
      "0 0 40px -6px oklch(0.86 0.13 215 / 0.65), inset 0 1px 0 oklch(1 0 0 / 0.4)",
  };
  if (to) {
    return (
      <Link to={to} className={cls} style={style}>
        {children}
      </Link>
    );
  }
  return (
    <a href={href ?? "#"} className={cls} style={style}>
      {children}
    </a>
  );
}

function GhostPill({
  children,
  to,
  href,
}: {
  children: React.ReactNode;
  to?: string;
  href?: string;
}) {
  const cls =
    "inline-flex items-center justify-center rounded-full border border-white/10 bg-white/5 px-7 py-3 text-[15px] font-medium text-foreground transition-colors hover:bg-white/10 backdrop-blur-sm";
  if (to) {
    return (
      <Link to={to} className={cls}>
        {children}
      </Link>
    );
  }
  return (
    <a href={href ?? "#"} className={cls}>
      {children}
    </a>
  );
}

function SectionLabel({
  children,
  center,
}: {
  children: React.ReactNode;
  center?: boolean;
}) {
  return (
    <div
      className={`flex items-center gap-2.5 font-mono text-[11px] uppercase tracking-[0.32em] text-primary ${
        center ? "justify-center" : ""
      }`}
    >
      <span
        className="h-2 w-2 rounded-full bg-primary"
        style={{ boxShadow: "0 0 12px oklch(0.86 0.13 215 / 0.9)" }}
      />
      {children}
    </div>
  );
}

/* ---------------------------------------------------------------- */
/* HERO                                                              */
/* ---------------------------------------------------------------- */

function Hero() {
  return (
    <section className="relative">
      {/* Floating colored glows for depth */}
      <div
        className="pointer-events-none absolute -left-32 top-32 h-[520px] w-[520px] rounded-full opacity-50 blur-3xl animate-drift"
        style={{
          background:
            "radial-gradient(circle, oklch(0.88 0.15 175 / 0.45), transparent 65%)",
        }}
      />
      <div
        className="pointer-events-none absolute right-[-160px] top-20 h-[560px] w-[560px] rounded-full opacity-50 blur-3xl animate-drift"
        style={{
          background:
            "radial-gradient(circle, oklch(0.78 0.13 255 / 0.5), transparent 65%)",
          animationDelay: "1.5s",
        }}
      />

      {/* Orbital conic halos behind the headline */}
      <div className="pointer-events-none absolute left-1/2 top-[42%] -translate-x-1/2 -translate-y-1/2">
        <div
          className="h-[780px] w-[780px] rounded-full opacity-[0.35] blur-2xl animate-spin-slow"
          style={{
            background:
              "conic-gradient(from 90deg, transparent 0deg, oklch(0.86 0.13 215 / 0.6) 60deg, transparent 140deg, oklch(0.78 0.13 255 / 0.55) 220deg, transparent 300deg)",
            mask: "radial-gradient(circle, black 30%, transparent 72%)",
            WebkitMask: "radial-gradient(circle, black 30%, transparent 72%)",
          }}
        />
      </div>
      {/* PCB trace pattern behind the headline */}
      <div className="pointer-events-none absolute left-1/2 top-[42%] flex -translate-x-1/2 -translate-y-1/2 items-center justify-center">
        <svg
          viewBox="0 0 800 800"
          className="h-[640px] w-[640px] opacity-[0.22]"
          fill="none"
          stroke="oklch(0.86 0.13 215)"
          strokeWidth="1.1"
          style={{
            mask: "radial-gradient(circle, black 35%, transparent 78%)",
            WebkitMask: "radial-gradient(circle, black 35%, transparent 78%)",
          }}
        >
          <defs>
            <radialGradient id="pad-grad" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="oklch(0.86 0.13 215)" stopOpacity="1" />
              <stop offset="100%" stopColor="oklch(0.86 0.13 215)" stopOpacity="0" />
            </radialGradient>
          </defs>
          {(() => {
            const traces = [
              "M40 200 L260 200 L300 240 L520 240 L560 200 L760 200",
              "M40 600 L220 600 L260 560 L520 560 L560 600 L760 600",
              "M120 40 L120 240 L160 280 L160 520 L120 560 L120 760",
              "M680 40 L680 220 L640 260 L640 540 L680 580 L680 760",
              "M260 400 L340 400 L380 360 L420 360 L460 400 L540 400",
              "M400 120 L400 260 L360 300 L360 360",
              "M400 680 L400 540 L440 500 L440 440",
            ];
            const accents = [
              "M200 320 L320 320 L380 380",
              "M600 480 L480 480 L420 420",
            ];
            return (
              <>
                {/* base traces */}
                {traces.map((d, i) => <path key={`t-${i}`} d={d} />)}
                {accents.map((d, i) => <path key={`a-${i}`} d={d} strokeOpacity={0.6} />)}
                {/* signal sweeps — bright pulse traveling along each trace */}
                {[...traces, ...accents].map((d, i) => (
                  <path
                    key={`sig-${i}`}
                    d={d}
                    stroke="oklch(0.92 0.1 215)"
                    strokeWidth="1.6"
                    strokeLinecap="round"
                    strokeDasharray="36 1200"
                    style={{ filter: "drop-shadow(0 0 6px oklch(0.86 0.13 215 / 0.9))" }}
                  >
                    <animate
                      attributeName="stroke-dashoffset"
                      from="1236"
                      to="0"
                      dur={`${10 + (i % 4) * 2.5}s`}
                      begin={`${(i * 0.9) % 6}s`}
                      repeatCount="indefinite"
                    />
                  </path>
                ))}
              </>
            );
          })()}
          {/* vias / pads */}
          {[
            [120, 200], [260, 200], [560, 200], [680, 220],
            [120, 560], [260, 560], [560, 560], [680, 580],
            [400, 120], [400, 680], [400, 400], [340, 400], [460, 400],
            [200, 320], [600, 480],
          ].map(([cx, cy], i) => (
            <g key={i}>
              <circle cx={cx} cy={cy} r="3.5" fill="oklch(0.86 0.13 215)" />
              <circle cx={cx} cy={cy} r="9" fill="url(#pad-grad)" opacity="0.7">
                <animate
                  attributeName="opacity"
                  values="0.25;0.85;0.25"
                  dur={`${4 + (i % 5) * 0.6}s`}
                  begin={`${(i * 0.4) % 3}s`}
                  repeatCount="indefinite"
                />
              </circle>
            </g>
          ))}
          {/* corner IC outline */}
          <rect x="320" y="340" width="160" height="120" rx="6" strokeOpacity="0.45" />
          {[0,1,2,3,4,5].map(i => (
            <line key={`tl-${i}`} x1={340 + i*22} y1="340" x2={340 + i*22} y2="328" strokeOpacity="0.45" />
          ))}
          {[0,1,2,3,4,5].map(i => (
            <line key={`bl-${i}`} x1={340 + i*22} y1="460" x2={340 + i*22} y2="472" strokeOpacity="0.45" />
          ))}
        </svg>
      </div>


      {/* Grain overlay */}
      <div className="bg-noise pointer-events-none absolute inset-0 opacity-[0.06] mix-blend-overlay" />

      <div className="relative mx-auto max-w-6xl px-6 pb-32 pt-24 text-center md:pt-32">
        {/* Eyebrow chip */}
        <Reveal>
          <div className="mx-auto inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3.5 py-1.5 backdrop-blur-md">
            <span
              className="h-1.5 w-1.5 rounded-full bg-primary"
              style={{ boxShadow: "0 0 10px oklch(0.86 0.13 215)" }}
            />
            <span className="font-mono text-[10.5px] uppercase tracking-[0.32em] text-primary/90">
              Silicore · Engineering Intelligence
            </span>
          </div>
        </Reveal>

        {/* Headline — Hardware Design above, Intelligence dominant */}
        <h1 className="mx-auto mt-12 max-w-6xl font-semibold tracking-[-0.035em]">
          <Reveal>
            <span className="block text-[40px] leading-[1.05] text-foreground sm:text-[56px] md:text-[72px] lg:text-[88px]">
              Hardware Design
            </span>
          </Reveal>
          <Reveal delay={200}>
            <span
              aria-label="Intelligence"
              className="animate-shimmer-text block bg-clip-text pb-[0.22em] text-[64px] leading-[1.1] text-transparent sm:text-[88px] md:text-[120px] lg:text-[160px]"
              style={{
                backgroundImage:
                  "linear-gradient(100deg, oklch(0.985 0.012 220) 0%, oklch(0.86 0.13 215) 30%, oklch(0.78 0.13 255) 55%, oklch(0.86 0.13 215) 75%, oklch(0.985 0.012 220) 100%)",
                filter:
                  "drop-shadow(0 0 60px oklch(0.86 0.13 215 / 0.55)) drop-shadow(0 0 140px oklch(0.78 0.13 255 / 0.35))",
              }}
            >
              Intelligence
            </span>
          </Reveal>
        </h1>

        <Reveal delay={550}>
          <p className="mx-auto mt-10 max-w-2xl text-base leading-relaxed text-muted-foreground md:text-lg">
            Silicore is deep engineering intelligence for PCB design — surfacing
            risk, exposing weakness, and sharpening performance long before the
            board ever ships to production.
          </p>
        </Reveal>

        <Reveal delay={750}>
          <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <PrimaryPill href="#cta">Request Demo</PrimaryPill>
            <GhostPill href="#what">Learn More</GhostPill>
          </div>
        </Reveal>

      </div>
    </section>
  );
}

/* ---------------------------------------------------------------- */
/* THE SYSTEM                                                        */
/* ---------------------------------------------------------------- */

function System() {
  const cards = [
    {
      title: "Silicore",
      desc:
        "The brand and company behind the system. Silicore represents a new category of hardware design intelligence built for teams designing real, high-stakes physical products.",
      glyph: "dot",
    },
    {
      title: "Silicore Nexus",
      desc:
        "The platform layer. Nexus is where the experience comes together into one coherent environment for hardware organizations, design review flow, and engineering coordination.",
      glyph: "grid",
    },
    {
      title: "Atlas Intelligence",
      desc:
        "The intelligence engine inside Nexus. Atlas interprets hardware context, organizes technical signal, and gives the platform a sharper understanding of what matters in design decisions.",
      glyph: "ring",
    },
  ] as const;

  return (
    <section id="system" className="relative py-24 md:py-36">
      <div className="mx-auto max-w-7xl px-6">
        <Reveal>
          <SectionLabel>The System</SectionLabel>
        </Reveal>
        <h2 className="mt-6 max-w-3xl text-4xl font-semibold leading-[1.05] tracking-[-0.02em] md:text-6xl lg:text-[68px]">
          <RevealWords text="Three names." stagger={70} />
          <br />
          <RevealWords text="One connected experience." stagger={55} startDelay={250} />
        </h2>

        <Reveal delay={400}>
          <p className="mt-8 max-w-2xl text-muted-foreground md:text-lg">
            Silicore is the company. Silicore Nexus is the platform. Atlas
            Intelligence is the reasoning layer inside it. The relationship is
            intentional — so the product feels deliberate before anyone ever
            reaches the dashboard.
          </p>
        </Reveal>

        <div className="mt-20 grid gap-12 md:grid-cols-3 md:gap-10">
          {cards.map((c, i) => (
            <Reveal key={c.title} delay={i * 150}>
              <SystemGlyph kind={c.glyph} />
              <h3 className="mt-7 text-[28px] font-semibold tracking-tight md:text-[32px]">
                {c.title}
              </h3>
              <p className="mt-4 max-w-sm text-[15px] leading-relaxed text-muted-foreground">
                {c.desc}
              </p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

function SystemGlyph({ kind }: { kind: "dot" | "grid" | "ring" }) {
  const glow =
    "0 0 40px -4px oklch(0.86 0.13 215 / 0.55), inset 0 1px 0 oklch(1 0 0 / 0.06)";
  return (
    <div
      className="relative flex h-12 w-12 items-center justify-center rounded-xl border border-white/10"
      style={{
        background:
          "linear-gradient(160deg, oklch(0.22 0.04 235), oklch(0.13 0.028 235))",
        boxShadow: glow,
      }}
    >
      {kind === "dot" && (
        <span
          className="h-3 w-3 rounded-full"
          style={{
            background: "oklch(0.86 0.13 215)",
            boxShadow: "0 0 14px oklch(0.86 0.13 215 / 0.95)",
          }}
        />
      )}
      {kind === "grid" && (
        <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="oklch(0.86 0.13 215)" strokeWidth="1.4">
          <rect x="4" y="4" width="16" height="16" rx="2" />
          <path d="M4 12h16M12 4v16" opacity="0.6" />
        </svg>
      )}
      {kind === "ring" && (
        <div className="relative">
          <span
            className="block h-5 w-5 rounded-full border-2"
            style={{ borderColor: "oklch(0.86 0.13 215)" }}
          />
          <span
            className="absolute left-1/2 top-1/2 h-1.5 w-1.5 -translate-x-1/2 -translate-y-1/2 rounded-full"
            style={{
              background: "oklch(0.86 0.13 215)",
              boxShadow: "0 0 10px oklch(0.86 0.13 215)",
            }}
          />
        </div>
      )}
    </div>
  );
}

/* ---------------------------------------------------------------- */
/* WHAT IT DOES                                                      */
/* ---------------------------------------------------------------- */

function WhatItDoes() {
  const items = [
    {
      title: "Clarity",
      sub: "Turn technical complexity into a readable operating surface.",
      desc:
        "Silicore Nexus is designed to transform dense engineering context into something leaders, reviewers, and design teams can actually navigate.",
    },
    {
      title: "Continuity",
      sub: "Connect hardware decisions into one platform narrative.",
      desc:
        "Atlas Intelligence gives Nexus continuity across design thinking, review context, and the broader system around the board.",
    },
    {
      title: "Confidence",
      sub: "Create a stronger sense of trust around hardware execution.",
      desc:
        "The result is a platform experience that feels premium, deliberate, and engineered for teams building advanced hardware products.",
    },
  ];
  return (
    <section id="what" className="relative border-t border-white/5 py-24 md:py-36">
      <div className="mx-auto max-w-7xl px-6">
        <div className="grid gap-16 lg:grid-cols-[1fr_1.25fr] lg:gap-24">
          <div>
            <Reveal>
              <SectionLabel>What it does</SectionLabel>
            </Reveal>
            <h2 className="mt-6 text-4xl font-semibold leading-[1.05] tracking-[-0.02em] md:text-6xl lg:text-[64px]">
              <RevealWords text="Built to make hardware systems feel legible." stagger={55} />
            </h2>
            <Reveal delay={500}>
              <p className="mt-8 max-w-md text-muted-foreground md:text-lg">
                This is not a dashboard-first homepage. It is a visual
                introduction to a company and platform that help hardware teams
                see their work more clearly, move with more confidence, and
                operate with stronger technical continuity.
              </p>
            </Reveal>
          </div>

          <div className="divide-y divide-white/5">
            {items.map((it, i) => (
              <Reveal key={it.title} delay={i * 150}>
                <div className="grid grid-cols-[120px_1fr] gap-8 py-8 first:pt-0 last:pb-0">
                  <div className="text-lg font-medium text-foreground">{it.title}</div>
                  <div>
                    <p className="text-lg font-medium text-foreground">{it.sub}</p>
                    <p className="mt-3 text-[15px] leading-relaxed text-muted-foreground">
                      {it.desc}
                    </p>
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

/* ---------------------------------------------------------------- */
/* LIFECYCLE                                                         */
/* ---------------------------------------------------------------- */

function Lifecycle() {
  const steps = [
    { n: "01", title: "Ingest", desc: "Upload your design files and structure the PCB data." },
    { n: "02", title: "Analyze", desc: "Run checks across electrical, thermal, and layout." },
    { n: "03", title: "Score & Prioritize", desc: "Highlight the most important risks and focus areas." },
    { n: "04", title: "Recommend", desc: "Provide clear, actionable suggestions to fix issues." },
    { n: "05", title: "Project Improvement", desc: "Track changes across revisions and continuously improve your designs." },
  ];
  return (
    <section className="relative border-t border-white/5 py-24 md:py-36">
      <div className="mx-auto max-w-7xl px-6">
        <Reveal>
          <SectionLabel>How Silicore works</SectionLabel>
        </Reveal>
        <h2 className="mt-6 max-w-4xl text-4xl font-semibold leading-[1.05] tracking-[-0.02em] md:text-6xl lg:text-[64px]">
          <RevealWords text="Intelligence across the Silicore lifecycle." stagger={55} />
        </h2>
        <Reveal delay={500}>
          <p className="mt-8 max-w-2xl text-muted-foreground md:text-lg">
            Silicore Nexus moves from raw design input to actionable engineering
            guidance through a connected lifecycle built for hardware teams.
          </p>
        </Reveal>

        <div className="relative mt-20">
          <div className="absolute left-0 right-0 top-7 hidden h-px bg-gradient-to-r from-transparent via-primary/40 to-transparent lg:block" />
          <ol className="grid gap-12 lg:grid-cols-5 lg:gap-6">
            {steps.map((s, i) => (
              <Reveal as="li" key={s.n} delay={i * 130} className="relative">
                <span
                  className="relative z-10 flex h-14 w-14 items-center justify-center rounded-full border border-white/10 font-mono text-xs text-primary"
                  style={{
                    background:
                      "linear-gradient(160deg, oklch(0.22 0.04 235), oklch(0.13 0.028 235))",
                    boxShadow:
                      "0 0 24px -4px oklch(0.86 0.13 215 / 0.55), inset 0 1px 0 oklch(1 0 0 / 0.06)",
                  }}
                >
                  {s.n}
                </span>
                <h3 className="mt-6 text-xl font-semibold tracking-tight">{s.title}</h3>
                <p className="mt-2 max-w-[18rem] text-[15px] leading-relaxed text-muted-foreground">
                  {s.desc}
                </p>
              </Reveal>
            ))}
          </ol>
        </div>
      </div>
    </section>
  );
}

/* ---------------------------------------------------------------- */
/* CTA                                                               */
/* ---------------------------------------------------------------- */

function CTA() {
  return (
    <section id="cta" className="relative border-t border-white/5 py-24 md:py-36">
      {/* CTA glow */}
      <div
        className="pointer-events-none absolute left-1/2 top-1/2 h-[500px] w-[700px] -translate-x-1/2 -translate-y-1/2 rounded-full opacity-50 blur-3xl"
        style={{
          background:
            "radial-gradient(circle, oklch(0.78 0.13 255 / 0.45), transparent 70%)",
        }}
      />
      <div className="relative mx-auto max-w-7xl px-6">
        <div className="grid items-center gap-12 lg:grid-cols-[1.4fr_1fr]">
          <h2 className="text-4xl font-semibold leading-[1.02] tracking-[-0.02em] md:text-6xl lg:text-[72px]">
            <Reveal>
              <span className="block text-foreground">Accelerate your</span>
            </Reveal>
            <Reveal delay={200}>
              <span
                className="mt-2 block bg-clip-text text-transparent"
                style={{
                  backgroundImage:
                    "linear-gradient(180deg, oklch(0.92 0.1 215), oklch(0.7 0.16 260))",
                  filter: "drop-shadow(0 0 50px oklch(0.78 0.13 255 / 0.45))",
                }}
              >
                Silicore journey?
              </span>
            </Reveal>
          </h2>

          <Reveal delay={350} className="flex flex-col items-start gap-5 lg:items-end">
            <p className="max-w-md text-muted-foreground md:text-lg lg:text-right">
              Analyze your designs with Silicore. Build with intelligence.
            </p>
            <div className="flex flex-wrap gap-3">
              <PrimaryPill to="/dashboard">Open Nexus</PrimaryPill>
              <GhostPill to="/login">Sign In</GhostPill>
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  );
}

/* ---------------------------------------------------------------- */
/* FOOTER                                                            */
/* ---------------------------------------------------------------- */

function Footer() {
  const cols = [
    { title: "Platform", items: ["Overview", "Features", "Lifecycle"] },
    { title: "Resources", items: ["Blog", "Webinars"] },
    { title: "Company", items: ["About Us", "Contact Us"] },
  ];
  return (
    <footer className="relative border-t border-white/5 py-20">
      <div className="mx-auto grid max-w-7xl gap-12 px-6 md:grid-cols-[1.4fr_1fr_1fr_1fr]">
        <div>
          <Logo />
          <p className="mt-6 max-w-xs text-[15px] leading-relaxed text-muted-foreground">
            Deep engineering intelligence for PCB design and hardware teams.
          </p>
          <div className="mt-7 flex items-center gap-3">
            <SocialDot label="in" />
            <SocialDot label="X" />
          </div>
        </div>
        {cols.map((c) => (
          <div key={c.title}>
            <div className="font-mono text-[10px] uppercase tracking-[0.28em] text-muted-foreground">
              {c.title}
            </div>
            <ul className="mt-5 space-y-3.5 text-[15px]">
              {c.items.map((i) => (
                <li key={i}>
                  <a
                    href="#"
                    className="text-foreground/85 transition-colors hover:text-primary"
                  >
                    {i}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="mx-auto mt-16 flex max-w-7xl items-center justify-between border-t border-white/5 px-6 pt-6 font-mono text-[11px] uppercase tracking-[0.22em] text-muted-foreground">
        <span>© 2026 Silicore</span>
        <span>Engineering Intelligence</span>
      </div>
    </footer>
  );
}

function SocialDot({ label }: { label: string }) {
  return (
    <a
      href="#"
      className="flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 bg-white/5 font-mono text-[11px] uppercase text-foreground/80 transition-colors hover:border-primary hover:text-primary"
    >
      {label}
    </a>
  );
}
