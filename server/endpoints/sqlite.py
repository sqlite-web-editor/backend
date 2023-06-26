"""
/sqlite api endpoints

rules:
    request.cookies.get("session_id") always be not None and actual thanks to middleware
"""

from typing import Dict, Any, Optional
from os.path import join as os_join 
from fastapi import Response, HTTPException, Request
from fastapi.responses import FileResponse
from session_auth import read_session_filepath
from session_auth.sa_types import Ok, Err, Result
from tempfiles_api import get_tables, get_table_content, delete_row_in_table, \
                          update_row_in_table, create_row_in_table, get_columns_meta
from .app import app


@app.post("/sqlite/execute/{query}", status_code=201)
async def sqlite_query(
    response: Response,
    request: Request,
    query: str
    ):
    "sql query executor"
    session_id: str = request.cookies.get("session_id") # type: ignore

    res: Ok[str] | Err = await read_session_filepath(session_id)

    if isinstance(res, Err):
        raise HTTPException(status_code=405)

    filename: str = res.value
    path: str = os_join("tempfiles", filename)


@app.get("/sqlite/download")
async def download_file(
    response: Response,
    request: Request
    ):
    session_id: str = request.cookies.get("session_id") # type: ignore
    path_to_file: str = os_join("tempfiles", session_id+".db")
    return FileResponse(path_to_file)



@app.get("/sqlite/tables", status_code=200)
async def sqlite_tables(
    response: Response,
    request: Request
    ):
    session_id: str = request.cookies.get("session_id") # type: ignore
    filename: str = session_id+".db"
    tables: Result = await get_tables(filename)

    match isinstance(tables, Ok):
        case True:
            return {"tables": tables.value}

        case False:
            raise HTTPException(status_code=500)
        

@app.get("/sqlite/tables/{tablename}/schema", status_code=200)
async def get_sqlite_table_schema(
    tablename: str,
    response: Response,
    request: Request
    ):
    session_id: str = request.cookies.get("session_id") # type: ignore
    filename: str = session_id+".db"
    return await get_columns_meta(filename, tablename)


@app.get("/sqlite/tables/{tablename}/content/{_from}/{to}", status_code=200)
async def get_sqlite_table_content(
    tablename: str,
    _from: int,
    to: int,
    response: Response,
    request: Request
    ):

    if to < _from:
        raise HTTPException(status_code=400, detail="The _from value (first after /content/) is greater than the to value (second after /content/)")

    session_id: str = request.cookies.get("session_id") # type: ignore
    filename: str = session_id+".db"
    return await get_table_content(filename, tablename, _from, to)


@app.delete("/sqlite/tables/{tablename}/content")
async def delete_sqlite_row(
    tablename: str,
    confirmation_values: Dict[str, Any],
    response: Response,
    request: Request,
    limit: Optional[int] = None
    ):
    if len(confirmation_values) == 0:
        raise HTTPException(400)
    
    session_id: str = request.cookies.get("session_id") # type: ignore
    filename: str = session_id+".db"
    rowcount: int = await delete_row_in_table(filename, tablename, confirmation_values, limit)
    return {"rowcount": rowcount}


@app.patch("/sqlite/tables/{tablename}/content")
async def update_sqlite_row(
    tablename: str,
    confirmation_values: Dict[str, Any],
    updated_values: Dict[str, Any],
    response: Response,
    request: Request,
    ):
    session_id: str = request.cookies.get("session_id") # type: ignore
    filename: str = session_id+".db"
    result = await update_row_in_table(
        filename,
        tablename,
        confirmation_values,
        updated_values
    )
    return {"founded and updated": result}


@app.post("/sqlite/tables/{tablename}/content")
async def create_sqlite_row(
    tablename: str,
    row_values: Dict[str, Any],
    response: Response,
    request: Request
    ):

    session_id: str = request.cookies.get("session_id") # type: ignore
    filename: str = session_id+".db"
    try:
        return await create_row_in_table(
            filename,
            tablename,
            row_values,
        )
    except KeyError as error:
        raise HTTPException(status_code=400, detail=str(error))
    
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))