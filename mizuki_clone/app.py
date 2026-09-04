"""
Mizuki Neural Interface — Medical Brain Imaging UI
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
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────
# CSS — minimal overrides so Streamlit layout stays intact
# ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Background */
.stApp { background-color: #040810 !important; }
body    { background-color: #040810 !important; }

/* Scanlines */
.stApp::after {
    content:''; position:fixed; inset:0; pointer-events:none; z-index:9990;
    background: repeating-linear-gradient(
        0deg,
        rgba(0,220,110,.016) 0px, rgba(0,220,110,.016) 1px,
        transparent 1px, transparent 3px
    );
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #060c18 !important;
    border-right: 1px solid #00cc6622 !important;
}
[data-testid="stSidebar"] * { color: #8899aa !important; }
[data-testid="stSidebar"] input {
    background: #030609 !important;
    color: #00ff99 !important;
    border: 1px solid #00cc6633 !important;
    font-family: 'Courier New', monospace !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: #060c18 !important;
    color: #00cc88 !important;
    border: 1px solid #00cc6633 !important;
    font-family: 'Courier New', monospace !important;
    font-size: 11px !important;
    letter-spacing: 1px !important;
    border-radius: 2px !important;
    width: 100%;
}
[data-testid="stSidebar"] .stButton > button:hover {
    border-color: #00ff99 !important;
    box-shadow: 0 0 6px #00ff9922 !important;
}

/* Main text */
.stApp, .stMarkdown, p, label { color: #8899aa !important; font-family: 'Courier New', monospace !important; }
h1,h2,h3 { color: #00ff99 !important; font-family: 'Courier New', monospace !important; letter-spacing: 3px !important; }

/* Plotly charts — transparent bg handled in figure layout */

/* Text input in main area */
.stTextInput input {
    background: #030609 !important;
    color: #00ff99 !important;
    border: 1px solid #00cc6633 !important;
    font-family: 'Courier New', monospace !important;
    border-radius: 2px !important;
}
.stTextInput label { color: #00cc6666 !important; font-size: 10px !important; letter-spacing: 2px !important; }

/* Main buttons */
.stButton > button {
    background: #060c18 !important;
    color: #00cc88 !important;
    border: 1px solid #00cc6633 !important;
    font-family: 'Courier New', monospace !important;
    font-size: 11px !important;
    letter-spacing: 1px !important;
    border-radius: 2px !important;
}
.stButton > button:hover {
    border-color: #00ff99 !important;
    box-shadow: 0 0 8px #00ff9922 !important;
}

/* Spinner */
.stSpinner > div { border-top-color: #00ff99 !important; }

/* Info/warning */
.stAlert { background: #060c18 !important; border-color: #00cc6633 !important; color: #8899aa !important; }

/* Remove top padding */
.block-container { padding-top: 0.5rem !important; padding-bottom: 0 !important; }

/* Blink animation */
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
.live-dot { animation: blink 1.2s step-end infinite; }

/* Neon glow for headers */
@keyframes neon { 0%,100%{text-shadow:0 0 4px #00ff99} 50%{text-shadow:0 0 14px #00ff99,0 0 28px #00ff9966} }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────
# Colors
# ─────────────────────────────────────────────────────────────────────
COLORS = {
    "技術":     "#ff4488",
    "アイデア": "#44aaff",
    "感情":     "#ff8800",
    "目標":     "#00ffaa",
    "学習":     "#bb44ff",
    "日常":     "#ffee22",
    "人間関係": "#ff5533",
    "その他":   "#558899",
}

def _cat(k: str) -> str:
    for cat, kws in CATEGORIES.items():
        if any(kw in k for kw in kws):
            return cat
    return "その他"

# ─────────────────────────────────────────────────────────────────────
# Seed data for first run
# ─────────────────────────────────────────────────────────────────────
SEED = [
    "PythonでAIオセロを作った。ミニマックス法とアルファベータ枝刈りで強いAIができた。",
    "Streamlitで脳内マップのUIを作っている。Plotlyの3Dグラフが綺麗に出た。",
    "機械学習とDeep Learningを毎日勉強している。CNNやTransformerが面白い。",
    "アイデアがどんどん浮かぶ。第二の脳を作りたい。記憶を整理したい。",
    "Claude APIを使ってチャットボットを作った。会話の質がすごく高い。",
    "音声ラベリングシステムを開発中。精度をもっと上げたい。",
    "GitHubで色々なAIプロジェクトを管理している。",
    "今日は疲れた。でもコードを書くのが楽しい。",
    "目標は自分専用のAIアシスタントを完成させること。",
    "友達にAIの話をしたらすごく興味を持ってくれた。",
    "ニューラルネットワークの仕組みを深く理解したい。",
    "Pythonのデータ分析が得意になってきた。Pandasもplotlibも使いこなしたい。",
]

def ensure_seed(brain: SecondBrain):
    if brain.stats()["memories"] == 0:
        for s in SEED:
            brain.remember(s, source="seed")

# ─────────────────────────────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────────────────────────────
def _init():
    if "brain" not in st.session_state:
        b = SecondBrain()
        ensure_seed(b)
        st.session_state.brain = b
    if "history" not in st.session_state:
        st.session_state.history = []
    if "agent" not in st.session_state:
        st.session_state.agent = None
    if "greeted" not in st.session_state:
        st.session_state.greeted = False

_init()
brain: SecondBrain = st.session_state.brain

def _ensure_agent(key: str):
    if key and (st.session_state.agent is None or
                getattr(st.session_state.agent, "_key", "") != key):
        st.session_state.agent = MizukiAgent(api_key=key, brain=brain)
        st.session_state.agent._key = key

def _maybe_greet():
    if not st.session_state.greeted and st.session_state.agent:
        g = st.session_state.agent.greeting()
        st.session_state.history.append(("bot", g, datetime.now().strftime("%H:%M")))
        st.session_state.greeted = True

# ─────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ◈ NEURAL LINK")
    api_key = st.text_input(
        "ANTHROPIC API KEY",
        value=os.environ.get("ANTHROPIC_API_KEY", ""),
        type="password",
        placeholder="sk-ant-...",
    )
    _ensure_agent(api_key)
    _maybe_greet()

    st.markdown("---")
    if st.button("☀ GREET"):
        if st.session_state.agent:
            g = st.session_state.agent.greeting()
            st.session_state.history.append(("bot", g, datetime.now().strftime("%H:%M")))
            st.rerun()

    if st.button("⬡ ANALYZE BRAIN"):
        if st.session_state.agent:
            with st.spinner(""):
                a = st.session_state.agent.analyze_brain()
            st.session_state.history.append(("bot", a, datetime.now().strftime("%H:%M")))
            st.rerun()

    if st.button("✕ CLEAR CHAT"):
        st.session_state.history = []
        if st.session_state.agent:
            st.session_state.agent.history = []
        st.session_state.greeted = False
        st.rerun()

    if st.button("⟳ RESET BRAIN"):
        from pathlib import Path
        Path(__file__).parent.joinpath("mizuki_brain.json").unlink(missing_ok=True)
        st.session_state.pop("brain", None)
        st.session_state.pop("greeted", None)
        st.rerun()

    st.markdown("---")
    s = brain.stats()
    cats = brain.category_counts()
    st.markdown(f"**MEM** `{s['memories']:04d}`")
    st.markdown(f"**CONCEPT** `{s['concepts']:04d}`")
    top1 = brain.top_concepts(1)
    if top1:
        st.markdown(f"**TOP** `{top1[0][0]}`")
    st.markdown("---")
    max_c = max(cats.values()) if cats else 1
    for cat, cnt in sorted(cats.items(), key=lambda x: -x[1]):
        col = COLORS.get(cat, "#558899")
        pct = int(cnt / max_c * 100)
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:6px;margin:2px 0;font-size:10px;'>"
            f"<span style='color:{col};width:60px'>{cat}</span>"
            f"<div style='flex:1;height:8px;background:#0a1020;border-radius:2px;'>"
            f"<div style='width:{pct}%;height:100%;background:{col};border-radius:2px;opacity:.8'></div></div>"
            f"<span style='color:#334455;width:18px;text-align:right'>{cnt}</span></div>",
            unsafe_allow_html=True,
        )

# ─────────────────────────────────────────────────────────────────────
# 3D Brain Network
# ─────────────────────────────────────────────────────────────────────
def make_brain_3d(brain: SecondBrain) -> go.Figure:
    top = brain.top_concepts(45)
    traces = []

    # ── Wrinkled brain surface ────────────────────────────────────────
    u = np.linspace(0, 2 * np.pi, 80)
    v = np.linspace(0, np.pi, 50)
    U, V = np.meshgrid(u, v)
    Xs = 1.25 * np.sin(V) * np.cos(U)
    Ys = 0.98 * np.sin(V) * np.sin(U)
    Zs = 0.88 * np.cos(V)
    w = (0.055 * np.sin(8*U) * np.sin(5*V) +
         0.035 * np.sin(14*U + 1.4) * np.sin(9*V + .7) +
         0.025 * np.cos(6*U - 1.2) * np.cos(11*V + 2.1))
    R = np.sqrt(Xs**2 + Ys**2 + Zs**2) + 1e-9
    Xs += w * Xs / R; Ys += w * Ys / R; Zs += w * Zs / R

    traces.append(go.Surface(
        x=Xs, y=Ys, z=Zs, opacity=0.09,
        colorscale=[[0,"#001122"],[.5,"#002244"],[1,"#003366"]],
        showscale=False, hoverinfo="skip",
    ))

    if not top:
        fig = go.Figure(data=traces)
        fig.update_layout(**_layout3d(450))
        return fig

    # ── Fibonacci node positions ──────────────────────────────────────
    n = len(top)
    phi_g = np.pi * (3 - np.sqrt(5))
    pos = {}
    for i, (k, _) in enumerate(top):
        t = i / max(n - 1, 1)
        y = 1 - t * 2
        r = np.sqrt(max(0.0, 1 - y*y))
        th = phi_g * i
        pos[k] = (r * np.cos(th) * 1.22, y * 0.95, r * np.sin(th) * 0.85)

    # ── Connections ───────────────────────────────────────────────────
    ex, ey, ez = [], [], []
    seen: set = set()
    for k, v in top:
        for conn, cw in v["connections"].items():
            if conn in pos and cw >= 1:
                key = tuple(sorted([k, conn]))
                if key not in seen:
                    p1, p2 = pos[k], pos[conn]
                    ex += [p1[0], p2[0], None]
                    ey += [p1[1], p2[1], None]
                    ez += [p1[2], p2[2], None]
                    seen.add(key)
    if ex:
        traces.append(go.Scatter3d(
            x=ex, y=ey, z=ez, mode="lines",
            line=dict(color="rgba(0,200,100,0.18)", width=1.5),
            hoverinfo="skip", showlegend=False,
        ))

    # ── Nodes ─────────────────────────────────────────────────────────
    by_cat: dict = {}
    for k, v in top:
        cat = _cat(k)
        if cat not in by_cat:
            by_cat[cat] = {"x":[],"y":[],"z":[],"text":[],"size":[],"hover":[]}
        px, py, pz = pos[k]
        by_cat[cat]["x"].append(px); by_cat[cat]["y"].append(py); by_cat[cat]["z"].append(pz)
        by_cat[cat]["text"].append(k)
        by_cat[cat]["size"].append(max(5, min(24, v["weight"] * 4)))
        by_cat[cat]["hover"].append(f"{k}  ×{v['weight']}")

    for cat, vals in by_cat.items():
        col = COLORS.get(cat, "#558899")
        traces.append(go.Scatter3d(
            x=vals["x"], y=vals["y"], z=vals["z"],
            mode="markers+text", name=cat,
            text=vals["text"], textfont=dict(size=7, color=col),
            textposition="top center",
            customdata=vals["hover"],
            hovertemplate="%{customdata}<extra></extra>",
            marker=dict(size=vals["size"], color=col, opacity=0.88,
                        line=dict(width=0.5, color="rgba(255,255,255,0.25)")),
        ))

    fig = go.Figure(data=traces)
    fig.update_layout(**_layout3d(450))
    return fig


def _layout3d(h: int) -> dict:
    ax = dict(
        showgrid=False, zeroline=False, showticklabels=False,
        showspikes=False, showaxeslabels=False,
        backgroundcolor="#040810",
        title=dict(text=""),
    )
    return dict(
        paper_bgcolor="#040810",
        scene=dict(bgcolor="#040810", xaxis=ax, yaxis=ax, zaxis=ax,
                   camera=dict(eye=dict(x=1.4, y=0.8, z=0.8))),
        margin=dict(l=0, r=0, t=0, b=0),
        height=h,
        showlegend=True,
        legend=dict(
            font=dict(color="#00ff99", size=9, family="Courier New"),
            bgcolor="rgba(4,8,16,0.85)",
            bordercolor="rgba(0,200,100,0.2)",
            borderwidth=1, x=0.01, y=0.99,
        ),
        uirevision="brain3d",
    )


# ─────────────────────────────────────────────────────────────────────
# 2D Concept Map
# ─────────────────────────────────────────────────────────────────────
def make_map_2d(brain: SecondBrain) -> go.Figure:
    data = brain.brain_map_data(30)
    nodes, edges = data["nodes"], data["edges"]
    bg = "#040810"

    if not nodes:
        fig = go.Figure()
        fig.update_layout(paper_bgcolor=bg, plot_bgcolor=bg, height=180,
                          margin=dict(l=0,r=0,t=0,b=0))
        return fig

    G = nx.Graph()
    for nd in nodes: G.add_node(nd["id"])
    for e in edges:  G.add_edge(e["source"], e["target"])
    pos = nx.spring_layout(G, k=2.8, seed=42)

    ex, ey = [], []
    for e in edges:
        if e["source"] in pos and e["target"] in pos:
            x0,y0 = pos[e["source"]]; x1,y1 = pos[e["target"]]
            ex += [x0,x1,None]; ey += [y0,y1,None]

    traces = [go.Scatter(x=ex, y=ey, mode="lines",
                         line=dict(color="rgba(0,180,80,0.18)", width=0.8),
                         hoverinfo="skip", showlegend=False)]

    by_cat: dict = {}
    for nd in nodes:
        cat = nd["category"]
        if cat not in by_cat:
            by_cat[cat] = {"x":[],"y":[],"text":[],"size":[]}
        x, y = pos[nd["id"]]
        by_cat[cat]["x"].append(x); by_cat[cat]["y"].append(y)
        by_cat[cat]["text"].append(nd["id"])
        by_cat[cat]["size"].append(max(6, min(20, nd["weight"] * 4)))

    for cat, v in by_cat.items():
        col = COLORS.get(cat, "#558899")
        traces.append(go.Scatter(
            x=v["x"], y=v["y"], mode="markers+text", name=cat,
            text=v["text"], textposition="top center",
            textfont=dict(size=8, color=col),
            marker=dict(size=v["size"], color=col, opacity=0.85,
                        line=dict(width=0.5, color="rgba(255,255,255,0.15)")),
        ))

    fig = go.Figure(data=traces)
    fig.update_layout(
        paper_bgcolor=bg, plot_bgcolor="#060c18",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        showlegend=False, height=180,
        margin=dict(l=4, r=4, t=4, b=4),
    )
    return fig


# ─────────────────────────────────────────────────────────────────────
# HUD Header
# ─────────────────────────────────────────────────────────────────────
now = datetime.now()
stats = brain.stats()
cats = brain.category_counts()
dominant = max(cats, key=cats.get) if cats else "---"
top1 = brain.top_concepts(1)
top_word = top1[0][0] if top1 else "---"

st.markdown(f"""
<div style="
  background:linear-gradient(90deg,#060c1a,#0a1428,#060c1a);
  border:1px solid #00cc6644; border-radius:3px;
  padding:8px 18px; font-family:'Courier New',monospace; font-size:11px;
  color:#00cc88; display:flex; justify-content:space-between; align-items:center;
  margin-bottom:8px; letter-spacing:2px;">
  <span style="font-size:14px;font-weight:bold;letter-spacing:4px;">◈ MIZUKI NEURAL INTERFACE</span>
  <span>{now.strftime('%Y/%m/%d  %H:%M:%S')}</span>
  <span>MEM:{stats['memories']:04d} | CONCEPT:{stats['concepts']:04d}</span>
  <span style="color:#ff4444;" class="live-dot">● LIVE</span>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────
# Metric tiles
# ─────────────────────────────────────────────────────────────────────
tm1, tm2, tm3, tm4 = st.columns(4)
for col_obj, val, lbl in [
    (tm1, f"{stats['memories']:04d}", "MEMORIES"),
    (tm2, f"{stats['concepts']:04d}", "CONCEPTS"),
    (tm3, dominant,                   "DOMINANT ZONE"),
    (tm4, top_word,                   "TOP CONCEPT"),
]:
    with col_obj:
        fs = "26px" if len(str(val)) <= 4 else "15px"
        st.markdown(
            f"<div style='background:#060c18;border:1px solid #00cc6633;border-radius:3px;"
            f"padding:8px 4px;text-align:center;font-family:Courier New,monospace;margin-bottom:6px'>"
            f"<div style='font-size:{fs};color:#00ff99;font-weight:bold;line-height:1.2'>{val}</div>"
            f"<div style='font-size:9px;color:#44666688;letter-spacing:2px;margin-top:2px'>{lbl}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

# ─────────────────────────────────────────────────────────────────────
# Main layout: 3D Brain | Chat + Data Table
# ─────────────────────────────────────────────────────────────────────
col_l, col_r = st.columns([6, 4], gap="small")

with col_l:
    st.markdown(
        "<div style='font-family:Courier New,monospace;font-size:9px;letter-spacing:3px;"
        "color:#00cc6666;border-bottom:1px solid #00cc6622;padding-bottom:3px;margin-bottom:4px'>"
        "◈ 3D NEURAL NETWORK</div>", unsafe_allow_html=True)
    st.plotly_chart(make_brain_3d(brain), use_container_width=True,
                    config={"displayModeBar": False})

    st.markdown(
        "<div style='font-family:Courier New,monospace;font-size:9px;letter-spacing:3px;"
        "color:#00cc6666;border-bottom:1px solid #00cc6622;padding-bottom:3px;margin-bottom:4px'>"
        "◈ CONCEPT MAP  [ AXIAL VIEW ]</div>", unsafe_allow_html=True)
    st.plotly_chart(make_map_2d(brain), use_container_width=True,
                    config={"displayModeBar": False})

with col_r:
    # ── Chat terminal ──────────────────────────────────────────────
    st.markdown(
        "<div style='font-family:Courier New,monospace;font-size:9px;letter-spacing:3px;"
        "color:#00cc6666;border-bottom:1px solid #00cc6622;padding-bottom:3px;margin-bottom:4px'>"
        "◈ NEURAL CHAT TERMINAL</div>", unsafe_allow_html=True)

    # Build chat HTML
    if not st.session_state.history:
        chat_body = (
            "<div style='color:#1a3344;font-size:11px;text-align:center;padding:30px 0'>"
            "[ NEURAL LINK STANDBY ]<br>API KEY を入力して接続"
            "</div>"
        )
    else:
        parts = []
        for role, text, ts in st.session_state.history:
            safe = text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
            if role == "user":
                parts.append(
                    f"<div style='color:#223344;font-size:9px;margin-top:6px'>{ts} USER</div>"
                    f"<div style='color:#44aaff;font-size:12px;padding-left:10px;"
                    f"border-left:2px solid #44aaff;margin-bottom:2px'>&gt; {safe}</div>"
                )
            else:
                parts.append(
                    f"<div style='color:#223344;font-size:9px;margin-top:2px'>{ts} NEURAL-AI</div>"
                    f"<div style='color:#00ff99;font-size:12px;padding-left:10px;"
                    f"border-left:2px solid #00cc66;margin-bottom:6px;white-space:pre-wrap'>{safe}</div>"
                )
        chat_body = "\n".join(parts)

    st.markdown(
        f"<div style='background:#030609;border:1px solid #00cc6633;border-radius:3px;"
        f"height:280px;overflow-y:auto;padding:10px 12px;font-family:Courier New,monospace'>"
        f"{chat_body}</div>",
        unsafe_allow_html=True,
    )

    # Input
    inp_c, btn_c = st.columns([5, 1])
    with inp_c:
        user_input = st.text_input("INPUT", label_visibility="collapsed",
                                   placeholder="> INPUT NEURAL SIGNAL...",
                                   key="chat_input")
    with btn_c:
        send = st.button("▶", use_container_width=True)

    if send and user_input.strip():
        if not st.session_state.agent:
            st.warning("API KEY を入力")
        else:
            ts = datetime.now().strftime("%H:%M")
            st.session_state.history.append(("user", user_input.strip(), ts))
            with st.spinner(""):
                reply = st.session_state.agent.chat(user_input.strip())
            st.session_state.history.append(("bot", reply, datetime.now().strftime("%H:%M")))
            st.rerun()

    # ── NEURAL REGION DATA table ───────────────────────────────────
    st.markdown(
        "<div style='font-family:Courier New,monospace;font-size:9px;letter-spacing:3px;"
        "color:#00cc6666;border-bottom:1px solid #00cc6622;padding-bottom:3px;"
        "margin:10px 0 4px 0'>◈ NEURAL REGION DATA</div>", unsafe_allow_html=True)

    top_list = brain.top_concepts(14)
    max_w = top_list[0][1]["weight"] if top_list else 1

    rows = ""
    for k, v in top_list:
        cat = _cat(k)
        col_hex = COLORS.get(cat, "#558899")
        pct = int(v["weight"] / max(max_w, 1) * 100)
        rows += (
            f"<tr>"
            f"<td style='color:{col_hex};padding:2px 4px'>{k}</td>"
            f"<td style='color:#334455;padding:2px 4px'>{cat}</td>"
            f"<td style='padding:2px 4px'>"
            f"<div style='width:{pct}%;height:6px;background:{col_hex};"
            f"border-radius:2px;opacity:.7;min-width:4px'></div></td>"
            f"<td style='color:#00ff99;text-align:right;padding:2px 4px'>{v['weight']}</td>"
            f"</tr>"
        )

    st.markdown(
        f"<table style='width:100%;border-collapse:collapse;font-family:Courier New,monospace;font-size:10px'>"
        f"<tr><th style='color:#00cc6666;padding:2px 4px;text-align:left;font-weight:normal;"
        f"letter-spacing:2px;border-bottom:1px solid #00cc6622'>CONCEPT</th>"
        f"<th style='color:#00cc6666;padding:2px 4px;text-align:left;font-weight:normal;"
        f"letter-spacing:2px;border-bottom:1px solid #00cc6622'>REGION</th>"
        f"<th style='color:#00cc6666;padding:2px 4px;text-align:left;font-weight:normal;"
        f"letter-spacing:2px;border-bottom:1px solid #00cc6622'>ACTIVITY</th>"
        f"<th style='color:#00cc6666;padding:2px 4px;text-align:right;font-weight:normal;"
        f"letter-spacing:2px;border-bottom:1px solid #00cc6622'>Hz</th></tr>"
        f"{rows}</table>",
        unsafe_allow_html=True,
    )
