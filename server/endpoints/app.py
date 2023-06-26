"""
Init app file
"""


import asyncio
import datetime
from typing import Iterable, Coroutine, Callable

import aiosqlite
from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from middleware import middleware_handler
from session_auth import read_all_sessions, delete_session
from tempfiles_api import delete_file
from app_config import COOKIE_RELEVANCE_CHECKING_TIMEOUT


app = FastAPI()

origins = ["http://127.0.0.1:3000", "http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=COOKIE_RELEVANCE_CHECKING_TIMEOUT,
)

class MiddlewareWrapper(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Coroutine],):
        response = await middleware_handler(request, call_next, BackgroundTasks())
        return response


app.add_middleware(MiddlewareWrapper)


@app.get("/")
async def server_root():
    return "server is running"


async def clean_old_sessions():
    "background task(asyncio task, not starlette task) for clean db from old sessions"
    while True:
        now: datetime.datetime = datetime.datetime.now()
        rows: Iterable[aiosqlite.Row] = await read_all_sessions()
        for row in rows:
            row_created: datetime.datetime = datetime.datetime.fromisoformat(row[3])
            diff: datetime.timedelta = now-row_created

            if diff.seconds > COOKIE_RELEVANCE_CHECKING_TIMEOUT or diff.days > 0:
                await delete_session(row[2])
                delete_file(row[1])

        await asyncio.sleep(COOKIE_RELEVANCE_CHECKING_TIMEOUT)


if COOKIE_RELEVANCE_CHECKING_TIMEOUT:
    loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
    loop.create_task(coro=clean_old_sessions(), name="clean_old_sessions")
