"""
Long-term Portfolio Dashboard Generator
Reads holdings.csv (investments) and retirement_holdings.csv (retirement),
fetches live prices via yfinance, and writes docs/index.html
"""

import csv
import json
import os
from datetime import datetime, timedelta
import yfinance as yf

# ── Config ────────────────────────────────────────────────────────────────────
HOLDINGS_FILE   = "holdings.csv"
RETIREMENT_FILE = "retirement_holdings.csv"
OUTPUT_FILE     = "docs/index.html"

COST_BASIS = {
    "MSFT":  35788.51,
    "FXAIX": 70255.36,
    "VWO":   38041.75,
    "TMUS":  16401.19,
    "NVDA":  18449.10,
    "FBTC":  20449.96,
    "GLD":    9668.72,
}
GROWTH_CAGR = {"conservative": 0.05, "moderate": 0.07, "optimistic": 0.10}

# ── Load holdings ─────────────────────────────────────────────────────────────
def load_holdings():
    holdings = []
    with open(HOLDINGS_FILE) as f:
        for row in csv.DictReader(f):
            holdings.append({
                "ticker":      row["ticker"].strip(),
                "shares":      float(row["shares"]),
                "asset_class": row["asset_class"].strip(),
                "name":        row["name"].strip(),
            })
    return holdings

def load_retirement_holdings():
    holdings = []
    with open(RETIREMENT_FILE) as f:
        for row in csv.DictReader(f):
            holdings.append({
                "ticker":            row["ticker"].strip(),
                "shares":            float(row["shares"]),
                "asset_class":       row["asset_class"].strip(),
                "name":              row["name"].strip(),
                "account":           row["account"].strip(),
                "fetch_live":        row["fetch_live"].strip().lower() == "yes",
                "last_price":        float(row["last_price"]),
                "cost_basis":        float(row["cost_basis"]),
                "last_day_gain":     float(row["last_day_gain"]),
                "last_day_gain_pct": float(row["last_day_gain_pct"]),
            })
    return holdings

# ── Fetch investment prices ───────────────────────────────────────────────────
def fetch_prices(holdings):
    tickers = [h["ticker"] for h in holdings]
    raw = yf.download(tickers, period="2d", auto_adjust=True, progress=False)
    results = {}
    for h in holdings:
        t = h["ticker"]
        try:
            closes = raw["Close"][t].dropna()
            p_today = float(closes.iloc[-1])
            p_prev  = float(closes.iloc[-2]) if len(closes) >= 2 else p_today
            results[t] = {
                "price":          round(p_today, 2),
                "day_change":     round(p_today - p_prev, 2),
                "day_change_pct": round((p_today - p_prev) / p_prev * 100, 2),
            }
        except Exception as e:
            print(f"Warning: could not fetch {t}: {e}")
            results[t] = {"price": 0, "day_change": 0, "day_change_pct": 0}
    return results

# ── Fetch retirement prices (live for public tickers, static for private) ─────
def fetch_retirement_prices(ret_holdings):
    live_tickers = [h["ticker"] for h in ret_holdings if h["fetch_live"]]
    live_data = {}
    if live_tickers:
        try:
            t = live_tickers[0]
            raw = yf.download(t, period="2d", auto_adjust=True, progress=False)
            closes = raw["Close"].dropna()
            p_today = float(closes.iloc[-1])
            p_prev  = float(closes.iloc[-2]) if len(closes) >= 2 else p_today
            live_data[t] = {
                "price":          round(p_today, 4),
                "day_change":     round((p_today - p_prev) * 1, 4),
                "day_change_pct": round((p_today - p_prev) / p_prev * 100, 2),
            }
        except Exception as e:
            print(f"Warning: could not fetch live retirement price: {e}")

    results = {}
    for h in ret_holdings:
        t = h["ticker"]
        if h["fetch_live"] and t in live_data:
            ld = live_data[t]
            results[t] = {
                "price":          ld["price"],
                "day_gain":       round(ld["day_change"] * h["shares"], 2),
                "day_gain_pct":   ld["day_change_pct"],
            }
        else:
            results[t] = {
                "price":        h["last_price"],
                "day_gain":     h["last_day_gain"],
                "day_gain_pct": h["last_day_gain_pct"],
            }
    return results

# ── Historical performance ────────────────────────────────────────────────────
def fetch_history(tickers, months=12):
    end   = datetime.today()
    start = end - timedelta(days=months * 31)
    raw   = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)
    history = {}
    for t in tickers:
        try:
            closes = raw["Close"][t].dropna()
            base = float(closes.iloc[0])
            history[t] = {
                "dates":  [d.strftime("%Y-%m-%d") for d in closes.index],
                "values": [round(float(v) / base * 100, 2) for v in closes],
            }
        except Exception:
            history[t] = {"dates": [], "values": []}
    return history

# ── Compute investment metrics ────────────────────────────────────────────────
def compute_metrics(holdings, prices):
    rows = []
    total_value = total_cost = total_day_gain = 0

    for h in holdings:
        t      = h["ticker"]
        p      = prices.get(t, {})
        price  = p.get("price", 0)
        shares = h["shares"]
        cost   = COST_BASIS.get(t, 0)
        value  = round(price * shares, 2)
        gain   = round(value - cost, 2)
        gain_pct     = round(gain / cost * 100, 2) if cost else 0
        day_gain     = round(p.get("day_change", 0) * shares, 2)
        day_gain_pct = p.get("day_change_pct", 0)

        total_value    += value
        total_cost     += cost
        total_day_gain += day_gain

        rows.append({
            "ticker": t, "name": h["name"], "asset_class": h["asset_class"],
            "shares": shares, "price": price, "value": value, "cost": cost,
            "gain": gain, "gain_pct": gain_pct,
            "day_gain": day_gain, "day_gain_pct": day_gain_pct,
        })

    total_gain     = round(total_value - total_cost, 2)
    total_gain_pct = round(total_gain / total_cost * 100, 2) if total_cost else 0
    total_day_pct  = round(total_day_gain / (total_value - total_day_gain) * 100, 2) if total_value else 0

    for r in rows:
        r["weight"] = round(r["value"] / total_value * 100, 2) if total_value else 0
    rows.sort(key=lambda x: x["value"], reverse=True)

    return {
        "rows": rows,
        "total_value": round(total_value, 2), "total_cost": round(total_cost, 2),
        "total_gain": round(total_gain, 2),   "total_gain_pct": total_gain_pct,
        "total_day_gain": round(total_day_gain, 2), "total_day_pct": total_day_pct,
    }

