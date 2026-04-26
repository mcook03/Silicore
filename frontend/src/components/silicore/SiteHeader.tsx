import { Link } from "@tanstack/react-router";
import { Logo } from "./Logo";

export function SiteHeader() {
  const nav = [
    { label: "Silicore", href: "#top" },
    { label: "Nexus", href: "#system" },
    { label: "Atlas", href: "#system" },
    { label: "Experience", href: "#what" },
  ];
  return (
    <header className="sticky top-4 z-50 px-4">
      <div
        className="mx-auto flex h-16 max-w-7xl items-center justify-between rounded-2xl border border-white/10 px-4 backdrop-blur-xl md:px-5"
        style={{
          background:
            "linear-gradient(180deg, oklch(0.18 0.03 235 / 0.85), oklch(0.13 0.028 235 / 0.7))",
          boxShadow:
            "inset 0 1px 0 oklch(1 0 0 / 0.05), 0 20px 60px -20px oklch(0.04 0.02 235 / 0.8)",
        }}
      >
        <Link to="/" className="flex items-center">
          <Logo />
        </Link>

        <nav className="hidden items-center gap-1 rounded-full border border-white/5 bg-background/40 p-1 md:flex">
          {nav.map((n, i) => (
            <a
              key={n.label}
              href={n.href}
              className={`rounded-full px-4 py-1.5 text-sm transition-colors ${
                i === 0
                  ? "bg-surface text-foreground shadow-[inset_0_1px_0_oklch(1_0_0_/_0.06)]"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {n.label}
            </a>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <Link
            to="/dashboard"
            className="hidden rounded-full px-4 py-2 text-sm text-foreground/90 transition-colors hover:bg-white/5 md:inline-flex"
          >
            Sign In
          </Link>
          <Link
            to="/dashboard"
            className="inline-flex items-center justify-center rounded-full px-5 py-2 text-sm font-medium text-primary-foreground transition-transform hover:scale-[1.02]"
            style={{
              background:
                "linear-gradient(180deg, oklch(0.92 0.1 215), oklch(0.78 0.13 255))",
              boxShadow:
                "0 0 30px -6px oklch(0.86 0.13 215 / 0.6), inset 0 1px 0 oklch(1 0 0 / 0.4)",
            }}
          >
            Open Nexus
          </Link>
        </div>
      </div>
    </header>
  );
}
