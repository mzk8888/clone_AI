"""
Mizuki personal AI agent — powered by Claude API.
Knows Mizuki's history, speaks Japanese naturally, acts as a second brain partner.
"""

from datetime import datetime
from typing import Dict, List, Optional

import anthropic

from brain import SecondBrain

_SYSTEM = """\
あなたはMizukiの専属AIパートナー「ミズキBot」です。

## Mizukiについて
- 日本人開発者、AIやPythonが大好き
- 制作物: AIオセロ、音声ラベリングシステム、GPT APIアプリ、AI学習プログラムなど
- 好奇心旺盛でどんどん新しいものを作る人
- カジュアルに日本語で話す

## あなたの役割
- **第二の脳**: Mizukiの思考を整理・拡張する思考パートナー
- **日常の相棒**: 「おはよう」から気軽に話せる存在
- **アイデアの触媒**: 話を深掘りして新しい視点を提供
- **記憶の管理者**: 過去の会話を覚えていて自然に参照する

## 会話スタイル
- フレンドリー・テンポよい
- 長すぎない返答（3〜6文程度）
- 過去の発言を「あの時言ってたこれ、繋がるね！」と自然に引用
- アイデアに積極的に乗っかる
- 絵文字を適度に使う

## 現在のコンテキスト
{time_ctx}

## Mizukiの脳内記憶
{brain_ctx}
"""


class MizukiAgent:
    def __init__(self, api_key: str, brain: SecondBrain):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.brain = brain
        self.history: List[Dict[str, str]] = []

    # ── Context builders ──────────────────────────────────────────────

    def _time_ctx(self) -> str:
        now = datetime.now()
        h = now.hour
        period = (
            "早朝" if h < 6 else
            "朝" if h < 10 else
            "午前" if h < 12 else
            "昼" if h < 14 else
            "午後" if h < 17 else
            "夕方" if h < 20 else
            "夜"
        )
        return f"{now.strftime('%Y/%m/%d %H:%M')} ({period})"

    def _brain_ctx(self, user_msg: str) -> str:
        lines: List[str] = []

        relevant = self.brain.recall(user_msg, n=3)
        if relevant:
            lines.append("【関連する記憶】")
            for m in relevant:
                lines.append(f"  - [{m.category}] {m.content[:90]}… ({m.timestamp[:10]})")

        recent = self.brain.recent(3)
        if recent:
            lines.append("【最近の記憶】")
            for m in recent:
                lines.append(f"  - {m.content[:80]}… ({m.timestamp[:10]})")

        top = self.brain.top_concepts(8)
        if top:
            lines.append("【よく出るテーマ】: " + ", ".join(k for k, _ in top))

        return "\n".join(lines) if lines else "まだ記憶ゼロ。これから一緒に育てよう！"

    def _system(self, user_msg: str) -> str:
        return _SYSTEM.format(
            time_ctx=self._time_ctx(),
            brain_ctx=self._brain_ctx(user_msg),
        )

    # ── Core chat ─────────────────────────────────────────────────────

    def chat(self, user_message: str) -> str:
        self.history.append({"role": "user", "content": user_message})

        resp = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=self._system(user_message),
            messages=self.history[-20:],
        )
        reply = resp.content[0].text
        self.history.append({"role": "assistant", "content": reply})

        # Auto-memorize the exchange
        self.brain.remember(f"User: {user_message}\nBot: {reply}", source="conversation")

        return reply

    # ── Special messages ──────────────────────────────────────────────

    def greeting(self) -> str:
        h = datetime.now().hour
        if h < 6:
            emoji, word = "🌙", "夜更かし中？"
        elif h < 10:
            emoji, word = "☀️", "おはよう！"
        elif h < 14:
            emoji, word = "🌤", "こんにちは！"
        elif h < 18:
            emoji, word = "🌇", "午後もがんばろ！"
        else:
            emoji, word = "🌙", "お疲れ様！"

        stats = self.brain.stats()
        top = self.brain.top_concepts(1)

        if stats["memories"] == 0:
            return f"{emoji} {word} はじめましてMizuki！一緒に第二の脳を育てていこう🧠"
        if top:
            return f"{emoji} {word} 最近「{top[0][0]}」についてよく考えてるね✨"
        return f"{emoji} {word} 脳内に{stats['concepts']}個のコンセプトが育ってるよ🌱"

    def analyze_brain(self) -> str:
        """Generate a natural-language summary of the brain map."""
        top = self.brain.top_concepts(10)
        cats = self.brain.category_counts()
        stats = self.brain.stats()

        if stats["memories"] == 0:
            return "まだ記憶がないよ。会話してから見てみて！"

        top_words = ", ".join(f"「{k}」({v['weight']}回)" for k, v in top[:5])
        dominant = max(cats, key=cats.get) if cats else "なし"

        prompt = (
            f"Mizukiの脳内トップキーワードは {top_words}。"
            f"一番多いカテゴリは「{dominant}」({cats.get(dominant, 0)}件)。"
            f"合計{stats['memories']}件の記憶・{stats['concepts']}個のコンセプトがある。"
            f"この脳内マップを見て、Mizukiの傾向や面白いパターン、次に探求すると良さそうなことを3点で教えて。フレンドリーに、絵文字つきで。"
        )
        return self.chat(prompt)
