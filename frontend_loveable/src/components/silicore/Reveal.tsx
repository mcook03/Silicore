import { useEffect, useRef, type ReactNode, type ElementType, type CSSProperties } from "react";

type RevealProps = {
  children: ReactNode;
  as?: ElementType;
  delay?: number;
  className?: string;
  once?: boolean;
};

export function Reveal({
  children,
  as: Tag = "div",
  delay = 0,
  className,
  once = true,
}: RevealProps) {
  const ref = useRef<HTMLElement | null>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) {
            (e.target as HTMLElement).dataset.reveal = "in";
            if (once) io.unobserve(e.target);
          } else if (!once) {
            (e.target as HTMLElement).dataset.reveal = "";
          }
        }
      },
      { threshold: 0.15, rootMargin: "0px 0px -10% 0px" },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [once]);

  const style: CSSProperties = { ["--reveal-delay" as string]: `${delay}ms` };

  return (
    <Tag ref={ref as never} data-reveal="" style={style} className={className}>
      {children}
    </Tag>
  );
}

/** Animates each word of `text` independently, staggered. */
export function RevealWords({
  text,
  className,
  stagger = 60,
  startDelay = 0,
}: {
  text: string;
  className?: string;
  stagger?: number;
  startDelay?: number;
}) {
  const ref = useRef<HTMLHeadingElement | null>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) {
            (e.target as HTMLElement).dataset.revealWords = "in";
            io.unobserve(e.target);
          }
        }
      },
      { threshold: 0.2 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  const words = text.split(" ");

  return (
    <span ref={ref} data-reveal-words="" className={className}>
      {words.map((w, i) => (
        <span key={`${w}-${i}`} style={{ transitionDelay: `${startDelay + i * stagger}ms` }}>
          {w}
          {i < words.length - 1 ? "\u00A0" : ""}
        </span>
      ))}
    </span>
  );
}
