"""∞Mind — L2 可視化層 / 脳ゾーン定義.

設計（IUI lab. ∞Mind）では、対話で言語化された思考・感情・目標などを
6つの「脳ゾーン」として可視化する。配色は京都の伝統色（西陣織の糸目）から取る。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class Zone:
    key: str
    jp: str
    en: str
    region_jp: str
    region_en: str
    color: str
    kyoto: str          # 京都伝統色の名前
    summary: str
    anchor: Tuple[float, float, float]  # 脳楕円体内の重心 (前後, 上下, 左右)
    keywords: Tuple[str, ...] = field(default=())

    def to_dict(self) -> Dict:
        return {
            "key": self.key,
            "jp": self.jp,
            "en": self.en,
            "region_jp": self.region_jp,
            "region_en": self.region_en,
            "color": self.color,
            "kyoto": self.kyoto,
            "summary": self.summary,
            "anchor": list(self.anchor),
        }


ZONES: Tuple[Zone, ...] = (
    Zone(
        key="thought", jp="思考", en="Thought",
        region_jp="前頭前野", region_en="PREFRONTAL",
        color="#2792C3", kyoto="縹色",
        summary="筋道を立てて考え、比べ、意味づける層。",
        anchor=(0.78, 0.18, 0.00),
        keywords=(
            "思考", "考え", "考える", "分析", "理解", "整理", "判断", "仮説", "なぜ",
            "理由", "構造", "設計", "ロジック", "検討", "比較", "把握", "言語化",
            "think", "analy", "design", "logic", "reason", "structure",
        ),
    ),
    Zone(
        key="emotion", jp="感情", en="Emotion",
        region_jp="大脳辺縁系", region_en="LIMBIC",
        color="#D05A6E", kyoto="今様色",
        summary="心が動いた瞬間を受け取る層。",
        anchor=(0.02, 0.00, 0.10),
        keywords=(
            "嬉しい", "楽しい", "悲しい", "辛い", "不安", "怖い", "好き", "嫌い",
            "疲れ", "わくわく", "感動", "しんどい", "安心", "寂し", "気持ち", "焦",
            "落ち込", "腹立", "ホッと", "感情", "ムカ", "泣",
            "happy", "sad", "anxious", "excited", "tired", "afraid",
        ),
    ),
    Zone(
        key="goals", jp="目標", en="Goals",
        region_jp="頭頂葉", region_en="PARIETAL",
        color="#68BE8D", kyoto="若竹色",
        summary="行き先を定め、進み続ける層。",
        anchor=(-0.42, 0.60, 0.00),
        keywords=(
            "目標", "やりたい", "したい", "作りたい", "なりたい", "目指", "挑戦",
            "計画", "予定", "達成", "締切", "ゴール", "続け", "習慣", "完成",
            "進め", "取り組", "実現", "やり切", "next",
            "goal", "plan", "achieve", "deadline", "milestone",
        ),
    ),
    Zone(
        key="values", jp="価値観", en="Values",
        region_jp="前帯状皮質", region_en="CINGULATE",
        color="#F8B500", kyoto="山吹色",
        summary="譲れないものが立ち上がる層。",
        anchor=(0.28, 0.52, 0.00),
        keywords=(
            "大切", "大事", "べき", "信念", "価値観", "誠実", "正しい", "公平",
            "尊重", "責任", "自分らしさ", "軸", "譲れ", "ずるい", "礼儀", "筋",
            "納得", "信じ", "誇り", "嘘",
            "value", "belief", "integrity", "fair", "respect",
        ),
    ),
    Zone(
        key="memory", jp="記憶", en="Memory",
        region_jp="海馬", region_en="HIPPOCAMPUS",
        color="#A59ACA", kyoto="藤紫",
        summary="過去を呼び戻し、いま結び直す層。",
        anchor=(-0.46, -0.24, 0.30),
        keywords=(
            "覚え", "思い出", "昔", "前に", "以前", "あの時", "経験", "子供の頃",
            "記録", "振り返", "過去", "学んだ", "当時", "懐かし", "あの頃",
            "memory", "remember", "past", "recall",
        ),
    ),
    Zone(
        key="ideas", jp="アイデア", en="Ideas",
        region_jp="側頭葉", region_en="TEMPORAL",
        color="#00A3AF", kyoto="浅葱色",
        summary="まだ形のないものが芽吹く層。",
        anchor=(0.18, -0.46, 0.46),
        keywords=(
            "アイデア", "思いつ", "発想", "ひらめ", "企画", "構想", "案", "もし",
            "作れそう", "面白", "新しい", "可能性", "やってみ", "試し", "ひょっと",
            "どうかな", "妄想", "こんなの",
            "idea", "concept", "maybe", "what if", "prototype",
        ),
    ),
)

ZONE_BY_KEY: Dict[str, Zone] = {z.key: z for z in ZONES}
ZONE_KEYS: Tuple[str, ...] = tuple(z.key for z in ZONES)
ZONE_JP: Dict[str, str] = {z.key: z.jp for z in ZONES}


# ── 形態素解析なしで日本語＋英語からトークンを拾う ───────────────────
# 内容語はほぼ漢字・カタカナ・英字に落ちる。ひらがな連続は助詞・活用なので拾わない。
_TOKEN_RE = re.compile(r"[一-龯々]{2,}|[ァ-ヴー]{3,}|[A-Za-z][A-Za-z0-9_+#.-]{1,}")

_STOP = {
    "こと", "もの", "よう", "ため", "これ", "それ", "あれ", "どれ", "とき",
    "した", "して", "する", "ある", "いる", "ない", "なる", "でき", "から",
    "まで", "たり", "たら", "れる", "られ", "られる", "せる", "させ", "いた",
    "おも", "はな", "きた", "いう", "そう", "だけ", "ほう", "です", "ます",
    "the", "and", "for", "with", "that", "this", "are", "was", "were", "have",
    "has", "not", "you", "but", "can", "will", "about", "into", "out",
    "is", "of", "to", "in", "on", "it", "be", "do", "an", "as", "at", "by",
    "or", "if", "so", "we", "my", "me", "no", "up", "re", "am", "id",
}


def tokenize(text: str, limit: int = 14) -> List[str]:
    """概念グラフのノード候補になる語を取り出す。出現順を保つ。"""
    seen: List[str] = []
    for raw in _TOKEN_RE.findall(text):
        tok = raw.lower() if raw.isascii() else raw
        if tok in _STOP or tok in seen:
            continue
        seen.append(tok)
        if len(seen) >= limit:
            break
    return seen


def score_zones(text: str) -> Dict[str, float]:
    """テキストの各ゾーンへの帰属度を 0..1 で返す（合計 1、無反応なら空）。"""
    lowered = text.lower()
    raw: Dict[str, float] = {}
    for zone in ZONES:
        hits = sum(1 for kw in zone.keywords if (kw if kw.isascii() else kw) in
                   (lowered if kw.isascii() else text))
        if hits:
            raw[zone.key] = float(hits)
    total = sum(raw.values())
    if not total:
        return {}
    return {k: round(v / total, 4) for k, v in raw.items()}


def primary_zone(scores: Dict[str, float], default: str = "thought") -> str:
    if not scores:
        return default
    return max(scores.items(), key=lambda kv: kv[1])[0]


def zone_of_concept(concept: str) -> str:
    """概念語そのものがどのゾーンに属するか（マップ着色用）。"""
    scores = score_zones(concept)
    return primary_zone(scores, default="thought") if scores else "thought"
