"""
/sqlite api endpoints

rules:
    request.cookies.get("session_id") always be not None and actual thanks to middleware
"""

from typing import Dict, Any, Optional
from os.path import join as os_join 
from fastapi import Response, HTTPException, Request
from fastapi.responses import FileResponse
from aiosqlite import Error, IntegrityError, Warning
from session_auth import read_session_filepath
from session_auth.sa_types import Ok, Err, Result
from tempfiles_api import get_tables, get_table_content, delete_row_in_table, \
                          update_row_in_table, create_row_in_table, get_columns_meta, get_table_rowcount
from .content_preparing import prepare_int_to_string, prepare_blob, convert_b64blob_to_bytes
from .app import app


# @app.post("/sqlite/execute/{query}", status_code=201)
# async def sqlite_query(
#     response: Response,
#     request: Request,
#     query: str
#     ):
#     "sql query executor"
#     session_id: str = request.cookies.get("session_id") # type: ignore

#     res: Ok[str] | Err = await read_session_filepath(session_id)

#     if isinstance(res, Err):
#         raise HTTPException(status_code=405)

#     filename: str = res.value
#     path: str = os_join("tempfiles", filename)


@app.get("/sqlite/download")
async def download_file(
    response: Response,
    request: Request
    ):
    session_id: str = request.cookies.get("session_id") # type: ignore
    path_to_file: str = os_join("tempfiles", session_id+".db")
    return FileResponse(path_to_file,  headers={"Content-Disposition": "attachment; filename=sqlite_web_redactor.db"})



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
        

@app.get("/sqlite/tables/{tablename}/rowcount", status_code=200)
async def get_sqlite_table_schema_rowcount(
    tablename: str,
    response: Response,
    request: Request
    ):
    session_id: str = request.cookies.get("session_id") # type: ignore
    filename: str = session_id+".db"
    return await get_table_rowcount(filename, tablename)


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

    if to<0 or _from<0:
        raise HTTPException(status_code=400, detail="Неверные значения to и(или) _from.")
    
    session_id: str = request.cookies.get("session_id") # type: ignore
    filename: str = session_id+".db"
    content = await get_table_content(filename, tablename, _from, to)
    return prepare_blob(prepare_int_to_string(content))


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
    indices: list[int] = []
    meta = await get_columns_meta(filename, tablename)

    for index, column in enumerate(meta):
        if column["type"] == "BLOB":
            indices.append(index)
    
    for blob_col_index in indices:
        blob_col_name = meta[blob_col_index]["name"]
        if blob_col_name in confirmation_values:
            confirmation_values[blob_col_name] = convert_b64blob_to_bytes(confirmation_values[blob_col_name])

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
    result: bool = False
    indices: list[int] = []
    meta = await get_columns_meta(filename, tablename)

    for index, column in enumerate(meta):
        if column["type"] == "BLOB":
            indices.append(index)

    for blob_col_index in indices:
        blob_col_name = meta[blob_col_index]["name"]
        if blob_col_name in updated_values:
            updated_values[blob_col_name] = convert_b64blob_to_bytes(updated_values[blob_col_name])
        if blob_col_name in confirmation_values:
            confirmation_values[blob_col_name] = convert_b64blob_to_bytes(confirmation_values[blob_col_name])
    try:
        result = await update_row_in_table(
            filename,
            tablename,
            confirmation_values,
            updated_values
        )
        
    except IntegrityError as error:
        if "UNIQUE" in error.args[0]:
            column_name = error.args[0].split(":")[1].split(tablename)[1][1::]
            raise HTTPException(status_code=409, detail=f"Значение в колонне {column_name} должно быть уникальным")
        
        if "datatype mismatch" in error.args[0]:
            raise HTTPException(status_code=409, detail=f"Ошибка типа в одной из колонн")
        
    except Warning:
        raise HTTPException(status_code=409, detail='Похоже на SQL инъекцию. Пожалуйста, не используйте символ ";" в сочетании с " (двойные кавычки)')
        
    return {"foundedAndUpdated": result}


@app.post("/sqlite/tables/{tablename}/content")
async def create_sqlite_row(
    tablename: str,
    row_values: Dict[str, Any],
    response: Response,
    request: Request
    ):
    session_id: str = request.cookies.get("session_id") # type: ignore
    filename: str = session_id+".db"

    indices: list[int] = []
    meta = await get_columns_meta(filename, tablename)

    for index, column in enumerate(meta):
        if column["type"] == "BLOB":
            indices.append(index)
    
    for blob_col_index in indices:
        blob_col_name = meta[blob_col_index]["name"]
        if blob_col_name in row_values:
            row_values[blob_col_name] = convert_b64blob_to_bytes(row_values[blob_col_name])

    try:
        row_data = await create_row_in_table(
            filename,
            tablename,
            row_values,
        )
        data = prepare_blob(
            prepare_int_to_string({
                "data": list([row_data.values()], ),
                "columns": meta,
            })
        )
        data_to_send = {}
        for column in data["columns"]:
            data_to_send[column["name"]] = data["data"][0][column["cid"]]

        return data_to_send
        
    # except KeyError as error:
    #     raise HTTPException(status_code=400, detail=str(error))

    except IntegrityError as error:
        if "UNIQUE" in error.args[0]:
            column_name = error.args[0].split(":")[1].split(tablename)[1][1::]
            raise HTTPException(status_code=409, detail=f"Значение в колонне {column_name} должно быть уникальным")
        
        if "datatype mismatch" in error.args[0]:
            raise HTTPException(status_code=409, detail="Ошибка типа в одной из колонн")

    except Warning:
        raise HTTPException(status_code=409, detail='Похоже на SQL инъекцию. Пожалуйста, не используйте символ ";"')