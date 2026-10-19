"use client";

import { useEffect, useRef, useState } from "react";
import {
  createChart,
  CandlestickSeries,
  LineSeries,
  HistogramSeries,
  ColorType,
  CrosshairMode,
  LineStyle,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp,
} from "lightweight-charts";
import { macd, sma, stochRsi, type Pt } from "../../lib/chartIndicators";

type Candle = { time: number; open: number; high: number; low: number; close: number; volume: number };
type Feed = { provider: string; fresh: boolean; fetchedAt: number };

const UP = "#26a69a";
const DOWN = "#ef5350";
const MAS = [
  { key: "ma5", period: 5, color: "#3fb950" },
  { key: "ma8", period: 8, color: "#f5e663" },
  { key: "ma50", period: 50, color: "#3b82f6" },
  { key: "ma100", period: 100, color: "#7c4dff" },
] as const;

const ts = (p: Pt[]) => p.map((x) => ({ time: x.time as UTCTimestamp, value: x.value }));
const dp = (p: number) => (p >= 1000 ? 2 : p >= 1 ? 4 : 6);

type Series = {
  candle: ISeriesApi<"Candlestick">;
  line: ISeriesApi<"Line">;
  volume: ISeriesApi<"Histogram">;
  ma: Record<string, ISeriesApi<"Line">>;
  macdLine: ISeriesApi<"Line">;
  macdSignal: ISeriesApi<"Line">;
  macdHist: ISeriesApi<"Histogram">;
  stochK: ISeriesApi<"Line">;
  stochD: ISeriesApi<"Line">;
};

type Lookup = {
  candles: Map<number, Candle>;
  ma: Record<string, Map<number, number>>;
  macd: Map<number, number>;
  signal: Map<number, number>;
  hist: Map<number, number>;
  k: Map<number, number>;
  d: Map<number, number>;
  lastTime: number | null;
};

const toMap = (p: Pt[]) => new Map(p.map((x) => [x.time, x.value] as [number, number]));
const emptyLookup = (): Lookup => ({
  candles: new Map(), ma: {}, macd: new Map(), signal: new Map(), hist: new Map(), k: new Map(), d: new Map(), lastTime: null,
});

