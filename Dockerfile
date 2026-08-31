# SignalGate - single service (web + API), doc 03 §10.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    SIGNALGATE_MODE=mock

WORKDIR /app

COPY requirements-lock.txt ./
RUN pip install --no-cache-dir -r requirements-lock.txt

COPY pyproject.toml README.md LICENSE NOTICE ./
COPY src ./src
COPY generator ./generator
RUN pip install --no-cache-dir . --no-deps

# Writable artifact roots (stateless service; artifacts on disk, doc 03 §1)
RUN mkdir -p /app/artifacts /app/data /app/reports
RUN python -m generator.build --out data

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD ["python", "-c", "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/healthz')"]

CMD ["sh", "-c", "uvicorn signalgate.api.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
