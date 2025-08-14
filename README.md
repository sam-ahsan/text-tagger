# TagServe — AI-Powered Text Tagging API

TagServe is a FastAPI-based microservice for tagging text with **Named Entities**, **topics**, and **custom domain terms** using NLP models.  
It is designed with production-readiness in mind, featuring asynchronous task processing, observability, and test coverage.

---

## Features

- **Single & Batch Tagging Endpoints**
  - `/v1/tag` for low-latency tagging
  - `/v1/tag/batch` for asynchronous large-scale tagging
- **Named Entity Recognition (NER)**
  - Detects organizations, people, locations, etc.
- **Topic Classification**
  - Assigns high-level topics (e.g., technology, business, AI)
- **Domain-Specific Tag Boosting**
  - Option to provide a custom dictionary to boost certain terms
- **Observability**
  - Prometheus metrics:
    - Task counts by status
    - Cache hits
    - Task duration histogram
    - Queue depth
  - `/healthz` endpoint with readiness check
- **Testing**
  - Unit tests for tagging logic
  - Integration tests for API endpoints
  - Mocked Redis and models for fast, deterministic tests
- **Asynchronous Processing**
  - Celery workers with Redis backend for batch processing
  - Eager execution mode in tests
- **Long Text Handling**
  - Automatic text chunking for long documents

---

## Architecture
Diagram TBD

---

## Getting Started

### Prerequisites
- Python 3.10+
- Docker & Docker Compose

### Installation
```bash
git clone https://github.com/sam-ahsan/text-tagger.git
cd text-tagger
make dev  # starts API + worker + Redis

curl -X POST http://localhost:8000/v1/tag \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["Elon Musk visited Berlin."],
    "language": "en"
  }'

# Submit batch
curl -X POST http://localhost:8000/v1/tag/batch \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["Elon Musk visited Berlin.", "NVIDIA announced new GPUs."]
  }'

# Poll for status
curl http://localhost:8000/v1/tag/batch/<job_id>

# Running tests
PYTHONENV ./ pytest -q -vv

# Viewing Metrics
curl http://localhost:8000/metrics
