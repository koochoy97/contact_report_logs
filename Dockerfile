## Stage 1: Build frontend
FROM node:20-slim AS frontend-build

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ .
RUN npm run build

## Stage 2: Python app + frontend dist
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV TZ=America/Lima

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium + all its OS dependencies
RUN playwright install --with-deps chromium

# wget for Docker HEALTHCHECK
RUN apt-get update && apt-get install -y --no-install-recommends wget \
    && rm -rf /var/lib/apt/lists/*

# Copy Python app
COPY app/ app/
COPY .env* ./

# Copy built frontend from stage 1
COPY --from=frontend-build /frontend/dist frontend/dist

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -qO- http://localhost:8001/api/health || exit 1

# Runs scheduler (cron 00:00 Lima) + API + frontend on port 8001
CMD ["python", "-m", "app.main"]
