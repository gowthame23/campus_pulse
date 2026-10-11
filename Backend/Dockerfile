# Campus Pulse API — FastAPI + Uvicorn
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# CLAUDE.md's documented run command is:
#   python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
# 127.0.0.1 only binds the container's loopback interface, which the
# published port cannot reach from outside — so we bind 0.0.0.0 here
# instead. Entrypoint module and port are otherwise unchanged, and
# --reload is intentionally omitted since CLAUDE.md's command doesn't use it.
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
