import { requireUser } from "../../../lib/auth";
import { evaluate, INTERVAL_MS, type Candle, type Result } from "../../../lib/market";

export async function GET(req: Request) {
  const session = await requireUser();
  if (!session.ok) return Response.json({ error: session.error }, { status: session.status });
  try {
    const { searchParams } = new URL(req.url);
    const symbol = (searchParams.get("symbol") || "BTCUSDT").toUpperCase();
    const interval = searchParams.get("interval") || "1m";
    if (!/^[A-Z0-9]{5,12}$/.test(symbol) || !INTERVAL_MS[interval]) {
      return Response.json({ error: "Invalid symbol or timeframe." }, { status: 400 });
    }
    const url = `https://data-api.binance.vision/api/v3/klines?symbol=${symbol}&interval=${interval}&limit=300`;
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) {
      return Response.json({ error: `Price feed error ${res.status}. Check the symbol name.` }, { status: 502 });
    }
    const rows = (await res.json()) as unknown[][];
    const all: Candle[] = rows.map((r) => ({
      t: Number(r[0]),
      o: parseFloat(r[1] as string),
      h: parseFloat(r[2] as string),
      l: parseFloat(r[3] as string),
      c: parseFloat(r[4] as string),
      v: parseFloat(r[5] as string),
    }));
    const bad = all.find(
      (c) =>
        ![c.o, c.h, c.l, c.c].every(Number.isFinite) ||
        c.h < Math.max(c.o, c.c, c.l) ||
        c.l > Math.min(c.o, c.c, c.h)
    );
    if (bad || all.length < 2) {
      return Response.json({ error: "Invalid candle data received from the price feed." }, { status: 502 });
    }

    const forming = all[all.length - 1];
    const fresh = Date.now() - forming.t < 2 * INTERVAL_MS[interval];
    let early: Result = evaluate(all); // includes the forming candle: provisional
    let confirmed: Result = evaluate(all.slice(0, -1)); // closed candles only
    if (!fresh) {
      const stale = "Data is stale (check your internet connection and Mac clock)";
      early = { ...early, direction: "NONE", failures: [stale, ...early.failures] };
      confirmed = { ...confirmed, direction: "NONE", failures: [stale, ...confirmed.failures] };
    }
    return Response.json({
      symbol,
      interval,
      source: "Binance public market data (crypto, live)",
      fetchedAt: Date.now(),
      fresh,
      price: forming.c,
      formingTime: forming.t,
      early,
      confirmed,
    });
  } catch (e) {
    return Response.json({ error: e instanceof Error ? e.message : "Unknown error" }, { status: 500 });
  }
}
