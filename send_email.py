"""
Long-term Portfolio Email Notifier
Sends a weekly summary of investments + retirement via Gmail.
Requires GitHub Secrets: GMAIL_ADDRESS, GMAIL_APP_PASS, NOTIFY_EMAIL, DASHBOARD_URL
"""

import csv
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import yfinance as yf

# ── Config ────────────────────────────────────────────────────────────────────
HOLDINGS_FILE   = "holdings.csv"
RETIREMENT_FILE = "retirement_holdings.csv"

COST_BASIS = {
    "MSFT":  35788.51,
    "FXAIX": 70255.36,
    "VWO":   38041.75,
    "TMUS":  16401.19,
    "NVDA":  18449.10,
    "FBTC":  20449.96,
    "GLD":    9668.72,
}

GMAIL_ADDRESS = os.environ["GMAIL_ADDRESS"]
GMAIL_APP_PASS = os.environ["GMAIL_APP_PASS"]
NOTIFY_EMAIL  = os.environ["NOTIFY_EMAIL"]
DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "")

# ── Load & price investments ──────────────────────────────────────────────────
def load_and_price():
    holdings = []
    with open(HOLDINGS_FILE) as f:
        for row in csv.DictReader(f):
            holdings.append({
                "ticker": row["ticker"].strip(),
                "shares": float(row["shares"]),
                "name":   row["name"].strip(),
            })

    tickers = [h["ticker"] for h in holdings]
    raw = yf.download(tickers, period="2d", auto_adjust=True, progress=False)

    rows = []
    total_value = total_cost = total_day_gain = 0

    for h in holdings:
        t = h["ticker"]
        try:
            closes     = raw["Close"][t].dropna()
            price      = float(closes.iloc[-1])
            prev_price = float(closes.iloc[-2]) if len(closes) >= 2 else price
        except Exception:
            price = prev_price = 0

        shares   = h["shares"]
        cost     = COST_BASIS.get(t, 0)
        value    = round(price * shares, 2)
        gain     = round(value - cost, 2)
        gain_pct = round(gain / cost * 100, 2) if cost else 0
        day_gain = round((price - prev_price) * shares, 2)
        day_pct  = round((price - prev_price) / prev_price * 100, 2) if prev_price else 0

        total_value    += value
        total_cost     += cost
        total_day_gain += day_gain

        rows.append({
            "ticker": t, "name": h["name"], "price": price,
            "value": value, "gain": gain, "gain_pct": gain_pct,
            "day_gain": day_gain, "day_pct": day_pct,
        })

    for r in rows:
        r["weight"] = round(r["value"] / total_value * 100, 2) if total_value else 0
    rows.sort(key=lambda x: x["value"], reverse=True)

    total_gain     = round(total_value - total_cost, 2)
    total_gain_pct = round(total_gain / total_cost * 100, 2) if total_cost else 0
    total_day_pct  = round(total_day_gain / (total_value - total_day_gain) * 100, 2) if total_value else 0

    return rows, {
        "total_value": round(total_value, 2), "total_gain": round(total_gain, 2),
        "total_gain_pct": total_gain_pct, "total_day_gain": round(total_day_gain, 2),
        "total_day_pct": total_day_pct,
    }

