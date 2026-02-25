# CourtFlow API – deploy with Docker or use for Render/Railway
FROM python:3.11-slim

WORKDIR /app

# Install FFmpeg (optional for API-only; needed if pipeline runs in same container)
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY dashboard/ ./dashboard/
COPY pyproject.toml ./

ENV PORT=8000
EXPOSE 8000

# PORT is overridden by Render/Railway at runtime
CMD ["sh", "-c", "uvicorn src.app.api:app --host 0.0.0.0 --port ${PORT}"]
