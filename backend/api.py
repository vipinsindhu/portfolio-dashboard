"""
Stock Recommendation API
Flask backend serving signals, macro data, and analysis
Supports both file-based (development) and database-backed (production) storage
"""

import os
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from signals import (
    generate_signals,
    update_signal_accuracy,
    load_signals,
    save_signals,
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
            self.DATABASE_URL = "sqlite:///portfolio.db"
            self.CORS_ORIGINS = "*"
            self.SIGNALS_FILE = "signals.json"
            self.MACRO_CONFIG_FILE = "macro_config.json"

    def get_config():
        return DummyConfig()


def create_app():
    app = Flask(__name__)

    # Load configuration
    config = get_config()
    app.config.from_object(config.__dict__)

    # Initialize CORS
    CORS(app, origins=app.config.get("CORS_ORIGINS", "*").split(","))

    # Initialize storage (database optional, file storage fallback)
    if HAS_DATABASE:
        try:
            engine = init_db(app.config["DATABASE_URL"])
            session = get_session(engine)
            signal_store = SignalStore(session=session, file_path=app.config["SIGNALS_FILE"])
            macro_store = MacroConfigStore(session=session, file_path=app.config["MACRO_CONFIG_FILE"])
            app.logger.info(f"Database initialized: {app.config['DATABASE_URL']}")
        except Exception as e:
            app.logger.warning(f"Database initialization failed, falling back to file storage: {e}")
            signal_store = SignalStore(session=None, file_path=app.config["SIGNALS_FILE"])
            macro_store = MacroConfigStore(session=None, file_path=app.config["MACRO_CONFIG_FILE"])
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
                data = load_signals()
                data["signals"] = signals + data.get("signals", [])
                data["generated_at"] = datetime.utcnow().isoformat()
                save_signals(data)
                return True

        signal_store = SimpleSignalStore()
        macro_store = None
        app.logger.info("Using file-based storage (database not available)")

    # ============= HEALTH & STATUS =============

    @app.route("/test")
    def test():
        return jsonify({"message": "test route works"}), 200

    @app.route("/api/health", methods=["GET"])
    def health():
        """Health check endpoint"""
        return jsonify({
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "environment": app.config.get("FLASK_ENV"),
            "storage": "database" if signal_store.use_database else "file",
        }), 200

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
        config = macro_store.get_config()
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

    @app.route("/api/signals/<signal_id>", methods=["GET"])
    def get_signal_detail(signal_id):
        """Get detailed view of a specific signal"""
        signal = signal_store.get_signal_by_id(signal_id)
        if not signal:
            return jsonify({"error": "Signal not found"}), 404
        return jsonify(signal), 200

    @app.route("/api/signals/generate", methods=["POST"])
    def generate_new_signals():
        """Generate new signals (admin endpoint)"""
        try:
            count = request.json.get("count", 5) if request.json else 5
            new_signals = generate_signals(count)

            if not new_signals:
                return jsonify({"error": "Failed to generate signals"}), 500

            # Save to storage (database or file)
            success = signal_store.save_signals(new_signals)
            if not success:
                return jsonify({"error": "Failed to save signals"}), 500

            return jsonify({
                "status": "success",
                "signals_generated": len(new_signals),
                "signals": new_signals
            }), 201

        except Exception as e:
            app.logger.error(f"Error generating signals: {e}")
            return jsonify({"error": str(e)}), 500

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

    # ============= ERROR HANDLERS =============

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Endpoint not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal error: {error}")
        return jsonify({"error": "Internal server error"}), 500

    return app


# Module-level app for gunicorn
app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("DEBUG", "false").lower() == "true")