# ── Compute retirement metrics ────────────────────────────────────────────────
def compute_retirement_metrics(ret_holdings, ret_prices):
    rows = []
    total_value = total_cost = total_day_gain = 0

    for h in ret_holdings:
        t      = h["ticker"]
        p      = ret_prices.get(t, {})
        price  = p.get("price", h["last_price"])
        shares = h["shares"]
        cost   = h["cost_basis"]
        value  = round(price * shares, 2)
        gain   = round(value - cost, 2)
        gain_pct     = round(gain / cost * 100, 2) if cost else 0
        day_gain     = p.get("day_gain", h["last_day_gain"])
        day_gain_pct = p.get("day_gain_pct", h["last_day_gain_pct"])

        total_value    += value
        total_cost     += cost
        total_day_gain += day_gain

        rows.append({
            "ticker": t, "name": h["name"], "asset_class": h["asset_class"],
            "account": h["account"], "is_live": h["fetch_live"],
            "shares": shares, "price": price, "value": value, "cost": cost,
            "gain": gain, "gain_pct": gain_pct,
            "day_gain": day_gain, "day_gain_pct": day_gain_pct,
        })

    total_gain     = round(total_value - total_cost, 2)
    total_gain_pct = round(total_gain / total_cost * 100, 2) if total_cost else 0
    total_day_pct  = round(total_day_gain / (total_value - total_day_gain) * 100, 2) if total_value else 0

    for r in rows:
        r["weight"] = round(r["value"] / total_value * 100, 2) if total_value else 0

    by_account = {}
    for r in rows:
        acct = r["account"]
        if acct not in by_account:
            by_account[acct] = {"rows": [], "total_value": 0, "total_gain": 0, "total_day_gain": 0}
        by_account[acct]["rows"].append(r)
        by_account[acct]["total_value"]    = round(by_account[acct]["total_value"] + r["value"], 2)
        by_account[acct]["total_gain"]     = round(by_account[acct]["total_gain"] + r["gain"], 2)
        by_account[acct]["total_day_gain"] = round(by_account[acct]["total_day_gain"] + r["day_gain"], 2)

    for acct, data in by_account.items():
        tc = data["total_value"] - data["total_gain"]
        data["total_gain_pct"] = round(data["total_gain"] / tc * 100, 2) if tc else 0
        data["rows"].sort(key=lambda x: x["value"], reverse=True)

    rows.sort(key=lambda x: x["value"], reverse=True)

    return {
        "rows": rows, "by_account": by_account,
        "total_value": round(total_value, 2), "total_cost": round(total_cost, 2),
        "total_gain": round(total_gain, 2),   "total_gain_pct": total_gain_pct,
        "total_day_gain": round(total_day_gain, 2), "total_day_pct": total_day_pct,
    }

# ── Growth projection ─────────────────────────────────────────────────────────
def growth_projection(start_value, years=11):
    base_year = datetime.today().year
    proj = {"years": list(range(base_year, base_year + years))}
    for label, rate in GROWTH_CAGR.items():
        proj[label] = [round(start_value * (1 + rate) ** i) for i in range(years)]
    return proj

# ── Asset class summary ───────────────────────────────────────────────────────
def asset_class_summary(rows):
    summary = {}
    total = sum(r["value"] for r in rows)
    for r in rows:
        ac = r["asset_class"]
        summary[ac] = summary.get(ac, 0) + r["value"]
    return {k: round(v / total * 100, 1) for k, v in summary.items()}

# ── Format helpers ────────────────────────────────────────────────────────────
def fmt_usd(v):
    sign = "-" if v < 0 else ""
    return f"{sign}${abs(v):,.2f}"

def fmt_pct(v):
    sign = "+" if v >= 0 else ""
    return f"{sign}{v:.2f}%"

def color_class(v):
    return "up" if v >= 0 else "down"

