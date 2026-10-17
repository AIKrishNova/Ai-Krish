import Image from "next/image";

export type LogoSize = "small" | "medium" | "large";

const SIZES: Record<LogoSize, { orb: number; text: string; row: boolean }> = {
  small: { orb: 40, text: "text-lg", row: true },
  medium: { orb: 88, text: "text-2xl", row: false },
  large: { orb: 148, text: "text-4xl", row: false },
};

const CSS = `
@media (prefers-reduced-motion:no-preference){
  .ak-logo-orb{animation:ak-logo-float 7s ease-in-out infinite}
  @keyframes ak-logo-float{0%,100%{transform:translateY(0)}50%{transform:translateY(-4px)}}
}`;

/** Circular orb only (no text). The image is masked to a circle with CSS. */
export function LogoMark({ px = 40, animate = false }: { px?: number; animate?: boolean }) {
  return (
    <span
      className={`${animate ? "ak-logo-orb " : ""}relative inline-block shrink-0 rounded-full bg-white`}
      style={{
        width: px,
        height: px,
        boxShadow:
          "0 0 0 1px rgba(99,102,241,.14), 0 8px 24px -6px rgba(91,61,245,.35), 0 0 28px rgba(34,211,238,.18)",
      }}
    >
      <Image
        src="/orb.png"
        alt="AI KRISH orb logo"
        width={512}
        height={512}
        priority
        draggable={false}
        className="h-full w-full select-none rounded-full object-cover object-center"
      />
    </span>
  );
}

/**
 * Orb image + separate "AI KRISH" text element.
 * small  -> orb, then text to its right (sidebar)
 * medium / large -> orb with the text centered directly below it
 */
export default function Logo({
  size = "medium",
  showText = true,
  tagline,
  className = "",
}: {
  size?: LogoSize;
  showText?: boolean;
  tagline?: string;
  className?: string;
}) {
  const s = SIZES[size];
  return (
    <div
      className={`inline-flex items-center ${
        s.row ? "flex-row gap-2.5" : "flex-col gap-3.5 text-center"
      } ${className}`}
    >
      <style>{CSS}</style>
      <LogoMark px={s.orb} animate={!s.row} />
      {showText && (
        <div className="leading-tight">
          <div
            className={`${s.text} font-extrabold tracking-[0.06em] text-[#0f1b3d]`}
            style={{
              fontFamily: "'Plus Jakarta Sans','Poppins','Inter',system-ui,sans-serif",
              backgroundImage: "linear-gradient(90deg,#0f1b3d 0%,#1e3a8a 62%,#6d28d9 100%)",
              WebkitBackgroundClip: "text",
              backgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            AI KRISH
          </div>
          {tagline && <div className="mt-0.5 text-[11px] text-slate-500">{tagline}</div>}
        </div>
      )}
    </div>
  );
}
