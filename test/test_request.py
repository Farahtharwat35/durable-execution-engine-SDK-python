import pytest

from src.app.Request import Request


@pytest.mark.asyncio
async def test_request_json():
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


@pytest.mark.asyncio
async def test_request_invalid_json():
    async def mock_receive():
        return {
            "type": "http.request",
            "body": b'{"key": value}',
            "more_body": False,
        }

    scope = {
        "method": "POST",
        "path": "/",
        "query_string": b"",
        "type": "http",
        "headers": [(b"content-type", b"application/json")],
    }
    request = Request(scope, mock_receive)

    with pytest.raises(ValueError, match="Invalid JSON"):
        await request.json()


@pytest.mark.asyncio
async def test_request_missing_content_type():
    async def mock_receive():
        return {
            "type": "http.request",
            "body": b'{"key": "value"}',
            "more_body": False,
        }

    scope = {
        "method": "POST",
        "path": "/",
        "query_string": b"",
        "type": "http",
        "headers": [],
    }
    request = Request(scope, mock_receive)
    error_msg = "Content-Type must be 'application/json'"
    with pytest.raises(ValueError, match=error_msg):
        await request.json()


@pytest.mark.asyncio
async def test_request_empty_body():
    async def mock_receive():
        return {
            "type": "http.request",
            "body": b"",
            "more_body": False,
        }

    scope = {
        "method": "POST",
        "path": "/",
        "query_string": b"",
        "type": "http",
        "headers": [(b"content-type", b"application/json")],
    }
    request = Request(scope, mock_receive)

    with pytest.raises(ValueError, match="Empty JSON body"):
        await request.json()
