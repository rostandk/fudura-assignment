#!/usr/bin/env python3
"""
setup_database.py
Initializes the TimescaleDB schema and continuous aggregates.
"""

import asyncio
import logging
from database import DatabaseClient
from config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s: %(message)s"
)

logger = logging.getLogger(__name__)

SQL_CREATE_SCHEMA = """
-- 1. Load TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- 2. Create base table
CREATE TABLE IF NOT EXISTS battery_telemetry (
    recorded_at   TIMESTAMPTZ      NOT NULL,
    device_id     UUID             NOT NULL,
    metric_name   TEXT             NOT NULL,
    value         DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (recorded_at, device_id, metric_name)
);

-- 3. Convert to hypertable (time + device partitioning)
SELECT create_hypertable(
  'battery_telemetry',
  'recorded_at',
  partitioning_column => 'device_id',
  number_partitions   => 4,
  if_not_exists       => TRUE
);

-- 4. Enable compression
ALTER TABLE battery_telemetry
  SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'device_id, metric_name'
  );

-- 5. Add compression policy (skip if exists)
DO $$
BEGIN
  PERFORM add_compression_policy('battery_telemetry', INTERVAL '7 days');
EXCEPTION
  WHEN duplicate_object THEN
    RAISE NOTICE 'Compression policy already exists, skipping';
END
$$;

-- 6. Create continuous aggregate for daily minimum SOC, no data yet
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_soc_min
WITH (timescaledb.continuous) AS
SELECT
  time_bucket('1 day', recorded_at) AS day,
  device_id,
  MIN(value) AS min_soc
FROM battery_telemetry
WHERE metric_name = 'StateOfChargePercentage'
GROUP BY day, device_id
WITH NO DATA;
"""

SQL_REFRESH_VIEW = "CALL refresh_continuous_aggregate('daily_soc_min', NULL, NULL);"

async def setup():
    logger.info("Starting TimescaleDB schema & continuous aggregate setup...")

    db = DatabaseClient(settings.database_url)
    await db.connect()
    try:
        await db.execute(SQL_CREATE_SCHEMA)
        logger.info("Schema and continuous aggregate created.")
    except Exception:
        logger.exception("Initial schema setup failed.")
        await db.close()
        return

    try:
        # Open new connection without transaction block
        conn = await db._pool.acquire()
        await conn.execute(SQL_REFRESH_VIEW)
        await db._pool.release(conn)
        logger.info("Continuous aggregate refreshed with data.")
    except Exception:
        logger.exception("Refreshing continuous aggregate failed.")
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(setup())
