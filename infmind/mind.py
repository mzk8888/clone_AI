"""∞Mind — 4層を束ねるループ本体.

    入力(L1 AIチャット) → 可視化(L2 脳ゾーン+VIA) → 分析(L3 分析マップ)
        → 統合(L4 第二の脳) ──┐
        └──────── ↻ 次の対話の文脈へ戻る ──────┘

observe() を呼ぶたびに一周する。回すほど文脈が厚くなり、自己理解が深まる。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

from . import via, zones
from .agent import MindAgent
from .analysis import AnalysisMap, analyze
from .extract import extract
from .store import Entry, MindStore

SEED = [
    "今日はAIオセロの評価関数をずっと考えていた。ミニマックスの深さを変えると急に強くなる。",
    "コードを書いている時間がいちばん落ち着く。没頭できるのが嬉しい。",
    "第二の脳を作りたい。自分の思考が自分で見えるようにしたい。",
    "昔やっていた音声認識の経験が、いまの設計の勘に効いている気がする。",
    "誠実であることは譲れない。曖昧にごまかすくらいなら、分からないと言いたい。",
    "Claude APIで対話の質が変わった。可能性をすごく感じる。",
    "疲れているけれど、手を動かすと気持ちが戻ってくる。",
    "友人にこの構想を話したら面白がってくれた。人に説明すると考えが整理される。",
]


class InfMind:
    """∞Mind 本体。"""

    def __init__(
        self,
        path: Path | str | None = None,
        api_key: Optional[str] = None,
        client=None,
    ):
        self.store = MindStore(path)
        key = api_key if api_key is not None else os.environ.get("ANTHROPIC_API_KEY", "")
        self.agent = MindAgent(api_key=key or None, client=client)
        self._analysis: Optional[AnalysisMap] = None

    # ── 状態 ──────────────────────────────────────────────────────
    @property
    def analysis(self) -> AnalysisMap:
        if self._analysis is None:
            self._analysis = analyze(self.store)
        return self._analysis

    def _invalidate(self) -> None:
        self._analysis = None

    @property
    def online(self) -> bool:
        """Claude に繋がっているか（オフラインでも辞書ベースで全層動く）。"""
        return self.agent.available

    def connect(self, api_key: str) -> bool:
        self.agent = MindAgent(api_key=api_key or None)
        return self.agent.available

    # ── ↻ 一周 ────────────────────────────────────────────────────
    def observe(self, text: str, reply: str = "", source: str = "dialogue") -> Entry:
        """L1 の発話を L2 の構造へ落とし、L4 に刻む。"""
        signal = extract(text, client=self.agent.client)
        entry = self.store.add(Entry(
            text=text.strip(),
            reply=reply,
            zone=signal.zone,
            zone_scores=signal.zone_scores,
            concepts=signal.concepts,
            strengths=signal.strengths,
            valence=signal.valence,
            insight=signal.insight,
            source=source,
        ))
        self._invalidate()
        return entry

    def converse(self, message: str) -> Dict:
        """対話 1 往復。応答を返し、同じ往復を脳へ刻む。"""
        context = MindAgent.build_context(self.store, self.analysis, query=message)
        reply = self.agent.reply(message, context)
        entry = self.observe(message, reply=reply, source="dialogue")
        return {"reply": reply, "entry": entry.to_dict(), "analysis": self.analysis.to_dict()}

    def greeting(self) -> str:
        return self.agent.greeting(self.analysis)

    # ── L4 統合 ───────────────────────────────────────────────────
    def report(self) -> str:
        """分析マップを、そのまま読める文章表に落とす。"""
        a = self.analysis
        lines = [
            f"観測数 {a.entries} / 概念 {a.concepts} / 記録日数 {a.depth['days']}日",
            f"自己理解の深度 {a.depth['overall']:.0%}"
            f"（量 {a.depth['volume']:.0%} / 広さ {a.depth['breadth']:.0%}"
            f" / 強みの覆い {a.depth['strength_coverage']:.0%} / 継続 {a.depth['continuity']:.0%}）",
            "",
            "【脳ゾーンの分布】",
        ]
        for d in sorted(a.zone_distribution, key=lambda d: -d["share"]):
            bar = "█" * max(0, round(d["share"] * 28))
            lines.append(f"  {d['jp']:<5}{d['share']*100:5.1f}%  {bar}  ({d['region_jp']})")

        lines += ["", "【強み 上位8】"]
        for r in a.strength_profile[:8]:
            if r["score"] <= 0:
                break
            lines.append(f"  {r['jp']:<10} {r['normalized']*100:5.1f}  "
                         f"[{via.VIRTUE_BY_KEY[r['virtue']].jp} / {zones.ZONE_JP[r['zone']]}]")

        lines += ["", "【徳性のバランス】"]
        for v in a.virtue_profile:
            lines.append(f"  {v['jp']:<5} {v['normalized']*100:5.1f}")

        b = a.balance
        lines += [
            "",
            f"【2因子バランス】 理性 {b['rational']:+.2f}（-1感情 / +1理性） × "
            f"個人内 {b['intra']:+.2f}（-1個人間 / +1個人内） 広がり {b['spread']:.2f}",
        ]

        if a.top_concepts:
            lines += ["", "【よく戻る概念】 " + "、".join(
                f"{c['id']}×{c['weight']}" for c in a.top_concepts[:12])]

        lines += ["", "【観測された傾向】"]
        lines += [f"  ・{t}" for t in a.tendencies]
        return "\n".join(lines)

    def synthesize(self) -> str:
        """分析マップを統合的な自己理解の語りに変える（要 API キー）。"""
        return self.agent.synthesize(self.report())

    # ── 可視化用の状態一式 ────────────────────────────────────────
    def state(self) -> Dict:
        a = self.analysis
        return {
            "online": self.online,
            "zones": [z.to_dict() for z in zones.ZONES],
            "via": via.catalog(),
            "analysis": a.to_dict(),
            "entries": [e.to_dict() for e in self.store.recent(30)],
        }

    # ── 種を蒔く / 消す ───────────────────────────────────────────
    def seed(self) -> int:
        """空のときだけ、脳に最初の灯をともす。"""
        if len(self.store):
            return 0
        for text in SEED:
            self.observe(text, source="seed")
        return len(SEED)

    def reset(self) -> None:
        self.store.reset()
        self.agent.reset()
        self._invalidate()
