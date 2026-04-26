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
} from "lucide-react";
import type { ReactNode } from "react";

const nav = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/analyze", label: "Board analysis", icon: CircuitBoard },
  { to: "/compare", label: "Compare", icon: GitCompareArrows },
  { to: "/projects", label: "Projects", icon: FolderKanban },
  { to: "/atlas", label: "Atlas AI", icon: Sparkles },
  { to: "/nexus-ops", label: "Nexus Ops", icon: Network },
  { to: "/jobs", label: "Jobs", icon: ListChecks },
  { to: "/history", label: "History", icon: History },
  { to: "/admin/audit", label: "Audit log", icon: ShieldCheck },
  { to: "/health", label: "Health", icon: Activity },
  { to: "/settings", label: "Settings", icon: Settings },
] as const;

export function AppShell({ children, title }: { children: ReactNode; title?: string }) {
  const location = useLocation();
  return (
    <div className="flex min-h-screen bg-background">
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col border-r border-sidebar-border bg-sidebar md:flex">
        <div className="flex h-16 items-center border-b border-sidebar-border px-5">
          <Link to="/"><Logo /></Link>
        </div>
        <nav className="flex-1 space-y-0.5 p-3">
          {nav.map(({ to, label, icon: Icon }) => {
            const active = location.pathname === to || (to !== "/dashboard" && location.pathname.startsWith(to));
            return (
              <Link
                key={to}
                to={to}
                className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors ${
                  active
                    ? "bg-sidebar-accent text-foreground"
                    : "text-sidebar-foreground hover:bg-sidebar-accent/60 hover:text-foreground"
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{label}</span>
                {active && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-primary" />}
              </Link>
            );
          })}
        </nav>
        <div className="border-t border-sidebar-border p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/15 font-mono text-xs text-primary">EM</div>
            <div className="min-w-0">
              <div className="truncate text-sm">Elena Morris</div>
              <div className="truncate text-xs text-muted-foreground">Pro · Astrabit Labs</div>
            </div>
          </div>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-border/60 bg-background/80 px-6 backdrop-blur-xl">
          <h1 className="text-[15px] font-medium tracking-tight">{title}</h1>
          <div className="ml-auto flex items-center gap-2">
            <div className="hidden items-center gap-2 rounded-md border border-border bg-surface px-3 py-1.5 text-sm text-muted-foreground sm:flex">
              <Search className="h-3.5 w-3.5" />
              <span>Search boards, projects…</span>
              <kbd className="ml-6 rounded border border-border px-1.5 py-0.5 font-mono text-[10px]">⌘K</kbd>
            </div>
            <button className="flex h-9 w-9 items-center justify-center rounded-md border border-border text-muted-foreground hover:text-foreground">
              <Bell className="h-4 w-4" />
            </button>
          </div>
        </header>
        <main className="flex-1 p-6 lg:p-8">{children}</main>
      </div>
    </div>
  );
}
