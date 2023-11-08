"""
Application config
MAX_FILE_SIZE - the maximum allowable size of a sqlite file. 
(bytes)         You can change it to your liking or set it to 0 to remove the limit.

COOKIE_RELEVANCE_CHECKING_TIMEOUT - the time after which it is worth checking obsolete cookies 
(seconds)                           and deleting them from the database. 
                                    0 for no limit
"""

MAX_FILE_SIZE = 1024 * 1024 * 5  # 5 mb
COOKIE_RELEVANCE_CHECKING_TIMEOUT = 60*30 # 30 min


FRONTEND_IP = "192.168.1.103"
FRONTEND_PORT = "3000"
FRONTEND_PROTOCOL = "http"