from typing import List, Iterable, Dict, Any, Optional, Tuple
from os.path import join as os_join
import logging
from sqlite3 import OperationalError, Error
import aiosqlite
from session_auth.sa_types import Path, Result, Err, Ok
from .utils import get_where_expression, get_set_expression, get_sql_values_expression


async def get_tables(filename: Path) -> Result[List[str]]:
    try:
        async with aiosqlite.connect(os_join("tempfiles", str(filename))) as conn:
            async with conn.execute("SELECT name FROM sqlite_master WHERE type='table'") as cursor:
                result: Iterable[aiosqlite.Row] = await cursor.fetchall()
                tables: List[str] = [row[0] for row in result]
                return Ok[List[str]](tables)

    except aiosqlite.Error as error:
        return Err(error)

    except Exception as error:
        logging.fatal(error)
        return Err(error)
    

async def get_table_rowcount(filename: str, tablename: str) -> int:
    async with aiosqlite.connect(os_join("tempfiles", str(filename))) as conn:
        async with conn.execute(f"SELECT COUNT(*) FROM {tablename}") as cur:
            result = await cur.fetchone()
            return result[0] # type: ignore


async def get_columns_meta(filename: str, tablename: str) -> List[Dict]:
    columns: List[dict] = []

    # ---, cid, name
    uniques: List[Tuple[int, int, str]] = []

    async with aiosqlite.connect(os_join("tempfiles", str(filename))) as conn:
            
        async with conn.execute(f"PRAGMA index_list({tablename})") as cur:
            index_list: Iterable[aiosqlite.Row] | None = await cur.fetchall()
            for row in index_list:
                async with conn.execute(f"PRAGMA index_info({row[1]})") as cur:
                    # тут None быть просто не может, это чтобы пилинте(pylint) не ругался
                    index_info: aiosqlite.Row = await cur.fetchone() # type: ignore
                    uniques.append(tuple(index_info)) # type: ignore

        async with conn.execute(f"PRAGMA table_info({tablename})") as cursor:
            result = await cursor.fetchall()

            for column_metadata in result:
                unique = False
                column_metadata = list(column_metadata)

                if "INT" in column_metadata[2]:
                    column_metadata[2] = "INTEGER"

                elif "CHAR" in column_metadata[2] or column_metadata[2]=="CLOB":
                    column_metadata[2] = "TEXT"

                elif column_metadata[2] in ["DOUBLE", "REAL", "FLOAT"]:
                    column_metadata[2] = "REAL"

                elif "BOOL" in column_metadata[2]:
                    column_metadata[2] = "BOOLEAN"

                for unique_column in uniques:
                    if unique_column[1] == column_metadata[0]:
                        unique=True
                    
                current_column = {
                    "cid": column_metadata[0],
                    "name": column_metadata[1],
                    "type": column_metadata[2],
                    "notnull": bool(column_metadata[3]) or bool(column_metadata[5]),
                    "dflt_value": column_metadata[4],
                    "pk": bool(column_metadata[5]),
                    "autoincrement": bool(column_metadata[5]),
                    "unique": unique
                }
                columns.append(current_column)

            try:
                query: str = f'SELECT COUNT(*) FROM sqlite_sequence WHERE name="{tablename}"'
                async with conn.execute(query) as cursor:
                    result = await cursor.fetchall()
                    for column in result:
                        cid: int = column[0]
                        columns[cid]["autoincrement"] = True
            except OperationalError:
                pass

    return columns


