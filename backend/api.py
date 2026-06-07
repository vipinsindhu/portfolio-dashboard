"""
Portfolio Dashboard API
Flask backend serving macro data, fund impact, and forecasts
"""

from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime
import json
import os

def load_macro_config():
    """Load macro_config.json"""
    config_file = "macro_config.json"
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {"macro_signals": {}, "last_updated": None}
    return {"macro_signals": {}, "last_updated": None}

def create_app():
    app = Flask(__name__)
    CORS(app)

    print("Creating Flask app with routes...", flush=True)

    @app.route("/api/health", methods=["GET"])
    def health():
        """Health check endpoint"""
        return jsonify({
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat()
        }), 200

    @app.route("/api/macro", methods=["GET"])
    def get_macro():
        """Return current macro configuration"""
        config = load_macro_config()
        return jsonify(config), 200

    @app.route("/api/macro-signals", methods=["GET"])
    def get_macro_signals():
        """Return current macro signals (alias for /api/macro)"""
        config = load_macro_config()
        return jsonify({
            "signals": config.get("macro_signals", {}),
            "metadata": {"last_updated": config.get("last_updated")}
        }), 200

    @app.route("/api/fund-impact", methods=["GET"])
    def get_fund_impact():
        """Return fund macro impact scores (placeholder)"""
        return jsonify({
            "funds": [],
            "metadata": {"message": "Fund impact analysis - use /api/macro-analysis for details"}
        }), 200

    @app.route("/api/forecasts", methods=["GET"])
    def get_forecasts():
        """Return fund forecasts (placeholder)"""
        return jsonify({
            "forecasts": [],
            "metadata": {"message": "Fund forecasts - use /api/macro-analysis for details"}
        }), 200

    @app.route("/api/macro-analysis", methods=["GET"])
    def get_full_analysis():
        """Return complete macro analysis dashboard"""
        config = load_macro_config()
        return jsonify({
            "macro_signals": config.get("macro_signals", {}),
            "fund_impact": {},
            "forecasts": {},
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
        """Trigger macro data refresh (alias for /api/refresh)"""
        try:
            import fetch_macro
            fetch_macro.main()
            config = load_macro_config()
            return jsonify({
                "status": "success",
                "message": "Macro analysis updated",
                "metadata": {"last_updated": config.get("last_updated")}
            }), 200
        except Exception as e:
            print(f"Error refreshing analysis: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

    print(f"Flask app created with routes: {[rule.rule for rule in app.url_map.iter_rules()]}", flush=True)
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=False)
