"""
Generate token (session id) for cookie
"""

import time


def generate_sid():
    "Just generate number based on unix time"
    # note: sid - session id
    sid: str = "".join(
        (
            str(round(time.time(), 5))
            .split(".")
        )
    )
    return sid
