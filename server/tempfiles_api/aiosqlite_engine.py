from typing import List, Iterable, Dict, Any, Optional
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


async def get_columns_meta(filename: str, tablename: str) -> List[Dict]:
    columns: List[dict] = []
    async with aiosqlite.connect(os_join("tempfiles", str(filename))) as conn:
        async with conn.execute(f"PRAGMA table_info({tablename})") as cursor:
            result = await cursor.fetchall()
            for column_metadata in result:
                current_column = {
                    "cid": column_metadata[0],
                    "name": column_metadata[1],
                    "type": column_metadata[2],
                    "notnull": bool(column_metadata[3]),
                    "dflt_value": column_metadata[4],
                    "pk": bool(column_metadata[5]),
                    "autoincrement": False
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


# когда в питон добавят структы нормальные легкие и быстрые а не ети PyObj
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
            

# TODO: отмена етих балбесных Path потому что оно ужос и путает патаму что мы не путь передаем а строку с именем файла и там еще ети типовые issues возникают
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
        limit: Optional[int]) -> int:

        """Deletes one or more rows (set by the limit argument, 
        None - no limit), returns the number of affected rows"""

        where_expression: str = get_where_expression(values)
        limit_expression: str = f"LIMIT {limit}" if limit else ""
        async with aiosqlite.connect(os_join("tempfiles", filename)) as conn:
            query: str = f"DELETE FROM {tablename} " + where_expression + limit_expression
            async with conn.execute(query) as cursor:
                await conn.commit()
                return cursor.rowcount
    

async def update_row_in_table(
    filename: str,
    tablename: str,
    confirmation_values: Dict[str, Any],
    updated_values: Dict[str, Any]) -> bool:

    set_expression: str = get_set_expression(updated_values)
    where_expression: str = get_where_expression(confirmation_values)

    try:
        async with aiosqlite.connect(os_join("tempfiles", filename)) as conn:
            query: str = f"UPDATE {tablename} {set_expression} {where_expression}"
            async with conn.execute(query) as cursor:
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
            if not column["notnull"]:
                continue

            column_name: str = column["name"]

            if values[column_name] is None:
                raise KeyError(f"{column_name} cant be null")


        async with aiosqlite.connect(os_join("tempfiles", filename)) as conn:
            insert_expression: str = f"INSERT INTO {tablename}"
            values_expression: str = get_sql_values_expression(values)
            query: str = f"{insert_expression} {values_expression}"

            async with conn.execute(query) as cursor:
                await conn.commit()

            where_expression: str = get_where_expression(values)
            query: str = f"SELECT * FROM {tablename} {where_expression}"

            async with conn.execute(query) as cursor:
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