"""
/session api endpoints
session creation policy: 1 file - 1 session
"""

from os.path import join as os_join
from fastapi import Response, UploadFile, HTTPException, Request
from session_auth import create_session, read_session_filepath, delete_session, generate_sid
from session_auth.sa_types import Ok, Err
from tempfiles_api import create_file, delete_file
from sqlite3_utils import is_correct_db
from app_config import MAX_FILE_SIZE, FRONTEND_IP
from .app import app


@app.post("/session/create", status_code=201)
async def session_create(
    file: UploadFile,
    response: Response,
    request: Request
    ):

    "Create a new session"

    if file.size is None:
        raise HTTPException(500, detail="invalid file")

    if file.size > MAX_FILE_SIZE and MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Upload file size greater than {MAX_FILE_SIZE/1024/1024}mb",
            headers={"maxFileSize": f"{MAX_FILE_SIZE/1024/1024}mb"}
        )

    session_id: str | None = request.cookies.get("session_id")

    if session_id is not None:
        result: Ok[str] | Err = await read_session_filepath(session_id)
        if isinstance(result, Ok):
            path_to_file: str = result.value
            await delete_session(session_id)
            delete_file(path_to_file)


    sid: str = generate_sid()
    filename: str = sid+".db"
    f_content: bytes = await file.read()

    await create_file(filename, f_content)
    is_correct = await is_correct_db(os_join("tempfiles", filename))

    if not is_correct:
        delete_file(filename)
        raise HTTPException(status_code=415, detail="Invalid sqlite file")

    await create_session(sid, filename)
    response.set_cookie(key="session_id",
                        value=sid,
                        httponly=True,
                        secure=False,
                        max_age=1800,
                        expires=1800,
                        samesite="lax",
                        domain=FRONTEND_IP)


@app.delete("/session/delete", status_code=204)
async def session_delete(response: Response, request: Request,):
    "delete the session"

    session_id: str | None = request.cookies.get("session_id")

    if session_id is None:
        raise HTTPException(status_code=405)

    res: Ok[str] | Err = await read_session_filepath(session_id)
    if isinstance(res, Err):
        raise HTTPException(status_code=405)

    path: str = res.value

    delete_file(path)
    await delete_session(session_id)
    response.delete_cookie("session_id")
