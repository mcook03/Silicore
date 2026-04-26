import { Link, useLocation } from "@tanstack/react-router";
import { Logo } from "./Logo";
import {
  LayoutDashboard,
  CircuitBoard,
  GitCompareArrows,
  FolderKanban,
  History,
  Settings,
  Search,
  Bell,
  Sparkles,
  Network,
  ListChecks,
  ShieldCheck,
  Activity,
  Menu,
  Command,
  ArrowUpRight,
  ChevronDown,
  Wrench,
} from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import { useApiData } from "@/lib/api";

const coreNav = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/analyze", label: "Board analysis", icon: CircuitBoard },
  { to: "/compare", label: "Compare", icon: GitCompareArrows },
  { to: "/projects", label: "Projects", icon: FolderKanban },
  { to: "/atlas", label: "Atlas AI", icon: Sparkles },
  { to: "/history", label: "History", icon: History },
  { to: "/settings", label: "Settings", icon: Settings },
] as const;

const internalToolsNav = [
  { to: "/nexus-ops", label: "Nexus Ops", icon: Network },
  { to: "/jobs", label: "Jobs", icon: ListChecks },
  { to: "/admin/audit", label: "Audit log", icon: ShieldCheck },
  { to: "/health", label: "Health", icon: Activity },
] as const;

