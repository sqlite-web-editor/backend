"""
Crud for our session db
"""

import aiosqlite
from .connection import path_to_db
from .sa_types import Path, Result, Err, Ok, CookieNotFoundError


async def cookie_create(cookie: str, generated_path: Path):
    "create a row in the cookie table from the given values"
    query: str = f"""
        INSERT INTO cookies (path, cookie) VALUES ('{generated_path}', '{cookie}')
    """
    async with aiosqlite.connect(path_to_db) as conn:
        await conn.execute(query)
        await conn.commit()


async def cookie_read(cookie: str) -> Result:
    "create a row in the cookie table from the given values"
    query: str = f"""SELECT path FROM cookies WHERE cookie={cookie}"""
    async with aiosqlite.connect(path_to_db) as conn:
        async with conn.execute(query) as cursor:
            res: aiosqlite.Row | None = await cursor.fetchone()

            if res is None:
                return Err(CookieNotFoundError)

            return Ok(res)


async def cookie_update():
    "not implemeted in this time"
    raise NotImplementedError()


async def cookie_delete(cookie: str) -> Result:
    "delete a row from cookies table by given cookie value"
    query: str = f"DELETE FROM cookies WHERE cookie={cookie}"
    async with aiosqlite.connect(path_to_db) as conn:
        async with conn.execute(query) as cursor:
            if cursor.rowcount == 0:
                return Err(CookieNotFoundError)

            await conn.commit()
            return Ok()
