export type Candle = { t: number; o: number; h: number; l: number; c: number; v: number };
export type Vote = "BULL" | "BEAR" | "NEUTRAL" | "INVALID";
export type Row = { name: string; value: string; vote: Vote };
export type Result = {
  ok: boolean;
  direction: "UP" | "DOWN" | "NONE";
  bull: number;
  bear: number;
  rows: Row[];
  failures: string[];
  candleTime: number;
  price: number;
};

export const INTERVAL_MS: Record<string, number> = {
  "1m": 60000,
  "3m": 180000,
  "5m": 300000,
  "15m": 900000,
  "30m": 1800000,
  "1h": 3600000,
  "4h": 14400000,
  "1d": 86400000,
};

// Editable strategy settings: "Jarvis 1-Minute Indicator Agreement - Version 1"
export const STRATEGY = {
  version: "Jarvis 1-Minute Indicator Agreement v1",
  upMin: 3, // UP needs at least 3 of 5 bullish votes
  downMin: 5, // DOWN needs all 5 of 5 bearish votes
  alligatorSepAtr: 0.1, // smallest gap between Alligator lines, as a fraction of ATR(14)
  stochK: 14,
  stochD: 3,
  stochSmooth: 3, // slow stochastic: %K is smoothed with a 3-period average
  minCandles: 60,
};

const nan = (n: number) => new Array<number>(n).fill(NaN);
const ok = (x: number) => Number.isFinite(x);

export function sma(values: number[], p: number): number[] {
  const out = nan(values.length);
  for (let i = p - 1; i < values.length; i++) {
    let s = 0;
    let good = true;
    for (let j = i - p + 1; j <= i; j++) {
      if (!ok(values[j])) {
        good = false;
        break;
      }
      s += values[j];
    }
    if (good) out[i] = s / p;
  }
  return out;
}

export function smma(values: number[], p: number): number[] {
  const out = nan(values.length);
  if (values.length < p) return out;
  let s = 0;
  for (let i = 0; i < p; i++) s += values[i];
  out[p - 1] = s / p;
  for (let i = p; i < values.length; i++) out[i] = (out[i - 1] * (p - 1) + values[i]) / p;
  return out;
}

export function ema(values: number[], p: number): number[] {
  const start = values.findIndex(ok);
  const out = nan(values.length);
  if (start === -1 || values.length - start < p) return out;
  let s = 0;
  for (let i = start; i < start + p; i++) s += values[i];
  out[start + p - 1] = s / p;
  const k = 2 / (p + 1);
  for (let i = start + p; i < values.length; i++) out[i] = values[i] * k + out[i - 1] * (1 - k);
  return out;
}

export function rsi(c: number[], p = 14): number[] {
  const out = nan(c.length);
  if (c.length <= p) return out;
  let g = 0;
  let l = 0;
  for (let i = 1; i <= p; i++) {
    const d = c[i] - c[i - 1];
    if (d >= 0) g += d;
    else l -= d;
  }
  g /= p;
  l /= p;
  out[p] = l === 0 ? 100 : 100 - 100 / (1 + g / l);
  for (let i = p + 1; i < c.length; i++) {
    const d = c[i] - c[i - 1];
    g = (g * (p - 1) + Math.max(d, 0)) / p;
    l = (l * (p - 1) + Math.max(-d, 0)) / p;
    out[i] = l === 0 ? 100 : 100 - 100 / (1 + g / l);
  }
  return out;
}

export function atr(cs: Candle[], p = 14): number[] {
  const tr = cs.map((x, i) =>
    i === 0 ? x.h - x.l : Math.max(x.h - x.l, Math.abs(x.h - cs[i - 1].c), Math.abs(x.l - cs[i - 1].c))
  );
  return smma(tr, p);
}

export function macd(c: number[], fast = 12, slow = 26, sig = 9) {
  const f = ema(c, fast);
  const s = ema(c, slow);
  const line = c.map((_, i) => (ok(f[i]) && ok(s[i]) ? f[i] - s[i] : NaN));
  const signal = ema(line, sig);
  return { line, signal };
}

