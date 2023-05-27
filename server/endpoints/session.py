"""
/session api endpoints
session creation policy: 1 file - 1 session
"""

from fastapi import Response, UploadFile, HTTPException, Request
from session_auth import cookie_create, cookie_read, \
                         cookie_delete, generate_sid
from session_auth.sa_types import Ok, Err
from tempfiles_api import create_file, delete_file
from sqlite3_utils import is_correct_db
from app_config import MAX_FILE_SIZE
from .app import app


@app.post("/session/create", status_code=201)
async def session_create(
    response: Response,
    file: UploadFile
    ):
    "creating cookies for session"
    if file.size is None:
        raise HTTPException(500, detail="moment")

    if file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Upload file size greater than {MAX_FILE_SIZE/1024/1024}mb",
            headers={"maxFileSize": f"{MAX_FILE_SIZE/1024/1024}mb"}
        )

    sid: str = generate_sid()
    filename: str = sid+".db"
    f_content: bytes = await file.read()
    await create_file(filename, f_content)
    is_correct = await is_correct_db(f"tempfiles/{filename}") # TODO: os.path.join moment

    if not is_correct:
        delete_file(filename)
        raise HTTPException(status_code=415, detail="Invalid sqlite file")

    await cookie_create(sid, filename) # yeah, that stupid one thing
    response.set_cookie(key="session_id", value=sid)



@app.delete("/session/delete", status_code=204)
async def session_delete(request: Request, response: Response):
    "deleting session cookies"
    session_id: str | None = request.cookies.get("session_id")

    if session_id is None:
        raise HTTPException(status_code=405)

    res: Ok | Err = await cookie_read(session_id)
    if isinstance(res, Err):
        raise HTTPException(status_code=405)

    path: str = res.value[0] # TODO: os.path.join moment

    delete_file(path)
    await cookie_delete(session_id)
    response.delete_cookie("session_id")