async def get_table_content(filename: str, tablename: str, _from: int, to: int) -> dict:
    '''
    this function returns something like
    {
        columns: List[
            Dict[str, str | int | bool | None]
        ],
        data: List[ List[Any] ]
    }

    example:
{
  "columns": [
    {
      "cid": 0,
      "name": "id",
      "type": "INTEGER",
      "notnull": true,
      "dflt_value": null,
      "pk": true
    },
    {
      "cid": 1,
      "name": "banned",
      "type": "BOOLEAN",
      "notnull": false,
      "dflt_value": null,
      "pk": false
    },
    {
      "cid": 2,
      "name": "discord_id",
      "type": "INTEGER",
      "notnull": false,
      "dflt_value": null,
      "pk": false
    }
  ],
  "data": [
    [
      1,
      0,
      XXXXXXXXXXXXXXXXXXX
    ],
    [
      2,
      0,
      XXXXXXXXXXXXXXXXXXX
    ],
    [
      3,
      1,
      XXXXXXXXXXXXXXXXXXX
    ]
  ]
}
    '''
    async with aiosqlite.connect(os_join("tempfiles", str(filename))) as conn:
        async with conn.execute(f"SELECT * FROM {tablename} LIMIT {to} OFFSET {_from}") as cursor:
            return {
                "columns": await get_columns_meta(filename, tablename),
                "data": list(await cursor.fetchall())
            }


async def check_table_exists(filename: str, tablename: str) -> bool:
    async with aiosqlite.connect(os_join("tempfiles", filename)) as conn:
        query: str = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        async with conn.execute(query, (tablename, )) as cursor:
            result: aiosqlite.Row | None = await cursor.fetchone()

            if result is None:
                return False

            return True
        

async def delete_row_in_table(
    filename: str, 
    tablename: str, 
    values: Dict[str, Any], 
    limit: Optional[int] = None) -> int:

    """Deletes one or more rows (set by the limit argument, 
    None - no limit), returns the number of affected rows"""

    where_expression: str = get_where_expression(values)
    limit_expression: str = f"LIMIT {limit}" if limit else ""
    async with aiosqlite.connect(os_join("tempfiles", filename)) as conn:
        query: str = f"DELETE FROM {tablename} " + where_expression + " " + limit_expression
        async with conn.execute(query, list(values.values())) as cursor:
            await conn.commit()
            return cursor.rowcount
    

async def update_row_in_table(
    filename: str,
    tablename: str,
    confirmation_values: Dict[str, Any],
    updated_values: Dict[str, Any]) -> bool:

    set_expression: str = get_set_expression(updated_values)
    where_expression: str = get_where_expression(confirmation_values)

    placeholders: List[Any] = list(updated_values.values())+list(confirmation_values.values())
    try:
        async with aiosqlite.connect(os_join("tempfiles", filename)) as conn:
            query: str = f"UPDATE {tablename} {set_expression} {where_expression} LIMIT 1"
            async with conn.execute(query, placeholders) as cursor:
                await conn.commit()
                return bool(cursor.rowcount)
    except OperationalError:
        return False


async def create_row_in_table(
    filename: str,
    tablename: str,
    values: Dict[str, Any]
    ) -> dict:
    "return created row or false if failed"
    try:
        columns: List[dict] = await get_columns_meta(filename, tablename)
        for column in columns:
            if not column["notnull"] or column["autoincrement"]:
                continue

            column_name: str = column["name"]

            # if values[column_name] is None:
            #     raise KeyError(f"{column_name} cant be null")


        async with aiosqlite.connect(os_join("tempfiles", filename)) as conn:
            insert_expression: str = f"INSERT INTO {tablename}"
            values_expression: str = get_sql_values_expression(values)
            query: str = f"{insert_expression} {values_expression}"
            async with conn.execute(query, list(values.values())) as cursor:
                await conn.commit()

            where_expression: str = get_where_expression(values)
            query: str = f"SELECT * FROM {tablename} {where_expression}"

            async with conn.execute(query, list(values.values())) as cursor:
                similar_rows: tuple = tuple(await cursor.fetchall())

                if similar_rows == tuple():
                    raise MemoryError
                
                created_row: aiosqlite.Row = similar_rows[-1]
                result: dict = {}

                for column_meta, value in zip(columns, created_row):
                    column_name: str = column_meta["name"]
                    result[column_name] = value

                return result

    except Error as e:
        raise e
