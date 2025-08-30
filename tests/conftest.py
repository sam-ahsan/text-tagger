# tests/conftest.py
import os

import fakeredis

from app.core.security import create_access_token
from app.core.users import create_user, get_user

# --- 1) Set env BEFORE importing app modules ---
os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "true")
os.environ.setdefault("CELERY_TASK_EAGER_PROPAGATES", "true")
# REDIS_URL won't be used, but leave it for code paths that read it
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("CACHE_TTL_SECONDS", "60")
os.environ.setdefault("CELERY_TAGGING_QUEUE", "tagging")
os.environ.setdefault("CACHE_NS", "test")

# --- 2) Patch get_redis BEFORE importing app.main so startup uses fakeredis ---
fake_r = fakeredis.FakeRedis(decode_responses=True)

from app.core import redis_client as redis_client_mod  # noqa: E402


def _fake_get_redis():
    return fake_r
# Monkeypatch-like override at import time (no pytest needed yet)
redis_client_mod.get_redis = _fake_get_redis  # type: ignore[attr-defined]

# --- 3) Now it is safe to import app.main (startup will use fake redis) ---
# --- 4) Import the rest AFTER main is loaded ---
from fastapi.testclient import TestClient  # noqa: E402

import app.main as main_mod  # noqa: E402
from app.services import tasks as tasks_mod  # noqa: E402
from app.services.tagging import TaggingService  # noqa: E402
from app.workers.celery_app import celery_app  # noqa: E402


# --- 5) Fake models so tests don't download HF models ---
class FakeNER:
    def predict(self, texts, languages=None):
        out = []
        for t in texts:
            ents = []
            lt = t.lower()
            if "elon" in lt:
                ents.append({"text": "Elon Musk", "label": "PER", "score": 0.99})
            if "berlin" in lt:
                ents.append({"text": "Berlin", "label": "LOC", "score": 0.98})
            if "nvidia" in lt:
                ents.append({"text": "NVIDIA", "label": "ORG", "score": 0.95})
            out.append(ents)
        return out

class FakeTopics:
    def __init__(self):
        self.threshold = 0.35
        self.top_k = 5
    def predict(self, texts, languages=None):
        res = []
        for t in texts:
            lt = t.lower()
            labels = []
            if "nvidia" in lt or "gpu" in lt:
                labels.append({"label": "technology", "score": 0.95})
            if "elon" in lt:
                labels.append({"label": "business", "score": 0.80})
            if not labels:
                labels = [{"label": "business", "score": 0.60}]
            res.append(labels[: self.top_k])
        return res

class FakeTagger(TaggingService):
    def __init__(self):
        self.ner_model = FakeNER()
        self.topic_model = FakeTopics()
        self.domain_boost = 0.85
        self.ner_weight = 1.0
        self.topic_weight = 1.0

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def patch_runtime_objects(monkeypatch):
    # Replace any module-level cached Redis clients created after import
    # API router module-level redis client:
    monkeypatch.setattr(main_mod.tag, "redis", fake_r, raising=True)
    # Celery task module-level redis:
    monkeypatch.setattr(tasks_mod, "_redis", fake_r, raising=True)

    # Force Celery eager + in-memory backend so AsyncResult doesn’t hit Redis
    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
        task_store_eager_result=True,
        broker_url="memory://",
        result_backend="cache+memory://"
    )

    # Fake taggers in both API and worker paths
    monkeypatch.setattr(main_mod.tag, "tagger", FakeTagger(), raising=True)
    monkeypatch.setattr(tasks_mod, "_tagger", FakeTagger(), raising=True)

    yield

@pytest.fixture()
def client():
    return TestClient(main_mod.app)

@pytest.fixture(scope="session")
def test_username() -> str:
    return "test-user"

@pytest.fixture(scope="session")
def test_tenant() -> str:
    return "test-tenant"

@pytest.fixture(scope="session")
def test_password() -> str:
    return "test-password"

@pytest.fixture()
def auth_headers(test_username, test_password, test_tenant, client):
    try:
        user = get_user(test_username)
        if not user:
            create_user(test_username, test_password, tenant_id=test_tenant, roles=["user"])
    except Exception:
        pass
    
    token = create_access_token(
        subject=test_username,
        extra={"tenant_id": test_tenant, "roles": ["user"]}
    )
    return {"Authorization": f"Bearer {token}"}
