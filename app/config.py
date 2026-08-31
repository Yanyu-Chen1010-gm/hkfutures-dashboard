"""
HKEX futures contract specifications & margin parameters.

Values are representative and MUST be validated against the current
HKEX "Daily Margin Rates" schedule before you rely on them in production.
The mechanics are faithful to the actual HKEX margin structure:
  - Initial Margin  (IM) : required on open
  - Maintenance Margin(MM): below this -> margin call / liquidation
Tiered by open position size.

Interview talking point: HKEX publishes daily margin per contract.
The tier makes margin non-linear in exposure — that's the nuance.
"""
from __future__ import annotations


class Contract:
    __slots__ = (
        "code", "name", "multiplier_hkd", "tick_size",
        "im_per_contract", "mm_per_contract", "im_per_contract_tier2",
    )

    def __init__(
        self,
        code: str,
        name: str,
        multiplier_hkd: float,
        tick_size: float,
        im_per_contract: float,
        mm_per_contract: float,
        im_per_contract_tier2: float,
    ):
        self.code = code
        self.name = name
        self.multiplier_hkd = multiplier_hkd     # HKD per index point
        self.tick_size = tick_size               # minimum price fluctuation
        self.im_per_contract = im_per_contract   # HKD
        self.mm_per_contract = mm_per_contract   # HKD
        self.im_per_contract_tier2 = im_per_contract_tier2


# Representative figures (Jan-2026 indicative). Replace with live HKEX board.
CONTRACTS: dict[str, Contract] = {
    "HSI": Contract(
        code="HSI",
        name="Hang Seng Index Futures",
        multiplier_hkd=50.0,    # 50 HKD per index point
        tick_size=1.0,         # 1 index point
        im_per_contract=92000.0,
        mm_per_contract=76000.0,
        im_per_contract_tier2=105000.0,  # above 1,000 contracts (illustrative)
    ),
    "MHI": Contract(
        code="MHI",
        name="Mini-Hang Seng Index Futures",
        multiplier_hkd=10.0,
        tick_size=1.0,
        im_per_contract=18400.0,
        mm_per_contract=15200.0,
        im_per_contract_tier2=21000.0,
    ),
    "HHI": Contract(
        code="HHI",
        name="Hang Seng China Enterprises Index Futures",
        multiplier_hkd=50.0,
        tick_size=1.0,
        im_per_contract=38000.0,
        mm_per_contract=31000.0,
        im_per_contract_tier2=44000.0,
    ),
}

# Index point value of a +1 index point move on ONE contract (in HKD).
# = multiplier. Kept explicit for the interview: "why is HSI point value 50 HKD?"
