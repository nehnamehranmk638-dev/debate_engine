import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_root_returns_200():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_debate_rejects_short_topic():
    response = client.post("/debate", json={
        "topic": "AI",
        "num_rounds": 1
    })
    assert response.status_code == 422

def test_debate_rejects_high_rounds():
    response = client.post("/debate", json={
        "topic": "Social media does more harm than good",
        "num_rounds": 10
    })
    assert response.status_code == 422

def test_debate_rejects_empty_topic():
    response = client.post("/debate", json={
        "topic": "          ",
        "num_rounds": 1
    })
    assert response.status_code in [400, 422]

def test_debate_returns_valid_structure():
    response = client.post("/debate", json={
        "topic": "Universal basic income would benefit society",
        "num_rounds": 1
    })
    assert response.status_code == 200
    data = response.json()

    # top level fields
    assert "topic" in data
    assert "rounds" in data
    assert "verdict" in data
    assert "response_time_seconds" in data

    # rounds structure
    assert len(data["rounds"]) == 1
    round1 = data["rounds"][0]
    assert "pro_argument" in round1
    assert "against_argument" in round1
    assert "pro_score" in round1
    assert "against_score" in round1
    assert "pro_sources" in round1
    assert "against_sources" in round1

    # verdict structure
    verdict = data["verdict"]
    assert verdict["winner"] in ["PRO", "AGAINST", "DRAW"]
    assert "pro_total" in verdict
    assert "against_total" in verdict
    assert "margin" in verdict

    # scores structure
    score = round1["pro_score"]
    assert 1 <= score["factual_grounding"] <= 10
    assert 1 <= score["logical_coherence"] <= 10
    assert 0 <= score["hallucination_penalty"] <= 5
    assert score["total"] >= 0