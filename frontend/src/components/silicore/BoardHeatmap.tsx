import { useMemo, useState } from "react";

type HeatMode = "thermal" | "density" | "findings";

type BoardHotspot = {
  x: number;
  y: number;
  radius: number;
  tone: "safe" | "low" | "medium" | "high" | "critical";
  message?: string;
  components?: string[];
  nets?: string[];
};

type BoardOutline = {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
};

type BoardPoint = {
  x: number;
  y: number;
};

type BoardTrace = {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
};

type BoardViewData = {
  has_data?: boolean;
  width?: number;
  height?: number;
  base_view_box?: string;
  outline_segments?: BoardOutline[];
  hotspots?: BoardHotspot[];
  summary_stats?: Array<{ label: string; value: number }>;
  components?: BoardPoint[];
  vias?: BoardPoint[];
  traces?: BoardTrace[];
};

type MatrixCell = {
  label?: string;
  board?: string;
  value: number;
  tone: "none" | "light" | "medium" | "strong";
};

type MatrixRow = {
  category: string;
  cells: MatrixCell[];
  total?: number;
};

type GridCell = {
  key: string;
  value: number;
  tone: BoardHotspot["tone"] | "safe";
  label: string;
};

const MODES: Array<{ id: HeatMode; label: string }> = [
  { id: "thermal", label: "Thermal" },
  { id: "density", label: "Density" },
  { id: "findings", label: "Findings" },
];

