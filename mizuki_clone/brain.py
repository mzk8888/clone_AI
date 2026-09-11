"""
Second Brain — Mizuki's persistent memory and concept knowledge graph.
Stores data in ~/.mizuki_brain.json, survives across sessions.
"""

import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

BRAIN_FILE = Path(__file__).parent / "mizuki_brain.json"

# Auto-classification keywords (Japanese + English)
CATEGORIES: Dict[str, List[str]] = {
    "技術":     ["python", "ai", "機械学習", "プログラミング", "コード", "api",
                 "model", "neural", "llm", "claude", "gpt", "streamlit", "git",
                 "アルゴリズム", "データ", "学習", "トレーニング"],
    "アイデア": ["アイデア", "考え", "思いつき", "もしかして", "どうかな",
                 "案", "提案", "したら", "できそう", "面白"],
    "感情":     ["嬉しい", "悲しい", "楽しい", "辛い", "不安", "わくわく",
                 "好き", "嫌い", "疲れ", "すごい", "やばい"],
    "目標":     ["目標", "やりたい", "したい", "作りたい", "なりたい",
                 "目指す", "夢", "計画", "予定", "挑戦"],
    "学習":     ["勉強", "学ぶ", "学習", "理解", "覚え", "知識", "スキル",
                 "読んだ", "調べた", "わかった"],
    "日常":     ["今日", "明日", "昨日", "朝", "夜", "食事", "睡眠", "天気",
                 "起きた", "寝た", "食べた"],
    "人間関係": ["友達", "家族", "同僚", "先生", "みんな", "誰か", "話した"],
}

STOP_WORDS = {
    "は", "が", "を", "に", "で", "と", "から", "まで", "より", "の", "も",
    "や", "か", "です", "ます", "した", "して", "する", "ある", "いる", "ない",
    "この", "その", "あの", "どの", "こと", "もの", "よう", "だ", "the", "a",
    "an", "is", "are", "was", "were", "be", "been", "have", "has", "do",
    "does", "that", "it", "its", "to", "of", "in", "for", "on", "with",
}


class Memory:
    def __init__(
        self,
        content: str,
        tags: List[str],
        category: str,
        timestamp: Optional[str] = None,
        source: str = "conversation",
    ):
        self.content = content
        self.tags = tags
        self.category = category
        self.timestamp = timestamp or datetime.now().isoformat()
        self.source = source

    def to_dict(self) -> Dict:
        return {
            "content": self.content,
            "tags": self.tags,
            "category": self.category,
            "timestamp": self.timestamp,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "Memory":
        return cls(
            d["content"], d["tags"], d["category"],
            d.get("timestamp"), d.get("source", "conversation"),
        )


class SecondBrain:
    def __init__(self):
        self.memories: List[Memory] = []
        # concept -> {weight: int, connections: {concept: int}}
        self.graph: Dict[str, Dict] = {}
        self._load()

    # ── Persistence ──────────────────────────────────────────────────

    def _load(self):
        if BRAIN_FILE.exists():
            try:
                data = json.loads(BRAIN_FILE.read_text(encoding="utf-8"))
                self.memories = [Memory.from_dict(m) for m in data.get("memories", [])]
                self.graph = data.get("graph", {})
            except Exception:
                pass

    def _save(self):
        data = {
            "memories": [m.to_dict() for m in self.memories],
            "graph": self.graph,
            "updated_at": datetime.now().isoformat(),
        }
        BRAIN_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── NLP helpers ───────────────────────────────────────────────────

    def extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful tokens from text."""
        # Pure kanji (2+), katakana (3+), long hiragana (4+), English (4+)
        tokens = re.findall(r"[一-龯]{2,}|[ァ-ン]{3,}|[ぁ-ん]{4,}|[a-zA-Z]{4,}", text.lower())
        hiragana_verb_stops = {
            "した", "して", "する", "ある", "いる", "ない", "なる", "でき", "から",
            "まで", "ため", "もの", "こと", "よう", "たり", "たら", "れる", "られ",
            "られる", "せる", "させ", "いた", "おも", "はな", "きた", "いう",
        }
        filtered = {
            t for t in tokens
            if t not in STOP_WORDS and t not in hiragana_verb_stops
        }
        return list(filtered)[:12]

    def classify(self, text: str) -> str:
        text_lower = text.lower()
        for cat, kws in CATEGORIES.items():
            if any(kw in text_lower for kw in kws):
                return cat
        return "その他"

    # ── Graph update ──────────────────────────────────────────────────

    def _update_graph(self, keywords: List[str]):
        for kw in keywords:
            if kw not in self.graph:
                self.graph[kw] = {"weight": 0, "connections": {}}
            self.graph[kw]["weight"] += 1

        for i, k1 in enumerate(keywords):
            for k2 in keywords[i + 1:]:
                self.graph[k1]["connections"][k2] = self.graph[k1]["connections"].get(k2, 0) + 1
                if k2 not in self.graph:
                    self.graph[k2] = {"weight": 0, "connections": {}}
                self.graph[k2]["connections"][k1] = self.graph[k2]["connections"].get(k1, 0) + 1

    # ── Public API ────────────────────────────────────────────────────

    def remember(self, content: str, source: str = "conversation") -> Memory:
        keywords = self.extract_keywords(content)
        category = self.classify(content)
        mem = Memory(content=content, tags=keywords, category=category, source=source)
        self.memories.append(mem)
        self._update_graph(keywords)
        self._save()
        return mem

    def recall(self, query: str, n: int = 4) -> List[Memory]:
        """Return most relevant memories for a query."""
        keywords = set(self.extract_keywords(query))
        scored = []
        for mem in self.memories:
            score = sum(1 for kw in keywords if kw in mem.tags or kw in mem.content.lower())
            if score > 0:
                scored.append((score, mem))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored[:n]]

    def recent(self, n: int = 5) -> List[Memory]:
        return self.memories[-(n):]

    def top_concepts(self, n: int = 30) -> List[Tuple[str, Dict]]:
        return sorted(self.graph.items(), key=lambda x: x[1]["weight"], reverse=True)[:n]

    def category_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = defaultdict(int)
        for m in self.memories:
            counts[m.category] += 1
        return dict(counts)

    def stats(self) -> Dict:
        return {
            "memories": len(self.memories),
            "concepts": len(self.graph),
            "categories": self.category_counts(),
        }

    def brain_map_data(self, max_nodes: int = 35) -> Dict:
        """Return nodes + edges for Plotly network visualization."""
        top = self.top_concepts(max_nodes)
        if not top:
            return {"nodes": [], "edges": []}

        top_keys = {k for k, _ in top}
        cat_map: Dict[str, str] = {}
        for text, kws in CATEGORIES.items():
            for kw in kws:
                cat_map[kw] = text

        nodes = []
        for k, v in top:
            cat = "その他"
            for kw, c in cat_map.items():
                if kw in k:
                    cat = c
                    break
            nodes.append({"id": k, "weight": v["weight"], "category": cat})

        edges = []
        seen: set = set()
        for k, v in top:
            for conn, w in v["connections"].items():
                if conn in top_keys:
                    key = tuple(sorted([k, conn]))
                    if key not in seen:
                        edges.append({"source": k, "target": conn, "weight": w})
                        seen.add(key)

        return {"nodes": nodes, "edges": edges}
