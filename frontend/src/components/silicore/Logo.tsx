export function Logo({ className = "", showWordmark = true }: { className?: string; showWordmark?: boolean }) {
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <img
        src="/static/silicore-logo.png"
        alt="Silicore"
        className="h-10 w-10 rounded-[10px] object-cover shadow-[0_10px_24px_-12px_oklch(0.1_0.03_240_/_0.9)]"
      />
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
