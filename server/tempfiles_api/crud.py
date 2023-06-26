"""
Create and delete methods for temporary files 
where sqlite databases reside
in functions pass only filename (8dea0961-...-...-2fe10a6s.db), without filename folder
"""

import os
from os.path import join as os_join
import aiofiles
from session_auth.sa_types import Path


async def create_file(filename: Path, content: bytes) -> None:
    "create file and write content. Path of created file = tempfiles/{filename}"
    async with aiofiles.open(f"tempfiles/{filename}", "wb") as file:
        await file.write(content)


def delete_file(filename: Path) -> None:
    "delete file in tempfiles folder by filename."
    os.remove(os_join("tempfiles", filename)) # type: ignore
