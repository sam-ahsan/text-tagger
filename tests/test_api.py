import time

def wait_for_success(client, job_id: str, headers: dict, timeout: float = 5.0, interval: float = 0.5):
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        response = client.get(f"/v1/tag/batch/{job_id}", headers=headers)
        assert response.status_code == 200
        last = response.json()
        status = last.get("status")
        if status == "SUCCESS":
            return last
        elif status == "FAILURE":
            raise AssertionError(f"Batch task failed: {last.get('error', 'Unknown error')}")
        time.sleep(interval)
    raise AssertionError(f"Timed out waiting for SUCCESS. Last status: {last.get('status')}")

def test_celery_eager_smoke():
    from app.services.tasks import tag_batch_task
    response = tag_batch_task.apply_async(kwargs={"texts": ["hi"], "language": "en"})
    assert response.state == "SUCCESS"
    assert response.get(timeout=0.1)

def test_root_and_health_ready(client):
    root = client.get("/")
    assert root.status_code == 200
    health = client.get("/healthz")
    assert health.status_code == 200
    ready = client.get("/readyz")
    assert ready.status_code in (200, 503)

def test_tag_endpoint(client, auth_headers):
    payload = {
        "texts": ["Elon Musk visited Berlin.", "NVIDIA announced new GPUs."],
        "language": "en",
        "domain_dict": ["technology", "AI"]
    }
    response = client.post("/v1/tag", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data and len(data["results"]) == 2
    assert data["results"][1]["topics"] is not None

def test_batch_submit_and_status(client, auth_headers):
    payload = {
        "texts": ["Elon Musk visited Berlin.", "NVIDIA announced new GPUs."],
        "language": "en",
        "domain_dict": ["technology", "AI"]
    }
    response = client.post("/v1/tag/batch", json=payload, headers=auth_headers)
    assert response.status_code == 200
    job_id = response.json()["job_id"]

    body = wait_for_success(client, job_id, headers=auth_headers)

    assert body["status"] == "SUCCESS"
    assert "result" in body and body["result"] and "results" in body["result"]
    results = body["result"]["results"]
    assert len(results) == 2
    assert any("technology" in [tag.lower() for tag in result["tags"]] for result in results)

def test_metrics_endpoint(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    assert "tagging_tasks_total" in content or "http_requests_total" in content
