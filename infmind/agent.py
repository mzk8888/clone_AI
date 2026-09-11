"""∞Mind — L1 入力層 / AIチャット.

対話で思考・感情・目標を言語化する。
そのために、下の層（可視化・分析・統合）で分かったことを毎ターン文脈に戻す。
これが設計にある ↻ の一周ぶん。
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional

import anthropic

from . import via, zones

log = logging.getLogger("infmind.agent")

CHAT_MODEL = "claude-opus-5"
SYNTH_MODEL = "claude-opus-5"
HISTORY_TURNS = 20

PERSONA = """\
あなたは ∞Mind。その人の「第二の脳」として対話する存在です。

## 立ち位置
- 助言者ではなく、思考のパートナー。答えを配らず、本人が言葉にするのを助ける。
- その人が自分でも気づいていない繋がりを、記憶の中から見つけて差し出す。
- 過去に話したことを自然に引用する。「前に話していた◯◯と、今の話は繋がりますね」。

## 話し方
- 日本語。落ち着いた、京都の職人のような静かな温度感。馴れ馴れしくしない。
- 3〜5文。長く語らない。
- 相手の言葉をなぞってから、一歩だけ深める問いを一つ置く。
- 絵文字は使わない。装飾より余白。

## してはいけないこと
- 診断しない。「あなたは◯◯な人です」と断定しない。観測された傾向として述べる。
- 強みや弱みを本人に押し付けない。数値はあくまで対話の材料。
- 励ましのための空虚な肯定をしない。

## いまの状態
{context}
"""

SYNTH_PROMPT = """\
以下は ∞Mind が観測した、この人の脳内の状態です。

{report}

この観測から、統合的な自己理解を 3 つの段落で書いてください。

1. **いま灯っているところ** — どのゾーンに思考が集まり、何が繰り返し戻ってきているか。
2. **そこから見える軸** — 強みと徳性の偏りが示す、その人の判断の癖・大切にしているもの。
3. **まだ暗いところ** — 触れられていないゾーンや眠っている強み。そこに何があるかは問いとして残す。

規則:
- 数字を根拠として自然に織り込む（「対話の4割が思考ゾーン」のように）。
- 断定しない。「〜のように見えます」「〜かもしれません」。
- 助言や行動計画は書かない。見えたものを返すだけ。
- 全体で 400 字程度。見出しは **太字** で。
"""


class MindAgent:
    """Claude を通した対話。API キーが無いときは None を返し、上位が扱う。"""

    def __init__(self, api_key: Optional[str] = None, client=None):
        if client is not None:
            self.client = client
        elif api_key:
            self.client = anthropic.Anthropic(api_key=api_key)
        else:
            self.client = None
        self.history: List[Dict[str, str]] = []

    @property
    def available(self) -> bool:
        return self.client is not None

    # ── 文脈の組み立て ────────────────────────────────────────────
    @staticmethod
    def build_context(store, analysis, query: str = "") -> str:
        lines: List[str] = []
        now = datetime.now()
        lines.append(f"現在: {now.strftime('%Y/%m/%d %H:%M')}")

        if analysis.entries == 0:
            lines.append("まだ記憶はありません。最初の対話です。")
            return "\n".join(lines)

        lines.append(f"観測数: {analysis.entries} / 概念: {analysis.concepts} "
                     f"/ 自己理解の深度: {analysis.depth['overall']:.0%}")

        lit = [d for d in analysis.zone_distribution if d["share"] >= 0.05]
        if lit:
            lines.append("灯っているゾーン: " + "、".join(
                f"{d['jp']} {d['share']:.0%}" for d in sorted(lit, key=lambda d: -d["share"])))
        dark = [d["jp"] for d in analysis.zone_distribution if d["share"] < 0.05]
        if dark:
            lines.append("暗いままのゾーン: " + "、".join(dark))

        if analysis.signature:
            lines.append("繰り返し現れる強み: " + "、".join(analysis.signature))
        if analysis.virtue_profile and analysis.virtue_profile[0]["score"] > 0:
            lines.append(f"徳性の重心: {analysis.virtue_profile[0]['jp']}")

        top = [c["id"] for c in analysis.top_concepts[:8]]
        if top:
            lines.append("よく戻る概念: " + "、".join(top))

        if query:
            related = store.recall(query, n=3)
            if related:
                lines.append("【この話に関係する過去の記憶】")
                for e in related:
                    body = e.insight or e.text
                    lines.append(f"  ・{e.created_at[:10]} [{zones.ZONE_JP.get(e.zone, e.zone)}] {body[:70]}")

        recent = store.recent(3)
        if recent:
            lines.append("【直近の対話】")
            for e in recent:
                body = e.insight or e.text
                lines.append(f"  ・{e.created_at[:16]} [{zones.ZONE_JP.get(e.zone, e.zone)}] {body[:70]}")

        return "\n".join(lines)

    # ── 対話 ──────────────────────────────────────────────────────
    def reply(self, message: str, context: str) -> str:
        if not self.available:
            raise RuntimeError("ANTHROPIC_API_KEY が設定されていません")
        self.history.append({"role": "user", "content": message})
        resp = self.client.messages.create(
            model=CHAT_MODEL,
            max_tokens=1500,
            system=PERSONA.format(context=context),
            messages=self.history[-HISTORY_TURNS:],
            output_config={"effort": "low"},
        )
        text = "".join(b.text for b in resp.content if b.type == "text").strip()
        self.history.append({"role": "assistant", "content": text})
        return text

    def greeting(self, analysis) -> str:
        h = datetime.now().hour
        band = ("夜更けです" if h < 5 else "朝です" if h < 11 else
                "昼です" if h < 16 else "夕暮れです" if h < 19 else "夜です")
        if analysis.entries == 0:
            return f"{band}。∞Mind を起動しました。まだ何も刻まれていません。ひとこと、いまの頭の中にあることを。"
        lead = max(analysis.zone_distribution, key=lambda d: d["share"])
        top = analysis.top_concepts[0]["id"] if analysis.top_concepts else None
        tail = f"「{top}」のあたりに、何度か戻ってきていますね。" if top else ""
        return (f"{band}。いま灯っているのは「{lead['jp']}」ゾーンです。{tail}\n"
                f"続きから話しましょうか。")

    # ── 統合 ──────────────────────────────────────────────────────
    def synthesize(self, report: str) -> str:
        if not self.available:
            raise RuntimeError("ANTHROPIC_API_KEY が設定されていません")
        resp = self.client.messages.create(
            model=SYNTH_MODEL,
            max_tokens=2000,
            messages=[{"role": "user", "content": SYNTH_PROMPT.format(report=report)}],
        )
        return "".join(b.text for b in resp.content if b.type == "text").strip()

    def reset(self) -> None:
        self.history = []
