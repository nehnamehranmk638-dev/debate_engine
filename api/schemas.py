from pydantic import BaseModel, Field
from typing import List

class DebateRequest(BaseModel):
    topic: str = Field(
    ...,
    min_length=10,
    max_length=300,
    description="The debate topic or proposition",
    json_schema_extra={"example": "Social media does more harm than good"}
)
    num_rounds: int = Field(
        default=2,
        ge=1,
        le=5,
        description="Number of debate rounds (1-5)"
    )

class ScoreDetail(BaseModel):
    factual_grounding: int
    logical_coherence: int
    responsiveness: int
    hallucination_penalty: int
    total: int
    reasoning: str

class RoundResult(BaseModel):
    round: int
    pro_argument: str
    against_argument: str
    pro_sources: List[str]
    against_sources: List[str]
    pro_score: ScoreDetail
    against_score: ScoreDetail

class VerdictResult(BaseModel):
    winner: str
    winner_reason: str
    pro_total: int
    against_total: int
    margin: int
    rounds_played: int

class DebateResponse(BaseModel):
    topic: str
    rounds: List[RoundResult]
    verdict: VerdictResult
    response_time_seconds: float

class ErrorResponse(BaseModel):
    error: str
    detail: str