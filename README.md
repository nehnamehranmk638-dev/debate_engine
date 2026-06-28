# 🧠 ArguMind

### *A Multi-Agent RAG Debate Engine*

A multi-agent AI system where two LLM agents argue opposing sides of any topic, each grounded in real-time web evidence. A judge agent scores every argument for factual grounding and penalizes hallucinations.

## 🌐 Live Demo

|             | Link                                                                       |
| ----------- | -------------------------------------------------------------------------- |
| Frontend    | [Streamlit App](https://your-streamlit-url.streamlit.app)                  |
| Backend API | [debate-engine-hgz1.onrender.com](https://debate-engine-hgz1.onrender.com) |
| API Docs    | [/docs](https://debate-engine-hgz1.onrender.com/docs)                      |

> **Note:** Backend may take 30–50 seconds on first request due to Render free tier cold start. Subsequent requests are fast.

---

## 🧠 What It Does

1. User provides any debate topic
2. Tavily API searches the web for real PRO and AGAINST evidence
3. Evidence is cleaned, chunked, embedded, and stored in two separate FAISS vector stores
4. PRO agent retrieves from PRO store → generates a grounded argument
5. AGAINST agent retrieves from AGAINST store → generates a grounded argument
6. Judge agent scores every argument on factual grounding, logical coherence, and responsiveness — and applies a hallucination penalty for unsupported claims
7. Winner declared based on cumulative scores across all rounds

---

## 🏗️ Architecture

User provides topic

↓

Tavily API searches web for PRO + AGAINST evidence

↓

Evidence cleaned → chunked (500 chars) → embedded → 2 FAISS stores

↓

PRO Agent → retrieves from PRO store → generates argument

AGAINST Agent → retrieves from AGAINST store → generates argument

↓

Judge Agent scores each argument per round

Hallucination penalty applied for unsupported claims

↓

Winner declared based on cumulative scores

---

## 🛠️ Tech Stack

| Layer               | Technology                            |
| ------------------- | ------------------------------------- |
| LLM                 | DeepSeek Chat via OpenRouter          |
| Embeddings          | text-embedding-ada-002 via OpenRouter |
| Vector Store        | FAISS (built dynamically per request) |
| Retrieval Framework | LangChain                             |
| Web Search          | Tavily API                            |
| API                 | FastAPI + Pydantic                    |
| Frontend            | Streamlit                             |
| Backend Deployment  | Render                                |
| Frontend Deployment | Streamlit Cloud                       |

---

## 📊 Metrics

| Metric                  | Value                                  |
| ----------------------- | -------------------------------------- |
| Average response time   | ~30 seconds per debate                 |
| Test coverage           | 19/19 tests passing                    |
| Judge score range       | 19–27 / 30 per round                   |
| Hallucination detection | Penalizes unsupported claims per round |
| Topics supported        | Any topic — fully dynamic              |

---

## 🚀 How to Run Locally

**1. Clone the repo**

```bash
git clone https://github.com/nehnamehranmk638-dev/debate_engine.git
cd debate_engine
```

**2. Create and activate virtual environment**

```bash
python -m venv venv

# Mac/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Create `.env` file in the root**

```env
OPENROUTER_API_KEY=your-openrouter-key

OPENROUTER_MODEL=deepseek/deepseek-chat

TAVILY_API_KEY=your-tavily-key
```

Get your keys from:

* OpenRouter: https://openrouter.ai
* Tavily: https://tavily.com

**5. Run the backend**

```bash
uvicorn api.main:app --reload
```

**6. Run the frontend (new terminal)**

```bash
streamlit run frontend/app.py
```

**7. Open the app**

```
http://localhost:8501
```

---

## 📡 API Reference

### `POST /debate`

Run a full debate on any topic.

**Request:**

```json
{
  "topic": "Social media does more harm than good",
  "num_rounds": 2
}
```

**Response:**

```json
{
  "topic": "Social media does more harm than good",
  "rounds": [
    {
      "round": 1,
      "pro_argument": "...",
      "against_argument": "...",
      "pro_sources": ["source1", "source2"],
      "against_sources": ["source1", "source2"],
      "pro_score": {
        "factual_grounding": 7,
        "logical_coherence": 8,
        "responsiveness": 9,
        "hallucination_penalty": 0,
        "total": 24,
        "reasoning": "..."
      },
      "against_score": { ... }
    }
  ],
  "verdict": {
    "winner": "PRO",
    "winner_reason": "PRO side presented better grounded arguments",
    "pro_total": 24,
    "against_total": 19,
    "margin": 5,
    "rounds_played": 1
  },
  "response_time_seconds": 30.86
}
```

### `GET /health`

Returns server status.

### `GET /docs`

Interactive API documentation (Swagger UI).

---

## 🗂️ Project Structure

```
debate-engine/

├── agents/
│   ├── debater.py          # PRO and AGAINST agent logic
│   └── judge.py            # Judge agent with hallucination detection

├── retrieval/
│   └── vector_store.py     # Tavily web search + FAISS store builder

├── api/
│   ├── main.py             # FastAPI app + CORS
│   ├── routes.py           # API endpoints
│   └── schemas.py          # Pydantic request/response models

├── frontend/
│   ├── app.py              # Streamlit UI
│   └── requirements.txt    # Frontend dependencies

├── tests/
│   ├── test_api.py         # API endpoint tests
│   ├── test_judge.py       # Judge scoring tests
│   └── test_retrieval.py   # Retrieval layer tests

├── conftest.py             # pytest path configuration

├── render.yaml             # Render deployment config

├── Procfile                # Process file

├── runtime.txt             # Python version

└── requirements.txt        # Backend dependencies
```

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

Expected output:

```
19 passed in ~50s
```

---

## 🔮 Future Improvements

* Cache FAISS stores by topic to reduce response time
* Add streaming responses so arguments appear as they generate
* Support 3+ debate positions beyond PRO/AGAINST
* Add debate history storage with PostgreSQL
* Add user authentication and saved debates
* CI/CD pipeline with GitHub Actions

---

## 👤 Author

Built by **Nehna Mehran**
