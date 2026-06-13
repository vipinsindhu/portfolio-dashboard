"""
Database abstraction layer for signals and macro data
Supports both JSON file storage (development) and SQL database (production)
"""

import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models import Signal, MacroConfig, GenerationTimestamp, Base


class SignalStore:
    """Abstraction for signal storage (file-based or database)"""

    def __init__(self, session: Optional[Session] = None, file_path: str = "signals.json"):
        """
        Initialize store

        Args:
            session: SQLAlchemy session (if None, falls back to file storage)
            file_path: Path to signals.json for file-based fallback
        """
        self.session = session
        self.file_path = file_path
        self.use_database = session is not None

    def save_signal(self, signal_dict: Dict[str, Any]) -> bool:
        """Save a signal"""
        try:
            if self.use_database:
                signal = Signal.from_dict(signal_dict)
                self.session.add(signal)
                self.session.commit()
            else:
                # Fallback to JSON file
                data = self._load_json_file()
                data["signals"].insert(0, signal_dict)
                data["generated_at"] = datetime.now(timezone.utc).isoformat()
                self._save_json_file(data)
            return True
        except Exception as e:
            print(f"Error saving signal: {e}")
            self.session.rollback() if self.session else None
            return False

    def save_signals(self, signals: List[Dict[str, Any]]) -> bool:
        """Save multiple signals"""
        try:
            if self.use_database:
                for signal_dict in signals:
                    signal = Signal.from_dict(signal_dict)
                    self.session.add(signal)
                self.session.commit()
                # Update generation timestamp
                self._update_generation_timestamp(len(signals))
            else:
                # Fallback to JSON file
                data = self._load_json_file()
                data["signals"] = signals + data["signals"]
                data["generated_at"] = datetime.now(timezone.utc).isoformat()
                self._save_json_file(data)
            return True
        except Exception as e:
            print(f"Error saving signals: {e}")
            self.session.rollback() if self.session else None
            return False

    def get_latest_signals(self, limit: int = 5) -> Dict[str, Any]:
        """Get latest N signals"""
        try:
            if self.use_database:
                signals = self.session.query(Signal).order_by(desc(Signal.created_at)).limit(limit).all()
                timestamp = self.session.query(GenerationTimestamp).filter_by(id="latest").first()
                generated_at = timestamp.generated_at.isoformat() if timestamp else None
                return {
                    "data": [s.to_dict() for s in signals],
                    "generated_at": generated_at,
                    "total": self.session.query(Signal).count(),
                }
            else:
                # Fallback to JSON file
                data = self._load_json_file()
                signals = data.get("signals", [])[:limit]
                return {
                    "data": signals,
                    "generated_at": data.get("generated_at"),
                    "total": len(data.get("signals", [])),
                }
        except Exception as e:
            print(f"Error getting latest signals: {e}")
            return {"data": [], "generated_at": None, "total": 0}

    def get_signal_archive(self, limit: int = 100) -> Dict[str, Any]:
        """Get signal archive with all signals"""
        try:
            if self.use_database:
                signals = self.session.query(Signal).order_by(desc(Signal.created_at)).limit(limit).all()
                return {
                    "signals": [s.to_dict() for s in signals],
                    "total": self.session.query(Signal).count(),
                }
            else:
                # Fallback to JSON file
                data = self._load_json_file()
                signals = data.get("signals", [])[:limit]
                return {
                    "signals": signals,
                    "total": len(data.get("signals", [])),
                }
        except Exception as e:
            print(f"Error getting archive: {e}")
            return {"signals": [], "total": 0}

    def get_signal_by_id(self, signal_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific signal by ID"""
        try:
            if self.use_database:
                signal = self.session.query(Signal).filter_by(id=signal_id).first()
                return signal.to_dict() if signal else None
            else:
                # Fallback to JSON file
                data = self._load_json_file()
                for signal in data.get("signals", []):
                    if signal.get("id") == signal_id:
                        return signal
                return None
        except Exception as e:
            print(f"Error getting signal: {e}")
            return None

    def update_signal_accuracy(self, signal_id: str, result: str, accuracy: int) -> bool:
        """Update signal accuracy (win/loss)"""
        try:
            if self.use_database:
                signal = self.session.query(Signal).filter_by(id=signal_id).first()
                if signal:
                    signal.result = result
                    signal.accuracy_pct = accuracy
                    self.session.commit()
                    return True
            else:
                # Fallback to JSON file
                data = self._load_json_file()
                for signal in data.get("signals", []):
                    if signal.get("id") == signal_id:
                        signal["result"] = result
                        signal["accuracy_pct"] = accuracy
                        self._save_json_file(data)
                        return True
            return False
        except Exception as e:
            print(f"Error updating accuracy: {e}")
            self.session.rollback() if self.session else None
            return False

    def get_signals_by_sector(self, sector: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get signals filtered by sector"""
        try:
            if self.use_database:
                signals = (
                    self.session.query(Signal)
                    .filter_by(sector=sector)
                    .order_by(desc(Signal.created_at))
                    .limit(limit)
                    .all()
                )
                return [s.to_dict() for s in signals]
            else:
                # Fallback to JSON file
                data = self._load_json_file()
                return [s for s in data.get("signals", []) if s.get("sector") == sector][:limit]
        except Exception as e:
            print(f"Error getting signals by sector: {e}")
            return []

    def _update_generation_timestamp(self, count: int):
        """Update the generation timestamp"""
        try:
            timestamp = self.session.query(GenerationTimestamp).filter_by(id="latest").first()
            if not timestamp:
                timestamp = GenerationTimestamp(id="latest", signal_count=count)
                self.session.add(timestamp)
            else:
                timestamp.generated_at = datetime.now(timezone.utc)
                timestamp.signal_count = count
            self.session.commit()
        except Exception as e:
            print(f"Error updating timestamp: {e}")

    def _load_json_file(self) -> Dict[str, Any]:
        """Load signals from JSON file (fallback)"""
        if os.path.exists(self.file_path):
            with open(self.file_path, "r") as f:
                return json.load(f)
        return {"signals": [], "generated_at": None}

    def _save_json_file(self, data: Dict[str, Any]):
        """Save signals to JSON file (fallback)"""
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=2)