# ── HTML builder ──────────────────────────────────────────────────────────────
def build_html(metrics, ret_metrics, proj, history, asset_s, updated_at):
    inv_rows = metrics["rows"]
    inv_v    = metrics["total_value"]
    inv_g    = metrics["total_gain"]
    inv_gp   = metrics["total_gain_pct"]
    inv_dg   = metrics["total_day_gain"]
    inv_dp   = metrics["total_day_pct"]

    ret_v    = ret_metrics["total_value"]
    ret_g    = ret_metrics["total_gain"]
    ret_gp   = ret_metrics["total_gain_pct"]
    ret_dg   = ret_metrics["total_day_gain"]
    ret_dp   = ret_metrics["total_day_pct"]
    by_acct  = ret_metrics["by_account"]

    combined_v  = round(inv_v + ret_v, 2)
    combined_g  = round(inv_g + ret_g, 2)
    combined_c  = round(metrics["total_cost"] + ret_metrics["total_cost"], 2)
    combined_gp = round(combined_g / combined_c * 100, 2) if combined_c else 0

    colors = ["#60a5fa","#34d399","#a78bfa","#fbbf24","#f472b6","#fb923c","#9ca3af"]

    # ── Investment table rows ──
    inv_table_rows = ""
    for r in inv_rows:
        g_cls  = color_class(r["gain"])
        dg_cls = color_class(r["day_gain"])
        w_flag = f'<span style="color:var(--amber);">{r["weight"]:.1f}%</span>' if r["weight"] > 30 else f'{r["weight"]:.1f}%'
        inv_table_rows += f"""
        <tr>
          <td><div class="ticker">{r['ticker']}</div><div class="name">{r['name']}</div></td>
          <td>{r['shares']:,.4f}</td>
          <td>${r['price']:,.2f}</td>
          <td>${r['value']:,.2f}</td>
          <td>{w_flag}</td>
          <td class="{g_cls}">{fmt_usd(r['gain'])}</td>
          <td class="{g_cls}">{fmt_pct(r['gain_pct'])}</td>
          <td class="{dg_cls}">{fmt_pct(r['day_gain_pct'])}</td>
        </tr>"""

    # ── Investment allocation bars ──
    inv_alloc_bars = ""
    for i, r in enumerate(inv_rows):
        c = colors[i % len(colors)]
        inv_alloc_bars += f"""
        <div class="alloc-row">
          <span class="alloc-name">{r['ticker']}</span>
          <div class="alloc-bar-bg"><div class="alloc-bar-fill" style="width:{r['weight']}%;background:{c};"></div></div>
          <span class="alloc-pct">{r['weight']:.1f}%</span>
        </div>"""

    # ── Retirement table rows per account ──
    def ret_account_table(acct_rows, is_live_acct):
        html = ""
        for r in acct_rows:
            g_cls  = color_class(r["gain"])
            dg_cls = color_class(r["day_gain"])
            badge  = "" if r["is_live"] else '<span style="font-size:9px;background:var(--amber-dim);color:var(--amber);padding:1px 5px;border-radius:3px;margin-left:4px;">cached</span>'
            html += f"""
            <tr>
              <td><div class="ticker" style="font-size:11px;">{r['name']}{badge}</div><div class="name">{r['asset_class']}</div></td>
              <td>{r['shares']:,.3f}</td>
              <td>${r['price']:,.4f}</td>
              <td>${r['value']:,.2f}</td>
              <td>{r['weight']:.1f}%</td>
              <td class="{g_cls}">{fmt_usd(r['gain'])}</td>
              <td class="{g_cls}">{fmt_pct(r['gain_pct'])}</td>
              <td class="{dg_cls}">{fmt_pct(r['day_gain_pct'])}</td>
            </tr>"""
        return html

    ret_sections_html = ""
    for acct_name, acct_data in by_acct.items():
        is_live = all(r["is_live"] for r in acct_data["rows"])
        cached_note = "" if is_live else """
        <div style="background:var(--amber-dim);border:1px solid rgba(251,191,36,.2);border-radius:6px;padding:8px 14px;font-size:11px;color:var(--amber);margin-bottom:12px;">
          ⚡ Fund prices from last exported file · not live market data
        </div>"""
        acct_g_cls = color_class(acct_data["total_gain"])
        ret_sections_html += f"""
    <div style="margin-bottom:28px;">
      <div class="section-head" style="margin-top:8px;">{acct_name}</div>
      {cached_note}
      <div class="chart-card" style="margin-bottom:0;">
        <div style="display:flex;gap:20px;margin-bottom:14px;">
          <div><div style="font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;">Value</div>
            <div style="font-size:18px;font-family:'Fraunces',serif;font-weight:300;">${acct_data['total_value']:,.0f}</div></div>
          <div><div style="font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;">Total gain</div>
            <div style="font-size:18px;font-family:'Fraunces',serif;font-weight:300;color:var(--{'green' if acct_data['total_gain'] >= 0 else 'red'});">{fmt_usd(acct_data['total_gain'])}</div></div>
          <div><div style="font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;">Return</div>
            <div style="font-size:18px;font-family:'Fraunces',serif;font-weight:300;color:var(--{'green' if acct_data['total_gain_pct'] >= 0 else 'red'});">{fmt_pct(acct_data['total_gain_pct'])}</div></div>
        </div>
        <table>
          <thead><tr>
            <th>Fund</th><th>Units</th><th>Price</th>
            <th>Value</th><th>Weight</th><th>Gain $</th><th>Gain %</th><th>Today</th>
          </tr></thead>
          <tbody>{ret_account_table(acct_data['rows'], is_live)}</tbody>
        </table>
      </div>
    </div>"""

    # ── JS data for investment charts ──
    inv_tickers   = [r["ticker"] for r in inv_rows]
    inv_values    = [r["value"] for r in inv_rows]
    inv_gains     = [r["gain"] for r in inv_rows]
    inv_gain_pcts = [r["gain_pct"] for r in inv_rows]
    inv_weights   = [r["weight"] for r in inv_rows]
    inv_colors    = colors[:len(inv_tickers)]

    hist_labels   = history.get(inv_tickers[0], {}).get("dates", [])
    line_colors   = ["#34d399","#60a5fa","#a78bfa","#fbbf24","#f472b6"]
    hist_datasets = []
    for i, t in enumerate(inv_tickers[:5]):
        h = history.get(t, {})
        hist_datasets.append({
            "label": t, "data": h.get("values", []),
            "borderColor": line_colors[i], "backgroundColor": "transparent",
            "borderWidth": 1.5, "tension": 0.3, "pointRadius": 0,
        })

    # ── JS data for retirement charts ──
    ret_all_rows  = ret_metrics["rows"]
    ret_labels    = [r["name"][:18] for r in ret_all_rows]
    ret_values    = [r["value"] for r in ret_all_rows]
    ret_gains     = [r["gain"] for r in ret_all_rows]
    ret_gain_pcts = [r["gain_pct"] for r in ret_all_rows]
    ret_weights   = [r["weight"] for r in ret_all_rows]
    ret_colors    = colors[:len(ret_all_rows)]

    best  = max(inv_rows, key=lambda x: x["gain_pct"])
    worst = min(inv_rows, key=lambda x: x["gain_pct"])
    top_w = max(inv_rows, key=lambda x: x["weight"])

    # ── Pre-compute retirement breakdown cards (avoid nested f-string triple-quotes) ──
    ret_breakdown_html = ""
    for acct, data in by_acct.items():
        n = len(data["rows"])
        fund_label = "fund" if n == 1 else "funds"
        gain_color = "green" if data["total_gain"] >= 0 else "red"
        ret_breakdown_html += (
            f'<div style="display:flex;justify-content:space-between;align-items:center;'
            f'padding:10px;background:var(--surface2);border-radius:8px;">'
            f'<div><div style="font-size:12px;">{acct}</div>'
            f'<div style="font-size:10px;color:var(--muted);">{n} {fund_label}</div></div>'
            f'<div style="text-align:right;">'
            f'<div style="font-size:14px;font-family:\'Fraunces\',serif;">'
            f'${data["total_value"]:,.0f}</div>'
            f'<div style="font-size:11px;color:var(--{gain_color});">'
            f'{fmt_pct(data["total_gain_pct"])} total</div></div></div>'
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Long-term Portfolio</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,600;1,9..144,300&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg:#0d0f12;--surface:#13161b;--surface2:#1a1e25;
    --border:rgba(255,255,255,0.07);--text:#e8eaf0;--muted:#6b7280;--dim:#3a4050;
    --green:#34d399;--green-dim:rgba(52,211,153,0.12);
    --red:#f87171;--red-dim:rgba(248,113,113,0.12);
    --amber:#fbbf24;--amber-dim:rgba(251,191,36,0.1);
    --blue:#60a5fa;--blue-dim:rgba(96,165,250,0.1);
    --purple:#a78bfa;--accent:#34d399;
  }}
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{background:var(--bg);color:var(--text);font-family:'DM Mono',monospace;font-size:13px;min-height:100vh;line-height:1.5;}}
  .header{{padding:28px 32px 20px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:flex-end;flex-wrap:wrap;gap:12px;}}
  .header-left h1{{font-family:'Fraunces',serif;font-size:26px;font-weight:300;letter-spacing:-0.5px;}}
  .header-left p{{font-size:11px;color:var(--muted);margin-top:3px;}}
  .header-right{{text-align:right;font-size:11px;color:var(--muted);}}
  .header-right .big{{display:block;font-size:24px;font-family:'Fraunces',serif;font-weight:300;color:var(--text);margin-bottom:2px;}}
  .tabs{{display:flex;padding:0 32px;border-bottom:1px solid var(--border);overflow-x:auto;}}
  .tab{{padding:14px 18px;font-size:11px;letter-spacing:.08em;color:var(--muted);cursor:pointer;border:none;border-bottom:2px solid transparent;background:none;text-transform:uppercase;transition:all .2s;white-space:nowrap;}}
  .tab:hover{{color:var(--text);}} .tab.active{{color:var(--accent);border-bottom-color:var(--accent);}}
  .content{{padding:24px 32px;}} .panel{{display:none;}} .panel.active{{display:block;}}
  .grid-4{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;}}
  .grid-3{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px;}}
  .grid-2{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px;}}
  .grid-2-1{{display:grid;grid-template-columns:2fr 1fr;gap:16px;margin-bottom:20px;}}
  .stat{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px;}}
  .stat-label{{font-size:10px;color:var(--muted);letter-spacing:.08em;text-transform:uppercase;margin-bottom:8px;}}
  .stat-value{{font-size:22px;font-family:'Fraunces',serif;font-weight:300;}}
  .stat-sub{{font-size:11px;margin-top:4px;}}
  .up{{color:var(--green);}} .down{{color:var(--red);}} .neutral{{color:var(--muted);}}
  .chart-card{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:20px;margin-bottom:16px;}}
  .chart-card-title{{font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-bottom:4px;}}
  .chart-card-subtitle{{font-size:12px;color:var(--text);margin-bottom:16px;font-family:'Fraunces',serif;font-weight:300;}}
  table{{width:100%;border-collapse:collapse;}}
  th{{font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);text-align:left;padding:8px 12px;border-bottom:1px solid var(--border);font-weight:400;}}
  th:not(:first-child){{text-align:right;}}
  td{{padding:11px 12px;border-bottom:1px solid var(--border);font-size:12px;}}
  td:not(:first-child){{text-align:right;}} tr:last-child td{{border-bottom:none;}}
  tr:hover td{{background:rgba(255,255,255,.02);}}
  .ticker{{font-weight:500;}} .name{{font-size:11px;color:var(--muted);margin-top:1px;}}
  .indicator{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:18px;}}
  .ind-header{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;}}
  .ind-name{{font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);}}
  .ind-value{{font-size:24px;font-family:'Fraunces',serif;font-weight:300;}}
  .ind-desc{{font-size:11px;color:var(--muted);line-height:1.5;margin-top:6px;}}
  .signal{{font-size:10px;padding:3px 10px;border-radius:20px;letter-spacing:.06em;font-weight:500;}}
  .sig-green{{background:var(--green-dim);color:var(--green);}} .sig-amber{{background:var(--amber-dim);color:var(--amber);}}
  .sig-red{{background:var(--red-dim);color:var(--red);}} .sig-blue{{background:var(--blue-dim);color:var(--blue);}}
  .gauge-track{{height:4px;background:var(--surface2);border-radius:2px;margin-top:12px;overflow:hidden;}}
  .gauge-fill{{height:100%;border-radius:2px;}}
  .section-head{{font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin-bottom:14px;padding-bottom:8px;border-bottom:1px solid var(--border);}}
  .alloc-row{{display:flex;align-items:center;gap:12px;margin-bottom:10px;}}
  .alloc-name{{width:55px;font-size:11px;color:var(--muted);flex-shrink:0;}}
  .alloc-bar-bg{{flex:1;height:5px;background:var(--surface2);border-radius:3px;overflow:hidden;}}
  .alloc-bar-fill{{height:100%;border-radius:3px;}}
  .alloc-pct{{width:40px;text-align:right;font-size:12px;}}
  .legend-row{{display:flex;flex-wrap:wrap;gap:16px;margin-top:10px;}}
  .legend-item{{display:flex;align-items:center;gap:6px;font-size:11px;color:var(--muted);}}
  .legend-dot{{width:8px;height:8px;border-radius:2px;flex-shrink:0;}}
  .refresh-badge{{display:inline-block;font-size:10px;padding:3px 10px;border-radius:20px;background:var(--green-dim);color:var(--green);letter-spacing:.06em;margin-top:6px;}}
  .account-pill{{display:inline-block;font-size:10px;padding:2px 8px;border-radius:12px;background:var(--surface2);color:var(--muted);margin-left:6px;}}
  @media(max-width:768px){{
    .grid-4{{grid-template-columns:repeat(2,1fr);}} .grid-3{{grid-template-columns:repeat(2,1fr);}}
    .grid-2,.grid-2-1{{grid-template-columns:1fr;}}
    .content{{padding:16px;}} .tabs{{padding:0 16px;}}
    .header{{padding:20px 16px 16px;}}
  }}
