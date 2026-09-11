"""∞Mind — L4 統合層 / 永続化.

対話ひとつひとつを Entry として残し、概念どうしの繋がりをグラフに畳み込む。
セッションを跨いで残ることが「第二の脳」の条件なので、書き込みは原子的に行う。
"""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_PATH = Path(
    os.environ.get("INFMIND_DATA", Path.home() / ".infmind" / "mind.json")
)


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


@dataclass
class Entry:
    """対話 1 往復から抽出された、脳に刻まれる 1 単位。"""

    text: str                                   # 本人の発話
    reply: str = ""                             # ∞Mind の応答
    zone: str = "thought"                       # 主ゾーン
    zone_scores: Dict[str, float] = field(default_factory=dict)
    concepts: List[str] = field(default_factory=list)
    strengths: Dict[str, float] = field(default_factory=dict)  # 強みJP名 -> 確信度
    valence: float = 0.0                        # -1 .. +1
    insight: str = ""                           # 言語化された一文
    source: str = "dialogue"
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict) -> "Entry":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in known})

    @property
    def day(self) -> str:
        return self.created_at[:10]


class MindStore:
    """entries とグラフを 1 ファイルに保持する。"""

    VERSION = 1

    def __init__(self, path: Path | str | None = None):
        self.path = Path(path) if path else DEFAULT_PATH
        self.entries: List[Entry] = []
        self.graph: Dict[str, Dict] = {}   # concept -> {weight, zone, links:{other:count}}
        self.meta: Dict = {}
        self.load()

    # ── 永続化 ────────────────────────────────────────────────────
    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            # 壊れたファイルで起動を止めない。退避して空から始める。
            try:
                self.path.rename(self.path.with_suffix(".corrupt.json"))
            except OSError:
                pass
            return
        self.entries = [Entry.from_dict(e) for e in data.get("entries", [])]
        self.graph = data.get("graph", {})
        self.meta = data.get("meta", {})

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": self.VERSION,
            "updated_at": _now(),
            "entries": [e.to_dict() for e in self.entries],
            "graph": self.graph,
            "meta": self.meta,
        }
        fd, tmp = tempfile.mkstemp(dir=str(self.path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False, indent=2)
            os.replace(tmp, self.path)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise

    def reset(self) -> None:
        self.entries = []
        self.graph = {}
        self.meta = {}
        self.path.unlink(missing_ok=True)

    # ── 書き込み ──────────────────────────────────────────────────
    def add(self, entry: Entry) -> Entry:
        self.entries.append(entry)
        self._weave(entry)
        self.save()
        return entry

    def _weave(self, entry: Entry) -> None:
        """概念を織り込む。同じ発話に現れた語どうしを結ぶ（西陣織の緯糸）。"""
        concepts = entry.concepts
        for c in concepts:
            node = self.graph.setdefault(c, {"weight": 0, "zone": entry.zone, "links": {}})
            node["weight"] += 1
            node["zone"] = entry.zone  # 最新の文脈でゾーンを更新
        for i, a in enumerate(concepts):
            for b in concepts[i + 1:]:
                self.graph[a]["links"][b] = self.graph[a]["links"].get(b, 0) + 1
                self.graph[b]["links"][a] = self.graph[b]["links"].get(a, 0) + 1

    # ── 読み出し ──────────────────────────────────────────────────
    def recent(self, n: int = 5) -> List[Entry]:
        return self.entries[-n:]

    def recall(self, query: str, n: int = 4) -> List[Entry]:
        """問いに関係する記憶を、概念の重なりと近さで拾う。"""
        from .zones import tokenize

        keys = set(tokenize(query))
        if not keys:
            return []
        scored: List[tuple[float, Entry]] = []
        for idx, e in enumerate(self.entries):
            overlap = len(keys & set(e.concepts))
            if not overlap:
                continue
            recency = idx / max(len(self.entries) - 1, 1)   # 新しいほど 1 に近い
            scored.append((overlap + 0.4 * recency, e))
        scored.sort(key=lambda t: t[0], reverse=True)
        return [e for _, e in scored[:n]]

    def top_concepts(self, n: int = 40) -> List[tuple[str, Dict]]:
        return sorted(self.graph.items(), key=lambda kv: kv[1]["weight"], reverse=True)[:n]

    def counts_by(self, attr: str) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for e in self.entries:
            out[getattr(e, attr)] = out.get(getattr(e, attr), 0) + 1
        return out

    def __len__(self) -> int:
        return len(self.entries)
