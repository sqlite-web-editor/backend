"""
Create and delete methods for temporary files 
where sqlite databases reside
"""

import multiprocessing
import os
import aiofiles
from session_auth.sa_types import Path


async def create_file(filename: Path, content: bytes) -> None:
    "create file and write content. Path of created file = tempfiles/{filename}"
    async with aiofiles.open(f"tempfiles/{filename}", "wb") as file:
        await file.write(content)


def delete_file(filename: Path) -> None:
    "delete file in tempfiles folder by filename. Create process for deleting :/"
    proc = multiprocessing.Process(target=os.remove, args=(f"tempfiles/{filename}",))
    proc.start()
    proc.join()
