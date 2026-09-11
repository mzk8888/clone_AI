"""∞Mind — L3 分析層 / 分析マップ.

蓄積された Entry から、思考傾向・価値観・強みを取り出す。
ここは決定論的に計算する。AIの語りはこの数字の上に乗せる（analysis → synthesis）。
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from . import via, zones
from .store import Entry, MindStore

# 強みスコアの減衰。古い発話ほど軽くする（いまの自分を映すため）。
HALF_LIFE = 40.0   # 何件前で重みが半分になるか


def _decay(rank_from_latest: int) -> float:
    return 0.5 ** (rank_from_latest / HALF_LIFE)


@dataclass
class AnalysisMap:
    entries: int
    concepts: int
    zone_distribution: List[Dict]
    zone_timeline: List[Dict]
    strength_profile: List[Dict]
    virtue_profile: List[Dict]
    balance: Dict[str, float]
    signature: List[str]
    dormant: List[str]
    top_concepts: List[Dict]
    links: List[Dict]
    tendencies: List[str]
    valence: Dict[str, float]
    depth: Dict[str, float]

    def to_dict(self) -> Dict:
        return self.__dict__.copy()


def _zone_distribution(entries: List[Entry]) -> List[Dict]:
    weights: Dict[str, float] = defaultdict(float)
    for e in entries:
        scores = e.zone_scores or {e.zone: 1.0}
        for k, v in scores.items():
            if k in zones.ZONE_BY_KEY:
                weights[k] += v
    total = sum(weights.values()) or 1.0
    out = []
    for z in zones.ZONES:
        w = weights.get(z.key, 0.0)
        out.append({
            "zone": z.key, "jp": z.jp, "en": z.en, "color": z.color,
            "region_jp": z.region_jp, "region_en": z.region_en,
            "weight": round(w, 3), "share": round(w / total, 4),
        })
    return out


def _zone_timeline(entries: List[Entry], days: int = 14) -> List[Dict]:
    by_day: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for e in entries:
        for k, v in (e.zone_scores or {e.zone: 1.0}).items():
            if k in zones.ZONE_BY_KEY:
                by_day[e.day][k] += v
    out = []
    for day in sorted(by_day)[-days:]:
        row = {"day": day, "total": round(sum(by_day[day].values()), 3)}
        row.update({k: round(v, 3) for k, v in by_day[day].items()})
        out.append(row)
    return out


def _strength_profile(entries: List[Entry]) -> List[Dict]:
    """強み = 直接検出されたぶん + 錨を下ろしたゾーンが灯ったぶん。"""
    raw: Dict[str, float] = defaultdict(float)
    n = len(entries)
    for i, e in enumerate(entries):
        w = _decay(n - 1 - i)
        for name, conf in e.strengths.items():
            s = via.resolve(name)
            if s:
                raw[s.jp] += conf * w
        # ゾーン連動：灯ったゾーンに錨を下ろす強みへ、薄く配る
        for zkey, share in (e.zone_scores or {e.zone: 1.0}).items():
            anchored = via.STRENGTHS_BY_ZONE.get(zkey, [])
            if not anchored:
                continue
            spread = 0.28 * share * w / len(anchored)
            for s in anchored:
                raw[s.jp] += spread

    top = max(raw.values()) if raw else 1.0
    out = []
    for s in via.STRENGTHS:
        v = raw.get(s.jp, 0.0)
        out.append({
            **s.to_dict(),
            "score": round(v, 4),
            "normalized": round(v / top, 4) if top else 0.0,
        })
    out.sort(key=lambda d: d["score"], reverse=True)
    return out


def _virtue_profile(profile: List[Dict]) -> List[Dict]:
    agg: Dict[str, float] = defaultdict(float)
    count: Counter = Counter()
    for row in profile:
        agg[row["virtue"]] += row["score"]
        count[row["virtue"]] += 1
    # 徳性ごとに属する強みの数が違う（3〜5）。合計で比べると数の多い徳性が有利に
    # なるので、1強みあたりの平均を徳性のスコアとする。
    means = {v.key: agg[v.key] / max(count[v.key], 1) for v in via.VIRTUES}
    peak = max(means.values(), default=0.0) or 1.0
    out = [
        {
            "key": v.key, "jp": v.jp, "en": v.en, "color": v.color, "zone": v.zone,
            "score": round(means[v.key], 4),
            "total": round(agg[v.key], 4),
            "normalized": round(means[v.key] / peak, 4),
        }
        for v in via.VIRTUES
    ]
    out.sort(key=lambda d: d["score"], reverse=True)
    return out


def _balance(profile: List[Dict]) -> Dict[str, float]:
    """活性化した強みの重心＝2因子バランス。"""
    wx = wy = tot = 0.0
    for row in profile:
        w = row["score"]
        if w <= 0:
            continue
        wx += row["rational"] * w
        wy += row["intra"] * w
        tot += w
    if not tot:
        return {"rational": 0.0, "intra": 0.0, "spread": 0.0}
    cx, cy = wx / tot, wy / tot
    var = sum(
        row["score"] * ((row["rational"] - cx) ** 2 + (row["intra"] - cy) ** 2)
        for row in profile if row["score"] > 0
    ) / tot
    return {"rational": round(cx, 4), "intra": round(cy, 4), "spread": round(var ** 0.5, 4)}


def _concepts(store: MindStore, limit: int = 36) -> Tuple[List[Dict], List[Dict]]:
    top = store.top_concepts(limit)
    keys = {k for k, _ in top}
    nodes = [
        {
            "id": k,
            "weight": v["weight"],
            "zone": v.get("zone", "thought"),
            "color": zones.ZONE_BY_KEY.get(v.get("zone", "thought"), zones.ZONES[0]).color,
        }
        for k, v in top
    ]
    seen = set()
    links = []
    for k, v in top:
        for other, w in v.get("links", {}).items():
            if other in keys:
                pair = tuple(sorted((k, other)))
                if pair not in seen:
                    seen.add(pair)
                    links.append({"source": pair[0], "target": pair[1], "weight": w})
    links.sort(key=lambda d: d["weight"], reverse=True)
    return nodes, links[:120]


def _tendencies(
    entries: List[Entry], dist: List[Dict], profile: List[Dict],
    virtues: List[Dict], balance: Dict[str, float], nodes: List[Dict],
) -> List[str]:
    """数字から直接言えることだけを日本語にする（AIの解釈はここに混ぜない）。"""
    out: List[str] = []
    if not entries:
        return ["まだ観測がありません。ひとこと話しかけると、ここに傾向が現れます。"]

    lead = dist and max(dist, key=lambda d: d["share"])
    if lead and lead["share"] > 0:
        out.append(
            f"対話の {lead['share']*100:.0f}% が「{lead['jp']}」ゾーンで灯っています"
            f"（{lead['region_jp']} / {lead['region_en']}）。"
        )
    quiet = [d for d in dist if d["share"] < 0.05]
    if quiet and len(quiet) <= 3:
        out.append("ほとんど触れていないのは " + "・".join(f"「{d['jp']}」" for d in quiet) + " です。")

    if profile and profile[0]["score"] > 0:
        names = "・".join(r["jp"] for r in profile[:3])
        out.append(f"繰り返し現れている強みは {names}。")

    if virtues and virtues[0]["score"] > 0:
        out.append(f"徳性の重心は「{virtues[0]['jp']}（{virtues[0]['en']}）」に寄っています。")

    r, i = balance["rational"], balance["intra"]
    axis_r = "理性寄り" if r > 0.12 else "感情寄り" if r < -0.12 else "理性と感情の中間"
    axis_i = "個人内（自分に向かう）" if i > 0.12 else "個人間（他者に向かう）" if i < -0.12 else "個人内と個人間の中間"
    out.append(f"2因子バランスは {axis_r} × {axis_i}。")

    if nodes and nodes[0]["weight"] >= 2:
        out.append(f"最も戻ってくる概念は「{nodes[0]['id']}」（{nodes[0]['weight']}回）。")

    vals = [e.valence for e in entries[-20:] if e.valence]
    if len(vals) >= 3:
        avg = sum(vals) / len(vals)
        mood = "心地よい側" if avg > 0.15 else "苦しい側" if avg < -0.15 else "ほぼ中立"
        out.append(f"直近の感情の向きは {mood}（平均 {avg:+.2f}）。")
    return out


def _depth(entries: List[Entry], dist: List[Dict], profile: List[Dict]) -> Dict[str, float]:
    """自己理解がどこまで進んだか。対話を重ねるほど上がる（↻ 継続更新）。"""
    volume = min(1.0, len(entries) / 60.0)
    touched = sum(1 for d in dist if d["share"] >= 0.05)
    breadth = touched / len(zones.ZONES)
    active = sum(1 for r in profile if r["normalized"] >= 0.25)
    strength_cov = active / len(via.STRENGTHS)
    days = len({e.day for e in entries})
    continuity = min(1.0, days / 21.0)
    overall = 0.35 * volume + 0.25 * breadth + 0.2 * strength_cov + 0.2 * continuity
    return {
        "volume": round(volume, 3),
        "breadth": round(breadth, 3),
        "strength_coverage": round(strength_cov, 3),
        "continuity": round(continuity, 3),
        "overall": round(overall, 3),
        "days": days,
    }


def analyze(store: MindStore) -> AnalysisMap:
    entries = store.entries
    dist = _zone_distribution(entries)
    profile = _strength_profile(entries)
    virtues = _virtue_profile(profile)
    balance = _balance(profile)
    nodes, links = _concepts(store)

    active = [r for r in profile if r["score"] > 0]
    vals = [e.valence for e in entries if e.valence]

    return AnalysisMap(
        entries=len(entries),
        concepts=len(store.graph),
        zone_distribution=dist,
        zone_timeline=_zone_timeline(entries),
        strength_profile=profile,
        virtue_profile=virtues,
        balance=balance,
        signature=[r["jp"] for r in profile[:5] if r["score"] > 0],
        dormant=[r["jp"] for r in reversed(profile[-5:])] if len(active) >= 8 else [],
        top_concepts=nodes,
        links=links,
        tendencies=_tendencies(entries, dist, profile, virtues, balance, nodes),
        valence={
            "mean": round(sum(vals) / len(vals), 3) if vals else 0.0,
            "recent": round(sum(vals[-10:]) / len(vals[-10:]), 3) if vals else 0.0,
            "samples": len(vals),
        },
        depth=_depth(entries, dist, profile),
    )