</style>
</head>
<body>

<div class="header">
  <div class="header-left">
    <h1>Long-term Portfolio</h1>
    <p>Investments · Retirement · Updated {updated_at}</p>
    <span class="refresh-badge">Live prices via yfinance</span>
  </div>
  <div class="header-right">
    <span class="big">${combined_v:,.0f}</span>
    Combined portfolio &nbsp;·&nbsp;
    <span class="{color_class(inv_dg)}">{fmt_pct(inv_dp)} investments today</span>
  </div>
</div>

<div class="tabs">
  <button class="tab active" onclick="showTab('overview',this)">Overview</button>
  <button class="tab" onclick="showTab('investments',this)">Investments</button>
  <button class="tab" onclick="showTab('retirement',this)">Retirement</button>
  <button class="tab" onclick="showTab('performance',this)">Performance</button>
  <button class="tab" onclick="showTab('macro',this)">Macro</button>
  <button class="tab" onclick="showTab('health',this)">Health</button>
</div>

<!-- ══════════════════ OVERVIEW ══════════════════ -->
<div class="content panel active" id="tab-overview">
  <div class="grid-4">
    <div class="stat">
      <div class="stat-label">Combined total</div>
      <div class="stat-value">${combined_v:,.0f}</div>
      <div class="stat-sub {color_class(combined_g)}">{fmt_usd(combined_g)} ({fmt_pct(combined_gp)}) all time</div>
    </div>
    <div class="stat">
      <div class="stat-label">Investments</div>
      <div class="stat-value">${inv_v:,.0f}</div>
      <div class="stat-sub {color_class(inv_dg)}">{fmt_usd(inv_dg)} today ({fmt_pct(inv_dp)})</div>
    </div>
    <div class="stat">
      <div class="stat-label">Retirement</div>
      <div class="stat-value">${ret_v:,.0f}</div>
      <div class="stat-sub {color_class(ret_g)}">{fmt_usd(ret_g)} ({fmt_pct(ret_gp)}) all time</div>
    </div>
    <div class="stat">
      <div class="stat-label">Best investment</div>
      <div class="stat-value">{best['ticker']}</div>
      <div class="stat-sub up">{fmt_pct(best['gain_pct'])} total</div>
    </div>
  </div>

  <div class="grid-2-1">
    <div class="chart-card">
      <div class="chart-card-title">10-year growth projection</div>
      <div class="chart-card-subtitle">From ${combined_v:,.0f} combined at 5%, 7%, 10% CAGR</div>
      <div style="position:relative;height:220px;"><canvas id="growthChart"></canvas></div>
      <div class="legend-row">
        <span class="legend-item"><span class="legend-dot" style="background:#34d399;"></span>Moderate 7%</span>
        <span class="legend-item"><span class="legend-dot" style="background:#60a5fa;"></span>Conservative 5%</span>
        <span class="legend-item"><span class="legend-dot" style="background:#fbbf24;"></span>Optimistic 10%</span>
      </div>
    </div>
    <div class="chart-card">
      <div class="chart-card-title">Investment allocation</div>
      <div class="chart-card-subtitle">By market value</div>
      <div style="position:relative;height:160px;"><canvas id="allocDonut"></canvas></div>
      <div style="margin-top:14px;">{inv_alloc_bars}</div>
    </div>
  </div>

  <div class="grid-2">
    <div class="stat" style="padding:20px;">
      <div class="stat-label">Retirement breakdown</div>
      <div style="margin-top:10px;display:flex;flex-direction:column;gap:10px;">
        {ret_breakdown_html}
      </div>
    </div>
    <div class="stat" style="padding:20px;">
      <div class="stat-label">Portfolio split</div>
      <div style="position:relative;height:160px;margin-top:10px;"><canvas id="splitDonut"></canvas></div>
    </div>
  </div>
  {'<div style="background:var(--amber-dim);border:1px solid rgba(251,191,36,.2);border-radius:8px;padding:12px 16px;font-size:11px;color:var(--amber);line-height:1.6;">⚠ Concentration alert: ' + top_w["ticker"] + ' represents ' + str(top_w["weight"]) + '% of your investment portfolio. Target below 25% for moderate risk.</div>' if top_w["weight"] > 30 else ''}