export function stochastic(cs: Candle[], kP: number, dP: number, smooth: number) {
  const raw = nan(cs.length);
  for (let i = kP - 1; i < cs.length; i++) {
    let hh = -Infinity;
    let ll = Infinity;
    for (let j = i - kP + 1; j <= i; j++) {
      hh = Math.max(hh, cs[j].h);
      ll = Math.min(ll, cs[j].l);
    }
    raw[i] = hh === ll ? 50 : ((cs[i].c - ll) / (hh - ll)) * 100;
  }
  const k = smooth > 1 ? sma(raw, smooth) : raw;
  const d = sma(k, dP);
  return { k, d };
}

export function psar(cs: Candle[], step = 0.02, maxStep = 0.2) {
  const n = cs.length;
  const sar = nan(n);
  if (n < 3) return sar;
  let up = cs[1].c >= cs[0].c;
  let ep = up ? Math.max(cs[0].h, cs[1].h) : Math.min(cs[0].l, cs[1].l);
  let s = up ? Math.min(cs[0].l, cs[1].l) : Math.max(cs[0].h, cs[1].h);
  let af = step;
  sar[1] = s;
  for (let i = 2; i < n; i++) {
    s = s + af * (ep - s);
    if (up) {
      s = Math.min(s, cs[i - 1].l, cs[i - 2].l);
      if (cs[i].l < s) {
        up = false;
        s = ep;
        ep = cs[i].l;
        af = step;
      } else if (cs[i].h > ep) {
        ep = cs[i].h;
        af = Math.min(af + step, maxStep);
      }
    } else {
      s = Math.max(s, cs[i - 1].h, cs[i - 2].h);
      if (cs[i].h > s) {
        up = true;
        s = ep;
        ep = cs[i].h;
        af = step;
      } else if (cs[i].l < ep) {
        ep = cs[i].l;
        af = Math.min(af + step, maxStep);
      }
    }
    sar[i] = s;
  }
  return sar;
}

// Alligator: smoothed averages of the median price. Jaw 13 shifted 8, Teeth 8 shifted 5, Lips 5 shifted 3.
// The shift only delays a line (we read older values), so no future data is ever used.
export function alligator(cs: Candle[]) {
  const med = cs.map((x) => (x.h + x.l) / 2);
  const jawS = smma(med, 13);
  const teethS = smma(med, 8);
  const lipsS = smma(med, 5);
  const i = cs.length - 1;
  const jaw = jawS[i - 8];
  const teeth = teethS[i - 5];
  const lips = lipsS[i - 3];
  return { jaw, teeth, lips };
}

const f = (x: number, d = 2) => (ok(x) ? x.toFixed(d) : "n/a");

