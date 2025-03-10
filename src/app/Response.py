import json
from typing import Dict, Any

class Response:

    def __init__(self, body: Any, status: int = 200, headers: Dict[bytes, bytes] = None):
        self.body = body
        self.status = status
        self.headers = headers or {}

    async def asgi_response(self, send):
        if not isinstance(self.body, (str, bytes)):
            self.body = json.dumps(self.body).encode("utf-8") 
        elif isinstance(self.body, str):
            self.body = self.body.encode("utf-8")
        await send({
            "type": "http.response.start",
            "status": self.status,
            "headers": [(b"content-type", b"text/plain")] + list(self.headers.items()),
        })
        await send({"type": "http.response.body", "body": self.body})