export function AppShell({ children, title }: { children: ReactNode; title?: string }) {
  const location = useLocation();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [internalToolsOpen, setInternalToolsOpen] = useState(false);
  const { data } = useApiData<{ user?: { name?: string; email?: string; roles?: string[]; organization_names?: string[] } }>("/api/frontend/session");
  const user = data?.user;
  const canAccessInternalTools = Boolean(user?.roles?.some((role) => role === "lead" || role === "admin"));
  const initials = ((user?.name || user?.email || "SC").match(/\b\w/g) || ["S", "C"]).slice(0, 2).join("").toUpperCase();
  const subtitle = user?.organization_names?.[0] || user?.roles?.join(" · ") || "Silicore workspace";
  const allNav = [...coreNav, ...internalToolsNav];
  const activeNav = allNav.find((item) => location.pathname === item.to || (item.to !== "/dashboard" && location.pathname.startsWith(item.to)));
  const internalRouteActive = internalToolsNav.some((item) => location.pathname === item.to || location.pathname.startsWith(item.to));

  useEffect(() => {
    setMobileNavOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (internalRouteActive) {
      setInternalToolsOpen(true);
    }
  }, [internalRouteActive]);

  useEffect(() => {
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const seen = new WeakSet<HTMLElement>();
    const elements = () => Array.from(document.querySelectorAll<HTMLElement>("[data-reveal]"));

    if (reducedMotion) {
      elements().forEach((element) => {
        element.dataset.reveal = "in";
      });
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.setAttribute("data-reveal", "in");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" },
    );

    const registerElements = () => {
      elements().forEach((element, index) => {
        if (seen.has(element)) {
          return;
        }
        seen.add(element);
        element.style.setProperty("--reveal-delay", `${Math.min(index * 40, 220)}ms`);
        observer.observe(element);
      });
    };

    registerElements();

    const mutationObserver = new MutationObserver(() => {
      registerElements();
    });

    mutationObserver.observe(document.body, { childList: true, subtree: true });

    return () => {
      observer.disconnect();
      mutationObserver.disconnect();
    };
  }, [location.pathname]);

  return (
    <div className="app-shell-bg flex min-h-screen bg-background">
      <aside className="sticky top-0 hidden h-screen w-72 shrink-0 flex-col border-r border-sidebar-border/70 bg-[linear-gradient(180deg,rgba(4,10,18,0.98),rgba(6,12,20,0.94))] md:flex">
        <div className="glow-divider flex h-20 items-center px-6">
          <Link to="/"><Logo /></Link>
        </div>
        <div className="px-4 pt-4">
          <div className="premium-subtle rounded-2xl px-4 py-3">
            <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground">Workspace</div>
            <div className="mt-2 text-sm font-medium text-foreground">{subtitle}</div>
            <div className="mt-1 text-xs text-muted-foreground">Authenticated product surface</div>
          </div>
        </div>
        <nav className="flex-1 space-y-1 p-4">
          {coreNav.map(({ to, label, icon: Icon }) => {
            const active = location.pathname === to || (to !== "/dashboard" && location.pathname.startsWith(to));
            return (
              <Link
                key={to}
                to={to}
                className={`interactive-lift flex items-center gap-3 rounded-2xl px-4 py-3 text-sm transition-colors ${
                  active
                    ? "border border-primary/20 bg-[linear-gradient(90deg,rgba(86,211,240,0.14),rgba(125,178,255,0.08))] text-foreground shadow-[0_14px_30px_-22px_rgba(86,211,240,0.75)]"
                    : "text-sidebar-foreground hover:bg-sidebar-accent/60 hover:text-foreground"
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{label}</span>
                {active && <span className="ml-auto h-2 w-2 rounded-full bg-primary shadow-[0_0_14px_rgba(86,211,240,0.85)]" />}
              </Link>
            );
          })}
          {canAccessInternalTools ? (
            <div className="pt-4">
              <button
                type="button"
                onClick={() => setInternalToolsOpen((current) => !current)}
                className={`interactive-lift flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left text-sm transition-colors ${
                  internalRouteActive
                    ? "border border-primary/20 bg-[linear-gradient(90deg,rgba(86,211,240,0.12),rgba(125,178,255,0.06))] text-foreground"
                    : "text-sidebar-foreground hover:bg-sidebar-accent/60 hover:text-foreground"
                }`}
              >
                <Wrench className="h-4 w-4" />
                <span className="font-medium">Internal tools</span>
                <span className="ml-auto inline-flex items-center gap-2">
                  <span className="rounded-full border border-border/70 px-2 py-0.5 font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
                    Hidden
                  </span>
                  <ChevronDown className={`h-4 w-4 transition-transform ${internalToolsOpen ? "rotate-180" : ""}`} />
                </span>
              </button>
              {internalToolsOpen ? (
                <div className="mt-2 space-y-1 pl-3">
                  {internalToolsNav.map(({ to, label, icon: Icon }) => {
                    const active = location.pathname === to || location.pathname.startsWith(to);
                    return (
                      <Link
                        key={to}
                        to={to}
                        className={`flex items-center gap-3 rounded-2xl px-4 py-3 text-sm transition-colors ${
                          active
                            ? "bg-primary/10 text-foreground shadow-[0_14px_30px_-22px_rgba(86,211,240,0.75)]"
                            : "text-muted-foreground hover:bg-sidebar-accent/45 hover:text-foreground"
                        }`}
                      >
                        <Icon className="h-4 w-4" />
                        <span>{label}</span>
                        {active ? <span className="ml-auto h-1.5 w-1.5 rounded-full bg-primary" /> : null}
                      </Link>
                    );
                  })}
                </div>
              ) : null}
            </div>
          ) : null}
        </nav>
        <div className="border-t border-sidebar-border/70 p-4">
          <div className="premium-subtle flex items-center gap-3 rounded-2xl p-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-primary/15 font-mono text-xs text-primary">{initials}</div>
            <div className="min-w-0">
              <div className="truncate text-sm">{user?.name || user?.email || "Silicore user"}</div>
              <div className="truncate text-xs text-muted-foreground">{subtitle}</div>
            </div>
          </div>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 border-b border-border/60 bg-background/78 px-4 backdrop-blur-xl sm:px-6">
          <div className="flex h-18 min-h-[4.5rem] items-center gap-3">
            <button
              type="button"
              className="premium-subtle flex h-10 w-10 items-center justify-center rounded-2xl text-muted-foreground md:hidden"
              onClick={() => setMobileNavOpen((current) => !current)}
              aria-label="Toggle navigation"
            >
              <Menu className="h-4 w-4" />
            </button>
            <div className="min-w-0">
              <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
                {activeNav?.label || "Silicore workspace"}
              </div>
              <h1 className="truncate text-[15px] font-medium tracking-tight sm:text-lg">{title}</h1>
            </div>
            <div className="ml-auto flex items-center gap-2">
              <div className="hidden items-center gap-2 rounded-full border border-primary/18 bg-primary/8 px-3 py-1.5 text-xs text-primary lg:flex">
                <Command className="h-3.5 w-3.5" />
                Live analysis surface
              </div>
              <div className="hidden items-center gap-2 rounded-2xl border border-border bg-surface/80 px-3 py-2 text-sm text-muted-foreground xl:flex">
                <span className="flex h-2 w-2 rounded-full bg-success shadow-[0_0_14px_rgba(96,240,198,0.7)]" />
                <span>Workspace ready</span>
              </div>
              <div className="hidden items-center gap-2 rounded-2xl border border-border bg-surface/78 px-3 py-2 text-sm text-muted-foreground sm:flex">
                <Search className="h-3.5 w-3.5" />
                <span>Search boards, projects…</span>
                <kbd className="ml-4 rounded-full border border-border px-2 py-0.5 font-mono text-[10px]">⌘K</kbd>
              </div>
              <button className="premium-subtle flex h-10 w-10 items-center justify-center rounded-2xl text-muted-foreground hover:text-foreground">
                <Bell className="h-4 w-4" />
              </button>
            </div>
          </div>
          {mobileNavOpen ? (
            <div className="pb-4 md:hidden">
              <div className="premium-panel rounded-[26px] p-3">
                <div className="grid gap-2 sm:grid-cols-2">
                  {coreNav.map(({ to, label, icon: Icon }) => {
                    const active = location.pathname === to || (to !== "/dashboard" && location.pathname.startsWith(to));
                    return (
                      <Link
                        key={to}
                        to={to}
                        className={`flex items-center gap-3 rounded-2xl px-4 py-3 text-sm ${
                          active
                            ? "border border-primary/20 bg-primary/10 text-foreground"
                            : "border border-transparent bg-background/35 text-muted-foreground"
                        }`}
                      >
                        <Icon className="h-4 w-4" />
                        <span>{label}</span>
                        <ArrowUpRight className="ml-auto h-3.5 w-3.5" />
                      </Link>
                    );
                  })}
                </div>
                {canAccessInternalTools ? (
                  <div className="mt-3 border-t border-border/60 pt-3">
                    <div className="mb-2 flex items-center gap-2 px-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                      <Wrench className="h-3.5 w-3.5" />
                      Internal tools
                    </div>
                    <div className="grid gap-2 sm:grid-cols-2">
                      {internalToolsNav.map(({ to, label, icon: Icon }) => {
                        const active = location.pathname === to || location.pathname.startsWith(to);
                        return (
                          <Link
                            key={to}
                            to={to}
                            className={`flex items-center gap-3 rounded-2xl px-4 py-3 text-sm ${
                              active
                                ? "border border-primary/20 bg-primary/10 text-foreground"
                                : "border border-transparent bg-background/35 text-muted-foreground"
                            }`}
                          >
                            <Icon className="h-4 w-4" />
                            <span>{label}</span>
                            <ArrowUpRight className="ml-auto h-3.5 w-3.5" />
                          </Link>
                        );
                      })}
                    </div>
                  </div>
                ) : null}
              </div>
            </div>
          ) : null}
        </header>
        <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
          <div className="mx-auto w-full max-w-[1600px] space-y-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