# ── Load & price retirement ───────────────────────────────────────────────────
def load_and_price_retirement():
    holdings = []
    with open(RETIREMENT_FILE) as f:
        for row in csv.DictReader(f):
            holdings.append({
                "ticker":       row["ticker"].strip(),
                "shares":       float(row["shares"]),
                "name":         row["name"].strip(),
                "account":      row["account"].strip(),
                "fetch_live":   row["fetch_live"].strip().lower() == "yes",
                "last_price":   float(row["last_price"]),
                "cost_basis":   float(row["cost_basis"]),
                "last_day_gain":      float(row["last_day_gain"]),
                "last_day_gain_pct":  float(row["last_day_gain_pct"]),
                "price_ticker": row.get("price_ticker", "").strip(),
                "exact_proxy":  row.get("exact_proxy", "no").strip().lower() == "yes",
            })

    # Batch-fetch all unique proxy tickers
    proxy_tickers = list({h["price_ticker"] for h in holdings if h["fetch_live"] and h["price_ticker"]})
    price_map = {}
    if proxy_tickers:
        try:
            if len(proxy_tickers) == 1:
                raw = yf.download(proxy_tickers[0], period="2d", auto_adjust=True, progress=False)
                closes = raw["Close"].dropna()
                p_today = float(closes.iloc[-1])
                p_prev  = float(closes.iloc[-2]) if len(closes) >= 2 else p_today
                price_map[proxy_tickers[0]] = {"price": p_today, "day_pct": (p_today - p_prev) / p_prev * 100 if p_prev else 0}
            else:
                raw = yf.download(proxy_tickers, period="2d", auto_adjust=True, progress=False)
                for pt in proxy_tickers:
                    try:
                        closes = raw["Close"][pt].dropna()
                        p_today = float(closes.iloc[-1])
                        p_prev  = float(closes.iloc[-2]) if len(closes) >= 2 else p_today
                        price_map[pt] = {"price": p_today, "day_pct": (p_today - p_prev) / p_prev * 100 if p_prev else 0}
                    except Exception:
                        pass
        except Exception:
            pass

    total_value = total_cost = total_gain = 0
    by_account = {}

    for h in holdings:
        pt = h["price_ticker"]
        if h["fetch_live"] and pt and pt in price_map:
            if pt == h["ticker"]:
                price = price_map[pt]["price"]
            else:
                price = h["last_price"] * (1 + price_map[pt]["day_pct"] / 100)
        else:
            price = h["last_price"]
        price = round(price, 6)
        value = round(price * h["shares"], 2)
        cost  = h["cost_basis"]
        gain  = round(value - cost, 2)

        total_value += value
        total_cost  += cost
        total_gain  += gain

        acct = h["account"]
        if acct not in by_account:
            by_account[acct] = {"value": 0, "gain": 0}
        by_account[acct]["value"] = round(by_account[acct]["value"] + value, 2)
        by_account[acct]["gain"]  = round(by_account[acct]["gain"] + gain, 2)

    total_gain_pct = round(total_gain / total_cost * 100, 2) if total_cost else 0

    return {
        "total_value": round(total_value, 2),
        "total_gain":  round(total_gain, 2),
        "total_gain_pct": total_gain_pct,
        "by_account":  by_account,
    }

# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt(v):
    sign = "+" if v >= 0 else ""
    return f"{sign}${abs(v):,.2f}" if abs(v) >= 0.01 else "$0.00"

def fmtp(v):
    sign = "+" if v >= 0 else ""
    return f"{sign}{v:.2f}%"

def arrow(v):
    return "▲" if v >= 0 else "▼"

def clr(v):
    return "#16a34a" if v >= 0 else "#dc2626"

