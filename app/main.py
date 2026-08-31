"""FastAPI app exposing the market snapshot and the risk engine."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import feed
from .config import CONTRACTS
from .risk import build_risk_profile

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("hkfutures")

app = FastAPI(title="HK Futures Risk & Market Monitor")

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
async def index() -> FileResponse:
    return FileResponse("app/static/index.html")


@app.get("/api/market")
async def market() -> dict:
    """Current index/futures snapshot. Marks source: live or demo."""
    return await feed.get_market()


@app.get("/api/contracts")
async def contracts() -> dict:
    """Contract parameter table (for the dropdowns / reference)."""
    return {c: v.__dict__ if hasattr(v, "__dict__") else dict(zip(
        ["code", "name", "multiplier_hkd", "tick_size", "im_per_contract",
         "mm_per_contract", "im_per_contract_tier2"],
        (v.code, v.name, v.multiplier_hkd, v.tick_size, v.im_per_contract,
         v.mm_per_contract, v.im_per_contract_tier2),
    )) for c, v in CONTRACTS.items()}


@app.get("/api/risk")
async def risk(
    contract: str = Query(..., description="Contract code, e.g. HSI / MHI / HHI"),
    entry: float = Query(..., description="Entry price in index points"),
    qty: int = Query(..., description="Position size; negative = short"),
) -> dict:
    """Risk profile for a position, marked to the current market price."""
    c = CONTRACTS.get(contract.upper())
    if c is None:
        raise HTTPException(404, f"Unknown contract '{contract}'")
    if qty == 0:
        raise HTTPException(400, "qty must be non-zero")
    mark = await feed.get_mark(contract)
    return build_risk_profile(c, entry, qty, mark)
