import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip,
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  BarChart, Bar, Legend,
} from "recharts";

const tooltipStyle = {
  background: "oklch(0.19 0.014 250)",
  border: "1px solid oklch(0.28 0.014 250)",
  borderRadius: 8,
  fontSize: 12,
};

const transparentCursor = { fill: "transparent", stroke: "transparent" };

const SEV_COLORS: Record<string, string> = {
  critical: "oklch(0.68 0.22 25)",
  medium: "oklch(0.78 0.18 75)",
  low: "oklch(0.72 0.14 220)",
};

export function SeverityDonut({
  data,
}: {
  data: { name: string; value: number }[];
}) {
  const total = data.reduce((s, d) => s + d.value, 0);
  return (
    <div className="flex items-center gap-6">
      <div className="relative h-[160px] w-[160px] shrink-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              innerRadius={52}
              outerRadius={74}
              paddingAngle={2}
              stroke="none"
            >
              {data.map((d) => (
                <Cell key={d.name} fill={SEV_COLORS[d.name.toLowerCase()] ?? "oklch(0.6 0.05 250)"} />
              ))}
            </Pie>
            <Tooltip cursor={transparentCursor} contentStyle={tooltipStyle} />
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <div className="text-2xl font-semibold">{total}</div>
          <div className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">findings</div>
        </div>
      </div>
      <div className="space-y-2">
        {data.map((d) => (
          <div key={d.name} className="flex items-center gap-3 text-sm">
            <span
              className="h-2.5 w-2.5 rounded-full"
              style={{ background: SEV_COLORS[d.name.toLowerCase()] ?? "oklch(0.6 0.05 250)" }}
            />
            <span className="capitalize">{d.name}</span>
            <span className="ml-auto font-mono text-xs text-muted-foreground">{d.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function ScoreTrend({
  data,
}: {
  data: { label: string; score: number }[];
}) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data}>
        <CartesianGrid stroke="oklch(0.28 0.014 250)" vertical={false} />
        <XAxis dataKey="label" stroke="oklch(0.55 0.018 250)" fontSize={11} tickLine={false} axisLine={false} />
        <YAxis domain={[0, 100]} stroke="oklch(0.55 0.018 250)" fontSize={11} tickLine={false} axisLine={false} />
        <Tooltip cursor={transparentCursor} contentStyle={tooltipStyle} />
        <Line
          type="monotone"
          dataKey="score"
          stroke="oklch(0.85 0.16 195)"
          strokeWidth={2}
          dot={{ r: 3, fill: "oklch(0.85 0.16 195)", strokeWidth: 0 }}
          activeDot={{ r: 5 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function CategoryBreakdown({
  data,
}: {
  data: { category: string; critical: number; medium: number; low: number }[];
}) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16 }}>
        <CartesianGrid stroke="oklch(0.28 0.014 250)" horizontal={false} />
        <XAxis type="number" stroke="oklch(0.55 0.018 250)" fontSize={11} tickLine={false} axisLine={false} />
        <YAxis
          type="category"
          dataKey="category"
          stroke="oklch(0.55 0.018 250)"
          fontSize={11}
          tickLine={false}
          axisLine={false}
          width={110}
        />
        <Tooltip cursor={transparentCursor} contentStyle={tooltipStyle} />
        <Legend wrapperStyle={{ fontSize: 11 }} iconType="circle" />
        <Bar dataKey="critical" stackId="a" fill={SEV_COLORS.critical} radius={[0, 0, 0, 0]} activeBar={{ stroke: "rgba(255,255,255,0.75)", strokeWidth: 1.4, fillOpacity: 1, filter: "drop-shadow(0 0 10px rgba(248,113,113,0.35))" }} />
        <Bar dataKey="medium" stackId="a" fill={SEV_COLORS.medium} activeBar={{ stroke: "rgba(255,255,255,0.72)", strokeWidth: 1.3, fillOpacity: 1, filter: "drop-shadow(0 0 10px rgba(250,204,21,0.32))" }} />
        <Bar dataKey="low" stackId="a" fill={SEV_COLORS.low} radius={[0, 4, 4, 0]} activeBar={{ stroke: "rgba(255,255,255,0.7)", strokeWidth: 1.3, fillOpacity: 1, filter: "drop-shadow(0 0 10px rgba(86,211,240,0.3))" }} />
      </BarChart>
    </ResponsiveContainer>
  );
}
