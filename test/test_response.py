import pytest
from src.app.Response import Response

@pytest.mark.asyncio
async def test_response_asgi():
    """Test Response ASGI serialization."""
    async def mock_send(message):
        if message["type"] == "http.response.start":
            assert message["status"] == 200
            assert message["headers"] == [
                (b"content-type", b"text/plain"),
                (b"x-custom", b"value"),
            ]
        elif message["type"] == "http.response.body":
            assert message["body"] == b'{"key": "value"}'

    response = Response(
        body={"key": "value"},
        headers={b"x-custom": b"value"},
    )
    await response.asgi_response(mock_send)