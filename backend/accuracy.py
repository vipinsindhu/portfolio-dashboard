"""
Signal accuracy tracking.

Signals are captured into an append-only history file (signal_history.json,
committed to the repo by the daily GitHub Actions workflow, which is what
makes it survive Railway's ephemeral filesystem). Evaluation matches each
signal's stated horizon:

- short_term (and legacy untagged) entries: scored at 30 days, absolute —
  buy wins if the return is positive, avoid if negative, hold if within
  +/-HOLD_WIN_BAND_PCT.
- long_term entries: scored at 90 days RELATIVE TO SPY (the honest long-term
  claim is "beats the market", not "goes up") — buy wins if the stock beat
  SPY over the window, avoid wins if it lagged SPY, hold wins if it tracked
  SPY within +/-HOLD_WIN_BAND_PCT points.

Run as a script (daily, via .github/workflows/accuracy.yml):
    python backend/accuracy.py [--base-url https://... ] [--history path]

The Flask endpoint /api/signals/accuracy reads the same history file and
serves compute_accuracy_stats(); it never fetches prices itself.
"""

import argparse
import json
import os
from datetime import datetime, timedelta

HISTORY_FILE = "signal_history.json"
DEFAULT_BASE_URL = "https://portfolio-builder.up.railway.app"
EVALUATION_WINDOW_DAYS = 30        # short_term and legacy entries
LONG_TERM_WINDOW_DAYS = 90         # long_term entries, scored vs the market
BENCHMARK_TICKER = "SPY"
HOLD_WIN_BAND_PCT = 5.0
# Give up on entries we still can't price this long after they become due
EVALUATION_RETRY_DAYS = 30


def evaluation_window_days(entry):
    return LONG_TERM_WINDOW_DAYS if entry.get("timeframe") == "long_term" else EVALUATION_WINDOW_DAYS


# ---------- storage ----------

def load_history(path=HISTORY_FILE):
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Accuracy] Error reading {path}: {e}")
    return {"signals": [], "updated_at": None}


def save_history(history, path=HISTORY_FILE):
    history["updated_at"] = datetime.utcnow().isoformat()
    with open(path, "w") as f:
        json.dump(history, f, indent=1)


# ---------- pure logic ----------

def merge_signals_into_history(history, signals, captured_at=None):
    """Append signals not seen before (by id). Returns number added."""
    captured_at = captured_at or datetime.utcnow().isoformat()
    known = {entry["id"] for entry in history["signals"]}
    added = 0

    for s in signals:
        sid = s.get("id")
        if not sid or sid in known or not s.get("ticker") or not s.get("direction"):
            continue
        if s.get("source") == "mock":
            continue  # never score mock fallback signals as if they were real calls
        history["signals"].append({
            "id": sid,
            "ticker": s["ticker"],
            "direction": s["direction"],
            "confidence": s.get("confidence"),
            "sector": s.get("sector"),
            "timeframe": s.get("timeframe"),
            "created_at": s.get("created_at") or captured_at,
            "captured_at": captured_at,
            "result": None,
            "return_pct": None,
            "evaluated_at": None,
        })
        known.add(sid)
        added += 1

    return added


def classify_outcome(direction, return_pct, benchmark_return_pct=None):
    """Absolute rules for short-term; relative-to-benchmark for long-term."""
    if benchmark_return_pct is not None:
        excess = return_pct - benchmark_return_pct
        if direction == "buy":
            return "win" if excess > 0 else "loss"
        if direction == "avoid":
            return "win" if excess < 0 else "loss"
        if direction == "hold":
            return "win" if abs(excess) <= HOLD_WIN_BAND_PCT else "loss"
        return None

    if direction == "buy":
        return "win" if return_pct > 0 else "loss"
    if direction == "avoid":
        return "win" if return_pct < 0 else "loss"
    if direction == "hold":
        return "win" if abs(return_pct) <= HOLD_WIN_BAND_PCT else "loss"
    return None