class MacroConfigStore:
    """Abstraction for macro configuration storage"""

    def __init__(self, session: Optional[Session] = None, file_path: str = "macro_config.json"):
        """
        Initialize store

        Args:
            session: SQLAlchemy session (if None, falls back to file storage)
            file_path: Path to macro_config.json for file-based fallback
        """
        self.session = session
        self.file_path = file_path
        self.use_database = session is not None

    def save_config(self, config_data: Dict[str, Any]) -> bool:
        """Save macro configuration"""
        try:
            if self.use_database:
                macro = self.session.query(MacroConfig).filter_by(id="current").first()
                if not macro:
                    macro = MacroConfig(id="current", config_data=config_data)
                    self.session.add(macro)
                else:
                    macro.config_data = config_data
                    macro.updated_at = datetime.now(timezone.utc)
                self.session.commit()
            else:
                # Fallback to JSON file
                with open(self.file_path, "w") as f:
                    json.dump(config_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving macro config: {e}")
            self.session.rollback() if self.session else None
            return False

    def get_config(self) -> Dict[str, Any]:
        """Get macro configuration"""
        try:
            if self.use_database:
                macro = self.session.query(MacroConfig).filter_by(id="current").first()
                if macro:
                    return macro.to_dict()
            else:
                # Fallback to JSON file
                if os.path.exists(self.file_path):
                    with open(self.file_path, "r") as f:
                        data = json.load(f)
                        return {
                            "macro_signals": data.get("macro_signals", {}),
                            "last_updated": data.get("last_updated"),
                        }
            return {"macro_signals": {}, "last_updated": None}
        except Exception as e:
            print(f"Error getting macro config: {e}")
            return {"macro_signals": {}, "last_updated": None}
