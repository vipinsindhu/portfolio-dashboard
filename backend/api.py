"""
Stock Recommendation API
Flask backend serving signals, macro data, and analysis
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from signals import (
    generate_signals,
    get_latest_signals,
    get_signal_archive,
    load_signals,
    save_signals,
    update_signal_accuracy,
    fetch_fundamentals,
)

def create_app():
    app = Flask(__name__)
    CORS(app)

    CONFIG_FILE = "macro_config.json"

    def load_macro_config():
        """Load macro_config.json"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                return {"macro_signals": {}, "last_updated": None}
        return {"macro_signals": {}, "last_updated": None}

    @app.route("/test")
    def test():
        return jsonify({"message": "test route works"}), 200

    @app.route("/api/health", methods=["GET"])
    def health():
        """Health check endpoint"""
        return jsonify({
            "status": "ok",
            "timestamp": datetime.now().isoformat()
        }), 200

    @app.route("/api/macro", methods=["GET"])
    def get_macro():
        """Return current macro configuration"""
        config = load_macro_config()
        return jsonify(config), 200

    @app.route("/api/macro-signals", methods=["GET"])
    def get_macro_signals():
        """Return macro signals (new endpoint)"""
        config = load_macro_config()
        return jsonify({
            "signals": config.get("macro_signals", {}),
            "last_updated": config.get("last_updated")
        }), 200

    @app.route("/api/macro-analysis", methods=["GET"])
    def get_macro_analysis():
        """Return complete macro analysis dashboard"""
        config = load_macro_config()
        return jsonify({
            "macro_signals": config.get("macro_signals", {}),
            "metadata": {"last_updated": config.get("last_updated"), "status": "ready"}
        }), 200

    @app.route("/api/refresh", methods=["POST"])
    def refresh():
        """Trigger macro data refresh"""
        try:
            # Import and run fetch_macro
            import fetch_macro
            fetch_macro.main()

            # Return updated config
            config = load_macro_config()
            return jsonify(config), 200
        except Exception as e:
            print(f"Error refreshing macro data: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/refresh-analysis", methods=["POST"])
    def refresh_analysis():
        """Trigger analysis refresh (alias for /api/refresh)"""
        try:
            import fetch_macro
            fetch_macro.main()
            config = load_macro_config()
            return jsonify({
                "status": "success",
                "message": "Analysis updated",
                "metadata": {"last_updated": config.get("last_updated")}
            }), 200
        except Exception as e:
            print(f"Error refreshing analysis: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

    # ============= SIGNAL ENDPOINTS =============

    @app.route("/api/signals", methods=["GET"])
    def get_signals():
        """Get latest signals"""
        limit = request.args.get("limit", 5, type=int)
        return jsonify(get_latest_signals(limit)), 200

    @app.route("/api/signals/archive", methods=["GET"])
    def get_signals_archive():
        """Get signal archive (past signals)"""
        limit = request.args.get("limit", 100, type=int)
        return jsonify(get_signal_archive(limit)), 200

    @app.route("/api/signals/<signal_id>", methods=["GET"])
    def get_signal_detail(signal_id):
        """Get detailed view of a specific signal"""
        signals_data = load_signals()
        signals = signals_data.get("signals", [])

        signal = next((s for s in signals if s.get("id") == signal_id), None)
        if not signal:
            return jsonify({"error": "Signal not found"}), 404

        return jsonify(signal), 200

    @app.route("/api/signals/generate", methods=["POST"])
    def generate_new_signals():
        """Generate new signals (admin endpoint)"""
        # In production, add authentication here
        try:
            count = request.json.get("count", 5) if request.json else 5
            new_signals = generate_signals(count)

            if not new_signals:
                return jsonify({"error": "Failed to generate signals"}), 500

            # Save to storage
            signals_data = load_signals()
            signals_data["signals"].extend(new_signals)
            signals_data["generated_at"] = datetime.now().isoformat()
            save_signals(signals_data)

            return jsonify({
                "status": "success",
                "signals_generated": len(new_signals),
                "signals": new_signals
            }), 201

        except Exception as e:
            print(f"Error generating signals: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/signals/accuracy", methods=["POST"])
    def update_accuracy():
        """Update signal accuracy (admin endpoint for scheduled task)"""
        try:
            update_signal_accuracy()
            return jsonify({
                "status": "success",
                "message": "Accuracy updated"
            }), 200
        except Exception as e:
            print(f"Error updating accuracy: {e}")
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
            print(f"Error fetching stock data for {ticker}: {e}")
            return jsonify({"error": str(e)}), 500

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=False)
