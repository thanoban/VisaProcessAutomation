FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY data ./data
COPY deployment ./deployment
COPY docs ./docs
COPY frontend ./frontend
COPY rag ./rag
COPY schemas ./schemas
COPY tools ./tools
COPY LICENSE README.md PLAN.md .env.example ./

EXPOSE 8080

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}"]