# ── Build HTML email ──────────────────────────────────────────────────────────
def build_email(rows, summary, ret_summary, updated_at):
    inv_v  = summary["total_value"]
    inv_g  = summary["total_gain"]
    inv_gp = summary["total_gain_pct"]
    inv_dg = summary["total_day_gain"]
    inv_dp = summary["total_day_pct"]

    ret_v  = ret_summary["total_value"]
    ret_g  = ret_summary["total_gain"]
    ret_gp = ret_summary["total_gain_pct"]

    combined_v = inv_v + ret_v
    combined_g = inv_g + ret_g

    # Alerts
    alerts = []
    top = max(rows, key=lambda x: x["weight"])
    if top["weight"] > 35:
        alerts.append(f"⚠ <strong>{top['ticker']}</strong> is {top['weight']:.1f}% of investments — consider rebalancing.")
    if inv_dp < -2:
        alerts.append(f"📉 Investments down <strong>{inv_dp:.2f}%</strong> today — significant daily move.")
    for r in rows:
        if r["gain_pct"] < 0:
            alerts.append(f"🔴 <strong>{r['ticker']}</strong> at a total loss ({fmtp(r['gain_pct'])}) — review position.")

    alerts_html = ""
    if alerts:
        items = "".join(f"<li style='margin-bottom:6px;'>{a}</li>" for a in alerts)
        alerts_html = f"""
        <div style="background:#fefce8;border:1px solid #fde68a;border-radius:8px;padding:16px 20px;margin-bottom:20px;">
          <p style="font-size:13px;font-weight:600;color:#92400e;margin:0 0 10px;">Alerts</p>
          <ul style="margin:0;padding-left:18px;font-size:13px;color:#78350f;line-height:1.7;">{items}</ul>
        </div>"""

    # Investment rows
    inv_rows_html = ""
    for r in rows:
        c  = clr(r["gain"])
        dc = clr(r["day_gain"])
        inv_rows_html += f"""
        <tr style="border-bottom:1px solid #f3f4f6;">
          <td style="padding:10px 12px;">
            <strong style="font-size:13px;">{r['ticker']}</strong>
            <div style="font-size:11px;color:#6b7280;">{r['name']}</div>
          </td>
          <td style="padding:10px 12px;text-align:right;font-size:13px;">${r['price']:,.2f}</td>
          <td style="padding:10px 12px;text-align:right;font-size:13px;">${r['value']:,.2f}</td>
          <td style="padding:10px 12px;text-align:right;font-size:13px;">{r['weight']:.1f}%</td>
          <td style="padding:10px 12px;text-align:right;font-size:13px;color:{c};">{fmt(r['gain'])}<br><span style="font-size:11px;">{fmtp(r['gain_pct'])}</span></td>
          <td style="padding:10px 12px;text-align:right;font-size:13px;color:{dc};">{arrow(r['day_gain'])} {fmtp(r['day_pct'])}</td>
        </tr>"""

    best  = max(rows, key=lambda x: x["gain_pct"])
    worst = min(rows, key=lambda x: x["gain_pct"])

    # Retirement account rows
    ret_acct_html = ""
    for acct, data in ret_summary["by_account"].items():
        acct_gp = round(data["gain"] / (data["value"] - data["gain"]) * 100, 2) if data["value"] != data["gain"] else 0
        ret_acct_html += f"""
        <tr style="border-bottom:1px solid #f3f4f6;">
          <td style="padding:10px 12px;font-size:13px;">{acct}</td>
          <td style="padding:10px 12px;text-align:right;font-size:13px;">${data['value']:,.0f}</td>
          <td style="padding:10px 12px;text-align:right;font-size:13px;color:{clr(data['gain'])};">{fmt(data['gain'])}</td>
          <td style="padding:10px 12px;text-align:right;font-size:13px;color:{clr(acct_gp)};">{fmtp(acct_gp)}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f9fafb;font-family:'Helvetica Neue',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f9fafb;padding:32px 16px;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">

  <!-- Header -->
  <tr><td style="background:#0d0f12;border-radius:12px 12px 0 0;padding:28px 32px;">
    <p style="margin:0;font-size:12px;color:#6b7280;letter-spacing:.08em;text-transform:uppercase;">Long-term portfolio</p>
    <h1 style="margin:6px 0 4px;font-size:28px;font-weight:300;color:#ffffff;">${combined_v:,.0f}</h1>
    <p style="margin:0;font-size:13px;color:#6b7280;">Combined · {updated_at}</p>
  </td></tr>

  <!-- Summary stats -->
  <tr><td style="background:#ffffff;padding:24px 32px 8px;">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>
        <td style="width:33%;padding-right:12px;">
          <div style="background:#f9fafb;border-radius:8px;padding:14px 16px;">
            <p style="margin:0 0 4px;font-size:10px;color:#9ca3af;text-transform:uppercase;letter-spacing:.08em;">Investments</p>
            <p style="margin:0;font-size:18px;font-weight:300;color:#111827;">${inv_v:,.0f}</p>
            <p style="margin:2px 0 0;font-size:11px;color:{clr(inv_dg)};">{arrow(inv_dg)} {fmtp(inv_dp)} today</p>
          </div>
        </td>
        <td style="width:33%;padding-right:12px;">
          <div style="background:#f9fafb;border-radius:8px;padding:14px 16px;">
            <p style="margin:0 0 4px;font-size:10px;color:#9ca3af;text-transform:uppercase;letter-spacing:.08em;">Retirement</p>
            <p style="margin:0;font-size:18px;font-weight:300;color:#111827;">${ret_v:,.0f}</p>
            <p style="margin:2px 0 0;font-size:11px;color:{clr(ret_g)};">{fmt(ret_g)} ({fmtp(ret_gp)}) total</p>
          </div>
        </td>
        <td style="width:33%;">
          <div style="background:#f9fafb;border-radius:8px;padding:14px 16px;">
            <p style="margin:0 0 4px;font-size:10px;color:#9ca3af;text-transform:uppercase;letter-spacing:.08em;">Total gain</p>
            <p style="margin:0;font-size:18px;font-weight:300;color:{clr(combined_g)};">{fmt(combined_g)}</p>
            <p style="margin:2px 0 0;font-size:11px;color:#6b7280;">Best: {best['ticker']} {fmtp(best['gain_pct'])}</p>
          </div>
        </td>
      </tr>
    </table>
  </td></tr>

  <!-- Alerts -->
  <tr><td style="background:#ffffff;padding:12px 32px 0;">{alerts_html}</td></tr>

  <!-- Investment holdings -->
  <tr><td style="background:#ffffff;padding:8px 32px 20px;">
    <p style="font-size:10px;color:#9ca3af;text-transform:uppercase;letter-spacing:.08em;margin:0 0 10px;">Investments</p>
    <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #f3f4f6;border-radius:8px;overflow:hidden;">
      <thead><tr style="background:#f9fafb;">
        <th style="padding:8px 12px;text-align:left;font-size:10px;color:#9ca3af;font-weight:400;letter-spacing:.06em;text-transform:uppercase;">Symbol</th>
        <th style="padding:8px 12px;text-align:right;font-size:10px;color:#9ca3af;font-weight:400;letter-spacing:.06em;text-transform:uppercase;">Price</th>
        <th style="padding:8px 12px;text-align:right;font-size:10px;color:#9ca3af;font-weight:400;letter-spacing:.06em;text-transform:uppercase;">Value</th>
        <th style="padding:8px 12px;text-align:right;font-size:10px;color:#9ca3af;font-weight:400;letter-spacing:.06em;text-transform:uppercase;">Weight</th>
        <th style="padding:8px 12px;text-align:right;font-size:10px;color:#9ca3af;font-weight:400;letter-spacing:.06em;text-transform:uppercase;">Total gain</th>
        <th style="padding:8px 12px;text-align:right;font-size:10px;color:#9ca3af;font-weight:400;letter-spacing:.06em;text-transform:uppercase;">Today</th>
      </tr></thead>
      <tbody>{inv_rows_html}</tbody>
    </table>
  </td></tr>

  <!-- Retirement summary -->
  <tr><td style="background:#ffffff;padding:0 32px 24px;">
    <p style="font-size:10px;color:#9ca3af;text-transform:uppercase;letter-spacing:.08em;margin:0 0 10px;">Retirement accounts</p>
    <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #f3f4f6;border-radius:8px;overflow:hidden;">
      <thead><tr style="background:#f9fafb;">
        <th style="padding:8px 12px;text-align:left;font-size:10px;color:#9ca3af;font-weight:400;letter-spacing:.06em;text-transform:uppercase;">Account</th>
        <th style="padding:8px 12px;text-align:right;font-size:10px;color:#9ca3af;font-weight:400;letter-spacing:.06em;text-transform:uppercase;">Value</th>
        <th style="padding:8px 12px;text-align:right;font-size:10px;color:#9ca3af;font-weight:400;letter-spacing:.06em;text-transform:uppercase;">Total gain</th>
        <th style="padding:8px 12px;text-align:right;font-size:10px;color:#9ca3af;font-weight:400;letter-spacing:.06em;text-transform:uppercase;">Return</th>
      </tr></thead>
      <tbody>{ret_acct_html}</tbody>
    </table>
    <p style="font-size:10px;color:#9ca3af;margin:8px 0 0;">⚡ 401k fund prices from last exported file · IRA price is live</p>
  </td></tr>

  <!-- CTA -->
  <tr><td style="background:#ffffff;padding:0 32px 32px;text-align:center;">
    <a href="{DASHBOARD_URL}" style="display:inline-block;background:#0d0f12;color:#34d399;text-decoration:none;padding:12px 28px;border-radius:8px;font-size:13px;letter-spacing:.04em;">
      View full dashboard →
    </a>
  </td></tr>

  <!-- Footer -->
  <tr><td style="background:#f3f4f6;border-radius:0 0 12px 12px;padding:16px 32px;text-align:center;">
    <p style="margin:0;font-size:11px;color:#9ca3af;line-height:1.6;">
      Generated automatically · Prices via yfinance · Not financial advice.
    </p>
  </td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""
    return html

# ── Send email ────────────────────────────────────────────────────────────────
def send_email(subject, html_body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = NOTIFY_EMAIL
    msg.attach(MIMEText(html_body, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASS.replace(" ", ""))
        server.sendmail(GMAIL_ADDRESS, NOTIFY_EMAIL, msg.as_string())

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("Loading investments...")
    rows, summary = load_and_price()

    print("Loading retirement...")
    ret_summary = load_and_price_retirement()

    combined_v = summary["total_value"] + ret_summary["total_value"]
    inv_dp     = summary["total_day_pct"]
    updated_at = datetime.utcnow().strftime("%b %d, %Y")
    direction  = "▲" if inv_dp >= 0 else "▼"
    subject    = f"Portfolio · ${combined_v:,.0f} combined · {direction} {inv_dp:+.2f}% investments today · {updated_at}"

    print("Building email...")
    html = build_email(rows, summary, ret_summary, updated_at)

    print(f"Sending to {NOTIFY_EMAIL}...")
    send_email(subject, html)
    print("Email sent.")

if __name__ == "__main__":
    main()
