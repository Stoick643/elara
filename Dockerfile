FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

RUN python -m venv .venv
COPY requirements.txt ./
RUN .venv/bin/pip install -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /app/.venv .venv/
COPY . .

CMD ["sh", "-c", ".venv/bin/flask db upgrade && .venv/bin/gunicorn 'app:create_app()' --bind 0.0.0.0:8080"]
