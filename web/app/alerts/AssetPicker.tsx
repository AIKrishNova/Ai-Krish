"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  BINANCE_TIMEFRAMES,
  CATALOGUE,
  CLASS_LABEL,
  CLASS_ORDER,
  getStatus,
  search,
  STATUS_LABEL,
  type Asset,
  type AssetClass,
  type AssetStatus,
} from "../../lib/catalogue";
import {
  ASSET_NAMES,
  PRIORITY_QUOTES,
  searchMarkets,
  type BinanceMarket,
} from "../../lib/binanceMarkets";

type Catalogue = {
  markets: BinanceMarket[];
  quotes: { quote: string; count: number }[];
  fetchedAt: number;
  stale: boolean;
  staleReason?: string;
  source: string;
  excluded: number;
};

const SHOW_LIMIT = 200;
const RELOAD_AFTER_MS = 5 * 60 * 1000;

const BADGE: Record<AssetStatus, string> = {
  live: "border-green-400/40 bg-green-500/10 text-green-300",
  provider_required: "border-yellow-300/40 bg-yellow-400/10 text-yellow-200",
  reference_only: "border-slate-400/30 bg-slate-400/10 text-slate-300",
};
const DOT: Record<AssetStatus, string> = {
  live: "bg-green-400",
  provider_required: "bg-yellow-300",
  reference_only: "bg-slate-400",
};

const STATIC_COUNTS = Object.fromEntries(
  CLASS_ORDER.map((c) => [c, CATALOGUE.filter((a) => a.assetClass === c).length])
) as Record<AssetClass, number>;

function marketToAsset(m: BinanceMarket): Asset {
  return {
    id: "binance:" + m.symbol,
    name: m.display,
    assetClass: "crypto",
    providerSymbol: m.symbol,
    provider: "binance",
    isOtcOrSynthetic: false,
    mapping: "provider_symbol_verified",
    modes: ["fixed-time"],
    refSymbol: m.symbol,
    timeframes: BINANCE_TIMEFRAMES,
    platformVerified: false,
    note: "Binance spot market price. Not an Olymp Trade quote.",
  };
}