export function BoardHeatmap({
  title = "Board heat map",
  boardView,
  matrixRows,
  emptyCopy = "No heat-map data is available for this view yet.",
}: {
  title?: string;
  boardView?: BoardViewData | null;
  matrixRows?: MatrixRow[] | null;
  emptyCopy?: string;
}) {
  const [mode, setMode] = useState<HeatMode>("thermal");
  const hasBoardData = Boolean(
    boardView?.has_data && ((boardView?.hotspots?.length || 0) > 0 || (boardView?.outline_segments?.length || 0) > 0),
  );
  const hasMatrixData = Boolean(matrixRows?.length);

  return (
    <div className="rounded-[30px] border border-border bg-[radial-gradient(circle_at_top_left,_rgba(86,211,240,0.08),_transparent_28%),linear-gradient(180deg,rgba(8,18,28,0.98),rgba(7,15,24,0.96))] p-6 shadow-[inset_0_1px_0_rgba(255,255,255,0.02)]">
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-muted-foreground">{title}</div>
          <div className="mt-1 text-sm text-muted-foreground">
            {hasBoardData
              ? "Hotspots across the board surface from real geometry-linked findings"
              : hasMatrixData
                ? "Real category intensity by board or revision"
                : "No real heat-map payload is available for this screen yet"}
          </div>
        </div>
        {hasBoardData ? (
          <div className="inline-flex rounded-full border border-border bg-background/40 p-1 text-xs">
            {MODES.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => setMode(item.id)}
                className={`rounded-full px-4 py-1.5 font-mono uppercase tracking-[0.18em] transition-all ${
                  mode === item.id
                    ? "bg-primary/18 text-primary shadow-[0_0_18px_rgba(86,211,240,0.18)]"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>
        ) : hasMatrixData ? (
          <MatrixLegend />
        ) : null}
      </div>

      {hasBoardData ? (
        <BoardViewHeatmap boardView={boardView!} mode={mode} />
      ) : hasMatrixData ? (
        <MatrixHeatmap rows={matrixRows!} />
      ) : (
        <p className="rounded-2xl border border-dashed border-border bg-background/40 p-5 text-sm text-muted-foreground">
          {emptyCopy}
        </p>
      )}
    </div>
  );
}

function BoardViewHeatmap({ boardView, mode }: { boardView: BoardViewData; mode: HeatMode }) {
  const width = boardView.width || 820;
  const height = boardView.height || 440;
  const cols = 24;
  const rows = 10;
  const cellWidth = width / cols;
  const cellHeight = height / rows;
  const stats = boardView.summary_stats || [];

  const cells = useMemo(() => {
    const hotspotValues = (boardView.hotspots || []).map((item) => ({
      ...item,
      weight: toneWeight(item.tone),
    }));
    const componentPoints = (boardView.components || []).map((item) => ({ x: item.x, y: item.y }));
    const viaPoints = (boardView.vias || []).map((item) => ({ x: item.x, y: item.y }));
    const tracePoints = (boardView.traces || []).slice(0, 180).map((item) => ({
      x: (item.x1 + item.x2) / 2,
      y: (item.y1 + item.y2) / 2,
    }));

    const computed: GridCell[] = [];
    let maxValue = 0;

    for (let row = 0; row < rows; row += 1) {
      for (let col = 0; col < cols; col += 1) {
        const centerX = (col + 0.5) * cellWidth;
        const centerY = (row + 0.5) * cellHeight;
        let thermalValue = 0;
        let findingValue = 0;
        let densityValue = 0;
        let strongestTone: BoardHotspot["tone"] | "safe" = "safe";
        let toneScore = 0;

        for (const spot of hotspotValues) {
          const dx = centerX - spot.x;
          const dy = centerY - spot.y;
          const distance = Math.sqrt((dx * dx) + (dy * dy));
          const normalizedThermal = Math.max(0, 1 - (distance / (spot.radius * 2.35)));
          const normalizedFinding = Math.max(0, 1 - (distance / (spot.radius * 1.35)));
          thermalValue += normalizedThermal * (spot.weight * 1.15);
          findingValue += normalizedFinding * (spot.weight * 1.3);
          if (normalizedFinding > 0.18 && spot.weight >= toneScore) {
            strongestTone = spot.tone;
            toneScore = spot.weight;
          }
        }

        densityValue += samplePointField(componentPoints, centerX, centerY, 56, 1.1);
        densityValue += samplePointField(viaPoints, centerX, centerY, 42, 0.8);
        densityValue += samplePointField(tracePoints, centerX, centerY, 54, 0.55);
        densityValue += thermalValue * 0.22;

        const rawValue =
          mode === "thermal"
            ? (thermalValue * 0.8) + (densityValue * 0.2)
            : mode === "density"
              ? densityValue
              : findingValue;

        maxValue = Math.max(maxValue, rawValue);
        computed.push({
          key: `${row}-${col}`,
          value: rawValue,
          tone: strongestTone,
          label: `Row ${row + 1}, col ${col + 1}`,
        });
      }
    }

    return computed.map((cell) => ({
      ...cell,
      value: maxValue > 0 ? cell.value / maxValue : 0,
    }));
  }, [boardView.components, boardView.hotspots, boardView.traces, boardView.vias, cellHeight, cellWidth, mode]);

  return (
    <div className="space-y-4">
      <div className="rounded-[28px] border border-border bg-[linear-gradient(180deg,rgba(9,19,29,0.98),rgba(10,18,28,0.96))] p-5">
        <div className="rounded-[26px] border border-white/6 bg-background/25 p-4">
          <div
            className="grid gap-[6px]"
            style={{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }}
          >
            {cells.map((cell) => (
              <div
                key={cell.key}
                title={`${cell.label} · ${(cell.value * 100).toFixed(0)} intensity`}
                className="aspect-square rounded-[6px] transition-[transform,box-shadow,opacity] duration-200 hover:scale-[1.08] hover:shadow-[0_0_18px_rgba(86,211,240,0.22)]"
                style={{
                  background: modeColor(mode, cell.tone, cell.value),
                  opacity: 0.32 + (cell.value * 0.68),
                  boxShadow: cell.value > 0.78 ? `0 0 16px ${glowColor(cell.tone)}` : undefined,
                }}
              />
            ))}
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between gap-4">
        <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">low</div>
        <div className="h-3 flex-1 rounded-full" style={{ background: modeLegend(mode) }} />
        <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">high</div>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        {stats.slice(0, 3).map((item) => (
          <div key={item.label} className="rounded-xl border border-border bg-background/35 p-3">
            <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{item.label}</div>
            <div className="mt-1 text-lg font-semibold">{item.value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function MatrixHeatmap({ rows }: { rows: MatrixRow[] }) {
  const columnCount = rows[0]?.cells?.length || 0;
  return (
    <div className="overflow-hidden rounded-2xl border border-border bg-background/45">
      <div
        className="grid gap-px bg-border/70 p-px"
        style={{ gridTemplateColumns: `minmax(132px, 1.2fr) repeat(${columnCount}, minmax(0, 1fr)) minmax(56px, 0.6fr)` }}
      >
        <div className="bg-background px-3 py-2 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">Category</div>
        {(rows[0]?.cells || []).map((cell, index) => (
          <div key={`head-${index}`} className="bg-background px-2 py-2 text-center font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
            {truncateLabel(cell.label || cell.board || `C${index + 1}`)}
          </div>
        ))}
        <div className="bg-background px-2 py-2 text-center font-mono text-[10px] uppercase tracking-wider text-muted-foreground">Total</div>

        {rows.map((row) => (
          <Row key={row.category} row={row} />
        ))}
      </div>
    </div>
  );
}

function Row({ row }: { row: MatrixRow }) {
  return (
    <>
      <div className="flex items-center bg-background px-3 py-3 text-sm font-medium">{row.category}</div>
      {row.cells.map((cell, index) => (
        <div
          key={`${row.category}-${index}`}
          className="flex min-h-[58px] items-center justify-center bg-background px-2 py-3 text-sm font-semibold transition-[transform,box-shadow] duration-200 hover:scale-[1.03] hover:shadow-[0_0_16px_rgba(86,211,240,0.16)]"
          style={{ background: matrixTone(cell.tone) }}
          title={`${cell.label || cell.board || "Cell"}: ${cell.value}`}
        >
          {cell.value}
        </div>
      ))}
      <div className="flex items-center justify-center bg-background px-2 py-3 text-sm font-semibold text-primary">
        {row.total ?? row.cells.reduce((sum, cell) => sum + cell.value, 0)}
      </div>
    </>
  );
}

function MatrixLegend() {
  return (
    <div className="flex flex-wrap items-center gap-2 text-[11px] text-muted-foreground">
      {[
        ["Low", "light"],
        ["Medium", "medium"],
        ["High", "strong"],
      ].map(([label, tone]) => (
        <span key={label} className="inline-flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-sm" style={{ background: matrixTone(tone as MatrixCell["tone"]) }} />
          {label}
        </span>
      ))}
    </div>
  );
}

function toneWeight(tone: BoardHotspot["tone"]) {
  return { safe: 0.4, low: 1, medium: 1.65, high: 2.35, critical: 3 }[tone] || 1;
}

function samplePointField(points: BoardPoint[], centerX: number, centerY: number, radius: number, scale: number) {
  let total = 0;
  for (const point of points) {
    const dx = centerX - point.x;
    const dy = centerY - point.y;
    const distance = Math.sqrt((dx * dx) + (dy * dy));
    total += Math.max(0, 1 - (distance / radius)) * scale;
  }
  return total;
}

function modeColor(mode: HeatMode, tone: BoardHotspot["tone"] | "safe", value: number) {
  const weight = Math.max(0, Math.min(1, value));
  if (mode === "density") {
    const hue = 195 - (weight * 165);
    return `oklch(${0.36 + (weight * 0.42)} ${0.06 + (weight * 0.18)} ${hue})`;
  }
  if (mode === "findings") {
    const palette = {
      safe: "oklch(0.34 0.04 225)",
      low: "oklch(0.44 0.13 205)",
      medium: "oklch(0.72 0.18 75)",
      high: "oklch(0.78 0.2 50)",
      critical: "oklch(0.72 0.22 25)",
    };
    return palette[tone] || palette.low;
  }
  return `oklch(${0.46 + (weight * 0.28)} ${0.08 + (weight * 0.2)} ${210 - (weight * 185)})`;
}

function modeLegend(mode: HeatMode) {
  if (mode === "density") {
    return "linear-gradient(90deg, oklch(0.46 0.12 220), oklch(0.68 0.16 190), oklch(0.8 0.18 75), oklch(0.72 0.22 25))";
  }
  if (mode === "findings") {
    return "linear-gradient(90deg, oklch(0.44 0.13 205), oklch(0.72 0.18 75), oklch(0.78 0.2 50), oklch(0.72 0.22 25))";
  }
  return "linear-gradient(90deg, oklch(0.7 0.14 220), oklch(0.74 0.17 185), oklch(0.82 0.18 75), oklch(0.72 0.22 25))";
}

function glowColor(tone: BoardHotspot["tone"] | "safe") {
  const map = {
    safe: "rgba(86,211,240,0.14)",
    low: "rgba(86,211,240,0.2)",
    medium: "rgba(250,204,21,0.24)",
    high: "rgba(251,146,60,0.28)",
    critical: "rgba(248,113,113,0.32)",
  };
  return map[tone] || map.low;
}

function matrixTone(tone: MatrixCell["tone"]) {
  const map = {
    none: "rgba(15, 23, 42, 0.28)",
    light: "rgba(86, 211, 240, 0.22)",
    medium: "rgba(250, 204, 21, 0.28)",
    strong: "rgba(248, 113, 113, 0.3)",
  };
  return map[tone] || map.none;
}

function truncateLabel(value: string) {
  if (value.length <= 10) {
    return value;
  }
  return `${value.slice(0, 10)}…`;
}
