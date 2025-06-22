FROM python:3.10-slim AS builder

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ../src ./src
COPY ./ ./example

FROM python:3.10-slim

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin


COPY src/ ./src/
COPY example/ ./example/

ENV DURABLE_ENGINE_BASE_URL=http://host.docker.internal:8080/api/v1
ENV PYTHONPATH=/app/src:/app
ENV PYTHONUNBUFFERED=1

ENV LOG_LEVEL=DEBUG

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/discover || exit 1

WORKDIR /app/example

CMD ["python", "main.py"]