"""
QuantumShield Standalone Background Job Worker Daemon.

Run independently from the web server:
    python backend/worker.py --workers 3 --db-path ./data/quantumshield.db
"""

import os
import sys
import time
import signal
import argparse
import logging
from pathlib import Path

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from quantumshield.storage.database import init_db
from quantumshield.services.job_worker import BackgroundJobManager
from config import get_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("quantumshield.worker.daemon")


def main():
    parser = argparse.ArgumentParser(description="QuantumShield Standalone Background Job Worker")
    parser.add_argument(
        "--workers",
        type=int,
        default=3,
        help="Number of concurrent worker threads (default: 3)",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="Path to SQLite database file",
    )
    parser.add_argument(
        "--lease-seconds",
        type=int,
        default=60,
        help="Heartbeat lease duration before marking abandoned jobs (default: 60)",
    )
    args = parser.parse_args()

    config = get_config()
    db_path = args.db_path or config.DATABASE_PATH
    logger.info(f"Initializing database at: {db_path}")
    init_db(db_path)

    logger.info(f"Starting BackgroundJobManager with {args.workers} workers...")
    manager = BackgroundJobManager(
        db_path=db_path,
        max_workers=args.workers,
        lease_seconds=args.lease_seconds,
    )
    manager.start()

    stop_requested = False

    def handle_signal(sig, frame):
        nonlocal stop_requested
        logger.info(f"Received termination signal ({sig}). Shutting down worker...")
        stop_requested = True

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    logger.info("Worker daemon running. Press Ctrl+C to terminate.")
    try:
        while not stop_requested:
            time.sleep(1)
    finally:
        manager.stop(timeout=5.0)
        logger.info("Worker daemon terminated cleanly.")


if __name__ == "__main__":
    main()