</div>

<!-- ══════════════════ INVESTMENTS ══════════════════ -->
<div class="content panel" id="tab-investments">
  <div class="grid-4">
    <div class="stat">
      <div class="stat-label">Total value</div>
      <div class="stat-value">${inv_v:,.0f}</div>
      <div class="stat-sub {color_class(inv_dg)}">{fmt_usd(inv_dg)} today ({fmt_pct(inv_dp)})</div>
    </div>
    <div class="stat">
      <div class="stat-label">Total gain</div>
      <div class="stat-value {color_class(inv_g)}">{fmt_usd(inv_g)}</div>
      <div class="stat-sub {color_class(inv_g)}">{fmt_pct(inv_gp)} all time</div>
    </div>
    <div class="stat">
      <div class="stat-label">Best performer</div>
      <div class="stat-value">{best['ticker']}</div>
      <div class="stat-sub up">{fmt_pct(best['gain_pct'])} total</div>
    </div>
    <div class="stat">
      <div class="stat-label">Worst performer</div>
      <div class="stat-value">{worst['ticker']}</div>
      <div class="stat-sub {color_class(worst['gain_pct'])}">{fmt_pct(worst['gain_pct'])} total</div>
    </div>
  </div>

  <div class="chart-card">
    <table>
      <thead><tr>
        <th>Symbol / name</th><th>Shares</th><th>Price</th>
        <th>Value</th><th>Weight</th><th>Gain $</th><th>Gain %</th><th>Today</th>
      </tr></thead>
      <tbody>{inv_table_rows}</tbody>
    </table>
  </div>

  <div class="grid-2">
    <div class="chart-card">
      <div class="chart-card-title">Gain / loss by position</div>
      <div class="chart-card-subtitle">Total dollar return</div>
      <div style="position:relative;height:220px;"><canvas id="gainChart"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-card-title">Return % by position</div>
      <div class="chart-card-subtitle">Percentage since purchase</div>
      <div style="position:relative;height:220px;"><canvas id="returnPct"></canvas></div>
    </div>
  </div>
</div>

