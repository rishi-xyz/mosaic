import os
import bcrypt
from asyncpg import create_pool, Pool


_pool: Pool | None = None


async def get_pool() -> Pool:
    global _pool
    if _pool is None:
        database_url = os.environ.get(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/mosaic?schema=public",
        )
        _pool = await create_pool(database_url, min_size=1, max_size=4)
    return _pool


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def validate_api_key(api_key: str) -> str | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            'SELECT "keyHash", "userId" FROM "ApiKey" WHERE "isActive" = true'
        )
        for row in rows:
            stored = row["keyHash"]
            if bcrypt.checkpw(api_key.encode(), stored.encode()):
                return row["userId"]
    return None


async def get_user_config(user_id: str) -> dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            'SELECT config FROM "UserConfig" WHERE "userId" = $1',
            user_id,
        )
        if row and row["config"]:
            config = row["config"]
            if isinstance(config, dict):
                return config
        return {}
