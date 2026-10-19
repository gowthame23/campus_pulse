# Campus Pulse API — FastAPI + Uvicorn
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# CLAUDE.md's documented run command is:
#   python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
CMD ["sh", "-c", "python -m uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