<!-- ══════════════════ RETIREMENT ══════════════════ -->
<div class="content panel" id="tab-retirement">
  <div class="grid-3">
    <div class="stat">
      <div class="stat-label">Total retirement</div>
      <div class="stat-value">${ret_v:,.0f}</div>
      <div class="stat-sub {color_class(ret_dg)}">{fmt_usd(ret_dg)} today</div>
    </div>
    <div class="stat">
      <div class="stat-label">Total gain</div>
      <div class="stat-value {color_class(ret_g)}">{fmt_usd(ret_g)}</div>
      <div class="stat-sub {color_class(ret_g)}">{fmt_pct(ret_gp)} all time</div>
    </div>
    <div class="stat">
      <div class="stat-label">Accounts</div>
      <div class="stat-value">{len(by_acct)}</div>
      <div class="stat-sub neutral">IRA + 401k</div>
    </div>
  </div>

  {ret_sections_html}

  <div class="grid-2">
    <div class="chart-card">
      <div class="chart-card-title">Retirement allocation</div>
      <div class="chart-card-subtitle">By fund value</div>
      <div style="position:relative;height:220px;"><canvas id="retAllocDonut"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-card-title">Gain by fund</div>
      <div class="chart-card-subtitle">Total dollar return</div>
      <div style="position:relative;height:220px;"><canvas id="retGainChart"></canvas></div>
    </div>
  </div>
</div>

<!-- ══════════════════ PERFORMANCE ══════════════════ -->
<div class="content panel" id="tab-performance">
  <div class="section-head">12-month relative performance · investments (normalised to 100)</div>
  <div class="chart-card">
    <div class="chart-card-title">Price performance – top 5 holdings</div>
    <div class="chart-card-subtitle">Rebased to 100 at start of period</div>
    <div style="position:relative;height:300px;"><canvas id="histChart"></canvas></div>
    <div class="legend-row" id="histLegend"></div>
  </div>
</div>

<!-- ══════════════════ MACRO ══════════════════ -->
<div class="content panel" id="tab-macro">
  <div class="section-head">Key macro indicators – updated manually each quarter</div>
  <div class="grid-3">
    <div class="indicator">
      <div class="ind-header"><div><div class="ind-name">Fed funds rate</div><div class="ind-value" style="color:var(--amber);">3.5–3.75%</div></div><span class="signal sig-amber">Watch</span></div>
      <div class="gauge-track"><div class="gauge-fill" style="width:62%;background:var(--amber);"></div></div>
      <div class="ind-desc">Drives borrowing costs. Lower rates benefit MSFT, NVDA and bonds.</div>
    </div>
    <div class="indicator">
      <div class="ind-header"><div><div class="ind-name">10-yr Treasury yield</div><div class="ind-value" style="color:var(--amber);">~4.1%</div></div><span class="signal sig-amber">Elevated</span></div>
      <div class="gauge-track"><div class="gauge-fill" style="width:70%;background:var(--amber);"></div></div>
      <div class="ind-desc">Benchmark for risk-free return. Rising yields compress growth stock valuations.</div>
    </div>
    <div class="indicator">
      <div class="ind-header"><div><div class="ind-name">Core PCE inflation</div><div class="ind-value" style="color:var(--red);">~3.0%</div></div><span class="signal sig-red">Above target</span></div>
      <div class="gauge-track"><div class="gauge-fill" style="width:80%;background:var(--red);"></div></div>
      <div class="ind-desc">Fed's preferred inflation gauge. Keeps rates high, supports gold (GLD).</div>
    </div>
    <div class="indicator">
      <div class="ind-header"><div><div class="ind-name">S&amp;P 500 P/E ratio</div><div class="ind-value" style="color:var(--amber);">~22x</div></div><span class="signal sig-amber">Stretched</span></div>
      <div class="gauge-track"><div class="gauge-fill" style="width:65%;background:var(--amber);"></div></div>
      <div class="ind-desc">Affects FXAIX and MSFT directly. Historical avg ~16–17x.</div>
    </div>
    <div class="indicator">
      <div class="ind-header"><div><div class="ind-name">US dollar index (DXY)</div><div class="ind-value" style="color:var(--blue);">~103</div></div><span class="signal sig-blue">Neutral</span></div>
      <div class="gauge-track"><div class="gauge-fill" style="width:50%;background:var(--blue);"></div></div>
      <div class="ind-desc">Weaker dollar boosts VWO and GLD. MSFT earns ~50% overseas.</div>
    </div>
    <div class="indicator">
      <div class="ind-header"><div><div class="ind-name">VIX (fear gauge)</div><div class="ind-value" style="color:var(--green);">~18</div></div><span class="signal sig-green">Calm</span></div>
      <div class="gauge-track"><div class="gauge-fill" style="width:30%;background:var(--green);"></div></div>
      <div class="ind-desc">Below 20 = calm. Above 30 = stress and potential buying opportunity.</div>
    </div>
    <div class="indicator">
      <div class="ind-header"><div><div class="ind-name">US GDP growth</div><div class="ind-value" style="color:var(--green);">+2.2%</div></div><span class="signal sig-green">Healthy</span></div>
      <div class="gauge-track"><div class="gauge-fill" style="width:55%;background:var(--green);"></div></div>
      <div class="ind-desc">Above 2% supports FXAIX and retirement index funds.</div>
    </div>
    <div class="indicator">
      <div class="ind-header"><div><div class="ind-name">Gold spot price</div><div class="ind-value" style="color:var(--green);">$3,300+</div></div><span class="signal sig-green">Strong</span></div>
      <div class="gauge-track"><div class="gauge-fill" style="width:78%;background:var(--green);"></div></div>
      <div class="ind-desc">Directly drives your GLD position. Supported by inflation and central bank buying.</div>
    </div>
    <div class="indicator">
      <div class="ind-header"><div><div class="ind-name">EM equity trend</div><div class="ind-value" style="color:var(--blue);">Neutral</div></div><span class="signal sig-blue">Monitor</span></div>
      <div class="gauge-track"><div class="gauge-fill" style="width:45%;background:var(--blue);"></div></div>
      <div class="ind-desc">Drives VWO and your retirement international stock funds.</div>
    </div>
  </div>
</div>

