"""
Portfolio Builder API
Flask backend serving macro data and refresh endpoint
"""

from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime
import json
import os

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

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=False)
