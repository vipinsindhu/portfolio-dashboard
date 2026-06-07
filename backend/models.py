"""
Database models for macro analysis and portfolio data
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class MacroSignal(db.Model):
    __tablename__ = 'macro_signals'

    id = db.Column(db.Integer, primary_key=True)
    signal_key = db.Column(db.String(50), unique=True, nullable=False)
    label = db.Column(db.String(100), nullable=False)
    value = db.Column(db.String(100), nullable=False)
    signal = db.Column(db.Integer, nullable=False)  # -1, 0, +1
    context = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "label": self.label,
            "value": self.value,
            "signal": self.signal,
            "context": self.context
        }

class FundImpact(db.Model):
    __tablename__ = 'fund_impact'

    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(20), unique=True, nullable=False)
    impact_data = db.Column(db.JSON, nullable=False)  # {fed_rate: -1, treasury: -1, ...}
    net_score = db.Column(db.Float, nullable=False)  # Sum of all impacts
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "ticker": self.ticker,
            "impact": self.impact_data,
            "net_score": self.net_score
        }

class FundForecast(db.Model):
    __tablename__ = 'fund_forecast'

    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    outlook = db.Column(db.String(50), nullable=False)  # "Bullish", "Moderate", etc.
    color = db.Column(db.String(20), nullable=False)  # Color code
    horizon = db.Column(db.String(20), nullable=False)  # "3-5 yr"
    scenario = db.Column(db.String(50), nullable=False)  # "+60-90%"
    driver = db.Column(db.Text, nullable=False)
    risk = db.Column(db.Text, nullable=False)
    current_price = db.Column(db.Float, nullable=True)
    shares = db.Column(db.Float, nullable=True)
    cost_basis = db.Column(db.Float, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "ticker": self.ticker,
            "name": self.name,
            "outlook": self.outlook,
            "color": self.color,
            "horizon": self.horizon,
            "scenario": self.scenario,
            "driver": self.driver,
            "risk": self.risk,
            "current_price": self.current_price,
            "shares": self.shares,
            "cost_basis": self.cost_basis
        }

class AnalysisMetadata(db.Model):
    __tablename__ = 'analysis_metadata'

    id = db.Column(db.Integer, primary_key=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default="pending")  # pending, running, success, error
    error_message = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "status": self.status,
            "error_message": self.error_message
        }
