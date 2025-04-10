import json
from typing import Any, Dict, Optional


class Response:
    def __init__(
        self,
        body: Any,
        status: int = 200,
        headers: Optional[Dict[bytes, bytes]] = None,
    ):
        self.body = body
        self.status = status
        self.headers = headers or {}
        for k, v in self.headers.items():
            if not isinstance(k, bytes) or not isinstance(v, bytes):
                raise TypeError("Header keys/values must be bytes")

    async def asgi_response(self, send):
        if self.body is None:
            body_bytes = b""
        else:
            if not isinstance(self.body, (str, bytes)):
                try:
                    body_bytes = json.dumps(self.body).encode("utf-8")
                except TypeError as e:
                    raise TypeError(f"Body serialization failed: {e}")
            else:
                body_bytes = (
                    self.body.encode("utf-8")
                    if isinstance(self.body, str)
                    else self.body
                )
        headers = list(self.headers.items())
        if b"content-type" not in self.headers:
            headers.insert(0, (b"content-type", b"text/plain"))
        await send(
            {
                "type": "http.response.start",
                "status": self.status,
                "headers": headers,
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": body_bytes,
            }
        )
