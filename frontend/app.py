import streamlit as st
import requests
import time
import os

# ── page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="RAG Debate Engine",
    page_icon="⚖️",
    layout="wide"
)

# ── backend URL ───────────────────────────────────────────────
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# ── custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        text-align: center;
        color: #888;
        margin-bottom: 2rem;
        font-size: 1rem;
    }
    .pro-card {
        background: linear-gradient(135deg, #1a3a5c, #1e5799);
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        color: white;
        margin-bottom: 1rem;
    }
    .against-card {
        background: linear-gradient(135deg, #5c1a1a, #991e1e);
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        color: white;
        margin-bottom: 1rem;
    }
    .score-box {
        background: #1e1e2e;
        border-radius: 10px;
        padding: 1rem;
        margin-top: 0.8rem;
    }
    .winner-banner {
        text-align: center;
        font-size: 2rem;
        font-weight: 700;
        padding: 1.5rem;
        border-radius: 16px;
        margin: 1.5rem 0;
    }
    .winner-pro {
        background: linear-gradient(135deg, #1a3a5c, #1e5799);
        color: white;
    }
    .winner-against {
        background: linear-gradient(135deg, #5c1a1a, #991e1e);
        color: white;
    }
    .winner-draw {
        background: linear-gradient(135deg, #2d2d2d, #4a4a4a);
        color: white;
    }
    .round-header {
        font-size: 1.3rem;
        font-weight: 600;
        margin: 1.5rem 0 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #333;
    }
    .source-tag {
        display: inline-block;
        background: rgba(255,255,255,0.15);
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 0.75rem;
        margin: 2px;
    }
    .metric-row {
        display: flex;
        justify-content: space-between;
        margin: 4px 0;
        font-size: 0.9rem;
    }
    .hallucination-warn {
        background: #ff4444;
        color: white;
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 0.8rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# ── helper functions ───────────────────────────────────────────

def render_score_card(score: dict, stance: str):
    """render a score card for one side"""
    color = "#4a9eff" if stance == "PRO" else "#ff6b6b"

    hal_penalty = score.get("hallucination_penalty", 0)
    hal_html = ""
    if hal_penalty > 0:
        hal_html = f'<span class="hallucination-warn">⚠ Hallucination -{hal_penalty}</span>'

    st.markdown(f"""
    <div class="score-box">
        <div class="metric-row">
            <span>📊 Factual Grounding</span>
            <span style="color:{color};font-weight:600">
                {score['factual_grounding']}/10
            </span>
        </div>
        <div class="metric-row">
            <span>🧠 Logical Coherence</span>
            <span style="color:{color};font-weight:600">
                {score['logical_coherence']}/10
            </span>
        </div>
        <div class="metric-row">
            <span>🎯 Responsiveness</span>
            <span style="color:{color};font-weight:600">
                {score['responsiveness']}/10
            </span>
        </div>
        <div class="metric-row">
            <span>Total Score</span>
            <span style="color:{color};font-weight:700;font-size:1.1rem">
                {score['total']}/30 {hal_html}
            </span>
        </div>
        <div style="margin-top:8px;font-size:0.82rem;color:#aaa;
                    font-style:italic;border-top:1px solid #333;
                    padding-top:8px;">
            Judge: {score['reasoning']}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_sources(sources: list):
    """render source tags"""
    if not sources:
        return
    tags = "".join([
        f'<span class="source-tag">📎 {s[:50]}{"..." if len(s)>50 else ""}</span>'
        for s in sources
    ])
    st.markdown(f'<div style="margin-top:8px">{tags}</div>',
                unsafe_allow_html=True)


def render_round(round_data: dict):
    """render one full debate round"""
    round_num = round_data["round"]

    st.markdown(
        f'<div class="round-header">⚔️ Round {round_num}</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        <div class="pro-card">
            <div style="font-size:0.8rem;opacity:0.8;
                        margin-bottom:6px;font-weight:600">
                ✅ PRO SIDE
            </div>
            <div style="line-height:1.6;font-size:0.95rem">
                {round_data['pro_argument']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        render_sources(round_data["pro_sources"])
        render_score_card(round_data["pro_score"], "PRO")

    with col2:
        st.markdown(f"""
        <div class="against-card">
            <div style="font-size:0.8rem;opacity:0.8;
                        margin-bottom:6px;font-weight:600">
                ❌ AGAINST SIDE
            </div>
            <div style="line-height:1.6;font-size:0.95rem">
                {round_data['against_argument']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        render_sources(round_data["against_sources"])
        render_score_card(round_data["against_score"], "AGAINST")


def render_verdict(verdict: dict, response_time: float):
    """render the final winner banner"""
    winner = verdict["winner"]

    if winner == "PRO":
        css_class = "winner-pro"
        emoji = "🏆"
        text = "PRO SIDE WINS"
    elif winner == "AGAINST":
        css_class = "winner-against"
        emoji = "🏆"
        text = "AGAINST SIDE WINS"
    else:
        css_class = "winner-draw"
        emoji = "🤝"
        text = "IT'S A DRAW"

    st.markdown(f"""
    <div class="winner-banner {css_class}">
        {emoji} {text} {emoji}
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("PRO Total", f"{verdict['pro_total']} pts")
    col2.metric("AGAINST Total", f"{verdict['against_total']} pts")
    col3.metric("Margin", f"{verdict['margin']} pts")
    col4.metric("Response Time", f"{response_time}s")

    st.info(f"**Judge's reason:** {verdict['winner_reason']}")


def call_debate_api(topic: str, num_rounds: int) -> dict:
    """call the FastAPI backend"""
    response = requests.post(
        f"{BACKEND_URL}/debate",
        json={"topic": topic, "num_rounds": num_rounds},
        timeout=300  # 5 min timeout for longer debates
    )
    response.raise_for_status()
    return response.json()


def check_backend_health() -> bool:
    """check if backend is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


# ── main app ──────────────────────────────────────────────────

def main():
    # header
    st.markdown(
        '<div class="main-title">⚖️ RAG Debate Engine</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="subtitle">Two AI agents argue any topic using '
        'real web evidence. A judge scores every argument.</div>',
        unsafe_allow_html=True
    )

    # backend health check
    if not check_backend_health():
        st.error(
            "⚠️ Backend is not running. "
            "Start it with: `uvicorn api.main:app --reload`"
        )
        st.stop()


    # divider
    st.divider()

    # input section
    col1, col2 = st.columns([3, 1])

    with col1:
        topic = st.text_input(
            "💬 Debate Topic",
            placeholder="e.g. Social media does more harm than good",
            help="Enter any debate proposition. Be specific for better results."
        )

    with col2:
        num_rounds = st.slider(
            "🔄 Rounds",
            min_value=1,
            max_value=5,
            value=2,
            help="More rounds = deeper debate + longer wait"
        )

    st.divider()

    # debate button
    run_button = st.button(
        "⚔️ Start Debate",
        type="primary",
        use_container_width=True,
        disabled=len(topic.strip()) < 10
    )

    if len(topic.strip()) > 0 and len(topic.strip()) < 10:
        st.warning("Topic must be at least 10 characters.")

    # run debate
    if run_button and topic.strip():
        st.divider()
        st.markdown(f"### 🎯 Debating: *{topic}*")
        st.caption(
            f"Running {num_rounds} round(s). "
            "This takes 20–40 seconds per round while agents search the web..."
        )

        with st.spinner(
            "🔍 Searching web for evidence... "
            "🤖 Agents preparing arguments... "
            "⚖️ Judge getting ready..."
        ):
            try:
                start = time.time()
                data = call_debate_api(topic, num_rounds)
                elapsed = round(time.time() - start, 1)

                # render each round
                for round_data in data["rounds"]:
                    render_round(round_data)
                    st.divider()

                # render verdict
                st.markdown("## 🏁 Final Verdict")
                render_verdict(
                    data["verdict"],
                    data["response_time_seconds"]
                )

            except requests.exceptions.Timeout:
                st.error(
                    "⏱️ Request timed out. "
                    "Try fewer rounds or a simpler topic."
                )
            except requests.exceptions.ConnectionError:
                st.error(
                    "🔌 Cannot connect to backend. "
                    "Make sure `uvicorn api.main:app --reload` is running."
                )
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

    # footer
    st.divider()
    st.markdown(
        '<div style="text-align:center;color:#666;font-size:0.8rem">'
        'Built with FastAPI · LangChain · FAISS · Tavily · DeepSeek · Streamlit'
        '</div>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()