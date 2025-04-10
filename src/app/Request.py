import json
from urllib.parse import parse_qs

class Request:
    def __init__(self, scope, receive):
        self.scope = scope
        self.receive = receive
        self.method = scope["method"]
        self.path = scope["path"]
        self.query_params = parse_qs(scope["query_string"].decode())
        self.headers = {k.decode(): v.decode() for k, v in scope["headers"]}

    async def json(self):
        content_type = self.headers.get("content-type", "")
        
        if not content_type.startswith("application/json"):
            raise ValueError("Content-Type must be 'application/json'")

        body = await self.body()

        if not body:
            raise ValueError("Empty JSON body")

        try:
            return json.loads(body)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON")

    async def body(self):
        body = b""
        while True:
            message = await self.receive()
            if message["type"] == "http.request":
                body += message.get("body", b"")
                if not message.get("more_body", False):
                    break
        return body