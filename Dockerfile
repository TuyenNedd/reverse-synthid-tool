# ============================================================
# Stage 1: Build frontend (React + Vite + TypeScript + Tailwind)
# ============================================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ============================================================
# Stage 2: Python backend serving API + static frontend
# ============================================================
FROM python:3.11-slim AS production

# Install system dependencies for opencv-python-headless
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (better layer caching)
COPY pyproject.toml ./
COPY src/ ./src/
COPY backend/ ./backend/
COPY artifacts/ ./artifacts/

RUN pip install --no-cache-dir -e .

# Copy built frontend static files
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create results directory
RUN mkdir -p .results

# Expose the API port
EXPOSE 8000

# Environment variables
ENV SYNTHID_HOST=0.0.0.0
ENV SYNTHID_PORT=8000
ENV SYNTHID_ARTIFACTS_DIR=/app/artifacts
ENV SYNTHID_RESULTS_DIR=/app/.results

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

# Run with uvicorn, serving both API and static files
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
