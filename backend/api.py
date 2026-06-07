"""
Portfolio Dashboard API
Flask backend serving macro data and analysis
"""

from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime
import json
import os

def load_macro_config():
    config_file = "macro_config.json"
    if os.path.exists(config_file):
        with open(config_file, "r") as f:
            return json.load(f)
    return {"macro_signals": {}, "last_updated": None}

def create_app():
    app = Flask(__name__)
    CORS(app)

    @app.route("/")
    def root():
        return jsonify({"message": "Portfolio Dashboard API"}), 200

    @app.route("/api/health")
    def health():
        return jsonify({
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat()
        }), 200

    @app.route("/api/macro")
    def get_macro():
        config = load_macro_config()
        return jsonify(config), 200

    @app.route("/api/macro-analysis")
    def get_full_analysis():
        config = load_macro_config()
        return jsonify({
            "macro_signals": config.get("macro_signals", {}),
            "metadata": {"last_updated": config.get("last_updated")}
        }), 200

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=False)
