import pytest
from src.app.Response import Response

@pytest.mark.asyncio
async def test_response_asgi():
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

@pytest.mark.asyncio
async def test_empty_body_with_content_type():
    async def mock_send(message):
        if message["type"] == "http.response.start":
            assert message["headers"] == [
                (b"content-type", b"application/json"), 
            ]

    response = Response(
        body=None,
        headers={b"content-type": b"application/json"},
    )
    await response.asgi_response(mock_send)

@pytest.mark.asyncio
async def test_invalid_header_type():
    with pytest.raises(TypeError, match="Header keys/values must be bytes"):
        Response(body="test", headers={"x-invalid": "string"}) 