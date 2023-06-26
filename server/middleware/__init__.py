from typing import Callable, Coroutine, List, Tuple

from starlette.background import BackgroundTask
from fastapi import Request, BackgroundTasks
from fastapi.responses import JSONResponse, Response

from .sqlite_auth import authorization_middleware
from .check_table_exists import check_table_exists_middleware


async def middleware_handler(
    request: Request,
    call_next: Callable[[Request], Coroutine],
    tasks: BackgroundTasks,
):
    "The function that manages the middleware"
    # zero index matches ''
    route: List[str] = request.url.path.split(r"/")

    if len(route) == 1:
        return JSONResponse(status_code=404, content="Page not found")


    match route[1]:
        case "sqlite":
            authorization_result: Tuple[BackgroundTask, str] | JSONResponse \
                = await authorization_middleware(request)

            if isinstance(authorization_result, JSONResponse):
                return authorization_result

            tasks.add_task(authorization_result[0])
            filename: str = authorization_result[1]

            if len(route) > 4 and route[2] == "tables":
                tablename: str = route[3]
                check_table_result: JSONResponse | None = await check_table_exists_middleware(
                                                filename=filename,
                                                tablename=tablename,
                                            )

                if isinstance(check_table_result, JSONResponse):
                    return check_table_result

    response: Response = await call_next(request)
    response.background = tasks
    #response.headers.append("access-control-allow-credentials", "true")
    #response.headers.append("access-control-allow-origin", "http://127.0.0.1:3000")
    return response
