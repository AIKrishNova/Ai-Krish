// Provider-aware instrument catalogue for Jarvis.
//
// Rules this file enforces:
//  - "name" is what you see; "providerSymbol" is what a data provider understands. They are separate.
//  - "refSymbol" is an informational market ticker only. It is NEVER sent to a data provider.
//  - Only instruments with an integrated provider AND a verified provider symbol are "live".
//  - Live Binance spot markets are NOT listed here. They are discovered at runtime from Binance
//    (see lib/binanceCatalogue.ts and /api/assets), so this list never claims a live market on its own.
//  - Olymp Trade has no public, documented price feed. No entry here has been verified as
//    available on Olymp Trade (platformVerified is false everywhere).
//  - Broker-specific OTC and composite instruments are "reference_only". They are never
//    mapped to Binance or any other lookalike price.

export type AssetClass =
  | "forex" | "stock" | "crypto" | "metal" | "commodity"
  | "index" | "etf" | "otc" | "composite";

export type ProviderId = "binance" | null;

export type MappingStatus =
  | "provider_symbol_verified" // symbol exists on that provider's own market
  | "unverified";              // listed for reference only, no feed

export const BINANCE_TIMEFRAMES = ["1m", "3m", "5m", "15m", "30m", "1h", "4h", "1d"] as const;
export type Timeframe = (typeof BINANCE_TIMEFRAMES)[number];

export interface Asset {
  id: string;
  name: string;
  assetClass: AssetClass;
  providerSymbol: string | null;
  provider: ProviderId;
  isOtcOrSynthetic: boolean;
  mapping: MappingStatus;
  modes: ("fixed-time" | "inzone" | "forex" | "stocks")[];
  note?: string;
  refSymbol?: string;              // informational ticker, never used for provider requests
  exchange?: string;               // informational
  timeframes?: readonly Timeframe[];
  platformVerified?: boolean;      // true only if availability on Olymp Trade was verified
}

export type AssetStatus = "live" | "provider_required" | "reference_only";

export const STATUS_LABEL: Record<AssetStatus, string> = {
  live: "Live market data available",
  provider_required: "Provider integration required",
  reference_only: "Reference only",
};

export const CLASS_LABEL: Record<AssetClass, string> = {
  forex: "Forex currency pairs",
  stock: "Stocks",
  crypto: "Cryptocurrencies",
  metal: "Metals",
  commodity: "Commodities",
  index: "Stock indices",
  etf: "ETFs",
  otc: "OTC assets",
  composite: "Composite and synthetic indices",
};

export const CLASS_ORDER: AssetClass[] = [
  "forex", "stock", "crypto", "metal", "commodity", "index", "etf", "otc", "composite",
];

// --- builders -------------------------------------------------------------

const ref = (
  id: string,
  name: string,
  assetClass: AssetClass,
  refSymbol?: string,
  exchange?: string
): Asset => ({
  id,
  name,
  assetClass,
  providerSymbol: null,
  provider: null,
  isOtcOrSynthetic: assetClass === "otc" || assetClass === "composite",
  mapping: "unverified",
  modes: [],
  refSymbol,
  exchange,
  platformVerified: false,
});

const FOREX: [string, string][] = [
  ["eurusd", "EUR/USD"], ["gbpusd", "GBP/USD"], ["usdjpy", "USD/JPY"], ["eurgbp", "EUR/GBP"],
  ["audusd", "AUD/USD"], ["usdcad", "USD/CAD"], ["usdchf", "USD/CHF"], ["nzdusd", "NZD/USD"],
  ["eurjpy", "EUR/JPY"], ["gbpjpy", "GBP/JPY"], ["eurchf", "EUR/CHF"], ["audjpy", "AUD/JPY"],
  ["euraud", "EUR/AUD"], ["audcad", "AUD/CAD"], ["cadjpy", "CAD/JPY"], ["chfjpy", "CHF/JPY"],
  ["gbpcad", "GBP/CAD"], ["gbpaud", "GBP/AUD"], ["gbpchf", "GBP/CHF"], ["eurcad", "EUR/CAD"],
];

const STOCKS: [string, string, string, string][] = [
  ["aapl", "Apple", "AAPL", "NASDAQ"], ["msft", "Microsoft", "MSFT", "NASDAQ"],
  ["nvda", "NVIDIA", "NVDA", "NASDAQ"], ["tsla", "Tesla", "TSLA", "NASDAQ"],
  ["amzn", "Amazon", "AMZN", "NASDAQ"], ["googl", "Alphabet (Google)", "GOOGL", "NASDAQ"],
  ["meta", "Meta", "META", "NASDAQ"], ["nflx", "Netflix", "NFLX", "NASDAQ"],
  ["amd", "AMD", "AMD", "NASDAQ"], ["intc", "Intel", "INTC", "NASDAQ"],
  ["sbux", "Starbucks", "SBUX", "NASDAQ"], ["v", "Visa", "V", "NYSE"],
  ["ma", "Mastercard", "MA", "NYSE"], ["jpm", "JPMorgan Chase", "JPM", "NYSE"],
  ["ba", "Boeing", "BA", "NYSE"], ["dis", "Disney", "DIS", "NYSE"],
  ["ko", "Coca-Cola", "KO", "NYSE"], ["mcd", "McDonald's", "MCD", "NYSE"],
  ["nke", "Nike", "NKE", "NYSE"], ["wmt", "Walmart", "WMT", "NYSE"],
  ["pfe", "Pfizer", "PFE", "NYSE"], ["jnj", "Johnson & Johnson", "JNJ", "NYSE"],
];

