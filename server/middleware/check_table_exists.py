from fastapi.responses import JSONResponse
from tempfiles_api import check_table_exists

async def check_table_exists_middleware(
    filename: str,
    tablename: str,
    ) -> JSONResponse | None:
    """
    middleware that checks the existence of the table,
    in case of absence it returns a ready-made response with a 404 code.
    If everything is ok returns None
    """

    table_exists: bool = await check_table_exists(filename, tablename)

    if table_exists:
        return

    return JSONResponse(status_code=404, content=f"table `{tablename}` doesnt exists")
