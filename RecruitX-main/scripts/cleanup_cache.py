#!/usr/bin/env python
"""
Script to clean up expired cache entries in the database.
This can be run as a scheduled task to maintain database performance.
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent directory to PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

from app.db.manager import DatabaseManager
from app.logger import logger


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Clean up expired cache entries")
    parser.add_argument(
        "--db-path",
        type=str,
        help="Path to database file (default: data/recruitx.db)",
    )
    parser.add_argument(
        "--force-all",
        action="store_true",
        help="Force cleanup of all cache entries, not just expired ones",
    )
    return parser.parse_args()


def main():
    """Main function"""
    args = parse_args()
    
    # Initialize database
    db_path = args.db_path or os.environ.get("DB_PATH", "data/recruitx.db")
    db = DatabaseManager(db_path)
    
    try:
        if args.force_all:
            # Delete all cache entries
            with db.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM cache")
                count = cursor.rowcount
            logger.info(f"Cleaned up all {count} cache entries")
        else:
            # Delete only expired entries
            count = db.clear_expired_cache()
            logger.info(f"Cleaned up {count} expired cache entries")
            
        return 0
    except Exception as e:
        logger.error(f"Error cleaning up cache: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 