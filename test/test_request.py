import pytest
from src.app.Request import Request

@pytest.mark.asyncio
async def test_request_json():
    """Test JSON body parsing."""
    async def mock_receive():
        return {
            "type": "http.request",
            "body": b'{"key": "value"}',
            "more_body": False,
        }

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/",
        "query_string": b"",
        "headers": [(b"content-type", b"application/json")],
    }
    request = Request(scope, mock_receive)
    assert await request.json() == {"key": "value"}