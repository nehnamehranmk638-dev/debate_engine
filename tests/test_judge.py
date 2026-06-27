import pytest
from agents.judge import JudgeAgent

@pytest.fixture
def judge():
    return JudgeAgent()

def test_judge_returns_valid_scores(judge):
    scores = judge.evaluate(
        topic="AI should be regulated",
        stance="PRO",
        argument="Government regulation ensures AI safety and transparency according to recent studies.",
        evidence_used="Recent studies show that government oversight of AI systems leads to safer and more transparent outcomes for users.",
        round_num=1
    )
    assert "factual_grounding" in scores
    assert "logical_coherence" in scores
    assert "responsiveness" in scores
    assert "hallucination_penalty" in scores
    assert "total" in scores
    assert "reasoning" in scores

def test_judge_scores_within_range(judge):
    scores = judge.evaluate(
        topic="AI should be regulated",
        stance="PRO",
        argument="Government regulation ensures AI safety and transparency.",
        evidence_used="Government oversight leads to safer AI outcomes.",
        round_num=1
    )
    assert 1 <= scores["factual_grounding"] <= 10
    assert 1 <= scores["logical_coherence"] <= 10
    assert 1 <= scores["responsiveness"] <= 10
    assert 0 <= scores["hallucination_penalty"] <= 5
    assert scores["total"] >= 0

def test_judge_total_is_correct(judge):
    scores = judge.evaluate(
        topic="AI should be regulated",
        stance="PRO",
        argument="Government regulation ensures AI safety and transparency.",
        evidence_used="Government oversight leads to safer AI outcomes.",
        round_num=1
    )
    expected_total = (
        scores["factual_grounding"] +
        scores["logical_coherence"] +
        scores["responsiveness"] -
        scores["hallucination_penalty"]
    )
    assert scores["total"] == expected_total

def test_extract_json_handles_markdown(judge):
    raw = '```json\n{"factual_grounding": 7, "logical_coherence": 8, "responsiveness": 7, "hallucination_penalty": 0, "total": 22, "reasoning": "good"}\n```'
    result = judge._extract_json(raw)
    assert result["factual_grounding"] == 7

def test_extract_json_handles_plain(judge):
    raw = '{"factual_grounding": 7, "logical_coherence": 8, "responsiveness": 7, "hallucination_penalty": 0, "total": 22, "reasoning": "good"}'
    result = judge._extract_json(raw)
    assert result["total"] == 22

def test_verdict_declares_winner(judge):
    rounds = [
        {
            "pro_score": {"total": 25},
            "against_score": {"total": 20}
        }
    ]
    result = judge.verdict("AI regulation", rounds, rounds)
    assert result["winner"] == "PRO"
    assert result["pro_total"] == 25
    assert result["against_total"] == 20
    assert result["margin"] == 5

def test_verdict_declares_draw(judge):
    rounds = [
        {
            "pro_score": {"total": 22},
            "against_score": {"total": 22}
        }
    ]
    result = judge.verdict("AI regulation", rounds, rounds)
    assert result["winner"] == "DRAW"