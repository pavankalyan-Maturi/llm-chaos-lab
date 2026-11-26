from fastapi.testclient import TestClient

from api.main import create_app

client = TestClient(create_app())
BODY = {"tenant_id": "t1", "messages": [{"role": "user", "content": "hi there"}], "max_tokens": 4}


def test_healthz():
    assert client.get("/healthz").json() == {"status": "ok"}


def test_chat():
    r = client.post("/v1/chat", json=BODY)
    assert r.status_code == 200
    assert r.json()["usage"] == {"input_tokens": 2, "output_tokens": 4}


def test_stream_is_unbuffered_sse():
    r = client.post("/v1/chat/stream", json=BODY)
    assert r.headers["content-type"].startswith("text/event-stream")
    assert r.headers["x-accel-buffering"] == "no"
    assert r.text.strip().endswith("data: [DONE]")


def test_metrics_exposed():
    client.post("/v1/chat", json=BODY)
    assert "lab_llm_tokens_total" in client.get("/metrics").text


def test_chaos_requires_token():
    assert client.get("/chaos").status_code == 401
    assert client.get("/chaos", headers={"X-Chaos-Token": "wrong"}).status_code == 401


def test_chaos_lists_no_active_faults():
    r = client.get("/chaos", headers={"X-Chaos-Token": "test-token"})
    assert r.status_code == 200
    assert r.json()["active"] == []


def test_chaos_rejects_unregistered_flag():
    r = client.post(
        "/chaos", headers={"X-Chaos-Token": "test-token"}, json={"flags": {"FAULT_GATEWAY_X": "1"}}
    )
    assert r.status_code == 400
