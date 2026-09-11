"""∞Mind — L1→L2 の橋渡し / 発話の構造化.

対話は生のままでは可視化できない。ここで発話を
「どのゾーンが灯ったか / どの概念が出たか / どの強みが現れたか」へ落とす。

Claude が使えるときは意味で読み、使えないときは辞書で読む。
どちらの経路でも同じ Signal が返るので、上の層は API キーの有無を気にしない。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from . import via, zones

log = logging.getLogger("infmind.extract")

EXTRACT_MODEL = "claude-opus-5"

_POSITIVE = (
    "嬉しい", "楽しい", "面白", "わくわく", "good", "最高", "できた", "成功",
    "ありがた", "感謝", "安心", "気持ちいい", "満足", "進んだ", "解決", "助かった",
)
_NEGATIVE = (
    "辛い", "しんどい", "悲しい", "不安", "怖い", "疲れ", "無理", "失敗",
    "落ち込", "焦", "腹立", "ムカ", "詰ま", "できない", "分からない", "嫌",
)


@dataclass
class Signal:
    """1 発話から取り出した構造。"""

    zone: str
    zone_scores: Dict[str, float]
    concepts: List[str]
    strengths: Dict[str, float]
    valence: float
    insight: str
    by: str = "heuristic"   # "claude" か "heuristic"
    notes: List[str] = field(default_factory=list)


# ── Claude に返させる形 ────────────────────────────────────────────
class _Extraction(BaseModel):
    zone: str = Field(description="主に灯った脳ゾーン: thought / emotion / goals / values / memory / ideas")
    secondary_zones: List[str] = Field(default_factory=list, description="同時に灯った他のゾーン(0-2個)")
    concepts: List[str] = Field(default_factory=list, description="発話の核になる名詞句を2〜6個、原文の表記のまま")
    strengths: List[str] = Field(default_factory=list, description="現れたVIAの強みの日本語名を0〜3個")
    valence: float = Field(description="感情の向き。-1(苦しい)〜0(中立)〜+1(心地よい)")
    insight: str = Field(description="本人が言語化しようとしていたことを、本人の言葉で一文にまとめる(40字以内)")


_SYSTEM = """\
あなたは ∞Mind の解析層です。ユーザーの発話を、第二の脳に刻む構造へ変換します。

脳ゾーンの定義:
- thought  思考 : 筋道を立てて考え、比べ、意味づけている
- emotion  感情 : 心が動いた、気持ちそのものを語っている
- goals    目標 : 行き先・やりたいこと・進めていることを語っている
- values   価値観: 譲れないもの、大切にしている基準を語っている
- memory   記憶 : 過去の出来事・経験を呼び戻している
- ideas    アイデア: まだ形のない発想・可能性を語っている

VIAの24の強み（この日本語名のみ使う）:
創造性, 好奇心, 判断力, 向学心, 大局観, 勇敢さ, 粘り強さ, 誠実さ, 熱意,
愛情, 親切心, 社会的知性, チームワーク, 公平さ, リーダーシップ, 寛容さ,
謙虚さ, 思慮深さ, 自律, 審美眼, 感謝, 希望, ユーモア, 超越

規則:
- 強みは「実際にその発話の中で発揮されている」ときだけ挙げる。話題にしただけなら挙げない。
- concepts は解釈せず、発話に実際に出てきた語を使う。
- insight は本人の一人称で、評価も助言も足さずに書く。
"""


def _heuristic(text: str) -> Signal:
    scores = zones.score_zones(text)
    zone = zones.primary_zone(scores)
    pos = sum(1 for w in _POSITIVE if w in text)
    neg = sum(1 for w in _NEGATIVE if w in text)
    valence = 0.0
    if pos or neg:
        valence = round((pos - neg) / (pos + neg), 2)
    concepts = zones.tokenize(text, limit=8)
    insight = text.strip().replace("\n", " ")
    if len(insight) > 60:
        insight = insight[:57] + "…"
    return Signal(
        zone=zone,
        zone_scores=scores or {zone: 1.0},
        concepts=concepts,
        strengths=via.detect(text),
        valence=valence,
        insight=insight,
        by="heuristic",
    )


def _merge(base: Signal, ex: _Extraction) -> Signal:
    """Claude の読みを土台の上に重ねる。辞書側の取りこぼしは残す。"""
    zone = ex.zone if ex.zone in zones.ZONE_BY_KEY else base.zone

    scores: Dict[str, float] = {zone: 1.0}
    for sec in ex.secondary_zones[:2]:
        if sec in zones.ZONE_BY_KEY and sec != zone:
            scores[sec] = 0.5
    total = sum(scores.values())
    scores = {k: round(v / total, 4) for k, v in scores.items()}

    concepts = list(base.concepts)
    for c in ex.concepts:
        c = c.strip()
        if c and c not in concepts:
            concepts.append(c)

    strengths = dict(base.strengths)
    for name in ex.strengths:
        s = via.resolve(name)
        if s:
            strengths[s.jp] = 0.9   # 意味で読めた分は確信度を上げる

    insight = ex.insight.strip() or base.insight
    return Signal(
        zone=zone,
        zone_scores=scores,
        concepts=concepts[:12],
        strengths=strengths,
        valence=max(-1.0, min(1.0, float(ex.valence))),
        insight=insight,
        by="claude",
    )


def extract(text: str, client=None) -> Signal:
    """発話 → Signal。client が無い/失敗した場合は辞書ベースに落ちる。"""
    base = _heuristic(text)
    if client is None:
        return base
    try:
        resp = client.messages.parse(
            model=EXTRACT_MODEL,
            max_tokens=1024,
            system=_SYSTEM,
            messages=[{"role": "user", "content": text}],
            output_format=_Extraction,
            output_config={"effort": "low"},
        )
        parsed: Optional[_Extraction] = resp.parsed_output
        if parsed is None:
            return base
        return _merge(base, parsed)
    except Exception as exc:  # 解析が落ちても対話は止めない
        log.warning("claude extraction failed, falling back to heuristic: %s", exc)
        base.notes.append(f"extract_fallback: {type(exc).__name__}")
        return base
