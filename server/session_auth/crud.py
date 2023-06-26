import datetime
from typing import Iterable
import aiosqlite
from .connection import path_to_db
from .sa_types import Path, Result, Err, Ok, CookieNotFoundError


async def create_session(session_id: str, generated_path: Path) -> None:
    "create a row in the cookie table from the given values"
    timestamp: datetime.datetime = datetime.datetime.now()
    query: str = """
        INSERT INTO `cookies` (path, cookie, timestamp) 
        VALUES (?, ?, ?)
    """
    async with aiosqlite.connect(path_to_db) as conn:
        await conn.execute(query, (generated_path, session_id, timestamp))
        await conn.commit()
        
async def read_session_filepath(session_id: str) -> Result[str]:
    "read a row by given cookie (session_id) value"
    query: str = "SELECT path FROM `cookies` WHERE cookie=?"
    async with aiosqlite.connect(path_to_db) as conn:
        async with conn.execute(query, (session_id,)) as cursor:
            res: aiosqlite.Row | None = await cursor.fetchone()

            if res is None:
                return Err(CookieNotFoundError)

            return Ok[str](res[0])


async def update_session_timestamp(session_id: str):
    "not implemeted at this time"
    query: str = "UPDATE `cookies` SET timestamp=? WHERE cookie=?"
    timestamp: datetime.datetime = datetime.datetime.now()

    async with aiosqlite.connect(path_to_db) as conn:
        async with conn.execute(query, (timestamp, session_id)) as cursor:
            await conn.commit()


async def delete_session(session_id: str) -> Result[None]:
    "delete a row from cookies table by given cookie value"
    query: str = "DELETE FROM `cookies` WHERE cookie=?"
    async with aiosqlite.connect(path_to_db) as conn:
        async with conn.execute(query, (session_id,)) as cursor:
            if cursor.rowcount == 0:
                return Err(CookieNotFoundError)

            await conn.commit()
            return Ok()


async def read_all_sessions() -> Iterable[aiosqlite.Row]:
    "read all sessions in db"
    query: str = "SELECT * FROM `cookies`"
    async with aiosqlite.connect(path_to_db) as conn:
        async with conn.execute(query) as cursor:
            rows: Iterable[aiosqlite.Row] = await cursor.fetchall()
            return rows
        


async def read_session_data(session_id: str) -> Result[aiosqlite.Row]:
    "read a row by given cookie (session_id) value"
    query: str = "SELECT * FROM `cookies` WHERE cookie=?"
    async with aiosqlite.connect(path_to_db) as conn:
        async with conn.execute(query, (session_id,)) as cursor:
            res: aiosqlite.Row | None = await cursor.fetchone()

            if res is None:
                return Err(CookieNotFoundError)

            return Ok[aiosqlite.Row](res)
    