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

type BoardViewData = {
  has_data?: boolean;
  width?: number;
  height?: number;
  base_view_box?: string;
  outline_segments?: BoardOutline[];
  hotspots?: BoardHotspot[];
  summary_stats?: Array<{ label: string; value: number }>;
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
  const hasBoardData = Boolean(boardView?.has_data && ((boardView?.hotspots?.length || 0) > 0 || (boardView?.outline_segments?.length || 0) > 0));
  const hasMatrixData = Boolean(matrixRows?.length);

  return (
    <div className="rounded-2xl border border-border bg-surface p-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">{title}</div>
          <div className="mt-0.5 text-sm text-muted-foreground">
            {hasBoardData
              ? "Real board hotspots from component, net, and finding positions"
              : hasMatrixData
                ? "Real category intensity by board or revision"
                : "No real heat-map payload is available for this screen yet"}
          </div>
        </div>
        {hasBoardData ? <BoardLegend /> : hasMatrixData ? <MatrixLegend /> : null}
      </div>

      {hasBoardData ? (
        <BoardViewHeatmap boardView={boardView!} />
      ) : hasMatrixData ? (
        <MatrixHeatmap rows={matrixRows!} />
      ) : (
        <p className="rounded-xl border border-dashed border-border bg-background/40 p-5 text-sm text-muted-foreground">
          {emptyCopy}
        </p>
      )}
    </div>
  );
}

function BoardViewHeatmap({ boardView }: { boardView: BoardViewData }) {
  const width = boardView.width || 820;
  const height = boardView.height || 440;
  const viewBox = boardView.base_view_box || `0 0 ${width} ${height}`;
  const stats = boardView.summary_stats || [];

  return (
    <div className="space-y-4">
      <div className="overflow-hidden rounded-xl border border-border bg-[radial-gradient(circle_at_top,_rgba(86,211,240,0.08),_transparent_35%),linear-gradient(180deg,rgba(7,13,22,0.96),rgba(12,18,28,0.94))] p-3">
        <svg viewBox={viewBox} className="h-auto w-full">
          <rect x="0" y="0" width={width} height={height} rx="20" fill="rgba(15,23,42,0.45)" />

          {(boardView.outline_segments || []).map((segment, index) => (
            <line
              key={`outline-${index}`}
              x1={segment.x1}
              y1={segment.y1}
              x2={segment.x2}
              y2={segment.y2}
              stroke="rgba(226,232,240,0.85)"
              strokeWidth="1.6"
              strokeLinecap="round"
            />
          ))}

          {(boardView.hotspots || []).map((spot, index) => (
            <g key={`hotspot-${index}`}>
              <circle cx={spot.x} cy={spot.y} r={spot.radius} fill={toneFill(spot.tone, 0.2)} />
              <circle cx={spot.x} cy={spot.y} r={Math.max(spot.radius * 0.58, 8)} fill={toneFill(spot.tone, 0.34)} />
              <circle cx={spot.x} cy={spot.y} r="4.5" fill={toneCore(spot.tone)} stroke="rgba(255,255,255,0.72)" strokeWidth="1.2" />
            </g>
          ))}
        </svg>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        {stats.slice(0, 3).map((item) => (
          <div key={item.label} className="rounded-xl border border-border bg-background/40 p-3">
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
    <div className="overflow-hidden rounded-xl border border-border bg-background/45">
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
          className="flex min-h-[58px] items-center justify-center bg-background px-2 py-3 text-sm font-semibold"
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

function BoardLegend() {
  return (
    <div className="flex flex-wrap items-center gap-2 text-[11px] text-muted-foreground">
      {[
        ["Low", "low"],
        ["Medium", "medium"],
        ["High", "high"],
        ["Critical", "critical"],
      ].map(([label, tone]) => (
        <span key={label} className="inline-flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full" style={{ background: toneCore(tone as BoardHotspot["tone"]) }} />
          {label}
        </span>
      ))}
    </div>
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

function toneFill(tone: BoardHotspot["tone"], opacity: number) {
  const map = {
    safe: `rgba(74, 222, 128, ${opacity})`,
    low: `rgba(86, 211, 240, ${opacity})`,
    medium: `rgba(250, 204, 21, ${opacity})`,
    high: `rgba(251, 146, 60, ${opacity})`,
    critical: `rgba(248, 113, 113, ${opacity})`,
  };
  return map[tone] || map.low;
}

function toneCore(tone: BoardHotspot["tone"]) {
  const map = {
    safe: "rgb(74, 222, 128)",
    low: "rgb(86, 211, 240)",
    medium: "rgb(250, 204, 21)",
    high: "rgb(251, 146, 60)",
    critical: "rgb(248, 113, 113)",
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