export default function CandleChart({ symbol, interval }: { symbol: string; interval: string }) {
  const boxRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<Series | null>(null);
  const candlesRef = useRef<Candle[]>([]);
  const lookupRef = useRef<Lookup>(emptyLookup());

  const [hoverTime, setHoverTime] = useState<number | null>(null);
  const [, setVersion] = useState(0);
  const [feed, setFeed] = useState<Feed | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [kind, setKind] = useState<"candles" | "line">("candles");
  const [showMa, setShowMa] = useState<Record<string, boolean>>({ ma5: true, ma8: true, ma50: true, ma100: true });
  const [showVol, setShowVol] = useState(true);

  // Create the chart once.
  useEffect(() => {
    if (!boxRef.current) return;
    const chart = createChart(boxRef.current, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: "#050b18" },
        textColor: "#8fb4c9",
        panes: { separatorColor: "#12304a", separatorHoverColor: "#1d5a85" },
      },
      grid: { vertLines: { color: "#0c1b2e" }, horzLines: { color: "#0c1b2e" } },
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: { borderColor: "#12304a" },
      timeScale: { borderColor: "#12304a", timeVisible: true, secondsVisible: false },
    });

    const candle = chart.addSeries(
      CandlestickSeries,
      { upColor: UP, downColor: DOWN, wickUpColor: UP, wickDownColor: DOWN, borderVisible: false },
      0
    );
    const line = chart.addSeries(LineSeries, { color: "#22d3ee", lineWidth: 2, visible: false, priceLineVisible: false }, 0);
    const volume = chart.addSeries(
      HistogramSeries,
      { priceFormat: { type: "volume" }, priceScaleId: "volume", lastValueVisible: false, priceLineVisible: false },
      0
    );
    chart.priceScale("volume").applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } });

    const ma: Record<string, ISeriesApi<"Line">> = {};
    for (const m of MAS) {
      ma[m.key] = chart.addSeries(
        LineSeries,
        { color: m.color, lineWidth: 1, priceLineVisible: false, lastValueVisible: true, crosshairMarkerVisible: false },
        0
      );
    }

    const macdHist = chart.addSeries(HistogramSeries, { priceLineVisible: false, lastValueVisible: false }, 1);
    const macdLine = chart.addSeries(LineSeries, { color: "#3b82f6", lineWidth: 1, priceLineVisible: false }, 1);
    const macdSignal = chart.addSeries(LineSeries, { color: "#e0a82e", lineWidth: 1, priceLineVisible: false }, 1);

    const stochK = chart.addSeries(LineSeries, { color: "#3b9bff", lineWidth: 1, priceLineVisible: false }, 2);
    const stochD = chart.addSeries(LineSeries, { color: "#ff8a1f", lineWidth: 1, priceLineVisible: false }, 2);
    for (const level of [20, 80]) {
      stochK.createPriceLine({ price: level, color: "#4b647a", lineWidth: 1, lineStyle: LineStyle.Dashed, axisLabelVisible: false, title: "" });
    }

    const panes = chart.panes();
    panes[0]?.setStretchFactor(3);
    panes[1]?.setStretchFactor(1);
    panes[2]?.setStretchFactor(1);

    chart.subscribeCrosshairMove((p) => setHoverTime(typeof p.time === "number" ? p.time : null));

    chartRef.current = chart;
    seriesRef.current = { candle, line, volume, ma, macdLine, macdSignal, macdHist, stochK, stochD };
    return () => {
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, []);

  // Series visibility toggles.
  useEffect(() => {
    const s = seriesRef.current;
    if (!s) return;
    s.candle.applyOptions({ visible: kind === "candles" });
    s.line.applyOptions({ visible: kind === "line" });
    s.volume.applyOptions({ visible: showVol });
    for (const m of MAS) s.ma[m.key].applyOptions({ visible: !!showMa[m.key] });
  }, [kind, showMa, showVol]);

  // Load candles for the selected asset and timeframe, then poll politely.
  useEffect(() => {
    const s = seriesRef.current;
    if (!s) return;
    let cancelled = false;

    candlesRef.current = [];
    lookupRef.current = emptyLookup();
    s.candle.setData([]);
    s.line.setData([]);
    s.volume.setData([]);
    setFeed(null);
    setError("");
    setLoading(true);

    function paint(full: boolean, changed: Candle[]) {
      const ser = seriesRef.current;
      if (!ser) return;
      const cs = candlesRef.current;
      const times = cs.map((c) => c.time);
      const closes = cs.map((c) => c.close);

      if (full) {
        ser.candle.setData(cs.map((c) => ({ ...c, time: c.time as UTCTimestamp })));
        ser.line.setData(cs.map((c) => ({ time: c.time as UTCTimestamp, value: c.close })));
        ser.volume.setData(
          cs.map((c) => ({ time: c.time as UTCTimestamp, value: c.volume, color: c.close >= c.open ? "#1e5a4f" : "#6b2d33" }))
        );
      } else {
        for (const c of changed) {
          const t = c.time as UTCTimestamp;
          ser.candle.update({ ...c, time: t });
          ser.line.update({ time: t, value: c.close });
          ser.volume.update({ time: t, value: c.volume, color: c.close >= c.open ? "#1e5a4f" : "#6b2d33" });
        }
      }

      const lk = emptyLookup();
      for (const c of cs) lk.candles.set(c.time, c);
      for (const m of MAS) {
        const pts = sma(closes, times, m.period);
        ser.ma[m.key].setData(ts(pts));
        lk.ma[m.key] = toMap(pts);
      }
      const md = macd(closes, times);
      ser.macdLine.setData(ts(md.macd));
      ser.macdSignal.setData(ts(md.signal));
      ser.macdHist.setData(
        md.hist.map((h) => ({ time: h.time as UTCTimestamp, value: h.value, color: h.value >= 0 ? UP : DOWN }))
      );
      lk.macd = toMap(md.macd);
      lk.signal = toMap(md.signal);
      lk.hist = toMap(md.hist);
      const st = stochRsi(closes, times);
      ser.stochK.setData(ts(st.k));
      ser.stochD.setData(ts(st.d));
      lk.k = toMap(st.k);
      lk.d = toMap(st.d);
      lk.lastTime = times.length ? times[times.length - 1] : null;
      lookupRef.current = lk;
      setVersion((v) => v + 1);
    }

    async function request(limit: number) {
      const res = await fetch(`/api/candles?symbol=${encodeURIComponent(symbol)}&interval=${interval}&limit=${limit}`, {
        cache: "no-store",
      });
      const d = await res.json();
      if (!res.ok || d.error) throw new Error(d.error ?? "Feed error");
      return d as { provider: string; fresh: boolean; fetchedAt: number; candles: Candle[] };
    }

    async function initial() {
      try {
        const d = await request(500);
        if (cancelled) return;
        candlesRef.current = d.candles;
        setFeed({ provider: d.provider, fresh: d.fresh, fetchedAt: d.fetchedAt });
        setError("");
        paint(true, []);
        chartRef.current?.timeScale().fitContent();
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Could not reach the price feed.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    async function poll() {
      if (document.hidden || candlesRef.current.length === 0) return;
      try {
        const d = await request(3);
        if (cancelled) return;
        const changed: Candle[] = [];
        for (const c of d.candles) {
          const last = candlesRef.current[candlesRef.current.length - 1];
          if (last && c.time === last.time) {
            candlesRef.current[candlesRef.current.length - 1] = c;
            changed.push(c);
          } else if (!last || c.time > last.time) {
            candlesRef.current.push(c);
            changed.push(c);
          }
        }
        if (candlesRef.current.length > 1500) candlesRef.current = candlesRef.current.slice(-1000);
        setFeed({ provider: d.provider, fresh: d.fresh, fetchedAt: d.fetchedAt });
        setError("");
        if (changed.length) paint(false, changed);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Could not reach the price feed.");
      }
    }

    initial();
    const timer = setInterval(poll, 5000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [symbol, interval]);

  const lk = lookupRef.current;
  const t = hoverTime !== null && lk.candles.has(hoverTime) ? hoverTime : lk.lastTime;
  const c = t !== null ? lk.candles.get(t) : undefined;
  const dec = c ? dp(c.close) : 2;
  const f = (n: number | undefined, d = dec) => (n === undefined ? "-" : n.toFixed(d));
  const stamp = t !== null ? new Date(t * 1000).toLocaleString() : "";
  const chg = c ? c.close - c.open : 0;

  return (
    <div className="flex h-full min-h-[560px] flex-col rounded-xl border border-cyan-400/20 bg-[#050b18]">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 border-b border-cyan-400/10 px-3 py-2 text-xs">
        <span className="font-semibold text-cyan-200">{symbol}</span>
        <span className="text-cyan-100/60">{interval}</span>
        {c && (
          <span className="tabular-nums text-cyan-100/80">
            O {f(c.open)} H {f(c.high)} L {f(c.low)} C{" "}
            <span className={chg >= 0 ? "text-green-400" : "text-red-400"}>{f(c.close)}</span>{" "}
            <span className="text-cyan-100/40">Vol {c.volume.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
          </span>
        )}
        {stamp && <span className="text-cyan-100/40">{stamp}</span>}
        <span className="ml-auto flex items-center gap-2">
          <button
            onClick={() => setKind(kind === "candles" ? "line" : "candles")}
            className="rounded border border-cyan-400/30 px-2 py-0.5 text-cyan-100/80 hover:bg-cyan-400/10"
          >
            {kind === "candles" ? "Candles" : "Line"}
          </button>
          <button
            onClick={() => chartRef.current?.timeScale().fitContent()}
            className="rounded border border-cyan-400/30 px-2 py-0.5 text-cyan-100/80 hover:bg-cyan-400/10"
          >
            Reset zoom
          </button>
        </span>
      </div>

      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 px-3 py-1 text-xs tabular-nums">
        {MAS.map((m) => (
          <label key={m.key} className="flex cursor-pointer items-center gap-1" style={{ color: m.color }}>
            <input type="checkbox" checked={!!showMa[m.key]} onChange={() => setShowMa((s) => ({ ...s, [m.key]: !s[m.key] }))} />
            MA {m.period} {t !== null ? f(lk.ma[m.key]?.get(t)) : ""}
          </label>
        ))}
        <label className="flex cursor-pointer items-center gap-1 text-cyan-100/60">
          <input type="checkbox" checked={showVol} onChange={() => setShowVol(!showVol)} />
          Volume
        </label>
      </div>

      <div className="relative min-h-0 flex-1">
        <div ref={boxRef} className="absolute inset-0" />
        {loading && <div className="absolute left-3 top-3 text-xs text-cyan-100/60">Loading candles...</div>}
        {error && !loading && (
          <div className="absolute left-3 top-3 rounded bg-red-500/10 px-2 py-1 text-xs text-red-300">
            {error} Showing the last data received, if any.
          </div>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-cyan-400/10 px-3 py-1 text-xs tabular-nums">
        <span className="text-cyan-100/50">MACD (12, 26, 9)</span>
        <span style={{ color: "#3b82f6" }}>{t !== null ? f(lk.macd.get(t), 4) : "-"}</span>
        <span style={{ color: "#e0a82e" }}>{t !== null ? f(lk.signal.get(t), 4) : "-"}</span>
        <span className={(lk.hist.get(t ?? -1) ?? 0) >= 0 ? "text-green-400" : "text-red-400"}>
          {t !== null ? f(lk.hist.get(t), 4) : "-"}
        </span>
        <span className="text-cyan-100/50">Stoch RSI (14, 14, 3, 3)</span>
        <span style={{ color: "#3b9bff" }}>{t !== null ? f(lk.k.get(t), 2) : "-"}</span>
        <span style={{ color: "#ff8a1f" }}>{t !== null ? f(lk.d.get(t), 2) : "-"}</span>
        <span className="ml-auto text-cyan-100/50">
          {feed ? `${feed.provider}. ${feed.fresh ? "Fresh" : "STALE"}. Updated ${new Date(feed.fetchedAt).toLocaleTimeString()}` : "No data yet"}
        </span>
      </div>
    </div>
  );
}
