"""

"""

import aiosqlite


#TODO: refactoring some moments in sa_types like Path or any funny things ^^
async def is_correct_db(path: str):
    try:
        print(path)
        async with aiosqlite.connect(path) as conn:
            cursor = await conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            await cursor.fetchone()
        return True
    except aiosqlite.Error:
        return False
    