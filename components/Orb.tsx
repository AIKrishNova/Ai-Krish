"use client";

import type { CSSProperties } from "react";

export type OrbMode = "idle" | "standby" | "listening" | "thinking" | "speaking";

// Colours come from the orb image: cyan, blue, violet, pink.
const TONE: Record<OrbMode, { glow: string; ring: string }> = {
  idle: { glow: "rgba(99,102,241,0.38)", ring: "#818cf8" },
  standby: { glow: "rgba(139,92,246,0.42)", ring: "#a78bfa" },
  listening: { glow: "rgba(34,211,238,0.50)", ring: "#22d3ee" },
  thinking: { glow: "rgba(99,102,241,0.50)", ring: "#6366f1" },
  speaking: { glow: "rgba(236,72,153,0.38)", ring: "#c084fc" },
};

const CSS = `
.kr-orb{position:relative;width:var(--s);height:var(--s);display:grid;place-items:center;flex:none}
.kr-glow{position:absolute;inset:-14%;border-radius:9999px;background:radial-gradient(circle,var(--glow) 0%,transparent 66%);filter:blur(16px);opacity:.6;transition:background .5s;animation:kr-breathe 6s ease-in-out infinite}
.kr-img{position:relative;width:80%;height:80%;object-fit:contain;user-select:none;-webkit-user-drag:none;animation:kr-float 7s ease-in-out infinite}
.kr-ring{position:absolute;inset:10%;border-radius:9999px;border:2px solid var(--ring);opacity:0;pointer-events:none}
.kr-listening .kr-ring,.kr-speaking .kr-ring{animation:kr-ripple 2.4s ease-out infinite}
.kr-listening .r2,.kr-speaking .r2{animation-delay:.8s}
.kr-listening .r3,.kr-speaking .r3{animation-delay:1.6s}
.kr-standby .r1{opacity:.35}
.kr-halo{position:absolute;inset:7%;border-radius:9999px;opacity:0;pointer-events:none;
  background:conic-gradient(from 0deg,transparent 0 50%,var(--ring) 100%);
  -webkit-mask:radial-gradient(farthest-side,transparent calc(100% - 3px),#000 calc(100% - 3px));
  mask:radial-gradient(farthest-side,transparent calc(100% - 3px),#000 calc(100% - 3px))}
.kr-thinking .kr-halo{opacity:1;animation:kr-spin 1.6s linear infinite}
.kr-thinking .kr-img{animation:kr-float 3s ease-in-out infinite}
.kr-wave{display:flex;align-items:center;justify-content:center;gap:3px;height:18px}
.kr-wave i{display:block;width:3px;height:6px;border-radius:2px;background:#8b5cf6;animation:kr-bar .9s ease-in-out infinite}
.kr-wave i:nth-child(2){animation-delay:.12s}.kr-wave i:nth-child(3){animation-delay:.24s}
.kr-wave i:nth-child(4){animation-delay:.36s}.kr-wave i:nth-child(5){animation-delay:.48s}
@keyframes kr-float{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}
@keyframes kr-breathe{0%,100%{opacity:.45;transform:scale(1)}50%{opacity:.75;transform:scale(1.06)}}
@keyframes kr-ripple{0%{transform:scale(.9);opacity:.55}100%{transform:scale(1.55);opacity:0}}
@keyframes kr-spin{to{transform:rotate(360deg)}}
@keyframes kr-bar{0%,100%{height:5px}50%{height:18px}}
@media (prefers-reduced-motion:reduce){
  .kr-glow,.kr-img,.kr-ring,.kr-halo,.kr-wave i{animation:none!important}
  .kr-listening .r1,.kr-speaking .r1{opacity:.5}
  .kr-wave i{height:10px}
}
`;

export function OrbStyles() {
  return <style>{CSS}</style>;
}

/** The supplied glass orb. Rings, halo and wave are driven by the assistant's state, not by live audio levels. */
export default function Orb({ mode, size = 288, small = false }: { mode: OrbMode; size?: number; small?: boolean }) {
  const t = TONE[mode];
  return (
    <div
      aria-hidden
      className={`kr-orb kr-${mode}`}
      style={{ "--s": `${size}px`, "--glow": t.glow, "--ring": t.ring } as CSSProperties}
    >
      <span className="kr-glow" />
      <span className="kr-ring r1" />
      <span className="kr-ring r2" />
      <span className="kr-ring r3" />
      <span className="kr-halo" />
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img className="kr-img" src={small ? "/orb-sm.webp" : "/orb.webp"} width={720} height={720} alt="" draggable={false} />
    </div>
  );
}

export function Wave() {
  return (
    <span className="kr-wave" aria-hidden>
      <i /><i /><i /><i /><i />
    </span>
  );
}
