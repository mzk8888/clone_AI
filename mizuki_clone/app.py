"""
Mizuki Neural Interface — Medical Brain Imaging UI
Dark HUD theme, 3D neural network, multi-panel layout.
"""
import os
import numpy as np
from datetime import datetime

import streamlit as st
import plotly.graph_objects as go
import networkx as nx

from brain import SecondBrain, CATEGORIES
from agent import MizukiAgent

# ─────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MIZUKI NEURAL INTERFACE",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────
# CSS — medical imaging dark theme
# ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Base ── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stSidebar"] { display: none !important; }
.block-container { padding: 0.4rem 0.8rem !important; max-width: 100% !important; }
body, .stApp { background-color: #040810 !important; color: #c8d8e8 !important; }

/* ── Scanlines overlay ── */
.stApp::after {
    content: '';
    position: fixed; top:0; left:0; right:0; bottom:0;
    background: repeating-linear-gradient(
        0deg,
        rgba(0,200,120,0.018) 0px, rgba(0,200,120,0.018) 1px,
        transparent 1px, transparent 3px
    );
    pointer-events: none; z-index: 9990;
}

/* ── HUD header ── */
.hud-header {
    background: linear-gradient(90deg, #060c1a 0%, #0a1428 50%, #060c1a 100%);
    border: 1px solid #00cc6644;
    border-radius: 3px;
    padding: 8px 18px;
    font-family: 'Courier New', monospace;
    font-size: 11px;
    letter-spacing: 2px;
    color: #00cc88;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
}
.hud-title { font-size: 15px; font-weight: bold; letter-spacing: 4px; }
.hud-live { color: #ff4444; animation: blink 1.2s step-end infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }

/* ── Panel containers ── */
.panel {
    background: #060c18;
    border: 1px solid #00cc6622;
    border-radius: 3px;
    padding: 8px;
    margin-bottom: 6px;
}
.panel-label {
    font-family: 'Courier New', monospace;
    font-size: 9px;
    letter-spacing: 3px;
    color: #00cc6666;
    border-bottom: 1px solid #00cc6622;
    padding-bottom: 4px;
    margin-bottom: 6px;
    text-transform: uppercase;
}

/* ── Metric tiles ── */
.metrics-row {
    display: flex; gap: 8px; margin-bottom: 6px;
}
.metric-tile {
    flex: 1;
    background: #060c18;
    border: 1px solid #00cc6633;
    border-radius: 3px;
    padding: 8px 4px;
    text-align: center;
    font-family: 'Courier New', monospace;
}
.metric-val { font-size: 26px; color: #00ff99; font-weight: bold; line-height: 1; }
.metric-lbl { font-size: 9px; color: #44666688; letter-spacing: 2px; margin-top: 2px; }

/* ── Category bars ── */
.cat-row {
    display: flex; align-items: center;
    font-family: 'Courier New', monospace;
    font-size: 10px; margin: 2px 0;
}
.cat-name { width: 70px; color: #8899aa; }
.cat-bar-wrap { flex:1; background:#0a1020; height:10px; border-radius:2px; overflow:hidden; margin:0 6px; }
.cat-bar-fill { height:100%; border-radius:2px; transition: width 0.6s; }
.cat-cnt { color: #334455; width: 24px; text-align: right; }

/* ── Chat terminal ── */
.chat-wrap {
    background: #030609;
    border: 1px solid #00cc6633;
    border-radius: 3px;
    height: 310px;
    overflow-y: auto;
    padding: 10px 12px;
    font-family: 'Courier New', monospace;
    font-size: 12px;
    scroll-behavior: smooth;
}
.chat-msg-user {
    color: #44aaff;
    margin: 5px 0 1px;
    padding-left: 12px;
    border-left: 2px solid #44aaff;
}
.chat-msg-bot {
    color: #00ff99;
    margin: 1px 0 8px;
    padding-left: 12px;
    border-left: 2px solid #00cc66;
    white-space: pre-wrap;
}
.chat-ts { color: #223344; font-size: 9px; margin-bottom: 1px; }
.chat-prompt {
    color: #00cc88;
    font-family: 'Courier New', monospace;
    font-size: 11px;
    margin-top: 4px;
}

/* ── Input ── */
.stTextInput > div > div > input {
    background: #030609 !important;
    color: #00ff99 !important;
    border: 1px solid #00cc6633 !important;
    border-radius: 3px !important;
    font-family: 'Courier New', monospace !important;
    font-size: 13px !important;
    caret-color: #00ff99 !important;
}
.stTextInput label { display: none !important; }

/* ── Buttons ── */
.stButton > button {
    background: #060c18 !important;
    color: #00cc88 !important;
    border: 1px solid #00cc6633 !important;
    border-radius: 3px !important;
    font-family: 'Courier New', monospace !important;
    font-size: 11px !important;
    letter-spacing: 1px !important;
    padding: 4px 10px !important;
}
.stButton > button:hover {
    border-color: #00ff99 !important;
    color: #00ff99 !important;
    box-shadow: 0 0 8px #00ff9933 !important;
}

/* ── Data table ── */
.data-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'Courier New', monospace;
    font-size: 10px;
}
.data-table th {
    color: #00cc6688;
    letter-spacing: 2px;
    padding: 3px 6px;
    border-bottom: 1px solid #00cc6622;
    text-align: left;
    font-weight: normal;
}
.data-table td {
    padding: 2px 6px;
    color: #8899aa;
    border-bottom: 1px solid #0a1020;
}
.data-table tr:hover td { background: #0a1428; color: #ccddee; }

/* ── Select / API input ── */
.stSelectbox label, .stTextInput label { color: #00cc6688 !important; font-family: 'Courier New', monospace !important; font-size: 10px !important; letter-spacing: 2px !important; }
div[data-baseweb="select"] { background: #060c18 !important; border-color: #00cc6633 !important; }

/* ── Remove extra margins ── */
.element-container { margin: 0 !important; }
div[data-testid="stVerticalBlock"] > div { gap: 4px !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────────────────────────────
def _init():
    if "brain" not in st.session_state:
        st.session_state.brain = SecondBrain()
    if "history" not in st.session_state:
        st.session_state.history = []
    if "agent" not in st.session_state:
        st.session_state.agent = None
    if "greeted" not in st.session_state:
        st.session_state.greeted = False
    if "api_key" not in st.session_state:
        st.session_state.api_key = os.environ.get("ANTHROPIC_API_KEY", "")

_init()
brain: SecondBrain = st.session_state.brain

# ─────────────────────────────────────────────────────────────────────
# 3D Brain Network figure
# ─────────────────────────────────────────────────────────────────────
COLORS_3D = {
    "技術":     "#ff4488",
    "アイデア": "#44aaff",
    "感情":     "#ff8800",
    "目標":     "#00ffaa",
    "学習":     "#bb44ff",
    "日常":     "#ffee22",
    "人間関係": "#ff5533",
    "その他":   "#558899",
}

def _cat_for(keyword: str) -> str:
    for cat, kws in CATEGORIES.items():
        if any(kw in keyword for kw in kws):
            return cat
    return "その他"

def make_brain_3d(brain: SecondBrain) -> go.Figure:
    top = brain.top_concepts(45)
    traces: list = []

    # ── Brain surface (wrinkled ellipsoid) ──────────────────────────
    u = np.linspace(0, 2 * np.pi, 70)
    v = np.linspace(0, np.pi, 45)
    U, V = np.meshgrid(u, v)
    Xs = 1.25 * np.sin(V) * np.cos(U)
    Ys = 0.98 * np.sin(V) * np.sin(U)
    Zs = 0.88 * np.cos(V)
    wrinkle = (0.055 * np.sin(8 * U) * np.sin(5 * V) +
               0.035 * np.sin(14 * U + 1.4) * np.sin(9 * V + 0.7) +
               0.025 * np.cos(6 * U - 1.2) * np.cos(11 * V + 2.1))
    R = np.sqrt(Xs**2 + Ys**2 + Zs**2) + 1e-9
    Xs += wrinkle * Xs / R
    Ys += wrinkle * Ys / R
    Zs += wrinkle * Zs / R

    traces.append(go.Surface(
        x=Xs, y=Ys, z=Zs,
        opacity=0.07,
        colorscale=[[0, "#001122"], [0.5, "#002244"], [1, "#003366"]],
        showscale=False, hoverinfo="skip", name="",
    ))

    if not top:
        fig = go.Figure(data=traces)
        fig.update_layout(**_3d_layout())
        return fig

    # ── Fibonacci node positions on surface ──────────────────────────
    n = len(top)
    phi_gold = np.pi * (3 - np.sqrt(5))
    positions = {}
    for i, (k, _) in enumerate(top):
        t = i / max(n - 1, 1)
        y = 1 - t * 2
        r = np.sqrt(max(0.0, 1 - y * y))
        th = phi_gold * i
        positions[k] = (
            r * np.cos(th) * 1.22,
            y * 0.95,
            r * np.sin(th) * 0.85,
        )

    # ── Connection lines ─────────────────────────────────────────────
    ex, ey, ez, lw = [], [], [], []
    seen: set = set()
    for k, v in top:
        for conn, w in v["connections"].items():
            if conn in positions and w >= 1:
                key = tuple(sorted([k, conn]))
                if key not in seen:
                    p1, p2 = positions[k], positions[conn]
                    ex += [p1[0], p2[0], None]
                    ey += [p1[1], p2[1], None]
                    ez += [p1[2], p2[2], None]
                    seen.add(key)
    if ex:
        traces.append(go.Scatter3d(
            x=ex, y=ey, z=ez, mode="lines",
            line=dict(color="rgba(0,200,100,0.12)", width=1.5),
            hoverinfo="skip", showlegend=False,
        ))

    # ── Nodes by category ────────────────────────────────────────────
    by_cat: dict = {}
    for k, v in top:
        cat = _cat_for(k)
        if cat not in by_cat:
            by_cat[cat] = {"x": [], "y": [], "z": [], "text": [], "size": [], "hover": []}
        px, py, pz = positions[k]
        by_cat[cat]["x"].append(px)
        by_cat[cat]["y"].append(py)
        by_cat[cat]["z"].append(pz)
        by_cat[cat]["text"].append(k)
        by_cat[cat]["size"].append(max(4, min(22, v["weight"] * 4)))
        by_cat[cat]["hover"].append(f"{k}  ×{v['weight']}")

    for cat, vals in by_cat.items():
        col = COLORS_3D.get(cat, "#558899")
        traces.append(go.Scatter3d(
            x=vals["x"], y=vals["y"], z=vals["z"],
            mode="markers+text",
            name=cat,
            text=vals["text"],
            textfont=dict(size=7, color=col),
            textposition="top center",
            customdata=vals["hover"],
            hovertemplate="%{customdata}<extra></extra>",
            marker=dict(
                size=vals["size"], color=col, opacity=0.88,
                line=dict(width=0.5, color="rgba(255,255,255,0.3)"),
            ),
        ))

    fig = go.Figure(data=traces)
    fig.update_layout(**_3d_layout())
    return fig


def _3d_layout() -> dict:
    ax = dict(showgrid=False, zeroline=False, showticklabels=False,
              showspikes=False, backgroundcolor="#040810")
    return dict(
        paper_bgcolor="#040810",
        scene=dict(bgcolor="#040810", xaxis=ax, yaxis=ax, zaxis=ax),
        margin=dict(l=0, r=0, t=0, b=0),
        height=430,
        showlegend=True,
        legend=dict(
            font=dict(color="#00ff99", size=9, family="Courier New"),
            bgcolor="rgba(4,8,16,0.85)",
            bordercolor="rgba(0,200,100,0.2)",
            borderwidth=1,
            x=0.01, y=0.99,
        ),
        uirevision="brain",
    )


# ─────────────────────────────────────────────────────────────────────
# 2D Concept Map
# ─────────────────────────────────────────────────────────────────────
def make_concept_2d(brain: SecondBrain) -> go.Figure:
    data = brain.brain_map_data(30)
    nodes, edges = data["nodes"], data["edges"]

    if not nodes:
        fig = go.Figure()
        fig.update_layout(
            paper_bgcolor="#040810", plot_bgcolor="#040810",
            height=200, margin=dict(l=0,r=0,t=0,b=0),
            annotations=[dict(text="NO DATA — START CHATTING",
                              x=0.5, y=0.5, showarrow=False,
                              font=dict(color="#00cc6644", size=14, family="Courier New"))],
        )
        return fig

    G = nx.Graph()
    for n in nodes:
        G.add_node(n["id"])
    for e in edges:
        G.add_edge(e["source"], e["target"])
    pos = nx.spring_layout(G, k=2.8, seed=42)

    ex, ey = [], []
    for e in edges:
        if e["source"] in pos and e["target"] in pos:
            x0, y0 = pos[e["source"]]
            x1, y1 = pos[e["target"]]
            ex += [x0, x1, None]; ey += [y0, y1, None]

    traces = [go.Scatter(
        x=ex, y=ey, mode="lines",
        line=dict(color="rgba(0,180,80,0.15)", width=0.8),
        hoverinfo="skip", showlegend=False,
    )]

    by_cat: dict = {}
    for n in nodes:
        cat = n["category"]
        if cat not in by_cat:
            by_cat[cat] = {"x":[], "y":[], "text":[], "size":[]}
        x, y = pos[n["id"]]
        by_cat[cat]["x"].append(x); by_cat[cat]["y"].append(y)
        by_cat[cat]["text"].append(n["id"])
        by_cat[cat]["size"].append(max(6, min(22, n["weight"] * 4)))

    for cat, v in by_cat.items():
        col = COLORS_3D.get(cat, "#558899")
        traces.append(go.Scatter(
            x=v["x"], y=v["y"], mode="markers+text", name=cat,
            text=v["text"], textposition="top center",
            textfont=dict(size=8, color=col),
            marker=dict(size=v["size"], color=col, opacity=0.85,
                        line=dict(width=0.5, color="rgba(255,255,255,0.2)")),
        ))

    fig = go.Figure(data=traces)
    fig.update_layout(
        paper_bgcolor="#040810", plot_bgcolor="#060c18",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        showlegend=False, height=200,
        margin=dict(l=4, r=4, t=4, b=4),
    )
    return fig


# ─────────────────────────────────────────────────────────────────────
# Helper: render chat history HTML
# ─────────────────────────────────────────────────────────────────────
def render_chat_html(history: list) -> str:
    if not history:
        return (
            "<div style='color:#223344;font-size:11px;font-family:Courier New;padding:20px;text-align:center;'>"
            "[ NEURAL LINK READY ]<br>API KEY を入力して会話を開始してください"
            "</div>"
        )
    parts = []
    for role, text, ts in history:
        if role == "user":
            parts.append(
                f"<div class='chat-ts'>{ts}  USER</div>"
                f"<div class='chat-msg-user'>&gt; {text}</div>"
            )
        else:
            safe = text.replace("<", "&lt;").replace(">", "&gt;")
            parts.append(
                f"<div class='chat-ts'>{ts}  NEURAL-AI</div>"
                f"<div class='chat-msg-bot'>{safe}</div>"
            )
    return "\n".join(parts)


# ─────────────────────────────────────────────────────────────────────
# Build agent when key is set
# ─────────────────────────────────────────────────────────────────────
def ensure_agent(key: str):
    if key and (st.session_state.agent is None or
                getattr(st.session_state.agent, "_key", "") != key):
        st.session_state.agent = MizukiAgent(api_key=key, brain=brain)
        st.session_state.agent._key = key

# Auto-greet once
def maybe_greet():
    if not st.session_state.greeted and st.session_state.agent:
        g = st.session_state.agent.greeting()
        st.session_state.history.append(
            ("bot", g, datetime.now().strftime("%H:%M:%S"))
        )
        st.session_state.greeted = True

# ─────────────────────────────────────────────────────────────────────
# ── LAYOUT ───────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────
now = datetime.now()

# ── HUD Header ───────────────────────────────────────────────────────
stats = brain.stats()
st.markdown(f"""
<div class='hud-header'>
  <span class='hud-title'>◈ MIZUKI NEURAL INTERFACE</span>
  <span>{now.strftime('%Y/%m/%d  %H:%M:%S')}</span>
  <span>MEM:{stats['memories']:04d} | CONCEPT:{stats['concepts']:04d}</span>
  <span class='hud-live'>● LIVE</span>
</div>
""", unsafe_allow_html=True)

# ── Top row: Metric tiles ─────────────────────────────────────────────
cats = brain.category_counts()
dominant = max(cats, key=cats.get) if cats else "---"
top5 = brain.top_concepts(1)
top_word = top5[0][0] if top5 else "---"

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f"<div class='metric-tile'><div class='metric-val'>{stats['memories']:04d}</div><div class='metric-lbl'>MEMORIES</div></div>", unsafe_allow_html=True)
with m2:
    st.markdown(f"<div class='metric-tile'><div class='metric-val'>{stats['concepts']:04d}</div><div class='metric-lbl'>CONCEPTS</div></div>", unsafe_allow_html=True)
with m3:
    st.markdown(f"<div class='metric-tile'><div class='metric-val' style='font-size:16px;padding-top:6px'>{dominant}</div><div class='metric-lbl'>DOMINANT ZONE</div></div>", unsafe_allow_html=True)
with m4:
    st.markdown(f"<div class='metric-tile'><div class='metric-val' style='font-size:16px;padding-top:6px'>{top_word}</div><div class='metric-lbl'>TOP CONCEPT</div></div>", unsafe_allow_html=True)

# ── Main row ──────────────────────────────────────────────────────────
col_brain, col_right = st.columns([6, 4])

with col_brain:
    # ── 3D Brain ──
    st.markdown("<div class='panel-label'>◈ 3D NEURAL NETWORK</div>", unsafe_allow_html=True)
    fig3d = make_brain_3d(brain)
    st.plotly_chart(fig3d, use_container_width=True, config={"displayModeBar": False})

    # ── 2D Concept map ──
    st.markdown("<div class='panel-label'>◈ CONCEPT MAP  [ AXIAL VIEW ]</div>", unsafe_allow_html=True)
    fig2d = make_concept_2d(brain)
    st.plotly_chart(fig2d, use_container_width=True, config={"displayModeBar": False})

with col_right:
    # ── API Key ──
    api_key = st.text_input("API KEY", value=st.session_state.api_key,
                             type="password", placeholder="sk-ant-...")
    st.session_state.api_key = api_key
    ensure_agent(api_key)
    maybe_greet()

    # ── Chat terminal ──
    st.markdown("<div class='panel-label'>◈ NEURAL CHAT TERMINAL</div>", unsafe_allow_html=True)
    chat_html = render_chat_html(st.session_state.history)
    st.markdown(
        f"<div class='chat-wrap' id='chat-end'>{chat_html}"
        "<script>var el=document.getElementById('chat-end');if(el)el.scrollTop=el.scrollHeight;</script>"
        "</div>",
        unsafe_allow_html=True,
    )

    # Input row
    inp_col, btn_col = st.columns([5, 1])
    with inp_col:
        user_input = st.text_input("msg", label_visibility="collapsed",
                                   placeholder="> INPUT NEURAL SIGNAL...")
    with btn_col:
        send = st.button("SEND", use_container_width=True)

    if (send or user_input) and user_input.strip():
        if not st.session_state.agent:
            st.warning("API KEY を入力してください")
        else:
            msg = user_input.strip()
            ts = now.strftime("%H:%M:%S")
            st.session_state.history.append(("user", msg, ts))
            with st.spinner(""):
                reply = st.session_state.agent.chat(msg)
            st.session_state.history.append(
                ("bot", reply, datetime.now().strftime("%H:%M:%S"))
            )
            st.rerun()

    # ── Action buttons ──
    a1, a2, a3 = st.columns(3)
    with a1:
        if st.button("GREET", use_container_width=True):
            if st.session_state.agent:
                g = st.session_state.agent.greeting()
                st.session_state.history.append(("bot", g, now.strftime("%H:%M:%S")))
                st.rerun()
    with a2:
        if st.button("ANALYZE", use_container_width=True):
            if st.session_state.agent:
                with st.spinner(""):
                    a = st.session_state.agent.analyze_brain()
                st.session_state.history.append(("bot", a, now.strftime("%H:%M:%S")))
                st.rerun()
    with a3:
        if st.button("CLEAR", use_container_width=True):
            st.session_state.history = []
            if st.session_state.agent:
                st.session_state.agent.history = []
            st.session_state.greeted = False
            st.rerun()

    # ── Region data table ──
    st.markdown("<div class='panel-label' style='margin-top:8px'>◈ NEURAL REGION DATA</div>", unsafe_allow_html=True)

    top_list = brain.top_concepts(16)
    max_w = top_list[0][1]["weight"] if top_list else 1

    rows = ""
    for k, v in top_list:
        cat = _cat_for(k)
        col = COLORS_3D.get(cat, "#558899")
        pct = int(v["weight"] / max(max_w, 1) * 100)
        rows += (
            f"<tr>"
            f"<td style='color:{col}'>{k}</td>"
            f"<td>{cat}</td>"
            f"<td><div style='width:{pct}%;height:6px;background:{col};border-radius:2px;opacity:0.7'></div></td>"
            f"<td style='text-align:right;color:#00ff99'>{v['weight']}</td>"
            f"</tr>"
        )

    st.markdown(
        f"<table class='data-table'>"
        f"<tr><th>CONCEPT</th><th>REGION</th><th>ACTIVITY</th><th>Hz</th></tr>"
        f"{rows}"
        f"</table>",
        unsafe_allow_html=True,
    )

    # ── Category activity bars ──
    st.markdown("<div class='panel-label' style='margin-top:8px'>◈ REGION ACTIVITY</div>", unsafe_allow_html=True)
    max_cat = max(cats.values()) if cats else 1
    bars_html = ""
    for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
        col = COLORS_3D.get(cat, "#558899")
        pct = int(count / max_cat * 100)
        bars_html += (
            f"<div class='cat-row'>"
            f"<span class='cat-name'>{cat}</span>"
            f"<div class='cat-bar-wrap'><div class='cat-bar-fill' style='width:{pct}%;background:{col};'></div></div>"
            f"<span class='cat-cnt'>{count}</span>"
            f"</div>"
        )
    if not bars_html:
        bars_html = "<div style='color:#223344;font-size:10px;font-family:Courier New'>NO ACTIVITY DETECTED</div>"
    st.markdown(bars_html, unsafe_allow_html=True)
