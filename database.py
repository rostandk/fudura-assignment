"""
database.py
Database client for PostgreSQL using asyncpg.
This module provides a simple interface for connecting to a PostgreSQL database
and includes logging for visibility.
"""

import asyncpg
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class DatabaseClient:
    def __init__(self, url: str):
        self._url = url
        self._pool = None

    async def connect(self):
        dbname = urlparse(self._url).path.lstrip('/')
        logger.info("Connecting to PostgreSQL at %s", dbname)
        self._pool = await asyncpg.create_pool(self._url)
        logger.info("Connection pool established.")

    async def execute(self, sql: str, *args):
        logger.debug("Executing SQL: %s", sql.splitlines()[0])  # Log first line only
        async with self._pool.acquire() as conn:
            try:
                result = await conn.execute(sql, *args)
                logger.debug("SQL execution completed.")
                return result
            except Exception as e:
                logger.exception(f"SQL execution failed.{e}")
                raise

    async def executemany(self, sql: str, args_list):
        logger.debug("Executing batch SQL (executemany): %s with %d rows", sql.splitlines()[0], len(args_list))
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                try:
                    await conn.executemany(sql, args_list)
                    logger.debug("Batch insert completed.")
                except Exception as e:
                    logger.exception(f"Batch insert failed: {e}")
                    raise

    async def close(self):
        logger.info("Closing database connection pool.")
        await self._pool.close()
        logger.info("Database connection pool closed.")