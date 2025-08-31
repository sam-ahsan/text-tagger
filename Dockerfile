# Dockerfile
# ========== Builder stage ==========
FROM python:3.10-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# Minimal OS deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only requirements first for better layer caching
COPY requirements.txt /app/requirements.txt

# Install deps (CPU-only torch via extra index in requirements.txt)
RUN python -m pip install --upgrade pip \
    && pip install -r requirements.txt

# ========== Final runtime stage ==========
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    # HF_HOME=/home/appuser/.cache/huggingface \
    HF_HOME=/data/hf \
    # HUGGINGFACE_HUB_CACHE=/home/appuser/.cache/huggingface
    HUGGINGFACE_HUB_CACHE=/data/hf \
    TORCH_HOME=/data/torch

# Create non-root user
RUN useradd -m -u 10001 appuser

WORKDIR /app

# Bring in installed site-packages and binaries from builder
COPY --from=builder /usr/local /usr/local

# Copy application code
COPY app /app/app

# Pre-create cache dirs and make them writable
# RUN mkdir -p /home/appuser/.cache/huggingface \
#             /home/appuser/.cache/torch \
#     && chown -R appuser:appuser /home/appuser/.cache
RUN mkdir -p /data/hf /data/torch && chown -R appuser:appuser /data

USER appuser

# Default: API command (dev/prod override in compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
