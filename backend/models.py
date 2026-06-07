"""
Database models for SQLAlchemy ORM
Supports signals, macro config, and future user management
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Signal(Base):
    """Investment signal model"""
    __tablename__ = "signals"

    id = Column(String(50), primary_key=True)
    ticker = Column(String(10), nullable=False, index=True)
    direction = Column(String(10), nullable=False)  # buy, hold, avoid
    confidence = Column(Integer, nullable=False)  # 1-10
    rationale = Column(Text, nullable=False)
    sector = Column(String(50), nullable=True)
    market_cap = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, index=True, default=datetime.utcnow)
    result = Column(String(10), nullable=True)  # win, loss
    accuracy_pct = Column(Integer, nullable=True)  # 0 or 100

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "ticker": self.ticker,
            "direction": self.direction,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "sector": self.sector,
            "market_cap": self.market_cap,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "result": self.result,
            "accuracy_pct": self.accuracy_pct,
        }

    @classmethod
    def from_dict(cls, data):
        """Create from dictionary"""
        return cls(
            id=data.get("id"),
            ticker=data.get("ticker"),
            direction=data.get("direction"),
            confidence=data.get("confidence"),
            rationale=data.get("rationale"),
            sector=data.get("sector"),
            market_cap=data.get("market_cap"),
            created_at=datetime.fromisoformat(data.get("created_at")) if data.get("created_at") else datetime.utcnow(),
            result=data.get("result"),
            accuracy_pct=data.get("accuracy_pct"),
        )


class MacroConfig(Base):
    """Macro economic configuration and context"""
    __tablename__ = "macro_config"

    id = Column(String(50), primary_key=True, default="current")
    config_data = Column(JSON, nullable=False)  # Store macro signals and metadata
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "macro_signals": self.config_data.get("macro_signals", {}),
            "last_updated": self.updated_at.isoformat() if self.updated_at else None,
        }


class GenerationTimestamp(Base):
    """Track when signals were last generated"""
    __tablename__ = "generation_timestamps"

    id = Column(String(50), primary_key=True, default="latest")
    generated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    signal_count = Column(Integer, nullable=False, default=0)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "signal_count": self.signal_count,
        }


# Future models for Phase 2 (commented out for now)
"""
class User(Base):
    '''User authentication and subscription management'''
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)  # UUID
    email = Column(String(255), unique=True, nullable=False, index=True)
    azure_ad_id = Column(String(255), unique=True, nullable=True)
    subscription_tier = Column(String(50), default="free")  # free, pro, enterprise
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Watchlist(Base):
    '''User watchlist'''
    __tablename__ = "watchlists"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    ticker = Column(String(10), nullable=False)
    added_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class ResearchNote(Base):
    '''User research notes'''
    __tablename__ = "research_notes"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    ticker = Column(String(10), nullable=False, index=True)
    notes = Column(Text, nullable=False)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
"""


def init_db(database_url: str):
    """Initialize database and create tables"""
    engine = create_engine(
        database_url,
        pool_size=10,
        pool_recycle=3600,
        echo=False,
    )
    Base.metadata.create_all(engine)
    return engine


def get_session(engine):
    """Get SQLAlchemy session"""
    Session = sessionmaker(bind=engine)
    return Session()
