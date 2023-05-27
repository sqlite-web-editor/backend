"""
Types for session_auth package
"""

from typing import Union, TypeVar, Generic, Any, Optional
from os import PathLike


T = TypeVar("T")
Path = Union[str, bytes, PathLike]


# pylint: disable=too-few-public-methods
class ResultOption(Generic[T]):
    "just a container for better data storage"
    def __init__(self, value: T = None):
        self.value=value


class Ok(ResultOption[Any]):
    "means that everything is fine (in the context of a function or value)"


class Err(ResultOption[Optional[Exception]]):
    "means that everything is bad (in the context of a function or value)"


Result = Union[Ok, Err]
CookieNotFoundError = KeyError("Cookie not found")
