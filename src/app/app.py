import sys
import os
import json
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Use absolute imports
from src import Request, Response  # Correct import

async def app(scope, receive, send):
    try:
        logger.debug(f"Incoming request: {scope}")

        # Check if this is an HTTP request
        if scope["type"] != "http":
            raise ValueError("Only HTTP requests are supported")

        # Create a Request object
        request = Request(scope, receive)  # This should now work
        logger.debug(f"Request created: {request.__dict__}")

        # Handle GET requests
        if request.method == "GET":
            logger.debug("Handling GET request")
            response = Response(
                body={"message": "Hello, world!", "status": "success", "query_params": request.query_params},
                status=200,
                headers={b"x-custom-header": b"value"}
            )
            await response.asgi_response(send)

        # Handle POST requests
        elif request.method == "POST":
            logger.debug("Handling POST request")
            try:
                body = await request.json()
                logger.debug(f"Received JSON body: {body}")
                response = Response(
                    body={"received_body": body},
                    status=200
                )
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                response = Response(
                    body={"error": "Invalid JSON"},
                    status=400
                )
            await response.asgi_response(send)

        # Handle unsupported methods
        else:
            logger.debug("Handling unsupported method")
            response = Response(
                body={"error": "Method Not Allowed"},
                status=405
            )
            await response.asgi_response(send)

    except Exception as e:
        logger.error(f"Internal server error: {e}", exc_info=True)
        response = Response(
            body={"error": "Internal Server Error"},
            status=500
        )
        await response.asgi_response(send)