FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY ampla_project ./ampla_project
COPY api ./api

RUN pip install --no-cache-dir fastapi uvicorn[standard] lxml

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
