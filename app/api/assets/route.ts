import { requireUser } from "../../../lib/auth";
import { NextResponse } from "next/server";
import { getBinanceCatalogue } from "../../../lib/binanceCatalogue";
import { quoteCounts, searchMarkets } from "../../../lib/binanceMarkets";

// GET /api/assets?provider=binance&category=crypto&search=eth&quote=USDT&limit=100&offset=0
// Only Binance spot is integrated. No Next.js segment config is exported (cacheComponents).
export async function GET(req: Request) {
  const session = await requireUser();
  if (!session.ok) return Response.json({ error: session.error }, { status: session.status });
  const u = new URL(req.url);
  const provider = (u.searchParams.get("provider") ?? "binance").toLowerCase();
  if (provider !== "binance") {
    return NextResponse.json(
      { error: "Unsupported provider. Only 'binance' (spot) is integrated." },
      { status: 400 }
    );
  }

  const category = (u.searchParams.get("category") ?? "crypto").toLowerCase();
  const search = (u.searchParams.get("search") ?? "").slice(0, 40);
  const quote = (u.searchParams.get("quote") ?? "").toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 12);
  const limit = Math.min(Math.max(Math.floor(Number(u.searchParams.get("limit"))) || 100, 1), 5000);
  const offset = Math.max(Math.floor(Number(u.searchParams.get("offset"))) || 0, 0);

  const cat = await getBinanceCatalogue();
  if (!cat.snapshot) {
    const err = cat.error;
    const status = err?.code === "rate_limited" ? 429 : 502;
    return NextResponse.json(
      {
        provider: "binance",
        error: err?.message ?? "Binance catalogue unavailable.",
        code: err?.code ?? "network",
        markets: [],
      },
      {
        status,
        headers: err?.retryAfterMs ? { "Retry-After": String(Math.ceil(err.retryAfterMs / 1000)) } : undefined,
      }
    );
  }

  const snap = cat.snapshot;
  const base = {
    provider: "binance",
    source: snap.source,
    fetchedAt: snap.fetchedAt,
    stale: cat.stale,
    staleReason: cat.stale ? cat.error?.message ?? "Catalogue refresh is overdue." : undefined,
    totalMarkets: snap.markets.length,
    excluded: snap.excluded,
    quotes: quoteCounts(snap.markets),
    category,
  };

  // Binance spot only lists cryptocurrencies. Other categories are not available from this provider.
  if (category !== "crypto") {
    return NextResponse.json({
      ...base,
      total: 0,
      offset,
      limit,
      markets: [],
      note: "Binance spot only provides cryptocurrency markets.",
    });
  }

  const matches = searchMarkets(snap.markets, search, quote);
  return NextResponse.json({
    ...base,
    total: matches.length,
    offset,
    limit,
    markets: matches.slice(offset, offset + limit),
    note: matches.length === 0 ? "No Binance spot markets match this search." : undefined,
  });
}
