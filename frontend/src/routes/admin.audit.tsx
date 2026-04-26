import { useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/silicore/AppShell";
import { Panel } from "@/components/silicore/Panel";
import { Input } from "@/components/ui/input";
import { Download, Filter } from "lucide-react";
import { useApiData } from "@/lib/api";

export const Route = createFileRoute("/admin/audit")({
  head: () => ({ meta: [{ title: "Audit log — Silicore" }] }),
  component: Audit,
});

type AuditEvent = {
  created_at?: string;
  actor_email?: string;
  actor_user_id?: string;
  event_type?: string;
  target_type?: string;
  target_id?: string;
  message?: string;
  ip_address?: string;
};

type AuditPayload = {
  events: AuditEvent[];
};

function Audit() {
  const { data, error } = useApiData<AuditPayload>("/api/frontend/admin/audit");
  const [query, setQuery] = useState("");
  const filtered = useMemo(
    () => (data?.events || []).filter((event) => JSON.stringify(event).toLowerCase().includes(query.toLowerCase())),
    [data, query],
  );

  return (
    <AppShell title="Audit log">
      <div className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm text-muted-foreground">Workspace activity from the real Silicore audit log.</p>
          <div className="flex gap-2">
            <div className="relative">
              <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search actor, action, target…" className="w-72 pl-8" />
              <Filter className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
            </div>
            <button
              type="button"
              onClick={() => {
                const content = JSON.stringify(filtered, null, 2);
                const blob = new Blob([content], { type: "application/json" });
                const href = URL.createObjectURL(blob);
                const link = document.createElement("a");
                link.href = href;
                link.download = "silicore-audit-log.json";
                link.click();
                URL.revokeObjectURL(href);
              }}
              className="inline-flex items-center rounded-full border border-border px-3 py-2 text-sm"
            >
              <Download className="mr-1.5 h-3.5 w-3.5" /> Export
            </button>
          </div>
        </div>

        {error ? <div className="rounded-xl border border-danger/20 bg-danger/10 px-4 py-3 text-sm text-danger">{error}</div> : null}

        <Panel title="Events">
          <div className="overflow-hidden rounded-xl border border-border">
            <table className="w-full text-sm">
              <thead className="bg-background/40 text-left font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th className="px-4 py-3">Time</th>
                  <th className="px-4 py-3">Actor</th>
                  <th className="px-4 py-3">Action</th>
                  <th className="px-4 py-3">Target</th>
                  <th className="px-4 py-3">IP</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((event, index) => (
                  <tr key={`${event.created_at}-${index}`} className="border-t border-border hover:bg-background/40">
                    <td className="px-4 py-3 font-mono text-xs">{event.created_at || "—"}</td>
                    <td className="px-4 py-3">{event.actor_email || event.actor_user_id || "system"}</td>
                    <td className="px-4 py-3"><span className="rounded border border-border px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{event.event_type || "event"}</span></td>
                    <td className="px-4 py-3 text-muted-foreground">{event.target_type || event.target_id || event.message || "—"}</td>
                    <td className="px-4 py-3 font-mono text-xs text-muted-foreground">{event.ip_address || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!filtered.length ? <div className="px-4 py-6 text-sm text-muted-foreground">No audit events matched the current filter.</div> : null}
          </div>
        </Panel>
      </div>
    </AppShell>
  );
}
