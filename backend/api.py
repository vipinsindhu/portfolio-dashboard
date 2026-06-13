"""
Stock Recommendation API
Flask backend serving signals, macro data, and analysis
Supports both file-based (development) and database-backed (production) storage
"""

import os
import sys
import threading
from dataclasses import asdict
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from signals import (
    auto_generate_signals,
    fetch_signal_candidates,
    generate_signals,
    generate_short_term_signals,
    generate_signals_if_stale,
    update_signal_accuracy,
    load_signals,
    save_signals,
    refresh_macro_data,
    fetch_macro_context,
    fetch_fundamentals,
)
from stock_discovery import discover_stocks
from sector_updater import update_sector_mappings
from educational import (
    get_all_lessons,
    get_lesson_by_id,
    get_lessons_by_category,
    get_lesson_categories,
)
from portfolio import (
    Portfolio,
    Holding,
    parse_csv,
    create_portfolio,
    validate_portfolio,
    save_portfolio,
    load_portfolio,
)
import analysis
import importlib
importlib.reload(analysis)
from analysis import analyze_portfolio
from signals_filter import (
    filter_signals_with_portfolio,
    TimeHorizon,
)

# Optional database imports
try:
    from config import get_config
    from models import init_db, get_session
    from signals_db import SignalStore, MacroConfigStore
    HAS_DATABASE = True
except ImportError:
    HAS_DATABASE = False

    class DummyConfig:
        def __init__(self):
            from storage_paths import data_path
            self.DATABASE_URL = "sqlite:///portfolio.db"
            self.CORS_ORIGINS = "*"
            self.SIGNALS_FILE = data_path("signals.json")
            self.MACRO_CONFIG_FILE = "macro_config.json"

    def get_config():
        return DummyConfig()


