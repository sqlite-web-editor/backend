"""
/sqlite api endpoints
"""

from fastapi import Response, UploadFile, HTTPException, Request
from session_auth import cookie_create, cookie_read, \
                         cookie_delete, generate_sid
from session_auth.sa_types import Ok, Err
from tempfiles_api import create_file, delete_file
from sqlite3_utils import is_correct_db
from app_config import MAX_FILE_SIZE
from .app import app


@app.post("/sqlite/{query}", status_code=201)
async def sqlite_query(
    response: Response,
    query: str
    ):
    "sql query executor"

