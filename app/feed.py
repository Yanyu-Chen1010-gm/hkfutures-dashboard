"""
Market data feed for HK futures.

Design goal: a client-support dashboard must NOT depend on a third-party
feed being alive. So this module exposes a single `get_market()` that:

  1. tries a live provider (async, short timeout),
  2. gracefully falls back to a deterministic DEMO feed,
  3. always returns a labelled dict so the UI can show which source is live.

Replace `LIVE_BASES` with your licensed/real provider (e.g. an HKEX
real-time API key) when you have one; the consumers don't change.

For the demo, the "price" is the underlying index level; the futures price
is derived as index + basis. In production you'd pull the actual front-month
future quote.
"""
from __future__ import annotations

import asyncio
import math
import time

import httpx

# Index levels (representative, Jan-2026). Seeded for the demo feed.
LIVE_BASES: dict[str, float] = {
    "HSI": 19750.0,
    "HHI": 7100.0,
}

# A gentle deterministic drift so the demo chart animates between refreshes.
# Uses sin(time) — deterministic, no RNG, easy to explain.
def _demo_price(base: float, contract: str) -> float:
    t = time.time()
    phase = hash(contract) % 100
    wave = 18.0 * math.sin(t / 90.0 + phase) + 9.0 * math.sin(t / 37.0 + 2 * phase)
    return round(base + wave, 2)


async def _try_live() -> dict | None:
    """Attempt a real feed. Returns None on any failure -> caller falls back."""
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            r = await client.get(
                "https://query1.finance.yahoo.com/v8/finance/chart/%5EHSI",
                params={"interval": "1m", "range": "1d"},
                headers={"User-Agent": "Mozilla/5.0"},
            )
            r.raise_for_status()
            j = r.json()
            meta = j["chart"]["result"][0]["meta"]
            return {"hsi": float(meta["regularMarketPrice"]), "source": "live"}
    except Exception:
        return None


async def get_market() -> dict:
    """Return the current market snapshot with a source label.

    Each index level falls back independently: a feed may provide HSI
    but not HHI. `source` is 'live' (all real), 'mixed' (part real, part
    demo), or 'demo'.
    """
    live = await _try_live() or {}
    hsi = live.get("hsi")
    hhi = live.get("hhi")
    if hsi is None:
        hsi = _demo_price(LIVE_BASES["HSI"], "HSI")
    if hhi is None:
        hhi = _demo_price(LIVE_BASES["HHI"], "HHI")

    if live.get("hsi") is not None and live.get("hhi") is not None:
        source = "live"
    elif live:
        source = "mixed"
    else:
        source = "demo"

    # Futures price = index + basis (demo: small positive basis from cost of carry).
    basis = 55.0
    return {
        "source": source,
        "hsi_index": round(hsi, 2),
        "hhi_index": round(hhi, 2),
        # front-month derivative prices (index + carry basis)
        "hsi_future": round(hsi + basis, 2),
        "hhi_future": round(hhi + basis, 2),
        "change_pct": (hsi - LIVE_BASES["HSI"]) / LIVE_BASES["HSI"] * 100.0,
        "updated": time.time(),
    }


async def get_mark(contract: str) -> float:
    """Mark price (index points) for a contract code, whatever the feed."""
    mkt = await get_market()
    if contract.upper() == "HSI":
        return mkt["hsi_future"]
    if contract.upper() == "HHI":
        return mkt["hhi_future"]
    # MHI tracks the same underlying as HSI (Mini-HSI is 1/5 the multiplier).
    return mkt["hsi_future"]
