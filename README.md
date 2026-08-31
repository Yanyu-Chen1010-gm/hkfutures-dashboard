# HK Futures · Risk & Market Monitor

A lightweight client-support dashboard for **HKEX futures** (HSI / MHI / HHI).
Built to be demo-able in an interview for a **quant futures client support**
role — it shows you understand the *risk language* a quant client uses:
notional, initial/maintenance margin, liquidation price, point value.

## What it does

| Panel | Purpose | What you can argue at interview |
|---|---|---|
| **Market monitor** | Live index/futures snapshot + sparkline | "How do I tie the derivative to the cash index? Basis." |
| **Risk & margin engine** | Compute margin, P&L, liquidation for a position | "Margin is tiered; liquidation = loss reaching maintenance margin." |
| **Margin reference** | Contract specs table | "HSI point value is HK$50/pt, not the index level." |

## Quick start (local)

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/uvicorn app.main:app --port 8031
# open http://localhost:8031
```

Run the risk-engine tests:
```bash
./venv/bin/python test_risk.py   # -> "risk engine: ALL ASSERTIONS PASS"
```

## Architecture (why each piece exists)

- [`app/feed.py`](app/feed.py) — **graceful-fallback feed layer**. Tries a live
  provider, falls back to a deterministic demo feed, and labels the UI with
  `live` / `mixed` / `demo`. **This is the production-correct pattern for a
  support tool: the dashboard never goes blank because a third-party feed
  hiccuped.** Swap in a licensed HKEX feed by replacing `_try_live()`; the
  consumers don't change.
- [`app/risk.py`](app/risk.py) — pure margin/risk math, unit-tested. No I/O.
- [`app/config.py`](app/config.py) — contract specs + margin. **Values are
  indicative**; validate against the live HKEX "Daily Margin Rates" page.
- [`app/main.py`](app/main.py) — FastAPI. Three endpoints: `/api/market`,
  `/api/contracts`, `/api/risk`.

## Deploy on a light server (No DB, no Docker)

1. Copy the project to the server, create venv, `pip install -r requirements.txt`.
2. `deploy/hkfutures.service` → systemd unit (bind to 127.0.0.1:8031).
3. `deploy/Caddyfile` → reverse proxy with **automatic Let's Encrypt HTTPS**.

```bash
sudo cp deploy/hkfutures.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now hkfutures
# then configure Caddy (or nginx + certbot) to proxy 8031
```

## Link it to your existing website

Two options, both cheap on a light server:

- **Subdomain**: Caddy `futures.yoursite.com { reverse_proxy 127.0.0.1:8031 }`.
- **Path under an existing domain**: `handle_path /futures { reverse_proxy 127.0.0.1:8031 }`
  (set your frontend asset paths accordingly, or use `<base href="/futures/">`).

Or **embed as an iframe** on your existing page:
```html
<iframe src="https://futures.yoursite.com" style="width:100%;height:600px;border:0"></iframe>
```

## Critical caveat for a real deploy

`config.py` margin numbers and the `feed.py` basis are **indicative**. Before
quoting anything to a client, replace them with the current HKEX daily margin
schedule and a licensed real-time feed. The *mechanics* are faithful; the
*numbers* are placeholders. Say this out loud if asked — it reads as good
risk awareness, which is exactly the job.
