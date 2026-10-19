// DISPLAY-ONLY indicator maths for the chart panes.
// The Jarvis signal engine in lib/market.ts stays the single source of truth for alerts.
// Nothing here feeds a vote. All values use closed-form past data only (no look-ahead).

export type Pt = { time: number; value: number };

export function sma(closes: number[], times: number[], period: number): Pt[] {
  const out: Pt[] = [];
  let sum = 0;
  for (let i = 0; i < closes.length; i++) {
    sum += closes[i];
    if (i >= period) sum -= closes[i - period];
    if (i >= period - 1) out.push({ time: times[i], value: sum / period });
  }
  return out;
}

// Returns an EMA array aligned to the input (NaN until seeded).
function emaRaw(v: number[], period: number): number[] {
  const k = 2 / (period + 1);
  const out = new Array(v.length).fill(NaN);
  let seed = 0;
  let count = 0;
  let prev = NaN;
  for (let i = 0; i < v.length; i++) {
    if (Number.isNaN(v[i])) continue;
    if (Number.isNaN(prev)) {
      seed += v[i];
      count++;
      if (count === period) {
        prev = seed / period;
        out[i] = prev;
      }
    } else {
      prev = v[i] * k + prev * (1 - k);
      out[i] = prev;
    }
  }
  return out;
}

export function macd(closes: number[], times: number[], fast = 12, slow = 26, signal = 9) {
  const ef = emaRaw(closes, fast);
  const es = emaRaw(closes, slow);
  const line = closes.map((_, i) => (Number.isNaN(ef[i]) || Number.isNaN(es[i]) ? NaN : ef[i] - es[i]));
  const sig = emaRaw(line, signal);
  const macdPts: Pt[] = [];
  const sigPts: Pt[] = [];
  const hist: Pt[] = [];
  for (let i = 0; i < closes.length; i++) {
    if (!Number.isNaN(line[i])) macdPts.push({ time: times[i], value: line[i] });
    if (!Number.isNaN(sig[i])) {
      sigPts.push({ time: times[i], value: sig[i] });
      hist.push({ time: times[i], value: line[i] - sig[i] });
    }
  }
  return { macd: macdPts, signal: sigPts, hist };
}

// Wilder RSI aligned to input (NaN until seeded).
function rsiRaw(closes: number[], period: number): number[] {
  const out = new Array(closes.length).fill(NaN);
  if (closes.length <= period) return out;
  let gain = 0;
  let loss = 0;
  for (let i = 1; i <= period; i++) {
    const d = closes[i] - closes[i - 1];
    if (d >= 0) gain += d;
    else loss -= d;
  }
  gain /= period;
  loss /= period;
  out[period] = loss === 0 ? 100 : 100 - 100 / (1 + gain / loss);
  for (let i = period + 1; i < closes.length; i++) {
    const d = closes[i] - closes[i - 1];
    gain = (gain * (period - 1) + Math.max(d, 0)) / period;
    loss = (loss * (period - 1) + Math.max(-d, 0)) / period;
    out[i] = loss === 0 ? 100 : 100 - 100 / (1 + gain / loss);
  }
  return out;
}

function smaRaw(v: number[], period: number): number[] {
  const out = new Array(v.length).fill(NaN);
  for (let i = period - 1; i < v.length; i++) {
    let s = 0;
    let ok = true;
    for (let j = i - period + 1; j <= i; j++) {
      if (Number.isNaN(v[j])) { ok = false; break; }
      s += v[j];
    }
    if (ok) out[i] = s / period;
  }
  return out;
}

// Stoch RSI (rsiLen, stochLen, smoothK, smoothD). This is NOT the plain Stochastic used by the Jarvis signal engine.
export function stochRsi(closes: number[], times: number[], rsiLen = 14, stochLen = 14, kLen = 3, dLen = 3) {
  const rsi = rsiRaw(closes, rsiLen);
  const raw = new Array(closes.length).fill(NaN);
  for (let i = 0; i < closes.length; i++) {
    if (i < stochLen - 1) continue;
    const win = rsi.slice(i - stochLen + 1, i + 1);
    if (win.some(Number.isNaN)) continue;
    const hi = Math.max(...win);
    const lo = Math.min(...win);
    raw[i] = hi === lo ? 0 : ((rsi[i] - lo) / (hi - lo)) * 100;
  }
  const k = smaRaw(raw, kLen);
  const d = smaRaw(k, dLen);
  const kPts: Pt[] = [];
  const dPts: Pt[] = [];
  for (let i = 0; i < closes.length; i++) {
    if (!Number.isNaN(k[i])) kPts.push({ time: times[i], value: k[i] });
    if (!Number.isNaN(d[i])) dPts.push({ time: times[i], value: d[i] });
  }
  return { k: kPts, d: dPts };
}
