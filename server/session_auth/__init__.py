"""
Package for storing cookies and creating a token for them
"""

from .connection import check_db
from .token_generator import generate_sid
from .crud import *


check_db()
