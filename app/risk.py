"""
Margin & exposure engine for HKEX futures.

This is the centrepiece: it shows you *understand* the mechanics a quant
client asks about every day. Pure functions — no I/O — so they're unit-testable.

Key concepts (defend these at interview):
  - Notional    = index level x multiplier x contracts
  - Initial Margin = margin on open. Tiered: bigger positions -> higher per-contract IM.
  - Maintenance Margin = floor you must keep; fall below it -> margin call.
  - Liquidation price = price at which loss wipes you to the maintenance margin.
  - The point value = multiplier (HKD per index point), NOT the index level.
"""
from __future__ import annotations

from .config import Contract


def notional(contract: Contract, price: float | None, qty: int) -> float:
    """Open notional exposure in HKD. price = futures price (index pts)."""
    p = price if price is not None else 0.0
    return p * contract.multiplier_hkd * abs(qty)


def initial_margin(contract: Contract, qty: int) -> float:
    """HKD required at open. Tiered by |qty| (illustrative tier at 1,000)."""
    per = contract.im_per_contract_tier2 if abs(qty) > 1000 else contract.im_per_contract
    return per * abs(qty)


def maintenance_margin(contract: Contract, qty: int) -> float:
    return contract.mm_per_contract * abs(qty)


def pnl_at(contract: Contract, entry: float, price: float, qty: int) -> float:
    """Unrealised P&L (HKD). qty>0 = long, qty<0 = short."""
    return (price - entry) * contract.multiplier_hkd * qty


def liquidation_price(
    contract: Contract, entry: float, qty: int, maintenance: float | None = None
) -> float | None:
    """
    The price that takes your position to exactly the maintenance margin.
    Margin is held in cash; loss on position > (maintenance margin) => liquidation.
    For a long:  loss = (entry - P) * mult * qty  >  maintenance
                 P < entry - maintenance / (mult * qty)
    For a short: loss = (P - entry) * mult * |qty|  >  maintenance
                 P > entry + maintenance / (mult * |qty|)
    Doesn't account for your *excess* cash, so it's the exchange's floor, not yours.
    """
    if qty == 0:
        return None
    mm = maintenance if maintenance is not None else maintenance_margin(contract, qty)
    per_point = contract.multiplier_hkd * abs(qty)
    if qty > 0:
        return entry - mm / per_point
    return entry + mm / per_point


def build_risk_profile(
    contract: Contract,
    entry: float,
    qty: int,
    price: float | None,
) -> dict:
    """Assemble the full risk snapshot a support desk would quote to a client."""
    r = {
        "contract": contract.code,
        "name": contract.name,
        "multiplier": contract.multiplier_hkd,
        "tick_size": contract.tick_size,
        "qty": qty,
        "entry": entry,
        "mark": price,
        "point_value": round(contract.multiplier_hkd, 2),
        "notional": round(notional(contract, price, qty), 2),
        "initial_margin": round(initial_margin(contract, qty), 2),
        "maintenance_margin": round(maintenance_margin(contract, qty), 2),
        "unrealised_pnl": round(pnl_at(contract, entry, price if price is not None else entry, qty), 2),
        "liq_price": liquidation_price(contract, entry, qty),
    }
    r["margin_ratio"] = round(r["unrealised_pnl"] / r["initial_margin"] * 100.0, 2)
    return r