<!-- ══════════════════ HEALTH ══════════════════ -->
<div class="content panel" id="tab-health">
  <div class="section-head">Portfolio health · investments</div>
  <div class="grid-4">
    <div class="stat">
      <div class="stat-label">Top concentration</div>
      <div class="stat-value" style="color:{'var(--amber)' if top_w['weight'] > 25 else 'var(--green)'};">{top_w['weight']:.1f}%</div>
      <div class="stat-sub" style="color:{'var(--amber)' if top_w['weight'] > 25 else 'var(--green)'};">{'⚠ Target below 25%' if top_w['weight'] > 25 else '✓ Within target'}</div>
    </div>
    <div class="stat">
      <div class="stat-label">Bond allocation</div>
      <div class="stat-value" style="color:var(--red);">{asset_s.get('Bonds', 0)}%</div>
      <div class="stat-sub" style="color:var(--red);">Target: 15–25%</div>
    </div>
    <div class="stat">
      <div class="stat-label">International</div>
      <div class="stat-value" style="color:var(--green);">{asset_s.get('Intl Equity', 0):.1f}%</div>
      <div class="stat-sub up">Target: 15–25%</div>
    </div>
    <div class="stat">
      <div class="stat-label">Commodities / hedge</div>
      <div class="stat-value" style="color:var(--amber);">{asset_s.get('Commodities', 0):.1f}%</div>
      <div class="stat-sub" style="color:var(--amber);">Target: 7–10%</div>
    </div>
  </div>
  <div class="grid-2">
    <div class="chart-card">
      <div class="chart-card-title">Health scorecard</div>
      <div class="chart-card-subtitle">Current vs. moderate-risk target</div>
      <div style="position:relative;height:260px;"><canvas id="radarChart"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-card-title">Monitoring schedule</div>
      <div style="display:flex;flex-direction:column;gap:10px;margin-top:8px;">
        <div style="padding:14px;border:1px solid var(--border);border-radius:8px;">
          <div style="font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--green);margin-bottom:8px;">Monthly</div>
          <div style="font-size:11px;color:var(--muted);line-height:1.8;">• Core PCE / CPI<br>• Fed meeting minutes<br>• VIX level<br>• Top holding weight</div>
        </div>
        <div style="padding:14px;border:1px solid var(--border);border-radius:8px;">
          <div style="font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--amber);margin-bottom:8px;">Quarterly</div>
          <div style="font-size:11px;color:var(--muted);line-height:1.8;">• GDP growth<br>• MSFT / NVDA earnings<br>• S&amp;P 500 P/E<br>• Rebalancing check<br>• Update 401k export</div>
        </div>
        <div style="padding:14px;border:1px solid var(--border);border-radius:8px;">
          <div style="font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--red);margin-bottom:8px;">Trigger alerts</div>
          <div style="font-size:11px;color:var(--muted);line-height:1.8;">• MSFT drops &gt;20%<br>• VIX spikes above 35<br>• Any single stock &gt;45%<br>• Retirement fund closes</div>
        </div>
      </div>
    </div>
  </div>
</div>

<script>
function showTab(name, el) {{
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  el.classList.add('active');
}}

const mono = "'DM Mono', monospace";
const grid = 'rgba(255,255,255,0.05)';

// ── Investment data ──
const invTickers  = {json.dumps(inv_tickers)};
const invBgColors = {json.dumps(inv_colors)};
const invValues   = {json.dumps(inv_values)};
const invGains    = {json.dumps(inv_gains)};
const invGainPcts = {json.dumps(inv_gain_pcts)};
const invWeights  = {json.dumps(inv_weights)};

// ── Retirement data ──
const retLabels   = {json.dumps(ret_labels)};
const retValues   = {json.dumps(ret_values)};
const retGains    = {json.dumps(ret_gains)};
const retWeights  = {json.dumps(ret_weights)};
const retColors   = {json.dumps(ret_colors)};

// ── Growth projection ──
new Chart(document.getElementById('growthChart'), {{
  type: 'line',
  data: {{
    labels: {json.dumps(proj["years"])},
    datasets: [
      {{ label:'Moderate 7%', data:{json.dumps(proj["moderate"])}, borderColor:'#34d399', backgroundColor:'rgba(52,211,153,0.06)', tension:.4, borderWidth:2, pointRadius:3, fill:true }},
      {{ label:'Conservative 5%', data:{json.dumps(proj["conservative"])}, borderColor:'#60a5fa', borderDash:[4,4], backgroundColor:'transparent', tension:.4, borderWidth:1.5, pointRadius:0 }},
      {{ label:'Optimistic 10%', data:{json.dumps(proj["optimistic"])}, borderColor:'#fbbf24', borderDash:[2,4], backgroundColor:'transparent', tension:.4, borderWidth:1.5, pointRadius:0 }}
    ]
  }},
  options: {{
    responsive:true, maintainAspectRatio:false,
    plugins:{{ legend:{{display:false}}, tooltip:{{callbacks:{{label:c=>' $'+c.parsed.y.toLocaleString()}}}} }},
    scales:{{
      x:{{ticks:{{color:'#6b7280',font:{{family:mono,size:11}}}},grid:{{color:grid}}}},
      y:{{ticks:{{color:'#6b7280',font:{{family:mono,size:11}},callback:v=>'$'+(v/1000).toFixed(0)+'K'}},grid:{{color:grid}}}}
    }}
  }}
}});

// ── Investment allocation donut ──
new Chart(document.getElementById('allocDonut'), {{
  type:'doughnut',
  data:{{ labels:invTickers, datasets:[{{ data:invWeights, backgroundColor:invBgColors, borderWidth:0, hoverOffset:4 }}] }},
  options:{{ responsive:true, maintainAspectRatio:false, cutout:'65%', plugins:{{ legend:{{display:false}}, tooltip:{{callbacks:{{label:c=>' '+c.label+': '+c.parsed+'%'}}}} }} }}
}});

// ── Portfolio split donut (investments vs retirement) ──
new Chart(document.getElementById('splitDonut'), {{
  type:'doughnut',
  data:{{
    labels:['Investments','Retirement'],
    datasets:[{{ data:[{inv_v}, {ret_v}], backgroundColor:['#60a5fa','#34d399'], borderWidth:0, hoverOffset:4 }}]
  }},
  options:{{ responsive:true, maintainAspectRatio:false, cutout:'60%',
    plugins:{{ legend:{{display:true, position:'bottom', labels:{{color:'#6b7280',font:{{family:mono,size:10}},boxWidth:8}}}},
    tooltip:{{callbacks:{{label:c=>' $'+c.parsed.toLocaleString()}}}} }}
  }}
}});

// ── Investment gain bar ──
new Chart(document.getElementById('gainChart'), {{
  type:'bar',
  data:{{ labels:invTickers, datasets:[{{ data:invGains, backgroundColor:ctx=>ctx.raw<0?'#f87171':'#34d399', borderWidth:0, borderRadius:3 }}] }},
  options:{{
    responsive:true, maintainAspectRatio:false,
    plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:c=>' $'+c.parsed.y.toLocaleString()}}}}}},
    scales:{{
      x:{{ticks:{{color:'#6b7280',font:{{family:mono,size:11}}}},grid:{{display:false}}}},
      y:{{ticks:{{color:'#6b7280',font:{{family:mono,size:11}},callback:v=>'$'+(v/1000).toFixed(0)+'K'}},grid:{{color:grid}}}}
    }}
  }}
}});

