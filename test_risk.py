from app.config import CONTRACTS
from app.risk import (
    notional, initial_margin, maintenance_margin,
    pnl_at, liquidation_price, build_risk_profile,
)

c = CONTRACTS["HSI"]

# Notional: 19800 idx x 50 HKD/pt x 10 ctr = 9,900,000
assert round(notional(c, 19800.0, 10)) == 9_900_000, notional(c, 19800.0, 10)

# Initial margin (below tier): 92,000 x 10 = 920,000
assert initial_margin(c, 10) == 920_000

# Tier2 kicks in above 1,000 contracts
assert initial_margin(c, 1500) == 105_000 * 1500

# Long P&L: entry 19500 -> mark 19800, +300 pts x 50 x 10 = +150,000
assert pnl_at(c, 19500, 19800, 10) == 150_000

# Liquidation long: entry 19500, mm=76,000x10=760,000
# liq = 19500 - 760000/(50*10) = 19500 - 1520 = 17980
assert liquidation_price(c, 19500, 10) == 19500 - 1520

prof = build_risk_profile(c, 19500, 10, 19800)
assert prof["notional"] == 9_900_000
assert prof["initial_margin"] == 920_000
assert prof["unrealised_pnl"] == 150_000
print("risk engine: ALL ASSERTIONS PASS")
