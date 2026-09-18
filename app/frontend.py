import json
import os
import plotly.graph_objects as go
import requests
import streamlit as st

# --- BACKEND CONFIGURATION ---
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
API_CHAT_URL = f"{BACKEND_URL}/api/v1/chat"

st.set_page_config(
    page_title="Daaruka.Earth — Environmental Intelligence",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- MODERN CHAT APP DESIGN SYSTEM (SCALED UP FONT SIZES) ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        font-size: 18px !important; /* Standard Base Font Size Upgraded */
    }
    
    .stApp {
        background-color: #090d0b;
        color: #e2e8f0;
    }

    /* GLOBAL CHAT & MARKDOWN TEXT SCALING */
    div[data-testid="stMarkdownContainer"] p, 
    div[data-testid="stMarkdownContainer"] li,
    div[data-testid="stMarkdownContainer"] span {
        font-size: 1.18rem !important; /* ~21px for high readability */
        line-height: 1.75 !important;
    }
    
    /* Top Header Bar */
    .top-nav {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.75rem 0rem 1.5rem 0rem;
        border-bottom: 1px solid #14241b;
        margin-bottom: 2rem;
    }
    .brand-logo {
        font-size: 1.6rem;
        font-weight: 700;
        color: #f8fafc;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .brand-logo span {
        color: #10b981;
    }
    .status-badge {
        background-color: #112218;
        border: 1px solid #1c3d2a;
        color: #34d399;
        padding: 0.4rem 1rem;
        border-radius: 9999px;
        font-size: 0.95rem;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .status-dot {
        width: 8px;
        height: 8px;
        background-color: #10b981;
        border-radius: 50%;
    }

    /* Hero Center Section */
    .hero-container {
        max-width: 900px;
        margin: 3rem auto 2rem auto;
        text-align: center;
    }
    .hero-title {
        font-size: 3.6rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        line-height: 1.15;
        background: linear-gradient(180deg, #ffffff 0%, #a7f3d0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .hero-subtitle {
        font-size: 1.3rem;
        color: #cbd5e1;
        font-weight: 400;
        max-width: 750px;
        margin: 0 auto 2.5rem auto;
        line-height: 1.6;
    }

    /* Assistant Header */
    .assistant-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1.2rem;
        color: #34d399;
        font-size: 1.1rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    .assistant-avatar {
        width: 32px;
        height: 32px;
        background-color: #059669;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
        color: #ffffff;
    }

    /* RAG Vector Citation Cards */
    .sources-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #cbd5e1;
        margin: 1.5rem 0 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .source-card {
        background-color: #0a110d;
        border: 1px solid #162a1f;
        border-radius: 10px;
        padding: 0.9rem;
    }
    .source-num {
        display: inline-block;
        background-color: #064e3b;
        color: #a7f3d0;
        font-size: 0.85rem;
        font-weight: 700;
        padding: 0.15rem 0.5rem;
        border-radius: 4px;
        margin-bottom: 0.4rem;
    }
    .source-filename {
        color: #f8fafc;
        font-size: 1rem;
        font-weight: 600;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .source-meta {
        color: #94a3b8;
        font-size: 0.88rem;
        margin-top: 0.3rem;
        line-height: 1.4;
    }

    /* Buttons & Prompt Pills */
    div.stButton > button {
        background-color: #111c17;
        color: #e2e8f0;
        border: 1px solid #1b2e23;
        border-radius: 9999px;
        padding: 0.65rem 1.2rem;
        font-size: 1.05rem;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    div.stButton > button:hover {
        background-color: #10b981;
        color: #000000;
        border-color: #10b981;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- SESSION STATE INITIALIZATION ---
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "environmental_state" not in st.session_state:
    st.session_state.environmental_state = {}
if "vulnerability_scores" not in st.session_state:
    st.session_state.vulnerability_scores = {}

# --- TOP NAV BAR ---
st.markdown(
    """
    <div class="top-nav">
        <div class="brand-logo">🌍 Daaruka<span>.Earth</span></div>
        <div class="status-badge">
            <div class="status-dot"></div> Scientific RAG Engine Active
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- SIDEBAR: EXPORT & SESSION DATA ---
with st.sidebar:
    st.title("⚙️ Control & Export")
    if st.session_state.conversation_id:
        st.caption(f"Session Token: `{st.session_state.conversation_id[:12]}...`")
        if st.button("🔄 Clear Chat", use_container_width=True):
            st.session_state.conversation_id = None
            st.session_state.messages = []
            st.session_state.environmental_state = {}
            st.session_state.vulnerability_scores = {}
            st.rerun()

    state = st.session_state.environmental_state
    if state:
        st.markdown("---")
        st.subheader("📍 Active Site Context")
        soil = state.get("soil", {})
        land = state.get("land", {})
        st.write(f"**Region:** `{state.get('region') or 'Unspecified'}`")
        st.write(f"**SOC:** `{soil.get('organic_carbon_percent') or 'N/A'}%`")
        st.write(f"**pH:** `{soil.get('ph') or 'N/A'}`")
        st.write(f"**Crop:** `{land.get('crop_type') or 'N/A'}`")

        st.markdown("---")
        st.subheader("📥 One-Click Export")
        export_payload = {
            "session_id": st.session_state.conversation_id,
            "environmental_state": st.session_state.environmental_state,
            "vulnerability_scores": st.session_state.vulnerability_scores,
            "messages": st.session_state.messages,
        }
        st.download_button(
            label="Export Assessment Report (JSON)",
            data=json.dumps(export_payload, indent=2),
            file_name=f"daaruka_assessment_{st.session_state.conversation_id[:8] if st.session_state.conversation_id else 'export'}.json",
            mime="application/json",
            use_container_width=True,
        )

# --- HERO LANDING (Shown when empty) ---
preset_query = None
if len(st.session_state.messages) == 0:
    st.markdown(
        """
        <div class="hero-container">
            <div class="hero-title">Understand Earth's<br/>connected systems.</div>
            <div class="hero-subtitle">
                Ask questions about biodiversity, soil, forests, water, climate, and human impact using a scientific knowledge base.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption("Try asking:")
    pill_col1, pill_col2, pill_col3 = st.columns(3)
    if pill_col1.button("How does deforestation affect biodiversity and climate change?", use_container_width=True):
        preset_query = "How does deforestation affect biodiversity and climate change?"
    if pill_col2.button("How does soil biodiversity affect ecosystem functioning?", use_container_width=True):
        preset_query = "How does soil biodiversity affect ecosystem functioning?"
    if pill_col3.button("Assess farm in Pune (0.4% SOC, pH 6.5, low rain)", use_container_width=True):
        preset_query = "My farm near Pune, India has 0.4% soil organic carbon, a pH of 6.5, and grows continuous wheat under low rainfall."

# --- CHAT THREAD DISPLAY ---
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant"):
            st.markdown(
                """
                <div class="assistant-header">
                    <div class="assistant-avatar">🌱</div>
                    DAARUKA.EARTH · Scientific Analysis
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(msg["content"])

            if "sources" in msg and msg["sources"]:
                st.markdown('<div class="sources-title">📚 Sources & Scientific Citations</div>', unsafe_allow_html=True)
                cols = st.columns(len(msg["sources"][:4]))
                for idx, (col, src) in enumerate(zip(cols, msg["sources"][:4]), 1):
                    with col:
                        score = src.get("score", 0.0)
                        score_pct = round((1.0 - min(score, 1.0)) * 100, 1) if isinstance(score, float) else "N/A"
                        st.markdown(
                            f"""
                            <div class="source-card">
                                <span class="source-num">{idx}</span>
                                <div class="source-filename">{src.get('title', 'Research Doc')}</div>
                                <div class="source-meta">
                                    Page {src.get('page', '1')} · Chunk {src.get('chunk_id', '0')}<br/>
                                    Match Score: <b>{score_pct}%</b>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

# --- USER INPUT HANDLING ---
user_input = st.chat_input("Ask Daaruka.Earth a scientific question...")
active_prompt = user_input or preset_query

if active_prompt:
    st.session_state.messages.append({"role": "user", "content": active_prompt})
    with st.chat_message("user"):
        st.markdown(active_prompt)

    payload = {
        "message": active_prompt,
        "conversation_id": st.session_state.conversation_id,
    }

    with st.chat_message("assistant"):
        st.markdown(
            """
            <div class="assistant-header">
                <div class="assistant-avatar">🌱</div>
                DAARUKA.EARTH · Scientific Analysis
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.status("Analyzing scientific knowledge...", expanded=True) as status:
            st.write("Searching the Daaruka.Earth knowledge base and generating an evidence-grounded answer...")
            try:
                res = requests.post(API_CHAT_URL, json=payload, timeout=240)
                res.raise_for_status()
                data = res.json()
                status.update(label="Scientific Analysis Complete", state="complete", expanded=False)

                st.session_state.conversation_id = data["conversation_id"]
                st.session_state.environmental_state = data["environmental_state"]
                st.session_state.vulnerability_scores = data.get("vulnerability_scores", {})

                report = data["response"]
                sources = data.get("sources", [])

                st.markdown(report)

                if sources:
                    st.markdown('<div class="sources-title">📚 Sources & Scientific Citations</div>', unsafe_allow_html=True)
                    source_cols = st.columns(min(len(sources), 4))
                    for idx, (col, src) in enumerate(zip(source_cols, sources[:4]), 1):
                        with col:
                            score = src.get("score", 0.0)
                            score_pct = round((1.0 - min(score, 1.0)) * 100, 1) if isinstance(score, float) else "N/A"
                            st.markdown(
                                f"""
                                <div class="source-card">
                                    <span class="source-num">{idx}</span>
                                    <div class="source-filename">{src.get('title', 'Research Doc')}</div>
                                    <div class="source-meta">
                                        Page {src.get('page', '1')} · Chunk {src.get('chunk_id', '0')}<br/>
                                        Match Score: <b>{score_pct}%</b>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": report,
                    "sources": sources,
                })

                if data["intent_type"] == "assessment":
                    st.markdown("---")
                    st.subheader("🧪 Interactive 'What-If' Scenario Simulator")
                    st.caption("Adjust management sliders to dynamically model soil organic carbon and water infiltration trajectory.")

                    s_col1, s_col2, s_col3 = st.columns(3)
                    with s_col1:
                        biochar = st.slider("Biochar Addition (t/ha)", 0.0, 10.0, 2.0, 0.5)
                    with s_col2:
                        cover_crop = st.slider("Cover Crop Area (%)", 0, 100, 50, 5)
                    with s_col3:
                        tillage_red = st.slider("Tillage Reduction (%)", 0, 100, 75, 5)

                    curr_soc = data["environmental_state"]["soil"].get("organic_carbon_percent") or 0.4
                    proj_soc_1y = curr_soc + (biochar * 0.08) + (cover_crop * 0.004) + (tillage_red * 0.002)
                    proj_soc_3y = curr_soc + (biochar * 0.18) + (cover_crop * 0.012) + (tillage_red * 0.006)

                    mc1, mc2, mc3 = st.columns(3)
                    mc1.metric("Current SOC", f"{curr_soc:.2f}%")
                    mc2.metric("1-Yr Projected SOC", f"{proj_soc_1y:.2f}%", f"+{proj_soc_1y - curr_soc:.2f}%")
                    mc3.metric("3-Yr Target SOC", f"{proj_soc_3y:.2f}%", f"+{proj_soc_3y - curr_soc:.2f}%")

                    st.markdown("---")
                    st.subheader("📊 Baseline vs. 3-Year Target Comparison")

                    graph_l, graph_r = st.columns(2)

                    with graph_l:
                        st.markdown("##### 5-Axis Ecological Recovery Radar")
                        categories = ["SOC Index", "pH Stability", "Water Infiltration", "Biodiversity", "Erosion Guard"]
                        base_radar = [min(curr_soc * 25, 100), 50, 30, 25, 35]
                        y3_radar = [min(proj_soc_3y * 25, 100), 80, 85, 75, 85]

                        fig_radar = go.Figure()
                        fig_radar.add_trace(go.Scatterpolar(
                            r=base_radar + [base_radar[0]],
                            theta=categories + [categories[0]],
                            fill='toself', name='Baseline', line_color='#ef4444'
                        ))
                        fig_radar.add_trace(go.Scatterpolar(
                            r=y3_radar + [y3_radar[0]],
                            theta=categories + [categories[0]],
                            fill='toself', name='3-Yr Target', line_color='#10b981'
                        ))
                        fig_radar.update_layout(
                            polar=dict(radialaxis=dict(visible=True, range=[0, 100], gridcolor="#1b2e23"), bgcolor="#09110d"),
                            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            font=dict(color="#e2e8f0", size=14), height=320, margin=dict(l=20, r=20, t=20, b=20)
                        )
                        st.plotly_chart(fig_radar, use_container_width=True)

                    with graph_r:
                        st.markdown("##### Temporal Recovery Path")
                        timeline = ["Baseline", "Year 1", "Year 2", "Year 3"]
                        soc_path = [curr_soc, proj_soc_1y, (proj_soc_1y + proj_soc_3y)/2, proj_soc_3y]

                        fig_line = go.Figure()
                        fig_line.add_trace(go.Scatter(
                            x=timeline, y=soc_path, name="SOC (%)", line=dict(color="#10b981", width=3)
                        ))
                        fig_line.update_layout(
                            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            font=dict(color="#e2e8f0", size=14), xaxis=dict(gridcolor="#1b2e23"), yaxis=dict(title="SOC %", gridcolor="#1b2e23"),
                            height=320, margin=dict(l=20, r=20, t=20, b=20)
                        )
                        st.plotly_chart(fig_line, use_container_width=True)

            except requests.exceptions.ReadTimeout:
                status.update(label="Backend Timeout", state="error")
                st.error("⏳ Request timed out (>240s). Ensure `ollama` is active.")
            except Exception as e:
                status.update(label="Connection Error", state="error")
                st.error(f"Failed to communicate with API engine: {e}")