"""
Migration script to move data from JSON files to SQL database
Run this once to migrate existing signals and macro config to the database

Usage:
    python migrate_to_database.py --database-url "mssql+pyodbc://user:pass@server/dbname?driver=ODBC+Driver+17+for+SQL+Server"

Or with environment variable:
    export DATABASE_URL="mssql+pyodbc://user:pass@server/dbname?driver=ODBC+Driver+17+for+SQL+Server"
    python migrate_to_database.py
"""

import json
import os
import sys
import argparse
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from models import init_db, get_session, Signal, MacroConfig, GenerationTimestamp
from config import get_config


def load_signals_from_file(file_path: str) -> dict:
    """Load signals from JSON file"""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return {"signals": [], "generated_at": None}

    with open(file_path, "r") as f:
        return json.load(f)


def load_macro_config_from_file(file_path: str) -> dict:
    """Load macro config from JSON file"""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return {"macro_signals": {}, "last_updated": None}

    with open(file_path, "r") as f:
        return json.load(f)


def migrate_signals(session, signals_data: dict) -> int:
    """Migrate signals from JSON to database"""
    signals = signals_data.get("signals", [])
    generated_at = signals_data.get("generated_at")

    migrated = 0
    for signal_dict in signals:
        try:
            # Check if signal already exists
            existing = session.query(Signal).filter_by(id=signal_dict["id"]).first()
            if existing:
                print(f"  Skipping {signal_dict['id']} (already exists)")
                continue

            signal = Signal.from_dict(signal_dict)
            session.add(signal)
            migrated += 1
        except Exception as e:
            print(f"  Error migrating signal {signal_dict.get('id')}: {e}")

    # Save generation timestamp
    try:
        timestamp = session.query(GenerationTimestamp).filter_by(id="latest").first()
        if not timestamp:
            timestamp = GenerationTimestamp(id="latest", signal_count=migrated)
            session.add(timestamp)
        else:
            timestamp.signal_count = migrated
            if generated_at:
                timestamp.generated_at = datetime.fromisoformat(generated_at)

        session.commit()
        print(f"✓ Migrated {migrated} signals")
        return migrated
    except Exception as e:
        print(f"✗ Error saving generation timestamp: {e}")
        session.rollback()
        return 0


def migrate_macro_config(session, config_data: dict) -> bool:
    """Migrate macro config from JSON to database"""
    try:
        # Check if config already exists
        existing = session.query(MacroConfig).filter_by(id="current").first()

        if existing:
            existing.config_data = config_data
            existing.updated_at = datetime.now(timezone.utc)
        else:
            macro = MacroConfig(id="current", config_data=config_data)
            session.add(macro)

        session.commit()
        print(f"✓ Migrated macro config")
        return True
    except Exception as e:
        print(f"✗ Error migrating macro config: {e}")
        session.rollback()
        return False


def main():
    parser = argparse.ArgumentParser(description="Migrate data from JSON files to database")
    parser.add_argument("--database-url", help="Database URL (or use DATABASE_URL env var)")
    parser.add_argument("--signals-file", default="signals.json", help="Path to signals.json")
    parser.add_argument("--macro-file", default="macro_config.json", help="Path to macro_config.json")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be migrated without making changes")

    args = parser.parse_args()

    # Get database URL
    database_url = args.database_url or os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not provided")
        print("Usage: python migrate_to_database.py --database-url 'your-database-url'")
        sys.exit(1)

    print(f"Migration Configuration:")
    print(f"  Database: {database_url}")
    print(f"  Signals file: {args.signals_file}")
    print(f"  Macro file: {args.macro_file}")
    print(f"  Dry run: {args.dry_run}")
    print()

    # Load data from files
    print("Loading data from files...")
    signals_data = load_signals_from_file(args.signals_file)
    macro_data = load_macro_config_from_file(args.macro_file)

    signal_count = len(signals_data.get("signals", []))
    print(f"Found {signal_count} signals and 1 macro config")
    print()

    if args.dry_run:
        print("DRY RUN - No changes will be made")
        print()
        if signal_count > 0:
            print("Sample signals:")
            for signal in signals_data.get("signals", [])[:3]:
                print(f"  - {signal.get('ticker')} ({signal.get('direction')})")
        print()
        print("To actually migrate, run without --dry-run")
        return

    # Initialize database
    print("Initializing database...")
    try:
        engine = init_db(database_url)
        session = get_session(engine)
        print("✓ Database initialized")
    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        sys.exit(1)

    print()

    # Migrate data
    print("Migrating data...")
    try:
        # Migrate signals
        print("  Signals:")
        signals_migrated = migrate_signals(session, signals_data)

        # Migrate macro config
        print("  Macro config:")
        macro_migrated = migrate_macro_config(session, macro_data)

        print()
        print("Migration Summary:")
        print(f"  Signals: {signals_migrated} migrated")
        print(f"  Macro config: {'Yes' if macro_migrated else 'No'}")
        print()
        print("✓ Migration complete!")

        # Optional: backup JSON files
        backup_dir = "backup"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            print(f"\nBacking up JSON files to {backup_dir}/")

            import shutil
            if os.path.exists(args.signals_file):
                shutil.copy(args.signals_file, os.path.join(backup_dir, os.path.basename(args.signals_file)))
            if os.path.exists(args.macro_file):
                shutil.copy(args.macro_file, os.path.join(backup_dir, os.path.basename(args.macro_file)))

            print(f"✓ Backups created in {backup_dir}/")

    except Exception as e:
        print(f"✗ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
