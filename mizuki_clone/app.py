"""
Mizuki Clone — 第二の脳 & パーソナルAIエージェント

Usage:
    ANTHROPIC_API_KEY=sk-ant-... streamlit run app.py
    or enter the key in the sidebar.
"""

import os
from datetime import datetime

import networkx as nx
import plotly.graph_objects as go
import streamlit as st

from brain import SecondBrain, CATEGORIES
from agent import MizukiAgent

# ─────────────────────────────────────────────────────────────────────
# Page setup
# ─────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Mizuki Bot 🧠",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* Chat bubbles */
.user-bubble {
    background: #2563eb;
    color: white;
    padding: 10px 16px;
    border-radius: 18px 18px 4px 18px;
    margin: 6px 0 6px 60px;
    font-size: 15px;
    line-height: 1.5;
}
.bot-bubble {
    background: #1e293b;
    color: #e2e8f0;
    padding: 10px 16px;
    border-radius: 18px 18px 18px 4px;
    margin: 6px 60px 6px 0;
    font-size: 15px;
    line-height: 1.5;
}
.greeting-banner {
    background: linear-gradient(135deg, #1e3a5f, #0f766e);
    color: white;
    padding: 18px 24px;
    border-radius: 12px;
    margin-bottom: 16px;
    font-size: 18px;
    font-weight: 600;
}
.stat-box {
    background: #0f172a;
    border-radius: 10px;
    padding: 12px;
    text-align: center;
    color: #94a3b8;
    font-size: 13px;
}
.stat-box b { font-size: 22px; color: #38bdf8; display: block; }
[data-testid="stSidebar"] { background: #0f172a; }
h1, h2, h3 { color: #e2e8f0; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────
# Voice input component (Web Speech API)
# ─────────────────────────────────────────────────────────────────────
VOICE_COMPONENT = """
<div style="display:flex; gap:8px; align-items:center; margin-bottom:8px;">
  <button id="voice-btn" onclick="toggleVoice()" style="
    background:#0f766e; color:white; border:none; border-radius:50%;
    width:42px; height:42px; font-size:20px; cursor:pointer; transition:all 0.2s;">
    🎤
  </button>
  <span id="voice-status" style="color:#94a3b8; font-size:13px;">クリックで音声入力</span>
</div>
<input type="text" id="voice-out" style="display:none"/>
<script>
let recognizing = false;
let recognition;
function toggleVoice() {
  if (!('webkitSpeechRecognition' in window)) {
    document.getElementById('voice-status').innerText = '⚠️ このブラウザは未対応';
    return;
  }
  if (recognizing) { recognition.stop(); return; }
  recognition = new webkitSpeechRecognition();
  recognition.lang = 'ja-JP';
  recognition.interimResults = false;
  recognition.onstart = () => {
    recognizing = true;
    document.getElementById('voice-btn').style.background = '#dc2626';
    document.getElementById('voice-btn').innerText = '⏹';
    document.getElementById('voice-status').innerText = '聴いてるよ…';
  };
  recognition.onresult = (e) => {
    const text = e.results[0][0].transcript;
    document.getElementById('voice-status').innerText = '✅ ' + text;
    window.parent.postMessage({type:'voice_input', text: text}, '*');
  };
  recognition.onerror = () => {
    document.getElementById('voice-status').innerText = '❌ エラーが発生したよ';
  };
  recognition.onend = () => {
    recognizing = false;
    document.getElementById('voice-btn').style.background = '#0f766e';
    document.getElementById('voice-btn').innerText = '🎤';
  };
  recognition.start();
}
</script>
"""

# ─────────────────────────────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────────────────────────────

def _init():
    if "brain" not in st.session_state:
        st.session_state.brain = SecondBrain()
    if "history" not in st.session_state:
        st.session_state.history = []  # list of (role, text)
    if "greeted" not in st.session_state:
        st.session_state.greeted = False
    if "agent" not in st.session_state:
        st.session_state.agent = None

_init()
brain: SecondBrain = st.session_state.brain

# ─────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧠 Mizuki Bot")
    st.markdown("---")

    # API Key
    default_key = os.environ.get("ANTHROPIC_API_KEY", "")
    api_key = st.text_input(
        "Anthropic API Key",
        value=default_key,
        type="password",
        placeholder="sk-ant-...",
        help="https://console.anthropic.com で取得",
    )

    if api_key and st.session_state.agent is None:
        st.session_state.agent = MizukiAgent(api_key=api_key, brain=brain)
    elif api_key and st.session_state.agent is not None:
        # Update key if changed
        st.session_state.agent.client.api_key = api_key

    st.markdown("---")

    # Stats
    s = brain.stats()
    cols = st.columns(2)
    with cols[0]:
        st.markdown(f"<div class='stat-box'><b>{s['memories']}</b>記憶</div>", unsafe_allow_html=True)
    with cols[1]:
        st.markdown(f"<div class='stat-box'><b>{s['concepts']}</b>概念</div>", unsafe_allow_html=True)

    st.markdown("")

    # Actions
    if st.button("🌅 挨拶してもらう", use_container_width=True):
        if st.session_state.agent:
            greeting = st.session_state.agent.greeting()
            st.session_state.history.append(("bot", greeting))
            st.session_state.greeted = True
            st.rerun()
        else:
            st.warning("API Keyを入力してください")

    if st.button("🔍 脳内分析してもらう", use_container_width=True):
        if st.session_state.agent:
            with st.spinner("分析中…"):
                analysis = st.session_state.agent.analyze_brain()
            st.session_state.history.append(("bot", analysis))
            st.rerun()
        else:
            st.warning("API Keyを入力してください")

    if st.button("🗑 会話履歴クリア", use_container_width=True):
        st.session_state.history = []
        if st.session_state.agent:
            st.session_state.agent.history = []
        st.rerun()

    st.markdown("---")

    # Category breakdown
    cats = brain.category_counts()
    if cats:
        st.markdown("**カテゴリ分布**")
        for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
            st.markdown(f"`{cat}` {count}件")

    st.markdown("---")
    st.markdown(
        "<div style='color:#475569; font-size:12px;'>AI: Claude claude-sonnet-4-6<br>"
        "Brain: Minimap + Graph NLP</div>",
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────
# Main area
# ─────────────────────────────────────────────────────────────────────

# Auto-greet on first load
if not st.session_state.greeted and st.session_state.agent:
    greeting = st.session_state.agent.greeting()
    st.session_state.history.append(("bot", greeting))
    st.session_state.greeted = True

tab_chat, tab_map, tab_memories = st.tabs(["💬 会話", "🧠 脳内マップ", "📚 記憶ブラウザ"])

# ─────────────────────────────────────────────────────────────────────
# Tab 1: Chat
# ─────────────────────────────────────────────────────────────────────
with tab_chat:
    if not api_key:
        st.warning("👈 サイドバーにAnthropicのAPI Keyを入力してください")
        st.info("API Keyは https://console.anthropic.com で無料取得できます")
    else:
        # Chat history
        for role, text in st.session_state.history:
            if role == "user":
                st.markdown(f"<div class='user-bubble'>{text}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='bot-bubble'>{text}</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        # Voice input
        st.components.v1.html(VOICE_COMPONENT, height=60)

        # Text input
        with st.form("chat_form", clear_on_submit=True):
            col_inp, col_btn = st.columns([6, 1])
            with col_inp:
                user_input = st.text_input(
                    "メッセージ", label_visibility="collapsed",
                    placeholder="何でも話しかけて…（Enterで送信）"
                )
            with col_btn:
                submitted = st.form_submit_button("送信", use_container_width=True)

        if submitted and user_input.strip():
            msg = user_input.strip()
            st.session_state.history.append(("user", msg))

            with st.spinner("考えてるよ…"):
                reply = st.session_state.agent.chat(msg)
            st.session_state.history.append(("bot", reply))
            st.rerun()

# ─────────────────────────────────────────────────────────────────────
# Tab 2: Brain Map
# ─────────────────────────────────────────────────────────────────────
with tab_map:
    st.markdown("### 🧠 Mizukiの脳内マップ")
    st.caption("会話を続けるほどノードが増えて、思考のつながりが見えてくるよ")

    map_data = brain.brain_map_data(max_nodes=40)
    nodes = map_data["nodes"]
    edges = map_data["edges"]

    if not nodes:
        st.info("まだデータが少ないよ。会話をすると脳内マップが育ちます🌱")
    else:
        # NetworkX layout
        G = nx.Graph()
        for n in nodes:
            G.add_node(n["id"], weight=n["weight"])
        for e in edges:
            G.add_edge(e["source"], e["target"], weight=e["weight"])

        pos = nx.spring_layout(G, k=2.5, seed=42, iterations=50)

        COLORS = {
            "技術":     "#22c55e",
            "アイデア": "#3b82f6",
            "感情":     "#ec4899",
            "目標":     "#f97316",
            "学習":     "#a855f7",
            "日常":     "#06b6d4",
            "人間関係": "#ef4444",
            "その他":   "#64748b",
        }

        # Edges
        ex, ey = [], []
        for e in edges:
            if e["source"] in pos and e["target"] in pos:
                x0, y0 = pos[e["source"]]
                x1, y1 = pos[e["target"]]
                ex += [x0, x1, None]
                ey += [y0, y1, None]

        traces = [go.Scatter(
            x=ex, y=ey, mode="lines",
            line=dict(width=0.8, color="rgba(148,163,184,0.3)"),
            hoverinfo="none", showlegend=False,
        )]

        # Nodes grouped by category
        by_cat: dict = {}
        for n in nodes:
            c = n["category"]
            if c not in by_cat:
                by_cat[c] = {"x": [], "y": [], "text": [], "size": [], "hover": []}
            x, y = pos[n["id"]]
            by_cat[c]["x"].append(x)
            by_cat[c]["y"].append(y)
            by_cat[c]["text"].append(n["id"])
            by_cat[c]["size"].append(max(12, min(45, n["weight"] * 6)))
            by_cat[c]["hover"].append(f"{n['id']}<br>重み: {n['weight']}<br>{c}")

        for cat, v in by_cat.items():
            traces.append(go.Scatter(
                x=v["x"], y=v["y"],
                mode="markers+text",
                name=cat,
                text=v["text"],
                textposition="top center",
                textfont=dict(size=11, color="white"),
                customdata=v["hover"],
                hovertemplate="%{customdata}<extra></extra>",
                marker=dict(
                    size=v["size"],
                    color=COLORS.get(cat, "#64748b"),
                    line=dict(width=1.5, color="white"),
                    opacity=0.9,
                ),
            ))

        fig = go.Figure(
            data=traces,
            layout=go.Layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(15,23,42,0.8)",
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                showlegend=True,
                legend=dict(
                    font=dict(color="white", size=12),
                    bgcolor="rgba(15,23,42,0.7)",
                    bordercolor="rgba(148,163,184,0.2)",
                    borderwidth=1,
                ),
                height=560,
                margin=dict(l=10, r=10, t=20, b=10),
                hovermode="closest",
            ),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Top concepts table
        st.markdown("#### 🔝 上位コンセプト")
        top = brain.top_concepts(15)
        cols = st.columns(5)
        for i, (k, v) in enumerate(top):
            with cols[i % 5]:
                st.markdown(
                    f"<div style='background:#1e293b;border-radius:8px;padding:8px;text-align:center;"
                    f"margin:4px;color:#e2e8f0;font-size:13px;'>"
                    f"<b style='color:#38bdf8'>{k}</b><br>"
                    f"<span style='color:#64748b'>{v['weight']}回</span></div>",
                    unsafe_allow_html=True,
                )

# ─────────────────────────────────────────────────────────────────────
# Tab 3: Memory Browser
# ─────────────────────────────────────────────────────────────────────
with tab_memories:
    st.markdown("### 📚 記憶ブラウザ")

    if not brain.memories:
        st.info("まだ記憶がないよ。会話を始めよう！")
    else:
        # Search
        search_q = st.text_input("🔍 記憶を検索", placeholder="キーワードで検索…")

        if search_q:
            results = brain.recall(search_q, n=10)
            if results:
                st.markdown(f"**{len(results)}件**ヒット")
                for m in results:
                    with st.expander(f"[{m.category}] {m.content[:60]}…  ({m.timestamp[:10]})"):
                        st.markdown(m.content)
                        st.markdown(f"**タグ**: {', '.join(m.tags)}")
            else:
                st.info("見つからなかった…")
        else:
            # Show recent memories
            st.markdown(f"**最新{min(20, len(brain.memories))}件**")
            for m in reversed(brain.memories[-20:]):
                cat_color = {
                    "技術": "#22c55e", "アイデア": "#3b82f6", "感情": "#ec4899",
                    "目標": "#f97316", "学習": "#a855f7", "日常": "#06b6d4",
                    "人間関係": "#ef4444",
                }.get(m.category, "#64748b")
                with st.expander(
                    f"[{m.category}] {m.content[:70]}…  _({m.timestamp[:10]})_"
                ):
                    st.markdown(m.content)
                    st.markdown(f"**タグ**: {', '.join(m.tags) if m.tags else 'なし'}")

        # Add manual memory
        st.markdown("---")
        st.markdown("#### ✍️ 手動で記憶を追加")
        with st.form("add_memory"):
            memo_text = st.text_area("書きとめたいことを入力", placeholder="アイデア、気づき、メモ…")
            if st.form_submit_button("脳に保存する 🧠"):
                if memo_text.strip():
                    brain.remember(memo_text.strip(), source="manual")
                    st.success("記憶に保存したよ！")
                    st.rerun()