// ── Investment return % bar ──
new Chart(document.getElementById('returnPct'), {{
  type:'bar',
  data:{{ labels:invTickers, datasets:[{{ data:invGainPcts, backgroundColor:ctx=>ctx.raw<0?'#f87171':'#60a5fa', borderWidth:0, borderRadius:3 }}] }},
  options:{{
    responsive:true, maintainAspectRatio:false,
    plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:c=>' '+c.parsed.y.toFixed(1)+'%'}}}}}},
    scales:{{
      x:{{ticks:{{color:'#6b7280',font:{{family:mono,size:11}}}},grid:{{display:false}}}},
      y:{{ticks:{{color:'#6b7280',font:{{family:mono,size:11}},callback:v=>v+'%'}},grid:{{color:grid}}}}
    }}
  }}
}});

// ── Retirement allocation donut ──
new Chart(document.getElementById('retAllocDonut'), {{
  type:'doughnut',
  data:{{ labels:retLabels, datasets:[{{ data:retWeights, backgroundColor:retColors, borderWidth:0, hoverOffset:4 }}] }},
  options:{{ responsive:true, maintainAspectRatio:false, cutout:'60%',
    plugins:{{ legend:{{display:false}}, tooltip:{{callbacks:{{label:c=>' '+c.parsed.toFixed(1)+'%'}}}} }}
  }}
}});

// ── Retirement gain bar ──
new Chart(document.getElementById('retGainChart'), {{
  type:'bar',
  data:{{ labels:retLabels, datasets:[{{ data:retGains, backgroundColor:ctx=>ctx.raw<0?'#f87171':'#34d399', borderWidth:0, borderRadius:3 }}] }},
  options:{{
    responsive:true, maintainAspectRatio:false,
    plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:c=>' $'+c.parsed.y.toLocaleString()}}}}}},
    scales:{{
      x:{{ticks:{{color:'#6b7280',font:{{family:mono,size:9}},maxRotation:30}},grid:{{display:false}}}},
      y:{{ticks:{{color:'#6b7280',font:{{family:mono,size:11}},callback:v=>'$'+(v/1000).toFixed(0)+'K'}},grid:{{color:grid}}}}
    }}
  }}
}});

// ── Performance history ──
const histDatasets = {json.dumps(hist_datasets)};
const lineColors   = ['#34d399','#60a5fa','#a78bfa','#fbbf24','#f472b6'];
new Chart(document.getElementById('histChart'), {{
  type:'line',
  data:{{ labels:{json.dumps(hist_labels)}, datasets:histDatasets }},
  options:{{
    responsive:true, maintainAspectRatio:false,
    plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:c=>' '+c.dataset.label+': '+c.parsed.y.toFixed(1)}}}}}},
    scales:{{
      x:{{ticks:{{color:'#6b7280',font:{{family:mono,size:10}},maxTicksLimit:8}},grid:{{color:grid}}}},
      y:{{ticks:{{color:'#6b7280',font:{{family:mono,size:11}},callback:v=>v.toFixed(0)}},grid:{{color:grid}}}}
    }}
  }}
}});
const leg = document.getElementById('histLegend');
histDatasets.forEach((d,i) => {{
  const el = document.createElement('span'); el.className='legend-item';
  el.innerHTML=`<span class="legend-dot" style="background:${{lineColors[i]}};"></span>${{d.label}}`;
  leg.appendChild(el);
}});

// ── Health radar ──
new Chart(document.getElementById('radarChart'), {{
  type:'radar',
  data:{{
    labels:['Diversification','Bond coverage','Geog. spread','Inflation hedge','Sector coverage','Retirement coverage'],
    datasets:[
      {{ label:'Current', data:[40,0,55,45,40,{min(100, round(ret_v/combined_v*100*2))}], borderColor:'#60a5fa', backgroundColor:'rgba(96,165,250,0.1)', pointBackgroundColor:'#60a5fa', borderWidth:2 }},
      {{ label:'Target',  data:[75,70,70,70,75,75], borderColor:'#34d399', backgroundColor:'rgba(52,211,153,0.05)', pointBackgroundColor:'#34d399', borderWidth:1.5, borderDash:[4,4] }}
    ]
  }},
  options:{{
    responsive:true, maintainAspectRatio:false, plugins:{{legend:{{display:false}}}},
    scales:{{r:{{min:0,max:100,ticks:{{display:false}},grid:{{color:'rgba(255,255,255,0.06)'}},
      pointLabels:{{color:'#6b7280',font:{{family:mono,size:10}}}},angleLines:{{color:'rgba(255,255,255,0.06)'}}}}}}
  }}
}});
</script>
</body>
</html>"""
    return html

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("Loading holdings...")
    holdings     = load_holdings()
    ret_holdings = load_retirement_holdings()

    print("Fetching investment prices...")
    prices = fetch_prices(holdings)

    print("Fetching retirement prices...")
    ret_prices = fetch_retirement_prices(ret_holdings)

    print("Fetching 12-month history...")
    inv_tickers = [h["ticker"] for h in holdings]
    history = fetch_history(inv_tickers)

    print("Computing metrics...")
    metrics     = compute_metrics(holdings, prices)
    ret_metrics = compute_retirement_metrics(ret_holdings, ret_prices)
    combined_v  = metrics["total_value"] + ret_metrics["total_value"]
    proj        = growth_projection(combined_v)
    asset_s     = asset_class_summary(metrics["rows"])

    updated_at = datetime.now().strftime("%b %d, %Y %H:%M UTC")

    print("Building HTML...")
    html = build_html(metrics, ret_metrics, proj, history, asset_s, updated_at)

    os.makedirs("docs", exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Done — written to {OUTPUT_FILE}")
    print(f"Investments: ${metrics['total_value']:,.2f}")
    print(f"Retirement:  ${ret_metrics['total_value']:,.2f}")
    print(f"Combined:    ${combined_v:,.2f}")

if __name__ == "__main__":
    main()