def evaluate_pending(history, price_fetcher, now=None):
    """
    Evaluate entries whose timeframe-specific window has elapsed.

    price_fetcher(ticker, start_date, end_date) -> (entry_price, exit_price)
    or None when prices are unavailable. Returns number evaluated.
    """
    now = now or datetime.utcnow()
    evaluated = 0
    benchmark_cache = {}

    for entry in history["signals"]:
        if entry["result"] is not None:
            continue

        try:
            created = datetime.fromisoformat(entry["created_at"])
        except (ValueError, TypeError):
            entry["result"] = "invalid"
            continue

        due_at = created + timedelta(days=evaluation_window_days(entry))
        if now < due_at:
            continue  # not due yet

        prices = None
        try:
            prices = price_fetcher(entry["ticker"], created, due_at)
        except Exception as e:
            print(f"[Accuracy] Price fetch failed for {entry['ticker']}: {e}")

        if not prices or not prices[0]:
            # leave pending so the next run retries; give up eventually
            if now > due_at + timedelta(days=EVALUATION_RETRY_DAYS):
                entry["result"] = "unavailable"
            continue

        # Long-term entries are scored against the market over the same window
        benchmark_return_pct = None
        if entry.get("timeframe") == "long_term":
            cache_key = (created.date().isoformat(), due_at.date().isoformat())
            if cache_key not in benchmark_cache:
                try:
                    benchmark_cache[cache_key] = price_fetcher(BENCHMARK_TICKER, created, due_at)
                except Exception as e:
                    print(f"[Accuracy] Benchmark fetch failed: {e}")
                    benchmark_cache[cache_key] = None
            benchmark = benchmark_cache[cache_key]
            if not benchmark or not benchmark[0]:
                # can't honestly score long-term without the benchmark; retry
                if now > due_at + timedelta(days=EVALUATION_RETRY_DAYS):
                    entry["result"] = "unavailable"
                continue
            benchmark_return_pct = (benchmark[1] - benchmark[0]) / benchmark[0] * 100
            entry["benchmark_return_pct"] = round(benchmark_return_pct, 2)

        entry_price, exit_price = prices
        return_pct = (exit_price - entry_price) / entry_price * 100
        entry["return_pct"] = round(return_pct, 2)
        entry["result"] = classify_outcome(entry["direction"], return_pct, benchmark_return_pct)
        entry["evaluated_at"] = now.isoformat()
        evaluated += 1

    return evaluated


def compute_accuracy_stats(history, now=None, window_weeks=4):
    """Rolling and overall win rates over evaluated entries."""
    now = now or datetime.utcnow()
    cutoff = now - timedelta(weeks=window_weeks)

    def summarize(entries):
        scored = [e for e in entries if e["result"] in ("win", "loss")]
        wins = len([e for e in scored if e["result"] == "win"])
        return {
            "evaluated": len(scored),
            "wins": wins,
            "win_rate": round(wins / len(scored) * 100, 1) if scored else None,
        }

    entries = history.get("signals", [])
    recent = [
        e for e in entries
        if e.get("evaluated_at") and datetime.fromisoformat(e["evaluated_at"]) >= cutoff
    ]

    by_direction = {}
    for direction in ("buy", "hold", "avoid"):
        by_direction[direction] = summarize(
            [e for e in entries if e["direction"] == direction]
        )

    by_timeframe = {}
    for timeframe in ("short_term", "long_term"):
        by_timeframe[timeframe] = summarize(
            [e for e in entries if e.get("timeframe") == timeframe]
        )

    pending = len([e for e in entries if e["result"] is None])
    captured_dates = [e.get("captured_at") for e in entries if e.get("captured_at")]

    return {
        "window_weeks": window_weeks,
        "recent": summarize(recent),
        "overall": summarize(entries),
        "by_direction": by_direction,
        "by_timeframe": by_timeframe,
        "pending": pending,
        "tracked_total": len(entries),
        "tracking_since": min(captured_dates) if captured_dates else None,
    }


# ---------- live data adapters ----------

def fetch_prices_yfinance(ticker, start, end):
    """Closing price on/after `start` and on/before `end` (datetimes)."""
    import yfinance as yf

    data = yf.Ticker(ticker).history(
        start=start.strftime("%Y-%m-%d"),
        # pad the end so the last trading day inside the window is included
        end=(end + timedelta(days=4)).strftime("%Y-%m-%d"),
        auto_adjust=True,
    )
    closes = data["Close"].dropna()
    if closes.empty:
        return None

    in_window = closes[closes.index.tz_localize(None) <= end.replace(tzinfo=None) + timedelta(days=1)]
    if in_window.empty:
        return None

    return float(closes.iloc[0]), float(in_window.iloc[-1])


def fetch_live_signals(base_url):
    import requests

    response = requests.get(f"{base_url}/api/signals/archive", params={"limit": 200}, timeout=30)
    response.raise_for_status()
    return response.json().get("signals", [])


def run_update(base_url=DEFAULT_BASE_URL, history_path=HISTORY_FILE):
    history = load_history(history_path)

    try:
        signals = fetch_live_signals(base_url)
        added = merge_signals_into_history(history, signals)
        print(f"[Accuracy] Captured {added} new signal(s) from {base_url}")
    except Exception as e:
        print(f"[Accuracy] Could not fetch live signals ({e}); evaluating existing history only")

    evaluated = evaluate_pending(history, fetch_prices_yfinance)
    print(f"[Accuracy] Evaluated {evaluated} signal(s)")

    save_history(history, history_path)
    stats = compute_accuracy_stats(history)
    print(f"[Accuracy] Stats: {json.dumps(stats['overall'])}, pending={stats['pending']}")
    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update signal accuracy history")
    parser.add_argument("--base-url", default=os.getenv("SIGNALS_API_BASE", DEFAULT_BASE_URL))
    parser.add_argument("--history", default=HISTORY_FILE)
    args = parser.parse_args()
    run_update(args.base_url, args.history)
