export function ScoreRing({ score, size = 96 }: { score: number; size?: number }) {
  const r = (size - 10) / 2;
  const c = 2 * Math.PI * r;
  const dash = (score / 100) * c;
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} stroke="currentColor" strokeOpacity="0.15" strokeWidth={5} fill="none" className="text-muted-foreground" />
        <circle
          cx={size / 2} cy={size / 2} r={r}
          stroke="currentColor" strokeWidth={5} fill="none"
          strokeDasharray={`${dash} ${c}`} strokeLinecap="round"
          className="text-primary transition-all duration-700"
          style={{ filter: "drop-shadow(0 0 6px oklch(0.85 0.16 195 / 0.6))" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-mono text-2xl font-semibold">{score}</span>
        <span className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">score</span>
      </div>
    </div>
  );
}