def create_app():
    # Determine frontend dist path - works in both dev and production
    # In Railway: /app/backend/api.py → /app/frontend/dist
    # In dev: ./backend/api.py → ./frontend/dist
    script_dir = os.path.dirname(os.path.abspath(__file__))  # ./backend or /app/backend
    base_dir = os.path.dirname(script_dir)  # . or /app
    frontend_dist = os.path.join(base_dir, "frontend", "dist")

    # Fallback to current working directory if path doesn't exist
    if not os.path.exists(frontend_dist):
        frontend_dist = os.path.join(os.getcwd(), "frontend", "dist")

    app = Flask(__name__)
    app.frontend_dist = frontend_dist  # Store for use in routes

    # Load configuration
    config = get_config()
    app.config.from_object(config.__dict__)

    # Initialize CORS
    CORS(app, origins=app.config.get("CORS_ORIGINS", "*").split(","))

    # Initialize storage (database optional, file storage fallback)
    use_database = HAS_DATABASE and app.config.get("DATABASE_URL")
    if use_database:
        try:
            engine = init_db(app.config.get("DATABASE_URL"))
            session = get_session(engine)
            signal_store = SignalStore(session=session, file_path=app.config.get("SIGNALS_FILE", "signals.json"))
            macro_store = MacroConfigStore(session=session, file_path=app.config.get("MACRO_CONFIG_FILE", "macro_config.json"))
            app.logger.info(f"Database initialized: {app.config['DATABASE_URL']}")
        except Exception as e:
            app.logger.warning(f"Database initialization failed, falling back to file storage: {e}")
            signal_store = SignalStore(session=None, file_path=app.config.get("SIGNALS_FILE", "signals.json"))
            macro_store = MacroConfigStore(session=None, file_path=app.config.get("MACRO_CONFIG_FILE", "macro_config.json"))
    else:
        # Fallback to simple file-based storage
        class SimpleSignalStore:
            def __init__(self):
                self.use_database = False
            def get_latest_signals(self, limit=5):
                signals = load_signals()
                return {"data": signals.get("signals", [])[:limit], "generated_at": signals.get("generated_at"), "total": len(signals.get("signals", []))}
            def get_signal_archive(self, limit=100):
                signals = load_signals()
                return {"signals": signals.get("signals", [])[:limit], "total": len(signals.get("signals", []))}
            def get_signal_by_id(self, signal_id):
                signals = load_signals()
                for s in signals.get("signals", []):
                    if s.get("id") == signal_id:
                        return s
                return None
            def save_signals(self, signals):
                # Replace signals completely (don't append) to avoid duplicates
                data = {
                    "signals": signals,
                    "generated_at": datetime.utcnow().isoformat()
                }
                save_signals(data)
                return True

        signal_store = SimpleSignalStore()
        macro_store = None
        if not use_database:
            storage_reason = "database not configured" if HAS_DATABASE else "database modules not available"
            app.logger.info(f"Using file-based storage ({storage_reason})")

    # ============= HEALTH & STATUS =============

    @app.route("/test")
    def test():
        return jsonify({"message": "test route works"}), 200

    @app.route("/api/health", methods=["GET"])
    def health():
        """Health check endpoint"""
        # List files in frontend directory for debugging
        files = []
        if os.path.exists(app.frontend_dist):
            try:
                files = os.listdir(app.frontend_dist)
            except Exception as e:
                files = [f"Error listing files: {e}"]

        return jsonify({
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "environment": app.config.get("FLASK_ENV"),
            "storage": "database" if signal_store.use_database else "file",
            "frontend_dist": app.frontend_dist,
            "frontend_exists": os.path.exists(app.frontend_dist),
            "frontend_files": files,
        }), 200

    # ============= FRONTEND ROUTES =============

    @app.route("/assets/<path:filename>")
    def serve_assets(filename):
        """Serve frontend assets"""
        assets_dir = os.path.join(app.frontend_dist, "assets")
        file_path = os.path.join(assets_dir, filename)

        # Debug logging
        app.logger.info(f"Asset request: {filename}")
        app.logger.info(f"Assets dir: {assets_dir}")
        app.logger.info(f"File path: {file_path}")
        app.logger.info(f"File exists: {os.path.exists(file_path)}")

        if not os.path.exists(file_path):
            app.logger.error(f"Asset not found: {file_path}")
            return jsonify({"error": "Asset not found"}), 404

        try:
            response = send_from_directory(assets_dir, filename)
            # Vite fingerprints asset filenames, so they are safe to cache forever
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            return response
        except Exception as e:
            app.logger.error(f"Error serving asset {filename}: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path):
        """Serve React frontend - catch-all for non-API routes"""
        if path.startswith("api/"):
            return jsonify({"error": "Endpoint not found"}), 404

        if not os.path.exists(app.frontend_dist):
            return jsonify({"error": f"Frontend not found at {app.frontend_dist}"}), 500

        full_path = os.path.join(app.frontend_dist, path)
        if os.path.isfile(full_path) and not path.endswith(".html"):
            response = send_from_directory(app.frontend_dist, path)
            # Unfingerprinted files (manifest, icons): cache briefly
            response.headers["Cache-Control"] = "public, max-age=3600"
            return response
        # index.html must always revalidate, otherwise phones keep showing
        # stale UI for days after a deploy
        response = send_from_directory(app.frontend_dist, "index.html")
        response.headers["Cache-Control"] = "no-cache"
        return response

    # ============= MACRO ENDPOINTS =============

    @app.route("/api/macro", methods=["GET"])
    def get_macro():
        """Return current macro configuration"""
        if macro_store:
            config = macro_store.get_config()
        else:
            config = {"macro_signals": {}, "last_updated": None}
        return jsonify(config), 200

    @app.route("/api/macro-signals", methods=["GET"])
    def get_macro_signals():
        """Return macro signals"""
        config = macro_store.get_config() if macro_store else {"macro_signals": {}, "last_updated": None}
        return jsonify({
            "signals": config.get("macro_signals", {}),
            "last_updated": config.get("last_updated")
        }), 200

    # ============= SIGNAL ENDPOINTS =============

    @app.route("/api/signals", methods=["GET"])
    def get_signals():
        """Get latest signals"""
        limit = request.args.get("limit", 5, type=int)
        signals_data = signal_store.get_latest_signals(limit)
        return jsonify(signals_data), 200

    @app.route("/api/stats", methods=["GET"])
    def get_stats():
        """Aggregate counts for the Welcome page stats section."""
        try:
            all_signals = signal_store.get_latest_signals(200).get("data", [])
            tickers = {s["ticker"] for s in all_signals if s.get("ticker")}
            sectors = {s["sector"] for s in all_signals if s.get("sector") and s["sector"] != "Other"}
            return jsonify({
                "ticker_count": len(tickers),
                "sector_count": len(sectors),
            }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/signals/accuracy", methods=["GET"])
    def get_signals_accuracy():
        """Rolling win-rate stats from the committed signal history"""
        try:
            from accuracy import load_history, compute_accuracy_stats
            stats = compute_accuracy_stats(load_history())
            return jsonify(stats), 200
        except Exception as e:
            app.logger.error(f"Error computing accuracy stats: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/signals/history", methods=["GET"])
    def get_signal_history():
        """Pre-registered track record: past calls from signal_history.json
        with their evaluated outcomes (win/loss/pending).

        Query parameters:
        - timeframe: short_term | long_term (untagged legacy counts as long_term)
        - direction: buy | hold | avoid
        - result: win | loss | pending
        - limit: max entries, newest first (default 200)
        """
        try:
            from accuracy import load_history, compute_accuracy_stats

            timeframe = request.args.get("timeframe")
            direction = request.args.get("direction")
            result = request.args.get("result")
            limit = request.args.get("limit", 200, type=int)

            history = load_history()
            entries = history.get("signals", [])

            if timeframe:
                entries = [e for e in entries if (e.get("timeframe") or "long_term") == timeframe]
            if direction:
                entries = [e for e in entries if e.get("direction") == direction]
            if result == "pending":
                entries = [e for e in entries if e.get("result") is None]
            elif result:
                entries = [e for e in entries if e.get("result") == result]

            entries = sorted(
                entries, key=lambda e: e.get("created_at") or "", reverse=True
            )[:limit]

            return jsonify({
                "entries": entries,
                "total": len(entries),
                "stats": compute_accuracy_stats(history),
            }), 200
        except Exception as e:
            app.logger.error(f"Error getting signal history: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/signals/archive", methods=["GET"])
    def get_signals_archive():
        """Get signal archive (past signals)"""
        limit = request.args.get("limit", 100, type=int)
        sector = request.args.get("sector", None, type=str)

        if sector:
            signals = signal_store.get_signals_by_sector(sector, limit)
            return jsonify({"signals": signals, "total": len(signals)}), 200

        archive = signal_store.get_signal_archive(limit)
        return jsonify(archive), 200

    @app.route("/api/signals/short-term", methods=["GET"])
    def get_short_term_signals():
        """Get top 10 buy/avoid signals for short-term trading

        Query parameters:
        - limit: number of signals to return (default: 10)
        - direction: filter by direction (buy/hold/avoid, default: all)
        - min_confidence: minimum confidence threshold (1-10, default: 6)
        - sector: filter by sector (default: all)
        """
        try:
            limit = request.args.get("limit", 10, type=int)
            direction = request.args.get("direction", None, type=str)
            min_confidence = request.args.get("min_confidence", 6, type=int)
            sector = request.args.get("sector", None, type=str)

            # Get latest 50 signals to filter from (increased for better sector diversity)
            signals_response = signal_store.get_latest_signals(50)
            all_signals = signals_response.get("data", []) if isinstance(signals_response, dict) else []
            generated_at = signals_response.get("generated_at") if isinstance(signals_response, dict) else None

            # Use the short-term generation pass when available; legacy
            # stores (no timeframe tags) fall back to the whole pool
            short_term_pool = [s for s in all_signals if s.get("timeframe") == "short_term"]
            if short_term_pool:
                all_signals = short_term_pool

            # Filter signals
            filtered_signals = []
            for signal in all_signals:
                # Check confidence threshold
                if signal.get("confidence", 0) < min_confidence:
                    continue

                # Check direction filter
                if direction and signal.get("direction") != direction:
                    continue

                # Check sector filter
                if sector and signal.get("sector") != sector:
                    continue

                filtered_signals.append(signal)

            # Deduplicate by ticker (keep highest confidence for each stock)
            ticker_signals = {}
            for signal in filtered_signals:
                ticker = signal.get("ticker", "")
                if ticker:
                    # Keep signal with highest confidence for this ticker
                    if ticker not in ticker_signals or signal.get("confidence", 0) > ticker_signals[ticker].get("confidence", 0):
                        ticker_signals[ticker] = signal

            deduped_signals = list(ticker_signals.values())

            # Sort by confidence (descending)
            sorted_signals = sorted(deduped_signals, key=lambda x: x.get("confidence", 0), reverse=True)

            # Take top N
            top_signals = sorted_signals[:limit]

            # Calculate stats
            if top_signals:
                avg_confidence = sum(s.get("confidence", 0) for s in top_signals) / len(top_signals)
                buy_count = len([s for s in top_signals if s.get("direction") == "buy"])
                hold_count = len([s for s in top_signals if s.get("direction") == "hold"])
                avoid_count = len([s for s in top_signals if s.get("direction") == "avoid"])
            else:
                avg_confidence = 0
                buy_count = hold_count = avoid_count = 0

            # Include portfolio recommendations if available
            recommendations = None
            try:
                portfolio = load_portfolio()
                if portfolio and portfolio.holding_count > 0:
                    # Get recommendations for this timeframe
                    recs = filter_signals_with_portfolio(all_signals, portfolio, TimeHorizon.SHORT_TERM, {})
                    recommendations = {
                        "sell_reduce": [asdict(s) for s in recs.get("sell_reduce", [])],
                        "hold": [asdict(s) for s in recs.get("hold", [])],
                        "add": [asdict(s) for s in recs.get("add", [])],
                        "portfolio_value": recs.get("portfolio_value", 0),
                        "portfolio_holdings": recs.get("portfolio_holdings", 0)
                    }
            except Exception as e:
                app.logger.warning(f"Could not build portfolio recommendations: {e}")

            response_data = {
                "signals": top_signals,
                "total": len(top_signals),
                "generated_at": generated_at,
                "stats": {
                    "avg_confidence": round(avg_confidence, 1),
                    "buy_count": buy_count,
                    "hold_count": hold_count,
                    "avoid_count": avoid_count,
                    "by_direction": {
                        "buy": buy_count,
                        "hold": hold_count,
                        "avoid": avoid_count
                    }
                },
                "filters": {
                    "min_confidence": min_confidence,
                    "direction": direction or "all",
                    "sector": sector or "all"
                }
            }

            # Add recommendations if available
            if recommendations:
                response_data["recommendations"] = recommendations

            return jsonify(response_data), 200

        except Exception as e:
            app.logger.error(f"Error getting short-term signals: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/signals/long-term", methods=["GET"])
    def get_long_term_signals():
        """Get signals for long-term investing (1+ years)

        Query parameters:
        - limit: number of signals to return (default: 15)
        - direction: filter by direction (buy/hold/avoid, default: all)
        - min_confidence: minimum confidence threshold (1-10, default: 5)
        - sector: filter by sector (default: all)
        """
        try:
            limit = request.args.get("limit", 15, type=int)
            direction = request.args.get("direction", None, type=str)
            min_confidence = request.args.get("min_confidence", 5, type=int)
            sector = request.args.get("sector", None, type=str)

            # Get latest 50 signals to filter from (increased for better sector diversity)
            signals_response = signal_store.get_latest_signals(50)
            all_signals = signals_response.get("data", []) if isinstance(signals_response, dict) else []
            generated_at = signals_response.get("generated_at") if isinstance(signals_response, dict) else None

            # Untagged (legacy) signals count as long-term
            all_signals = [s for s in all_signals if s.get("timeframe") != "short_term"]

            # Filter signals
            filtered_signals = []
            for signal in all_signals:
                # Check confidence threshold (lower bar for long-term fundamentals)
                if signal.get("confidence", 0) < min_confidence:
                    continue

                # Check direction filter
                if direction and signal.get("direction") != direction:
                    continue

                # Check sector filter
                if sector and signal.get("sector") != sector:
                    continue

                filtered_signals.append(signal)

            # Deduplicate by ticker (keep highest confidence for each stock)
            ticker_signals = {}
            for signal in filtered_signals:
                ticker = signal.get("ticker", "")
                if ticker:
                    # Keep signal with highest confidence for this ticker
                    if ticker not in ticker_signals or signal.get("confidence", 0) > ticker_signals[ticker].get("confidence", 0):
                        ticker_signals[ticker] = signal

            deduped_signals = list(ticker_signals.values())

            # Sort by confidence (descending)
            sorted_signals = sorted(deduped_signals, key=lambda x: x.get("confidence", 0), reverse=True)

            # Take top N
            top_signals = sorted_signals[:limit]

            # Calculate stats
            if top_signals:
                avg_confidence = sum(s.get("confidence", 0) for s in top_signals) / len(top_signals)
                buy_count = len([s for s in top_signals if s.get("direction") == "buy"])
                hold_count = len([s for s in top_signals if s.get("direction") == "hold"])
                avoid_count = len([s for s in top_signals if s.get("direction") == "avoid"])
            else:
                avg_confidence = 0
                buy_count = hold_count = avoid_count = 0

            # Include portfolio recommendations if available
            recommendations = None
            try:
                portfolio = load_portfolio()
                if portfolio and portfolio.holding_count > 0:
                    # Get recommendations for this timeframe
                    recs = filter_signals_with_portfolio(all_signals, portfolio, TimeHorizon.LONG_TERM, {})
                    recommendations = {
                        "sell_reduce": [asdict(s) for s in recs.get("sell_reduce", [])],
                        "hold": [asdict(s) for s in recs.get("hold", [])],
                        "add": [asdict(s) for s in recs.get("add", [])],
                        "portfolio_value": recs.get("portfolio_value", 0),
                        "portfolio_holdings": recs.get("portfolio_holdings", 0)
                    }
            except Exception as e:
                app.logger.warning(f"Could not build portfolio recommendations: {e}")

            response_data = {
                "signals": top_signals,
                "total": len(top_signals),
                "generated_at": generated_at,
                "stats": {
                    "avg_confidence": round(avg_confidence, 1),
                    "buy_count": buy_count,
                    "hold_count": hold_count,
                    "avoid_count": avoid_count,
                    "by_direction": {
                        "buy": buy_count,
                        "hold": hold_count,
                        "avoid": avoid_count
                    }
                },
                "filters": {
                    "min_confidence": min_confidence,
                    "direction": direction or "all",
                    "sector": sector or "all"
                }
            }

            # Add recommendations if available
            if recommendations:
                response_data["recommendations"] = recommendations

            return jsonify(response_data), 200

        except Exception as e:
            app.logger.error(f"Error getting long-term signals: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/signals/<path:signal_id>", methods=["GET"])
    def get_signal_detail(signal_id):
        """Get detailed view of a specific signal"""
        # Reject requests for special endpoints
        if signal_id in ["long-term", "short-term", "archive", "generate", "accuracy", "history"]:
            return jsonify({"error": "Endpoint not found"}), 404

        signal = signal_store.get_signal_by_id(signal_id)
        if not signal:
            return jsonify({"error": "Signal not found"}), 404
        return jsonify(signal), 200

    # Generation takes minutes (stock discovery, ~100 market-data fetches,
    # two LLM passes) — far past the HTTP worker's 30s request timeout — so
    # the endpoint kicks it off in a background thread and returns at once.
    generation_state = {"running": False, "lock": threading.Lock()}

    @app.route("/api/signals/generate", methods=["POST"])
    def generate_new_signals():
        """Trigger background signal regeneration (admin endpoint).

        Delegates to auto_generate_signals, which keeps existing real
        signals when a pass fails and never overwrites them with mocks.
        """
        with generation_state["lock"]:
            if generation_state["running"]:
                return jsonify({"status": "already_running"}), 409
            generation_state["running"] = True

        def run():
            try:
                auto_generate_signals()
            except Exception as e:
                app.logger.error(f"Background signal generation failed: {e}")
            finally:
                generation_state["running"] = False

        threading.Thread(target=run, daemon=True).start()
        return jsonify({
            "status": "started",
            "note": "Generation runs in the background; watch generated_at on /api/signals/short-term to see it land.",
        }), 202

    @app.route("/api/signals/accuracy", methods=["POST"])
    def update_accuracy():
        """Update signal accuracy (admin endpoint for scheduled task)"""
        try:
            archive = signal_store.get_signal_archive(limit=1000)
            signals = archive.get("signals", [])

            updated_count = 0
            for signal in signals:
                if signal.get("result") is None:
                    # Check if 30 days have passed
                    created_at = datetime.fromisoformat(signal["created_at"])
                    if datetime.utcnow() - created_at > timedelta(days=30):
                        # For now, just mark as processing
                        # In production, fetch real price data
                        signal_store.update_signal_accuracy(
                            signal["id"],
                            result="pending",
                            accuracy=None
                        )
                        updated_count += 1

            return jsonify({
                "status": "success",
                "message": f"Accuracy updated for {updated_count} signals"
            }), 200
        except Exception as e:
            app.logger.error(f"Error updating accuracy: {e}")
            return jsonify({"error": str(e)}), 500

    # ============= STOCK RESEARCH ENDPOINTS =============

    @app.route("/api/stock/<ticker>", methods=["GET"])
    def get_stock_data(ticker):
        """Get stock fundamentals and research data"""
        try:
            ticker = ticker.upper()
            data = fetch_fundamentals(ticker)

            if not data or not data.get("current_price"):
                return jsonify({"error": f"No data found for {ticker}"}), 404

            return jsonify(data), 200
        except Exception as e:
            app.logger.error(f"Error fetching stock data for {ticker}: {e}")
            return jsonify({"error": str(e)}), 500

    # ============= LEARN TAB ENDPOINTS =============

    @app.route("/api/learn/lessons", methods=["GET"])
    def get_lessons():
        """Get all educational lessons"""
        try:
            category = request.args.get("category")
            difficulty = request.args.get("difficulty")

            lessons = get_all_lessons()

            if category:
                lessons = [l for l in lessons if l["category"] == category]

            if difficulty:
                lessons = [l for l in lessons if l["difficulty"] == difficulty]

            return jsonify({
                "lessons": lessons,
                "total": len(lessons)
            }), 200
        except Exception as e:
            app.logger.error(f"Error fetching lessons: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/learn/lessons/<lesson_id>", methods=["GET"])
    def get_lesson(lesson_id):
        """Get single lesson by ID"""
        try:
            lesson = get_lesson_by_id(lesson_id)

            if not lesson:
                return jsonify({"error": "Lesson not found"}), 404

            return jsonify(lesson), 200
        except Exception as e:
            app.logger.error(f"Error fetching lesson: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/learn/categories", methods=["GET"])
    def get_categories():
        """Get lesson categories"""
        try:
            categories = get_lesson_categories()
            return jsonify({"categories": categories}), 200
        except Exception as e:
            app.logger.error(f"Error fetching categories: {e}")
            return jsonify({"error": str(e)}), 500

    # ============= PORTFOLIO ENDPOINTS =============

    @app.route("/api/portfolio", methods=["GET"])
    def get_portfolio():
        """Get current portfolio"""
        try:
            portfolio = load_portfolio()

            if not portfolio:
                return jsonify({
                    "message": "No portfolio loaded",
                    "portfolio": None
                }), 200

            return jsonify({
                "portfolio": {
                    "holdings": [
                        {
                            "symbol": h.symbol,
                            "quantity": h.quantity,
                            "purchase_price": h.purchase_price,
                            "current_price": h.current_price,
                            "current_value": h.current_value,
                            "gain_loss": h.gain_loss,
                            "gain_loss_pct": h.gain_loss_pct
                        }
                        for h in portfolio.holdings
                    ],
                    "total_value": portfolio.total_current_value,
                    "total_cost_basis": portfolio.total_cost_basis,
                    "total_gain_loss": portfolio.total_gain_loss,
                    "total_gain_loss_pct": portfolio.total_gain_loss_pct,
                    "holding_count": portfolio.holding_count,
                    "created_at": portfolio.created_at,
                    "updated_at": portfolio.updated_at
                }
            }), 200
        except Exception as e:
            app.logger.error(f"Error fetching portfolio: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/portfolio/upload", methods=["POST"])
    def upload_portfolio():
        """Upload portfolio via CSV"""
        try:
            if "file" not in request.files:
                return jsonify({"error": "No file provided"}), 400

            file = request.files["file"]
            csv_content = file.read().decode("utf-8")

            # Parse CSV
            holdings = parse_csv(csv_content)

            # Create portfolio
            portfolio = create_portfolio(holdings)

            # Validate
            validation = validate_portfolio(portfolio)

            if not validation["valid"]:
                return jsonify({
                    "error": "Invalid portfolio",
                    "errors": validation["errors"]
                }), 400

            # Save
            save_portfolio(portfolio)

            # Convert holdings to dict format for response
            holdings_list = [
                {
                    "symbol": h.symbol,
                    "quantity": h.quantity,
                    "purchase_price": h.purchase_price,
                    "total_cost": h.quantity * h.purchase_price
                }
                for h in holdings
            ]

            return jsonify({
                "status": "success",
                "message": f"Loaded {len(holdings)} holdings",
                "holdings": len(holdings),
                "holdings_list": holdings_list
            }), 201
        except Exception as e:
            app.logger.error(f"Error uploading portfolio: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/portfolio/add-holding", methods=["POST"])
    def add_holding():
        """Add single holding to portfolio"""
        try:
            data = request.json

            # Validate input
            if not all(k in data for k in ["symbol", "quantity", "purchase_price"]):
                return jsonify({"error": "Missing required fields"}), 400

            # Load or create portfolio
            portfolio = load_portfolio()
            if not portfolio:
                portfolio = create_portfolio([])

            # Add holding
            holding = Holding(
                symbol=data["symbol"].upper(),
                quantity=float(data["quantity"]),
                purchase_price=float(data["purchase_price"]),
                current_price=float(data.get("current_price", data["purchase_price"]))
            )

            portfolio.add_holding(holding)

            # Save
            save_portfolio(portfolio)

            return jsonify({
                "status": "success",
                "message": f"Added {holding.symbol}",
                "holding": {
                    "symbol": holding.symbol,
                    "quantity": holding.quantity,
                    "purchase_price": holding.purchase_price,
                    "current_value": holding.current_value
                }
            }), 201
        except Exception as e:
            app.logger.error(f"Error adding holding: {e}")
            return jsonify({"error": str(e)}), 500

    # ============= ANALYSIS ENDPOINTS =============

    @app.route("/api/portfolio/analysis", methods=["GET"])
    def analyze_portfolio_route():
        """Analyze current portfolio for pitfalls"""
        try:
            portfolio = load_portfolio()

            if not portfolio:
                return jsonify({
                    "error": "No portfolio loaded",
                    "message": "Upload a portfolio first"
                }), 400

            # Run analysis
            analysis = analyze_portfolio(portfolio)

            return jsonify({
                "status": "success",
                "pitfalls": [
                    {
                        "lesson_id": p.lesson_id,
                        "lesson_title": p.lesson_title,
                        "severity": p.severity,
                        "message": p.message,
                        "recommendation": p.recommendation,
                        "affected_holdings": p.affected_holdings
                    }
                    for p in analysis.pitfalls
                ],
                "risk_metrics": analysis.risk_metrics,
                "sector_allocation": analysis.sector_allocation,
                "concentration_metrics": analysis.concentration_metrics,
                "recommendations": analysis.recommendations,
                "summary": analysis.summary,
                "holding_count": portfolio.holding_count,
                "portfolio_value": portfolio.total_current_value
            }), 200
        except Exception as e:
            app.logger.error(f"Error analyzing portfolio: {e}")
            return jsonify({"error": str(e)}), 500

    # ============= SIGNALS FILTERING ENDPOINTS =============


    @app.route("/api/portfolio/recommendations", methods=["GET"])
    def get_portfolio_recommendations():
        """Get signals tailored to user's portfolio"""
        try:
            timeframe = request.args.get("timeframe", "short_term")
            portfolio = load_portfolio()

            # Load signals
            signals_data = load_signals()
            signals = signals_data.get("signals", [])

            # Load macro
            macro_data = fetch_macro_context(use_cache=True)

            # Filter with portfolio context
            horizon = TimeHorizon.SHORT_TERM if timeframe == "short_term" else TimeHorizon.LONG_TERM
            recommendations = filter_signals_with_portfolio(
                signals,
                portfolio,
                horizon,
                macro_data
            )

            return jsonify({
                "status": "success",
                "timeframe": timeframe,
                "portfolio_holdings": recommendations.get("portfolio_holdings", 0),
                "portfolio_value": recommendations.get("portfolio_value", 0),
                "sell_reduce": [
                    {
                        "ticker": s.ticker,
                        "direction": s.direction,
                        "confidence": s.confidence,
                        "rationale": s.rationale,
                        "portfolio_context": s.portfolio_context,
                        "weight_in_portfolio": f"{s.weight_in_portfolio:.1%}"
                    }
                    for s in recommendations.get("sell_reduce", [])
                ],
                "hold": [
                    {
                        "ticker": s.ticker,
                        "direction": s.direction,
                        "confidence": s.confidence,
                        "rationale": s.rationale,
                        "weight_in_portfolio": f"{s.weight_in_portfolio:.1%}"
                    }
                    for s in recommendations.get("hold", [])
                ],
                "add": [
                    {
                        "ticker": s.ticker,
                        "direction": s.direction,
                        "confidence": s.confidence,
                        "rationale": s.rationale,
                        "portfolio_context": s.portfolio_context
                    }
                    for s in recommendations.get("add", [])
                ]
            }), 200
        except Exception as e:
            app.logger.error(f"Error getting recommendations: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/portfolio/full", methods=["GET"])
    def get_portfolio_full():
        """Single call: analysis + LT and ST recommendations for the loaded portfolio.
        Used by PortfolioContext so all three tabs share one fetch."""
        try:
            portfolio = load_portfolio()
            if not portfolio or portfolio.holding_count == 0:
                return jsonify({"has_portfolio": False}), 200

            signals_data = load_signals()
            all_signals = signals_data.get("signals", [])

            result_analysis = analyze_portfolio(portfolio)

            def _recs(horizon):
                recs = filter_signals_with_portfolio(all_signals, portfolio, horizon, {})
                return {
                    "sell_reduce": [asdict(s) for s in recs.get("sell_reduce", [])],
                    "hold":        [asdict(s) for s in recs.get("hold", [])],
                    "add":         [asdict(s) for s in recs.get("add", [])],
                    "portfolio_value":    recs.get("portfolio_value", 0),
                    "portfolio_holdings": recs.get("portfolio_holdings", 0),
                }

            return jsonify({
                "has_portfolio": True,
                "analysis": {
                    "status":                "success",
                    "pitfalls": [
                        {
                            "lesson_id":        p.lesson_id,
                            "lesson_title":     p.lesson_title,
                            "severity":         p.severity,
                            "message":          p.message,
                            "recommendation":   p.recommendation,
                            "affected_holdings": p.affected_holdings,
                        }
                        for p in result_analysis.pitfalls
                    ],
                    "risk_metrics":          result_analysis.risk_metrics,
                    "sector_allocation":     result_analysis.sector_allocation,
                    "concentration_metrics": result_analysis.concentration_metrics,
                    "recommendations":       result_analysis.recommendations,
                    "summary":               result_analysis.summary,
                    "holding_count":         portfolio.holding_count,
                    "portfolio_value":       portfolio.total_current_value,
                },
                "long_term":  _recs(TimeHorizon.LONG_TERM),
                "short_term": _recs(TimeHorizon.SHORT_TERM),
            }), 200
        except Exception as e:
            app.logger.error(f"Error in portfolio/full: {e}")
            return jsonify({"error": str(e)}), 500

    # ============= ERROR HANDLERS =============

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Endpoint not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal error: {error}")
        return jsonify({"error": "Internal server error"}), 500

    # Skip blocking startup - stock discovery happens on first request or via scheduler
    print("[STARTUP] Flask app initialized (stock discovery deferred to first request)")

    # Initialize APScheduler for periodic data refresh
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        refresh_macro_data,
        trigger="interval",
        hours=1,
        id="macro_refresh",
        name="Refresh macro data every hour",
        replace_existing=True
    )
    scheduler.add_job(
        generate_signals_if_stale,
        trigger="interval",
        hours=1,
        id="signal_generation",
        name="Hourly check; regenerate stale timeframes (short-term >6h, long-term >24h)",
        replace_existing=True
    )
    scheduler.add_job(
        update_sector_mappings,
        trigger="interval",
        days=7,
        id="sector_update",
        name="Update sector mappings from Finnhub every 7 days",
        replace_existing=True
    )
    scheduler.add_job(
        discover_stocks,
        trigger="interval",
        hours=24,
        id="stock_discovery",
        name="Refresh high-quality stock discovery daily",
        replace_existing=True
    )

    @app.before_request
    def start_scheduler():
        """Start scheduler on first request if not already running"""
        if not scheduler.running and not app.config.get("TESTING"):
            scheduler.start()
            # Deploys reset both the stored signals and the hourly timer, so
            # regenerate immediately (in the scheduler's thread pool, not this
            # request) whenever the committed signals are already stale.
            scheduler.add_job(
                generate_signals_if_stale,
                id="startup_signal_refresh",
                replace_existing=True,
            )
            app.logger.info("[OK] Schedulers started: startup refresh (if stale) + macro refresh (1h) + signal stale-check (1h; short>6h, long>24h) + sector update (7d)")

    return app


# Module-level app for gunicorn
app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("DEBUG", "false").lower() == "true")
