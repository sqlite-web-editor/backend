from typing import Tuple

from starlette.background import BackgroundTask
from fastapi import Request
from fastapi.responses import JSONResponse

from session_auth import read_session_filepath, update_session_timestamp
from session_auth.sa_types import Ok, Err


async def authorization_middleware(
    request: Request,
    ) -> Tuple[BackgroundTask, str] | JSONResponse:
    """
    middleware that checks for the existence of a session and a database file.
    Takes responsibility for creating a task to update the timestamp in our database.
    Returns Tuple[BackgroundTask, str] - task with timestamp update, and file name.
    Or returns a JSONResponse with a 405 error code if no record is found.
    """
    headers = {"access-control-allow-credentials": "true",
               "access-control-allow-origin": "http://127.0.0.1:3000"}
    session_id: str | None = request.cookies.get("session_id")

    if session_id is None:
        return JSONResponse(content="Invalid session id",
                            status_code=405, headers=headers)

    result: Ok[str] | Err = await read_session_filepath(session_id)

    if isinstance(result, Err):
        return JSONResponse(content="Invalid session id",
                            status_code=405, headers=headers)

    update_session_task: BackgroundTask = BackgroundTask(update_session_timestamp, session_id)
    return (update_session_task, result.value)
