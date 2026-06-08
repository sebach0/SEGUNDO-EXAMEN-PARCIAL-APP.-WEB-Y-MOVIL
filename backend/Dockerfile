# Backend FastAPI — multi-stage, slim bookworm
# Sin # syntax= ni --mount=cache: evita fallos "frontend grpc server closed" en Docker Desktop/Windows
# Deps: wheels only (asyncpg/crypto have manylinux wheels) → no apt build chain

FROM python:3.11-slim-bookworm AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt

FROM python:3.11-slim-bookworm AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN useradd -m -u 1001 appuser

COPY --from=builder /install /usr/local
COPY --chown=appuser:appuser . .

RUN mkdir -p /app/uploads/evidencias && chown -R appuser:appuser /app/uploads

USER appuser

EXPOSE 8000

ENV UVICORN_PORT=8000
CMD ["python", "start.py"]
