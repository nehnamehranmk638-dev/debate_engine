from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router

app = FastAPI(
    title="RAG Debate Engine",
    description="""
    A multi-agent debate system where two LLM agents argue opposing sides
    of any topic, each grounded by real web evidence retrieved via Tavily.
    A judge agent scores arguments for factual grounding and penalizes hallucinations.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - allows frontend to call this API later
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include all routes
app.include_router(router)