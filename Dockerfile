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

# System dependencies for Playwright Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
    libpango-1.0-0 libcairo2 libasound2 libxshmfence1 \
    fonts-liberation wget ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium
RUN playwright install chromium

# Copy Python app
COPY app/ app/
COPY .env* ./

# Copy built frontend from stage 1
COPY --from=frontend-build /frontend/dist frontend/dist

EXPOSE 8001

# Runs scheduler (cron 00:00 Lima) + API + frontend on port 8001
CMD ["python", "-m", "app.main"]
