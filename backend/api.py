"""
Portfolio Dashboard API - Database-backed macro analysis
Flask backend serving macro data, fund impact, and forecasts
"""

from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime
import atexit

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from models import db, MacroSignal, FundImpact, FundForecast, AnalysisMetadata
    from macro_analyzer import run_analysis
    DB_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Database modules not available: {e}")
    DB_AVAILABLE = False

def create_app():
    app = Flask(__name__)
    CORS(app)

    if DB_AVAILABLE:
        # Database config - use SQLite for simplicity, upgrade to PostgreSQL in production
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portfolio.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        # Initialize database
        db.init_app(app)

        with app.app_context():
            db.create_all()

        # Setup background scheduler for daily analysis
        try:
            scheduler = BackgroundScheduler()
            scheduler.add_job(
                func=lambda: run_analysis(),
                trigger="cron",
                hour=9,  # Run at 9 AM daily
                minute=0,
                id='macro_analysis_job',
                name='Daily macro analysis',
                replace_existing=True
            )
            scheduler.start()
            atexit.register(lambda: scheduler.shutdown())
        except Exception as e:
            print(f"Warning: Could not start scheduler: {e}")

    @app.route("/api/health", methods=["GET"])
    def health():
        """Health check endpoint"""
        return jsonify({
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat()
        }), 200

    @app.route("/api/macro-signals", methods=["GET"])
    def get_macro_signals():
        """Return current macro signals"""
        if not DB_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503
        try:
            signals = MacroSignal.query.all()
            metadata = AnalysisMetadata.query.first()
            return jsonify({
                "signals": {s.signal_key: s.to_dict() for s in signals},
                "metadata": metadata.to_dict() if metadata else None
            }), 200
        except Exception as e:
            print(f"Error in macro-signals: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/fund-impact", methods=["GET"])
    def get_fund_impact():
        """Return fund macro impact scores"""
        if not DB_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503
        try:
            impacts = FundImpact.query.all()
            metadata = AnalysisMetadata.query.first()
            return jsonify({
                "funds": [i.to_dict() for i in impacts],
                "metadata": metadata.to_dict() if metadata else None
            }), 200
        except Exception as e:
            print(f"Error in fund-impact: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/forecasts", methods=["GET"])
    def get_forecasts():
        """Return fund forecasts with current prices"""
        if not DB_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503
        try:
            forecasts = FundForecast.query.all()
            metadata = AnalysisMetadata.query.first()
            return jsonify({
                "forecasts": [f.to_dict() for f in forecasts],
                "metadata": metadata.to_dict() if metadata else None
            }), 200
        except Exception as e:
            print(f"Error in forecasts: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/macro-analysis", methods=["GET"])
    def get_full_analysis():
        """Return complete macro analysis dashboard"""
        if not DB_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503
        try:
            signals = {s.signal_key: s.to_dict() for s in MacroSignal.query.all()}
            impacts = {i.ticker: i.to_dict() for i in FundImpact.query.all()}
            forecasts = {f.ticker: f.to_dict() for f in FundForecast.query.all()}
            metadata = AnalysisMetadata.query.first()
            return jsonify({
                "macro_signals": signals,
                "fund_impact": impacts,
                "forecasts": forecasts,
                "metadata": metadata.to_dict() if metadata else None
            }), 200
        except Exception as e:
            print(f"Error in macro-analysis: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/refresh-analysis", methods=["POST"])
    def refresh_analysis():
        """Trigger immediate macro data refresh"""
        if not DB_AVAILABLE:
            return jsonify({"error": "Database not available"}), 503
        try:
            success, message = run_analysis()
            if success:
                metadata = AnalysisMetadata.query.first()
                return jsonify({
                    "status": "success",
                    "message": message,
                    "metadata": metadata.to_dict() if metadata else None
                }), 200
            else:
                return jsonify({
                    "status": "error",
                    "message": message
                }), 500
        except Exception as e:
            print(f"Error refreshing analysis: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=False)
