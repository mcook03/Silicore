export function Logo({ className = "", showWordmark = true }: { className?: string; showWordmark?: boolean }) {
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <div className="relative h-10 w-10">
        <div
          className="absolute inset-0 rounded-[10px] blur-md opacity-70"
          style={{ background: "radial-gradient(circle, oklch(0.86 0.13 215 / 0.6), transparent 70%)" }}
        />
        <div
          className="relative flex h-10 w-10 items-center justify-center rounded-[10px] border border-white/10"
          style={{
            background:
              "linear-gradient(140deg, oklch(0.22 0.04 235), oklch(0.13 0.028 235))",
            boxShadow: "inset 0 1px 0 oklch(1 0 0 / 0.08), 0 8px 20px -8px oklch(0.04 0.02 235 / 0.8)",
          }}
        >
          <svg viewBox="0 0 32 32" className="h-6 w-6" fill="none">
            <defs>
              <linearGradient id="s-grad" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="oklch(0.92 0.1 215)" />
                <stop offset="60%" stopColor="oklch(0.78 0.13 255)" />
                <stop offset="100%" stopColor="oklch(0.65 0.16 265)" />
              </linearGradient>
            </defs>
            <path
              d="M22 9.5c-1.4-1.6-3.6-2.5-6-2.5-3.6 0-6 2-6 4.6 0 2.3 1.7 3.6 5.4 4.4l2.2.5c2 .5 2.7 1 2.7 2 0 1.2-1.3 2-3.4 2-2.4 0-4.2-1-5.5-2.6L9 21.4C10.6 23 13 24 16 24c4 0 6.6-2 6.6-4.9 0-2.4-1.6-3.7-5.4-4.5l-2.2-.5c-1.9-.4-2.6-.9-2.6-1.8 0-1 1.1-1.7 2.9-1.7 2 0 3.6.8 4.7 2.1L22 9.5z"
              fill="url(#s-grad)"
            />
          </svg>
        </div>
      </div>
      {showWordmark && (
        <div className="flex flex-col leading-none">
          <span className="text-[18px] font-semibold tracking-tight text-foreground">Silicore</span>
          <span className="mt-1 font-mono text-[9px] uppercase tracking-[0.22em] text-muted-foreground">
            Engineering Intelligence
          </span>
        </div>
      )}
    </div>
  );
}
