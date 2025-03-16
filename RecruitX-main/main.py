import asyncio
import os
from pathlib import Path

from app.agent.manus import Manus
from app.logger import logger
from app.db.manager import DatabaseManager


async def main():
    # Initialize database
    db_path = os.environ.get("DB_PATH", Path(__file__).parent / "data/recruitx.db")
    db = DatabaseManager(db_path)
    logger.info(f"Database initialized at {db.db_path}")
    
    agent = Manus()
    try:
        prompt = input("Enter your prompt: ")
        if not prompt.strip():
            logger.warning("Empty prompt provided.")
            return

        logger.warning("Processing your request...")
        await agent.run(prompt)
        logger.info("Request processing completed.")
    except KeyboardInterrupt:
        logger.warning("Operation interrupted.")


if __name__ == "__main__":
    asyncio.run(main())