export default function AssetPicker({
  selectedId,
  symbol,
  onSelect,
}: {
  selectedId: string;
  symbol?: string;
  onSelect: (asset: Asset) => void;
}) {
  const [cls, setCls] = useState<AssetClass | "all">("all");
  const [quote, setQuote] = useState("all");
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const [cat, setCat] = useState<Catalogue | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "ready" | "error">("idle");
  const [error, setError] = useState("");
  const loadedAt = useRef(0);
  const boxRef = useRef<HTMLDivElement>(null);

  const load = useCallback(async (silent: boolean) => {
    if (!silent) setStatus("loading");
    try {
      const res = await fetch("/api/assets?provider=binance&category=crypto&limit=5000", { cache: "no-store" });
      const d = await res.json();
      if (!res.ok || d.error) throw new Error(d.error ?? "Catalogue request failed.");
      setCat({
        markets: d.markets,
        quotes: d.quotes,
        fetchedAt: d.fetchedAt,
        stale: !!d.stale,
        staleReason: d.staleReason,
        source: d.source,
        excluded: d.excluded ?? 0,
      });
      loadedAt.current = Date.now();
      setError("");
      setStatus("ready");
    } catch (e) {
      // Keep any catalogue we already have (it is flagged with its own refresh time). Never invent markets.
      setError(e instanceof Error ? e.message : "Could not load the Binance catalogue.");
      if (!silent || !cat) setStatus("error");
    }
  }, [cat]);

  useEffect(() => {
    if (!open) return;
    if (status === "idle") load(false);
    else if (status === "ready" && Date.now() - loadedAt.current > RELOAD_AFTER_MS) load(true);
  }, [open, status, load]);

  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const isBinanceId = selectedId.startsWith("binance:");
  const staticSelected = CATALOGUE.find((a) => a.id === selectedId);
  const dynamicSelected = useMemo(
    () => (isBinanceId && cat ? cat.markets.find((m) => "binance:" + m.symbol === selectedId) ?? null : null),
    [isBinanceId, cat, selectedId]
  );
  const label = dynamicSelected
    ? dynamicSelected.display
    : staticSelected
    ? staticSelected.name
    : isBinanceId
    ? selectedId.slice("binance:".length)
    : symbol ?? "Select asset";
  const dot: AssetStatus | null = staticSelected ? getStatus(staticSelected) : isBinanceId ? "live" : null;

  // Quote filter list: top quotes by market count, plus the named ones whenever they exist.
  const quoteOptions = useMemo(() => {
    if (!cat) return [];
    return cat.quotes.filter((x, i) => i < 20 || PRIORITY_QUOTES.includes(x.quote));
  }, [cat]);

  const showCrypto = cls === "all" || cls === "crypto";
  const marketMatches = useMemo(
    () => (cat && showCrypto ? searchMarkets(cat.markets, q, quote === "all" ? "" : quote) : []),
    [cat, showCrypto, q, quote]
  );
  const staticMatches = useMemo(() => (quote === "all" ? search(q, cls) : []), [q, cls, quote]);

  function choose(a: Asset) {
    onSelect(a);
    setOpen(false);
    setQ("");
  }

  const cryptoCount = cat ? cat.markets.length : null;
  const nothing = marketMatches.length === 0 && staticMatches.length === 0 && status !== "loading";

  return (
    <div ref={boxRef} className="relative flex flex-wrap items-center gap-2">
      <select
        value={cls}
        onChange={(ev) => setCls(ev.target.value as AssetClass | "all")}
        aria-label="Asset category"
        className="rounded-lg border border-cyan-400/30 bg-black/40 px-3 py-2 text-sm"
      >
        <option value="all">All categories</option>
        {CLASS_ORDER.map((c) => (
          <option key={c} value={c}>
            {CLASS_LABEL[c]} ({c === "crypto" ? (cryptoCount ?? "Binance spot") : STATIC_COUNTS[c]})
          </option>
        ))}
      </select>

      {cat && showCrypto && (
        <select
          value={quote}
          onChange={(ev) => setQuote(ev.target.value)}
          aria-label="Quote currency"
          className="rounded-lg border border-cyan-400/30 bg-black/40 px-3 py-2 text-sm"
        >
          <option value="all">All quote currencies</option>
          {quoteOptions.map((x) => (
            <option key={x.quote} value={x.quote}>
              {x.quote} ({x.count})
            </option>
          ))}
        </select>
      )}

      <button
        type="button"
        onClick={() => setOpen(!open)}
        aria-haspopup="listbox"
        aria-expanded={open}
        className="flex min-w-[14rem] items-center justify-between gap-2 rounded-lg border border-cyan-400/30 bg-black/40 px-3 py-2 text-left text-sm"
      >
        <span className="flex items-center gap-2">
          {dot && <span className={"h-2 w-2 rounded-full " + DOT[dot]} />}
          {label}
        </span>
        <span className="text-cyan-100/50">{open ? "\u25B2" : "\u25BC"}</span>
      </button>

      {open && (
        <div className="absolute left-0 top-full z-30 mt-1 w-[28rem] max-w-[92vw] rounded-xl border border-cyan-400/30 bg-[#07101f] shadow-xl">
          <input
            autoFocus
            value={q}
            onChange={(ev) => setQ(ev.target.value)}
            placeholder="Search symbol or name, e.g. ETH, SOLUSDT, bitcoin, EURUSD"
            className="w-full rounded-t-xl border-b border-cyan-400/20 bg-black/40 px-3 py-2 text-sm outline-none"
          />

          <div className="border-b border-cyan-400/10 px-3 py-1.5 text-[11px] text-cyan-100/60">
            {status === "loading" && "Loading the Binance spot catalogue..."}
            {cat && (
              <>
                {cat.markets.length.toLocaleString()} Binance spot markets discovered. Last refresh{" "}
                {new Date(cat.fetchedAt).toLocaleTimeString()}.
              </>
            )}
            {cat?.stale && (
              <span className="ml-1 text-yellow-300">
                Showing the last successful catalogue. {cat.staleReason}
              </span>
            )}
            {error && (
              <span className="ml-1 text-red-300">
                {error}{" "}
                <button type="button" onClick={() => load(false)} className="underline">
                  Retry
                </button>
              </span>
            )}
          </div>

          <div role="listbox" className="max-h-80 overflow-y-auto py-1">
            {nothing && (
              <div className="px-3 py-3 text-sm text-cyan-100/50">
                {status === "error" && !cat
                  ? "No live Binance markets are available right now. Other categories remain listed for reference."
                  : "No assets match this search."}
              </div>
            )}

            {CLASS_ORDER.map((c) => {
              if (c === "crypto") {
                if (marketMatches.length === 0) return null;
                const shown = marketMatches.slice(0, SHOW_LIMIT);
                return (
                  <div key={c}>
                    <div className="sticky top-0 bg-[#07101f] px-3 pb-1 pt-2 text-xs text-cyan-300/80">
                      {CLASS_LABEL[c]}, Binance spot ({marketMatches.length.toLocaleString()})
                    </div>
                    {shown.map((m) => {
                      const id = "binance:" + m.symbol;
                      return (
                        <button
                          type="button"
                          role="option"
                          aria-selected={id === selectedId}
                          key={id}
                          onClick={() => choose(marketToAsset(m))}
                          className={
                            "flex w-full items-center justify-between gap-2 px-3 py-1.5 text-left text-sm hover:bg-cyan-400/10 " +
                            (id === selectedId ? "bg-cyan-400/10" : "")
                          }
                        >
                          <span>
                            <span className="font-medium">{m.display}</span>
                            <span className="ml-2 text-xs text-cyan-100/40">{m.symbol}</span>
                            <span className="block text-[11px] text-cyan-100/40">
                              Base {m.base}
                              {ASSET_NAMES[m.base] ? " (" + ASSET_NAMES[m.base] + ")" : ""}, quote {m.quote}
                            </span>
                          </span>
                          <span className={"shrink-0 rounded border px-1.5 py-0.5 text-[10px] " + BADGE.live}>
                            {STATUS_LABEL.live}
                          </span>
                        </button>
                      );
                    })}
                    {marketMatches.length > SHOW_LIMIT && (
                      <div className="px-3 py-1 text-[11px] text-cyan-100/50">
                        Showing the first {SHOW_LIMIT} of {marketMatches.length.toLocaleString()}. Type more of the
                        symbol, or pick a quote currency, to narrow the list.
                      </div>
                    )}
                  </div>
                );
              }
              const group = staticMatches.filter((a) => a.assetClass === c);
              if (group.length === 0) return null;
              return (
                <div key={c}>
                  <div className="sticky top-0 bg-[#07101f] px-3 pb-1 pt-2 text-xs text-cyan-300/80">{CLASS_LABEL[c]}</div>
                  {group.map((a) => {
                    const s = getStatus(a);
                    return (
                      <button
                        type="button"
                        role="option"
                        aria-selected={a.id === selectedId}
                        key={a.id}
                        onClick={() => choose(a)}
                        className={
                          "flex w-full items-center justify-between gap-2 px-3 py-1.5 text-left text-sm hover:bg-cyan-400/10 " +
                          (a.id === selectedId ? "bg-cyan-400/10" : "")
                        }
                      >
                        <span>
                          {a.name}
                          {a.refSymbol && <span className="ml-2 text-xs text-cyan-100/40">{a.refSymbol}</span>}
                        </span>
                        <span className={"shrink-0 rounded border px-1.5 py-0.5 text-[10px] " + BADGE[s]}>
                          {STATUS_LABEL[s]}
                        </span>
                      </button>
                    );
                  })}
                </div>
              );
            })}
          </div>

          <div className="border-t border-cyan-400/20 px-3 py-2 text-[11px] text-cyan-100/50">
            Binance prices are Binance spot prices, not Olymp Trade prices. Olymp Trade availability is not verified for
            any listed asset. Only Binance spot is integrated.
          </div>
        </div>
      )}
    </div>
  );
}