const METALS: [string, string, string][] = [
  ["gold", "Gold", "XAUUSD"], ["silver", "Silver", "XAGUSD"],
  ["platinum", "Platinum", "XPTUSD"], ["palladium", "Palladium", "XPDUSD"],
];

const COMMODITIES: [string, string, string][] = [
  ["wti", "Crude oil (WTI)", "WTI"], ["brent", "Brent oil", "BRENT"], ["natgas", "Natural gas", "NATGAS"],
];

const INDICES: [string, string, string][] = [
  ["ndx", "NASDAQ 100", "NDX"], ["spx", "S&P 500", "SPX"], ["dji", "Dow Jones", "DJI"],
  ["dax", "DAX 40", "DAX"], ["ftse", "FTSE 100", "FTSE"], ["cac", "CAC 40", "CAC"],
  ["n225", "Nikkei 225", "N225"], ["hsi", "Hang Seng", "HSI"], ["sx5e", "Euro Stoxx 50", "SX5E"],
  ["asx", "ASX 200", "ASX200"],
];

const ETFS: [string, string, string][] = [
  ["spy", "SPDR S&P 500 ETF", "SPY"], ["qqq", "Invesco QQQ", "QQQ"],
  ["iwm", "iShares Russell 2000", "IWM"], ["gld", "SPDR Gold Shares", "GLD"],
  ["slv", "iShares Silver Trust", "SLV"], ["eem", "iShares MSCI Emerging Markets", "EEM"],
  ["uso", "United States Oil Fund", "USO"],
];

// OTC variants are broker-specific. They carry no ticker on purpose.
const OTC: [string, string][] = [
  ["eurusd-otc", "EUR/USD OTC"], ["gbpusd-otc", "GBP/USD OTC"], ["usdjpy-otc", "USD/JPY OTC"],
  ["audusd-otc", "AUD/USD OTC"], ["eurgbp-otc", "EUR/GBP OTC"], ["usdcad-otc", "USD/CAD OTC"],
  ["btc-otc", "Bitcoin OTC"], ["eth-otc", "Ethereum OTC"], ["gold-otc", "Gold OTC"],
  ["silver-otc", "Silver OTC"], ["aapl-otc", "Apple OTC"], ["tsla-otc", "Tesla OTC"],
];

const COMPOSITE: [string, string][] = [
  ["asia-comp", "Asia Composite Index"], ["metal-comp", "Metal Composite Index"],
  ["oil-comp", "Oil Composite Index"], ["crypto-comp", "Crypto Composite Index"],
  ["compound", "Compound Index"],
];

export const CATALOGUE: Asset[] = [
  ...FOREX.map(([id, n]) => ref(id, n, "forex", n.replace("/", ""))),
  ...STOCKS.map(([id, n, t, ex]) => ref(id, n, "stock", t, ex)),
  ...METALS.map(([id, n, t]) => ref(id, n, "metal", t)),
  ...COMMODITIES.map(([id, n, t]) => ref(id, n, "commodity", t)),
  ...INDICES.map(([id, n, t]) => ref(id, n, "index", t)),
  ...ETFS.map(([id, n, t]) => ref(id, n, "etf", t)),
  ...OTC.map(([id, n]) => ref(id, n, "otc")),
  ...COMPOSITE.map(([id, n]) => ref(id, n, "composite")),
];

// --- helpers (signatures unchanged) ---------------------------------------

export const isLive = (a: Asset) =>
  a.provider !== null && a.providerSymbol !== null && a.mapping === "provider_symbol_verified";

export function getStatus(a: Asset): AssetStatus {
  if (isLive(a)) return "live";
  return a.isOtcOrSynthetic ? "reference_only" : "provider_required";
}

export function unavailableReason(a: Asset): string | null {
  const s = getStatus(a);
  if (s === "live") return null;
  if (s === "reference_only") {
    return "Reference only. This is a broker-specific OTC or composite instrument with no public data feed, and its availability on Olymp Trade has not been verified. Live candles need an authorized provider that supplies this exact instrument.";
  }
  return "Provider integration required. Live candles need a compatible, authorized market-data provider for this instrument, and none is connected. Its availability on Olymp Trade has not been verified.";
}

const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9]/g, "");

export function search(q: string, cls?: AssetClass | "all"): Asset[] {
  const raw = q.trim().toLowerCase();
  const n = norm(q);
  return CATALOGUE.filter((a) => {
    if (cls && cls !== "all" && a.assetClass !== cls) return false;
    if (!raw) return true;
    return (
      a.name.toLowerCase().includes(raw) ||
      (a.providerSymbol ?? "").toLowerCase().includes(raw) ||
      (n.length > 0 &&
        (norm(a.name).includes(n) || norm(a.refSymbol ?? "").includes(n) || norm(a.providerSymbol ?? "").includes(n)))
    );
  });
}
