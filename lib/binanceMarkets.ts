// Shared (browser + server) helpers for Binance spot markets.
// No imports on purpose, so it can be tested on its own.

export interface BinanceMarket {
  symbol: string;  // exact provider symbol used for API requests, e.g. BTCUSDT
  display: string; // readable form for the selector, e.g. BTC/USDT
  base: string;    // e.g. BTC
  quote: string;   // e.g. USDT
}

// Binance's exchangeInfo has tickers only, not full asset names. These aliases exist
// purely so "bitcoin" finds BTC pairs. They are search hints, not provider data.
export const ASSET_NAMES: Record<string, string> = {
  BTC: "Bitcoin", ETH: "Ethereum", BNB: "BNB", SOL: "Solana", XRP: "XRP Ripple",
  ADA: "Cardano", DOGE: "Dogecoin", DOT: "Polkadot", LINK: "Chainlink", AVAX: "Avalanche",
  TRX: "TRON", LTC: "Litecoin", BCH: "Bitcoin Cash", SHIB: "Shiba Inu", UNI: "Uniswap",
  ATOM: "Cosmos", XLM: "Stellar", ETC: "Ethereum Classic", NEAR: "NEAR Protocol",
  APT: "Aptos", FIL: "Filecoin", ARB: "Arbitrum", OP: "Optimism", TON: "Toncoin",
  PEPE: "Pepe", AAVE: "Aave", ALGO: "Algorand", HBAR: "Hedera", SUI: "Sui",
  INJ: "Injective", USDT: "Tether", USDC: "USD Coin", FDUSD: "First Digital USD", DAI: "Dai",
};

export const PRIORITY_QUOTES = ["USDT", "USDC", "BTC", "ETH", "BNB", "FDUSD"];

const SYMBOL_RE = /^[A-Z0-9]{5,20}$/;

export function parseExchangeInfo(json: unknown): { markets: BinanceMarket[]; ignored: number } | null {
  if (typeof json !== "object" || json === null) return null;
  const list = (json as { symbols?: unknown }).symbols;
  if (!Array.isArray(list) || list.length === 0) return null;

  const markets: BinanceMarket[] = [];
  const seen = new Set<string>();
  let ignored = 0;
  for (const item of list) {
    if (typeof item !== "object" || item === null) { ignored++; continue; }
    const o = item as Record<string, unknown>;
    const { symbol, baseAsset, quoteAsset } = o;
    if (
      typeof symbol !== "string" || typeof baseAsset !== "string" || typeof quoteAsset !== "string" ||
      !SYMBOL_RE.test(symbol)
    ) { ignored++; continue; }
    // Only confirmed, currently trading spot markets.
    if (o.status !== "TRADING" || o.isSpotTradingAllowed !== true) { ignored++; continue; }
    if (seen.has(symbol)) continue;
    seen.add(symbol);
    markets.push({ symbol, display: baseAsset + "/" + quoteAsset, base: baseAsset, quote: quoteAsset });
  }
  return markets.length > 0 ? { markets, ignored } : null;
}

const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9]/g, "");
const quoteRank = (q: string) => {
  const i = PRIORITY_QUOTES.indexOf(q);
  return i === -1 ? PRIORITY_QUOTES.length : i;
};

export function searchMarkets(markets: BinanceMarket[], query: string, quote?: string): BinanceMarket[] {
  const n = norm(query);
  const q = (quote ?? "").toUpperCase();
  const scored: { m: BinanceMarket; score: number }[] = [];
  for (const m of markets) {
    if (q && m.quote !== q) continue;
    let score = 0;
    if (n) {
      const sym = norm(m.symbol);
      const base = norm(m.base);
      const name = norm(ASSET_NAMES[m.base] ?? "");
      if (sym === n || base === n || name === n) score = 1;
      else if (sym.startsWith(n) || base.startsWith(n) || (name && name.startsWith(n))) score = 2;
      else if (sym.includes(n) || (name && name.includes(n))) score = 3;
      else continue;
    }
    scored.push({ m, score });
  }
  scored.sort(
    (a, b) =>
      a.score - b.score ||
      quoteRank(a.m.quote) - quoteRank(b.m.quote) ||
      (a.m.symbol < b.m.symbol ? -1 : a.m.symbol > b.m.symbol ? 1 : 0)
  );
  return scored.map((s) => s.m);
}

export function quoteCounts(markets: BinanceMarket[]): { quote: string; count: number }[] {
  const counts = new Map<string, number>();
  for (const m of markets) counts.set(m.quote, (counts.get(m.quote) ?? 0) + 1);
  return [...counts.entries()]
    .map(([quote, count]) => ({ quote, count }))
    .sort((a, b) => b.count - a.count || (a.quote < b.quote ? -1 : 1));
}
