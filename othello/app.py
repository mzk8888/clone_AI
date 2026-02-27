"""
AI Othello (Reversi) — Streamlit App

Player = Black (●)   AI = White (○)
"""

import streamlit as st
import numpy as np
import time

from game import OthelloGame, BLACK, WHITE, EMPTY
from ai import OthelloAI

# ──────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="AI オセロ",
    page_icon="⬛",
    layout="centered",
)

# ──────────────────────────────────────────────
# CSS
# ──────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Board background */
    .board-wrapper {
        display: flex;
        justify-content: center;
        margin: 10px 0;
    }
    .cell-btn button {
        font-size: 28px !important;
        line-height: 1 !important;
        width: 62px !important;
        height: 62px !important;
        padding: 0 !important;
        border-radius: 4px !important;
        border: 1px solid #2d6a4f !important;
        background-color: #40916c !important;
        color: white !important;
        transition: background-color 0.15s;
    }
    .cell-btn button:hover {
        background-color: #52b788 !important;
        cursor: pointer;
    }
    .hint-btn button {
        background-color: #74c69d !important;
        opacity: 0.85;
    }
    .stButton > button { border-radius: 8px; }
    h1 { text-align: center; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
# Session state helpers
# ──────────────────────────────────────────────
DIFFICULTY = {"やさしい": 2, "ふつう": 4, "むずかしい": 6}


def init_state():
    st.session_state.game = OthelloGame()
    st.session_state.message = "あなたの番です (●黒)"
    st.session_state.game_over = False
    st.session_state.thinking = False


if "game" not in st.session_state:
    init_state()

# ──────────────────────────────────────────────
# Sidebar — settings
# ──────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ 設定")
    difficulty_label = st.selectbox(
        "AIの強さ", list(DIFFICULTY.keys()), index=1
    )
    ai_depth = DIFFICULTY[difficulty_label]
    ai = OthelloAI(depth=ai_depth)

    if st.button("🔄 新しいゲーム", use_container_width=True):
        init_state()
        st.rerun()

    st.markdown("---")
    st.markdown("### ルール")
    st.markdown(
        """
- あなたは **● 黒**、AIは **○ 白** です
- 相手の石を自分の石で挟むと、間の石がすべてひっくり返ります
- 有効な手がない場合はパスになります
- 最終的に石が多い方の勝ちです
        """
    )

# ──────────────────────────────────────────────
# Header & score
# ──────────────────────────────────────────────
st.title("⬛ AI オセロ ⬜")

game: OthelloGame = st.session_state.game
black_count, white_count = game.get_score()

col_b, col_w = st.columns(2)
with col_b:
    st.metric("● あなた (黒)", black_count)
with col_w:
    st.metric("○ AI (白)", white_count)

st.info(st.session_state.message)

# ──────────────────────────────────────────────
# Board rendering
# ──────────────────────────────────────────────
PIECE = {BLACK: "●", WHITE: "○", EMPTY: "　"}

valid_moves = set(game.get_valid_moves(BLACK)) if not st.session_state.game_over else set()


def cell_label(r: int, c: int) -> str:
    v = game.board[r][c]
    if v != EMPTY:
        return PIECE[v]
    if (r, c) in valid_moves:
        return "·"
    return "　"


# Render 8×8 board
for row in range(8):
    cols = st.columns(8)
    for col in range(8):
        lbl = cell_label(row, col)
        is_hint = (row, col) in valid_moves
        with cols[col]:
            btn_key = f"cell_{row}_{col}"
            # Only valid-move hint cells are clickable
            disabled = st.session_state.game_over or not is_hint
            if st.button(lbl, key=btn_key, disabled=disabled):
                if (row, col) in valid_moves and not st.session_state.game_over:
                    # Player move
                    game = game.apply_move(row, col, BLACK)
                    st.session_state.game = game

                    # Check game over after player move
                    if game.is_game_over():
                        winner = game.get_winner()
                        if winner == BLACK:
                            st.session_state.message = "🎉 あなたの勝ちです！"
                        elif winner == WHITE:
                            st.session_state.message = "😔 AIの勝ちです。"
                        else:
                            st.session_state.message = "🤝 引き分けです！"
                        st.session_state.game_over = True
                        st.rerun()

                    # Check if AI has moves
                    ai_moves = game.get_valid_moves(WHITE)
                    if not ai_moves:
                        player_moves = game.get_valid_moves(BLACK)
                        if player_moves:
                            st.session_state.message = "AIはパスします。あなたの番です (●黒)"
                        st.rerun()

                    # AI move
                    st.session_state.message = "AIが考えています…"
                    st.rerun()

# ──────────────────────────────────────────────
# AI turn logic (runs after rerun)
# ──────────────────────────────────────────────
game = st.session_state.game

if not st.session_state.game_over:
    player_moves = game.get_valid_moves(BLACK)
    ai_moves = game.get_valid_moves(WHITE)

    if "AIが考えています" in st.session_state.message:
        with st.spinner("AIが考えています…"):
            best = ai.get_best_move(game, WHITE)
        if best:
            game = game.apply_move(best[0], best[1], WHITE)
            st.session_state.game = game

        if game.is_game_over():
            winner = game.get_winner()
            if winner == BLACK:
                st.session_state.message = "🎉 あなたの勝ちです！"
            elif winner == WHITE:
                st.session_state.message = "😔 AIの勝ちです。"
            else:
                st.session_state.message = "🤝 引き分けです！"
            st.session_state.game_over = True
        else:
            new_player_moves = game.get_valid_moves(BLACK)
            if not new_player_moves:
                st.session_state.message = "あなたはパスします。AIの番です…"
                # Trigger AI again
                best2 = ai.get_best_move(game, WHITE)
                if best2:
                    game = game.apply_move(best2[0], best2[1], WHITE)
                    st.session_state.game = game
                if game.is_game_over():
                    winner = game.get_winner()
                    if winner == BLACK:
                        st.session_state.message = "🎉 あなたの勝ちです！"
                    elif winner == WHITE:
                        st.session_state.message = "😔 AIの勝ちです。"
                    else:
                        st.session_state.message = "🤝 引き分けです！"
                    st.session_state.game_over = True
                else:
                    st.session_state.message = "あなたの番です (●黒)"
            else:
                st.session_state.message = "あなたの番です (●黒)"
        st.rerun()

# ──────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:gray; font-size:12px;'>"
    "AI: Minimax + Alpha-Beta Pruning"
    "</div>",
    unsafe_allow_html=True,
)