export function evaluate(cs: Candle[]): Result {
  const empty: Result = {
    ok: false,
    direction: "NONE",
    bull: 0,
    bear: 0,
    rows: [],
    failures: [],
    candleTime: cs.length ? cs[cs.length - 1].t : 0,
    price: cs.length ? cs[cs.length - 1].c : NaN,
  };
  if (cs.length < STRATEGY.minCandles) {
    empty.failures.push(`Not enough candle history (${cs.length} of ${STRATEGY.minCandles} needed)`);
    return empty;
  }
  const n = cs.length - 1;
  const closes = cs.map((x) => x.c);
  const price = closes[n];
  const dec = price < 10 ? 5 : 2;

  // 1. Alligator
  const al = alligator(cs);
  const a = atr(cs, 14)[n];
  let alVote: Vote = "INVALID";
  let aligned: "BULL" | "BEAR" | "NONE" | "INVALID" = "INVALID";
  let separated = false;
  if (ok(al.jaw) && ok(al.teeth) && ok(al.lips) && ok(a)) {
    if (al.lips > al.teeth && al.teeth > al.jaw) aligned = "BULL";
    else if (al.lips < al.teeth && al.teeth < al.jaw) aligned = "BEAR";
    else aligned = "NONE";
    const gap = Math.min(Math.abs(al.lips - al.teeth), Math.abs(al.teeth - al.jaw));
    separated = gap >= STRATEGY.alligatorSepAtr * a;
    alVote = aligned === "BULL" ? "BULL" : aligned === "BEAR" ? "BEAR" : "NEUTRAL";
  }

  // 2. Parabolic SAR
  const sar = psar(cs)[n];
  const sarVote: Vote = !ok(sar) ? "INVALID" : sar < price ? "BULL" : sar > price ? "BEAR" : "NEUTRAL";

  // 3. MACD
  const m = macd(closes);
  const mv = m.line[n];
  const ms = m.signal[n];
  const macdVote: Vote = !ok(mv) || !ok(ms) ? "INVALID" : mv > ms ? "BULL" : mv < ms ? "BEAR" : "NEUTRAL";

  // 4. Stochastic
  const st = stochastic(cs, STRATEGY.stochK, STRATEGY.stochD, STRATEGY.stochSmooth);
  const k = st.k[n];
  const d = st.d[n];
  const stVote: Vote = !ok(k) || !ok(d) ? "INVALID" : k > d ? "BULL" : k < d ? "BEAR" : "NEUTRAL";

  // 5. RSI
  const r = rsi(closes, 14)[n];
  const rVote: Vote = !ok(r) ? "INVALID" : r > 50 ? "BULL" : r < 50 ? "BEAR" : "NEUTRAL";

  const rows: Row[] = [
    {
      name: "Alligator",
      value: `Lips ${f(al.lips, dec)} / Teeth ${f(al.teeth, dec)} / Jaw ${f(al.jaw, dec)}`,
      vote: alVote,
    },
    { name: "Parabolic SAR", value: f(sar, dec), vote: sarVote },
    { name: "MACD", value: `${f(mv, 4)} vs signal ${f(ms, 4)}`, vote: macdVote },
    { name: "Stochastic", value: `%K ${f(k, 1)} / %D ${f(d, 1)}`, vote: stVote },
    { name: "RSI", value: f(r, 1), vote: rVote },
  ];

  const bull = rows.filter((x) => x.vote === "BULL").length;
  const bear = rows.filter((x) => x.vote === "BEAR").length;
  const invalid = rows.filter((x) => x.vote === "INVALID").length;

  const failures: string[] = [];
  if (invalid > 0) failures.push(`${invalid} indicator(s) unavailable`);
  if (aligned === "NONE") failures.push("Alligator is tangled");
  else if (aligned !== "INVALID" && !separated) failures.push("Alligator lines too close together");

  let direction: "UP" | "DOWN" | "NONE" = "NONE";
  if (invalid === 0) {
    if (bull >= STRATEGY.upMin && aligned === "BULL" && separated) direction = "UP";
    else if (bear >= STRATEGY.downMin && aligned === "BEAR" && separated) direction = "DOWN";
  }
  if (direction === "NONE") {
    if (bull < STRATEGY.upMin && bear < STRATEGY.downMin)
      failures.push(`Votes: ${bull} bullish, ${bear} bearish (UP needs ${STRATEGY.upMin}, DOWN needs ${STRATEGY.downMin})`);
    else if (aligned === "BULL" && bull >= STRATEGY.upMin && !separated) failures.push("UP votes met but Alligator filter failed");
    else if (aligned === "BEAR" && bear >= STRATEGY.downMin && !separated) failures.push("DOWN votes met but Alligator filter failed");
    else if (bull >= STRATEGY.upMin && aligned !== "BULL") failures.push("UP votes met but Alligator is not bullish");
    else if (bear >= STRATEGY.downMin && aligned !== "BEAR") failures.push("DOWN votes met but Alligator is not bearish");
  }

  return { ok: invalid === 0, direction, bull, bear, rows, failures, candleTime: cs[n].t, price };
}
