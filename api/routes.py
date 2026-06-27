import time
from fastapi import APIRouter, HTTPException, Request
from api.schemas import DebateRequest, DebateResponse, ErrorResponse
from agents.debater import DebaterAgent
from agents.judge import JudgeAgent

router = APIRouter()

@router.post(
    "/debate",
    response_model=DebateResponse,
    summary="Run a full debate on any topic",
    description="""
    Accepts a topic and number of rounds.
    Builds PRO and AGAINST agents grounded in real web evidence.
    Returns full debate transcript with judge scores and winner.
    Expect 20-30 seconds response time due to web search and LLM calls.
    """
)
async def run_debate(req: DebateRequest, request: Request):
    start_time = time.time()

    # validate topic is not empty or whitespace
    if not req.topic.strip():
        raise HTTPException(
            status_code=400,
            detail="Topic cannot be empty or whitespace"
        )

    try:
        # initialize agents fresh for this topic
        # (web search + FAISS build happens here)
        pro_agent = DebaterAgent(stance="PRO", topic=req.topic)
        against_agent = DebaterAgent(stance="AGAINST", topic=req.topic)
        judge = JudgeAgent()

        rounds = []
        prev_pro = ""
        prev_against = ""

        for round_num in range(1, req.num_rounds + 1):
            # agents argue
            pro_result = pro_agent.argue(
                round_num=round_num,
                opponent_arg=prev_against
            )
            against_result = against_agent.argue(
                round_num=round_num,
                opponent_arg=prev_pro
            )

            # judge scores both
            pro_score = judge.evaluate(
                topic=req.topic,
                stance="PRO",
                argument=pro_result["argument"],
                evidence_used=pro_result["evidence_used"],
                opponent_arg=prev_against,
                round_num=round_num
            )
            against_score = judge.evaluate(
                topic=req.topic,
                stance="AGAINST",
                argument=against_result["argument"],
                evidence_used=against_result["evidence_used"],
                opponent_arg=prev_pro,
                round_num=round_num
            )

            rounds.append({
                "round": round_num,
                "pro_argument": pro_result["argument"],
                "against_argument": against_result["argument"],
                "pro_sources": pro_result["sources"],
                "against_sources": against_result["sources"],
                "pro_score": pro_score,
                "against_score": against_score
            })

            prev_pro = pro_result["argument"]
            prev_against = against_result["argument"]

        # final verdict
        verdict = judge.verdict(req.topic, rounds, rounds)
        response_time = round(time.time() - start_time, 2)

        return DebateResponse(
            topic=req.topic,
            rounds=rounds,
            verdict=verdict,
            response_time_seconds=response_time
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Debate engine error: {str(e)}"
        )


@router.get(
    "/health",
    summary="Health check",
    description="Returns ok if the server is running"
)
async def health():
    return {"status": "ok", "message": "Debate engine is running"}


@router.get(
    "/",
    summary="Root",
    description="Welcome message"
)
async def root():
    return {
        "message": "Welcome to the RAG Debate Engine",
        "docs": "/docs",
        "health": "/health",
        "debate": "POST /debate"
    }