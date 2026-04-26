import { useMemo, useState } from "react";

type Mode = "thermal" | "density" | "findings";

const MODES: { id: Mode; label: string }[] = [
  { id: "thermal", label: "Thermal" },
  { id: "density", label: "Density" },
  { id: "findings", label: "Findings" },
];

// Deterministic pseudo-random so the SSR/CSR output matches.
function seeded(x: number, y: number, mode: Mode) {
  const seed = { thermal: 11, density: 23, findings: 41 }[mode];
  const v = Math.sin(x * 12.9898 + y * 78.233 + seed) * 43758.5453;
  return v - Math.floor(v);
}

function colorFor(value: number, mode: Mode) {
  // value 0..1
  if (mode === "thermal") {
    // cool blue → hot red/orange
    const hue = 250 - value * 230; // 250 → 20
    return `oklch(0.72 ${0.12 + value * 0.12} ${hue})`;
  }
  if (mode === "density") {
    // teal scale
    return `oklch(${0.32 + value * 0.5} ${0.05 + value * 0.13} 195)`;
  }
  // findings: green → amber → red
  const hue = 150 - value * 130; // 150 → 20
  return `oklch(${0.55 + value * 0.2} ${0.1 + value * 0.16} ${hue})`;
}

export function BoardHeatmap({
  cols = 18,
  rows = 12,
  title = "Board heatmap",
}: {
  cols?: number;
  rows?: number;
  title?: string;
}) {
  const [mode, setMode] = useState<Mode>("thermal");

  const cells = useMemo(() => {
    const arr: { x: number; y: number; v: number }[] = [];
    for (let y = 0; y < rows; y++) {
      for (let x = 0; x < cols; x++) {
        // Combine two noise samples for a more "regional" hot-spot feel.
        const v = (seeded(x, y, mode) * 0.6 + seeded(x / 2, y / 2, mode) * 0.4);
        arr.push({ x, y, v });
      }
    }
    return arr;
  }, [cols, rows, mode]);

  return (
    <div className="rounded-2xl border border-border bg-surface p-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{title}</div>
          <div className="mt-0.5 text-sm text-muted-foreground">
            Hotspots across the board surface ·{" "}
            <span className="text-foreground">{mode}</span>
          </div>
        </div>
        <div className="inline-flex rounded-full border border-border bg-background/40 p-0.5 text-xs">
          {MODES.map((m) => (
            <button
              key={m.id}
              type="button"
              onClick={() => setMode(m.id)}
              className={`rounded-full px-3 py-1 font-mono uppercase tracking-wider transition-colors ${
                mode === m.id ? "bg-primary/15 text-primary" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      <div className="relative overflow-hidden rounded-xl border border-border bg-background/60 p-3">
        <div
          className="grid gap-[3px]"
          style={{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }}
        >
          {cells.map((c) => (
            <div
              key={`${c.x}-${c.y}`}
              title={`(${c.x},${c.y}) · ${(c.v * 100).toFixed(0)}`}
              className="aspect-square rounded-[3px] transition-transform hover:scale-110"
              style={{ background: colorFor(c.v, mode), opacity: 0.35 + c.v * 0.65 }}
            />
          ))}
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between gap-4">
        <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">low</div>
        <div
          className="h-2 flex-1 rounded-full"
          style={{
            background:
              mode === "thermal"
                ? "linear-gradient(90deg, oklch(0.72 0.12 250), oklch(0.78 0.18 195), oklch(0.78 0.2 75), oklch(0.72 0.22 20))"
                : mode === "density"
                ? "linear-gradient(90deg, oklch(0.32 0.05 195), oklch(0.82 0.18 195))"
                : "linear-gradient(90deg, oklch(0.6 0.16 150), oklch(0.72 0.2 75), oklch(0.7 0.22 20))",
          }}
        />
        <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">high</div>
      </div>
    </div>
  );
}
