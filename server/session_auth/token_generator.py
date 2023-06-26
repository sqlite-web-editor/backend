"""
Generate token (session id) for cookie
"""

import uuid

def generate_sid():
    "generate random sid using uuid4"
    # note: sid - session id
    sid: str = str(uuid.uuid4())
    return sid
