from __future__ import annotations

import ssl
from functools import lru_cache
from pathlib import Path

CA_FILE = Path(__file__).resolve().parent.parent / "certs" / "prod-ca-2021.crt"


@lru_cache(maxsize=1)
def ssl_context() -> ssl.SSLContext:
    return ssl.create_default_context(cafile=str(CA_FILE))
