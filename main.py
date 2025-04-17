"""
main.py
This script loads telemetry data from JSON files.
It transforms it and inserts it into a PostgreSQL / TimescaleDB database.
It uses asyncpg for database operations and asyncio for asynchronous execution.
"""
import logging
import asyncio
from loader import load_assets, load_telemetry
from transformer import transform
from database import DatabaseClient
from config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s: %(message)s"
)

logger = logging.getLogger(__name__)

INSERT_SQL = """
INSERT INTO battery_telemetry (recorded_at, device_id, metric_name, value)
VALUES ($1, $2, $3, $4)
ON CONFLICT DO NOTHING
"""

async def run():
    db = DatabaseClient(settings.database_url)
    await db.connect()

    assets = load_assets()
    for asset in assets.items:
        telemetry = load_telemetry(asset.deviceId)
        if not telemetry:
            continue
        records = transform(asset.deviceId, telemetry)
        args = [(r.time, r.device_id, r.metric_name, r.value) for r in records]
        await db.executemany(INSERT_SQL, args)

    await db.close()

if __name__ == "__main__":
    asyncio.run(run())
