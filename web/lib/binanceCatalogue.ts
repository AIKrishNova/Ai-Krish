// Server-side Binance spot catalogue.
//
//  - Source: Binance's official public exchangeInfo endpoint (permissions=SPOT).
//    The official market-data mirror is tried only if the main host is unreachable or refuses.
//  - Cached in memory for 10 minutes. Concurrent requests share one upstream call.
//  - Failures are remembered briefly so a broken or rate-limited feed is not hammered.
//  - On failure the last good catalogue is returned but flagged stale (never silently).
//    If there is no good catalogue, the caller gets an error. Nothing is ever made up.
//  - No Next.js route-segment config is used, so this is compatible with cacheComponents.

import { parseExchangeInfo, type BinanceMarket } from "./binanceMarkets";

const HOSTS = ["https://api.binance.com", "https://data-api.binance.vision"];
const PATH = "/api/v3/exchangeInfo?permissions=SPOT";
const TTL_MS = 10 * 60 * 1000;
const MAX_STALE_MS = 24 * 60 * 60 * 1000;
const FAIL_BACKOFF_MS = 30 * 1000;
const TIMEOUT_MS = 10_000;

export type CatalogueErrorCode = "timeout" | "rate_limited" | "http_error" | "invalid_response" | "network";

export interface CatalogueError {
  code: CatalogueErrorCode;
  message: string;
  at: number;
  retryAfterMs?: number;
}

export interface Snapshot {
  markets: BinanceMarket[];
  symbols: Set<string>;
  fetchedAt: number;
  source: string;  // host that served this catalogue
  excluded: number; // symbols returned but not confirmed as trading spot markets
}

export interface CatalogueResult {
  snapshot: Snapshot | null;
  stale: boolean;
  error: CatalogueError | null;
}

let snapshot: Snapshot | null = null;
let lastError: CatalogueError | null = null;
let nextAttemptAt = 0;
let inflight: Promise<void> | null = null;

function fail(error: CatalogueError, backoffMs: number) {
  lastError = error;
  nextAttemptAt = Date.now() + backoffMs;
}

async function refresh(): Promise<void> {
  let last: CatalogueError | null = null;
  for (const host of HOSTS) {
    let res: Response;
    try {
      res = await fetch(host + PATH, {
        cache: "no-store",
        signal: AbortSignal.timeout(TIMEOUT_MS),
        headers: { Accept: "application/json" },
      });
    } catch (e) {
      const timedOut = e instanceof Error && (e.name === "TimeoutError" || e.name === "AbortError");
      last = {
        code: timedOut ? "timeout" : "network",
        message: timedOut ? host + " did not answer within 10 seconds." : "Could not reach " + host + ".",
        at: Date.now(),
      };
      continue;
    }

    if (res.status === 429 || res.status === 418) {
      const ra = Number(res.headers.get("retry-after"));
      const wait = Number.isFinite(ra) && ra > 0 ? ra * 1000 : 60_000;
      fail(
        { code: "rate_limited", message: "Binance rate limit reached (HTTP " + res.status + "). Retrying later.", at: Date.now(), retryAfterMs: wait },
        wait
      );
      return;
    }
    if (!res.ok) {
      last = { code: "http_error", message: host + " returned HTTP " + res.status + ".", at: Date.now() };
      continue;
    }

    let json: unknown;
    try {
      json = await res.json();
    } catch {
      last = { code: "invalid_response", message: host + " returned data that is not valid JSON.", at: Date.now() };
      continue;
    }
    const parsed = parseExchangeInfo(json);
    if (!parsed) {
      last = {
        code: "invalid_response",
        message: host + " returned an unexpected catalogue format or no trading spot markets.",
        at: Date.now(),
      };
      continue;
    }

    snapshot = {
      markets: parsed.markets,
      symbols: new Set(parsed.markets.map((m) => m.symbol)),
      fetchedAt: Date.now(),
      source: host,
      excluded: parsed.ignored,
    };
    lastError = null;
    nextAttemptAt = 0;
    return;
  }
  fail(last ?? { code: "network", message: "Binance catalogue unavailable.", at: Date.now() }, FAIL_BACKOFF_MS);
}

export async function getBinanceCatalogue(): Promise<CatalogueResult> {
  const now = Date.now();
  const fresh = snapshot !== null && now - snapshot.fetchedAt < TTL_MS;
  if (!fresh && now >= nextAttemptAt) {
    if (!inflight) {
      inflight = refresh().finally(() => {
        inflight = null;
      });
    }
    await inflight;
  }

  const age = snapshot ? Date.now() - snapshot.fetchedAt : Infinity;
  if (snapshot && age < MAX_STALE_MS) {
    const stale = age >= TTL_MS;
    return { snapshot, stale, error: stale ? lastError : null };
  }
  return {
    snapshot: null,
    stale: false,
    error: lastError ?? { code: "network", message: "Binance catalogue has not loaded yet.", at: Date.now() },
  };
}
