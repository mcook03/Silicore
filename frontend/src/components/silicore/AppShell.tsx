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
  Command,
  ArrowUpRight,
  ChevronDown,
  Wrench,
  PanelLeftOpen,
  Orbit,
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
      <aside className="shell-chassis sticky top-0 hidden h-screen w-[19rem] shrink-0 flex-col px-4 pb-4 pt-5 md:flex">
        <div className="nav-pillar flex items-center gap-3 rounded-[28px] px-4 py-4">
          <Link to="/" className="flex min-w-0 items-center gap-3">
            <Logo />
          </Link>
          <div className="min-w-0">
            <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground">Silicore</div>
            <div className="truncate text-sm text-foreground">{subtitle}</div>
          </div>
        </div>
        <div className="mt-4 px-1">
          <div className="signal-rail">
            <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground">Product surfaces</div>
            <div className="mt-2 text-sm leading-6 text-muted-foreground">
              Analysis-first navigation for live engineering work.
            </div>
          </div>
        </div>
        <nav className="mt-5 flex-1 space-y-2">
          {coreNav.map(({ to, label, icon: Icon }) => {
            const active = location.pathname === to || (to !== "/dashboard" && location.pathname.startsWith(to));
            return (
              <Link
                key={to}
                to={to}
                data-active={active ? "true" : "false"}
                className={`nav-chip flex items-center gap-3 px-4 py-3 text-sm ${active ? "text-foreground" : "text-sidebar-foreground"}`}
              >
                <span className={`flex h-10 w-10 items-center justify-center rounded-2xl border ${active ? "border-primary/18 bg-primary/10 text-primary" : "border-white/6 bg-white/3 text-muted-foreground"}`}>
                  <Icon className="h-4 w-4" />
                </span>
                <span className="min-w-0">
                  <span className="block truncate text-sm">{label}</span>
                  <span className="block font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                    {to === "/dashboard" ? "overview" : to.slice(1).replace("-", " ")}
                  </span>
                </span>
                {active ? <Orbit className="ml-auto h-3.5 w-3.5 text-primary" /> : null}
              </Link>
            );
          })}
          {canAccessInternalTools ? (
            <div className="pt-4">
              <div className="px-1 pb-2 font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Internal</div>
              <button
                type="button"
                onClick={() => setInternalToolsOpen((current) => !current)}
                data-active={internalRouteActive ? "true" : "false"}
                className={`nav-chip flex w-full items-center gap-3 px-4 py-3 text-left text-sm ${internalRouteActive ? "text-foreground" : "text-sidebar-foreground"}`}
              >
                <span className={`flex h-10 w-10 items-center justify-center rounded-2xl border ${internalRouteActive ? "border-primary/18 bg-primary/10 text-primary" : "border-white/6 bg-white/3 text-muted-foreground"}`}>
                  <Wrench className="h-4 w-4" />
                </span>
                <span className="font-medium">Internal tools</span>
                <span className="ml-auto inline-flex items-center gap-2">
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
                        data-active={active ? "true" : "false"}
                        className={`nav-chip flex items-center gap-3 px-4 py-3 text-sm ${active ? "text-foreground" : "text-muted-foreground"}`}
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
        <div className="nav-pillar mt-4 flex items-center gap-3 rounded-[28px] p-4">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-primary/14 bg-primary/10 font-mono text-xs text-primary">{initials}</div>
          <div className="min-w-0">
            <div className="truncate text-sm">{user?.name || user?.email || "Silicore user"}</div>
            <div className="truncate font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">{subtitle}</div>
          </div>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="command-deck sticky top-0 z-30 px-4 sm:px-6">
          <div className="flex min-h-[5.2rem] items-center gap-3 py-3">
            <button
              type="button"
              className="command-strip flex h-11 w-11 items-center justify-center rounded-2xl text-muted-foreground md:hidden"
              onClick={() => setMobileNavOpen((current) => !current)}
              aria-label="Toggle navigation"
            >
              <PanelLeftOpen className="h-4 w-4" />
            </button>
            <div className="min-w-0">
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
                {activeNav?.label || "Silicore workspace"}
              </div>
              <h1 className="truncate text-lg font-medium tracking-tight text-foreground sm:text-[1.2rem]">{title}</h1>
            </div>
            <div className="ml-auto flex items-center gap-2">
              <div className="command-strip hidden items-center gap-2 rounded-full px-3 py-2 text-xs text-primary lg:flex">
                <Command className="h-3.5 w-3.5" />
                Engineering-grade analysis workspace
              </div>
              <div className="command-strip hidden items-center gap-2 rounded-full px-3 py-2 text-xs text-muted-foreground xl:flex">
                <span className="flex h-2 w-2 rounded-full bg-success shadow-[0_0_14px_rgba(96,240,198,0.7)]" />
                <span>Session live</span>
              </div>
              <div className="command-strip hidden items-center gap-2 rounded-2xl px-3 py-2 text-sm text-muted-foreground sm:flex">
                <Search className="h-3.5 w-3.5" />
                <span>Search boards, runs, workspaces</span>
                <kbd className="ml-3 rounded-full border border-border/70 px-2 py-0.5 font-mono text-[10px]">⌘K</kbd>
              </div>
              <button className="command-strip flex h-11 w-11 items-center justify-center rounded-2xl text-muted-foreground hover:text-foreground">
                <Bell className="h-4 w-4" />
              </button>
            </div>
          </div>
          {mobileNavOpen ? (
            <div className="pb-4 md:hidden">
              <div className="editorial-surface rounded-[30px] p-3">
                <div className="grid gap-2 sm:grid-cols-2">
                  {coreNav.map(({ to, label, icon: Icon }) => {
                    const active = location.pathname === to || (to !== "/dashboard" && location.pathname.startsWith(to));
                    return (
                      <Link
                        key={to}
                        to={to}
                        data-active={active ? "true" : "false"}
                        className={`nav-chip flex items-center gap-3 px-4 py-3 text-sm ${active ? "text-foreground" : "text-muted-foreground"}`}
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
                            data-active={active ? "true" : "false"}
                            className={`nav-chip flex items-center gap-3 px-4 py-3 text-sm ${active ? "text-foreground" : "text-muted-foreground"}`}
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
          <div className="mx-auto w-full max-w-[1660px] space-y-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
