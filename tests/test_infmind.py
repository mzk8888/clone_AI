"""∞Mind のテスト。

Claude を呼ぶ経路はモックで検証する（API キー無しでも通る）。
    python3 -m unittest discover -s tests -v
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from infmind import InfMind, via, zones          # noqa: E402
from infmind.analysis import analyze             # noqa: E402
from infmind.extract import _Extraction, extract  # noqa: E402
from infmind.store import Entry, MindStore       # noqa: E402


def tmp_path() -> Path:
    return Path(tempfile.mkdtemp()) / "mind.json"


# ── Claude のモック ────────────────────────────────────────────────
class FakeMessages:
    def __init__(self, parsed=None, text="モックの返答です。", fail=False):
        self._parsed, self._text, self._fail = parsed, text, fail
        self.parse_calls, self.create_calls = [], []

    def parse(self, **kw):
        self.parse_calls.append(kw)
        if self._fail:
            raise RuntimeError("boom")
        return SimpleNamespace(parsed_output=self._parsed)

    def create(self, **kw):
        self.create_calls.append(kw)
        if self._fail:
            raise RuntimeError("boom")
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=self._text)])


class FakeClient:
    def __init__(self, **kw):
        self.messages = FakeMessages(**kw)


# ── L2 可視化 ──────────────────────────────────────────────────────
class TestZonesAndVia(unittest.TestCase):
    def test_six_zones_with_distinct_colors(self):
        self.assertEqual(len(zones.ZONES), 6)
        self.assertEqual(len({z.color for z in zones.ZONES}), 6)

    def test_tokenizer_drops_grammar_keeps_content(self):
        toks = zones.tokenize("今日はAIオセロの設計を考えていた。楽しかったけど疲れた。")
        self.assertIn("設計", toks)
        self.assertIn("ai", toks)
        self.assertNotIn("えていた", toks)

    def test_zone_scores_normalize_to_one(self):
        s = zones.score_zones("目標を決めて、考えて、嬉しかった")
        self.assertAlmostEqual(sum(s.values()), 1.0, places=4)

    def test_24_strengths_anchor_to_real_zones(self):
        self.assertEqual(len(via.STRENGTHS), 24)
        self.assertEqual(len({s.jp for s in via.STRENGTHS}), 24)
        for s in via.STRENGTHS:
            self.assertIn(s.zone, zones.ZONE_BY_KEY, s.jp)
            self.assertIn(s.virtue, via.VIRTUE_BY_KEY, s.jp)
            self.assertTrue(-1 <= s.rational <= 1 and -1 <= s.intra <= 1, s.jp)

    def test_every_zone_has_at_least_one_strength(self):
        for z in zones.ZONES:
            self.assertTrue(via.STRENGTHS_BY_ZONE.get(z.key), z.jp)

    def test_resolve_by_jp_en_and_glyph(self):
        for name in ("感謝", "Gratitude", "謝"):
            self.assertEqual(via.resolve(name).jp, "感謝")
        self.assertIsNone(via.resolve("存在しない強み"))


# ── L4 統合 / 永続化 ───────────────────────────────────────────────
class TestStore(unittest.TestCase):
    def test_survives_restart(self):
        p = tmp_path()
        a = MindStore(p)
        a.add(Entry(text="設計を考えた", zone="thought", concepts=["設計", "構造"]))
        b = MindStore(p)
        self.assertEqual(len(b), 1)
        self.assertEqual(b.entries[0].text, "設計を考えた")

    def test_co_occurrence_links_are_symmetric(self):
        s = MindStore(tmp_path())
        s.add(Entry(text="x", concepts=["設計", "構造"]))
        self.assertEqual(s.graph["設計"]["links"]["構造"], 1)
        self.assertEqual(s.graph["構造"]["links"]["設計"], 1)

    def test_corrupt_file_does_not_block_startup(self):
        p = tmp_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("{ not json", encoding="utf-8")
        s = MindStore(p)
        self.assertEqual(len(s), 0)
        self.assertTrue(p.with_suffix(".corrupt.json").exists())

    def test_recall_prefers_overlapping_concepts(self):
        s = MindStore(tmp_path())
        s.add(Entry(text="音声認識の話", concepts=["音声認識", "精度"]))
        s.add(Entry(text="料理の話", concepts=["料理", "野菜"]))
        hits = s.recall("音声認識をやりたい")
        self.assertEqual([e.text for e in hits], ["音声認識の話"])


# ── L1→L2 抽出 ────────────────────────────────────────────────────
class TestExtract(unittest.TestCase):
    def test_heuristic_works_without_claude(self):
        sig = extract("毎日コツコツ続けている。目標を達成したい。")
        self.assertEqual(sig.by, "heuristic")
        self.assertIn(sig.zone, zones.ZONE_BY_KEY)
        self.assertIn("粘り強さ", sig.strengths)

    def test_valence_signs(self):
        self.assertGreater(extract("嬉しい。楽しい。最高だった。").valence, 0)
        self.assertLess(extract("辛い。しんどい。不安だ。").valence, 0)

    def test_claude_reading_layers_over_heuristic(self):
        client = FakeClient(parsed=_Extraction(
            zone="values", secondary_zones=["emotion"],
            concepts=["誠実さ", "軸"], strengths=["誠実さ", "Humility"],
            valence=0.4, insight="ごまかさないことが自分の軸だ",
        ))
        sig = extract("正直であることが自分の軸だと思う。", client=client)
        self.assertEqual(sig.by, "claude")
        self.assertEqual(sig.zone, "values")
        self.assertIn("emotion", sig.zone_scores)
        self.assertAlmostEqual(sum(sig.zone_scores.values()), 1.0, places=3)
        self.assertIn("誠実さ", sig.strengths)
        self.assertIn("謙虚さ", sig.strengths)   # 英語名も解決される
        self.assertEqual(sig.insight, "ごまかさないことが自分の軸だ")

    def test_claude_failure_falls_back_silently(self):
        sig = extract("目標を決めた。", client=FakeClient(fail=True))
        self.assertEqual(sig.by, "heuristic")
        self.assertTrue(any("extract_fallback" in n for n in sig.notes))

    def test_unknown_zone_from_model_is_rejected(self):
        client = FakeClient(parsed=_Extraction(
            zone="not_a_zone", concepts=[], strengths=[], valence=0.0, insight="x"))
        sig = extract("考えていた", client=client)
        self.assertIn(sig.zone, zones.ZONE_BY_KEY)

    def test_extraction_request_uses_current_model(self):
        client = FakeClient(parsed=_Extraction(
            zone="thought", concepts=[], strengths=[], valence=0.0, insight="x"))
        extract("考えていた", client=client)
        kw = client.messages.parse_calls[0]
        self.assertEqual(kw["model"], "claude-opus-5")
        self.assertIs(kw["output_format"], _Extraction)


# ── L3 分析 ────────────────────────────────────────────────────────
class TestAnalysis(unittest.TestCase):
    def _mind(self, texts):
        m = InfMind(tmp_path(), api_key="")
        for t in texts:
            m.observe(t)
        return m

    def test_empty_brain_is_safe(self):
        a = analyze(MindStore(tmp_path()))
        self.assertEqual(a.entries, 0)
        self.assertEqual(len(a.zone_distribution), 6)
        self.assertEqual(a.balance["rational"], 0.0)
        self.assertTrue(a.tendencies)

    def test_zone_shares_sum_to_one(self):
        a = self._mind(["考えていた", "嬉しかった", "目標を決めた"]).analysis
        self.assertAlmostEqual(sum(d["share"] for d in a.zone_distribution), 1.0, places=3)

    def test_virtue_score_is_a_per_strength_mean(self):
        """徳性ごとに強みの数が違うので、合計ではなく平均で比べる。"""
        a = self._mind(["毎日コツコツ続けている", "感謝している", "新しい発想が浮かんだ"]).analysis
        scores = [v["score"] for v in a.virtue_profile]
        self.assertEqual(scores, sorted(scores, reverse=True))
        norms = [v["normalized"] for v in a.virtue_profile]
        self.assertEqual(norms, sorted(norms, reverse=True))
        self.assertAlmostEqual(max(norms), 1.0, places=3)

    def test_balance_stays_in_range(self):
        a = self._mind(["チームのみんなに感謝", "一人で考え抜いた", "楽しかった"]).analysis
        self.assertTrue(-1 <= a.balance["rational"] <= 1)
        self.assertTrue(-1 <= a.balance["intra"] <= 1)

    def test_depth_rises_with_dialogue(self):
        """↻ 対話を重ねるほど自己理解が深まる。"""
        few = self._mind(["考えた"]).analysis.depth["overall"]
        many = self._mind([
            "設計を考えた", "嬉しかった", "目標を決めた", "大切にしている軸がある",
            "昔の経験を思い出した", "新しいアイデアが浮かんだ", "毎日続けている",
            "みんなに感謝している", "美しいデザインにしたい", "正直でいたい",
        ]).analysis.depth["overall"]
        self.assertGreater(many, few)

    def test_links_only_connect_listed_concepts(self):
        a = self._mind(["設計と構造を考えた", "音声認識の精度を上げたい"]).analysis
        ids = {c["id"] for c in a.top_concepts}
        for l in a.links:
            self.assertIn(l["source"], ids)
            self.assertIn(l["target"], ids)

    def test_state_is_json_serializable(self):
        json.dumps(self._mind(["考えた", "嬉しかった"]).state(), ensure_ascii=False)


# ── ループ全体 ─────────────────────────────────────────────────────
class TestLoop(unittest.TestCase):
    def test_offline_mind_still_runs_every_layer(self):
        m = InfMind(tmp_path(), api_key="")
        self.assertFalse(m.online)
        self.assertEqual(m.seed(), 8)
        self.assertEqual(m.seed(), 0)          # 二度は蒔かない
        self.assertGreater(m.analysis.entries, 0)
        self.assertIn("脳ゾーンの分布", m.report())
        self.assertTrue(m.greeting())

    def test_converse_runs_the_full_cycle(self):
        m = InfMind(tmp_path(), api_key="", client=FakeClient(
            parsed=_Extraction(zone="goals", concepts=["第二の脳"],
                               strengths=["希望"], valence=0.5, insight="第二の脳を作りたい"),
            text="なるほど。その「第二の脳」は、何を見えるようにしたいのでしょう。",
        ))
        self.assertTrue(m.online)
        before = m.analysis.entries
        r = m.converse("第二の脳を作りたい。")
        self.assertIn("第二の脳", r["reply"])
        self.assertEqual(r["entry"]["zone"], "goals")
        self.assertEqual(r["analysis"]["entries"], before + 1)
        # 対話は脳に残る
        self.assertEqual(m.store.entries[-1].reply, r["reply"])

    def test_context_feeds_prior_state_back_into_the_prompt(self):
        client = FakeClient(
            parsed=_Extraction(zone="thought", concepts=["設計"],
                               strengths=[], valence=0.0, insight="設計を考えている"),
            text="ええ。",
        )
        m = InfMind(tmp_path(), api_key="", client=client)
        m.observe("音声認識の精度を上げたい。")
        m.converse("音声認識の設計をどう詰めるか。")
        system = client.messages.create_calls[-1]["system"]
        self.assertIn("音声認識", system)              # 過去の記憶が戻っている
        self.assertIn("灯っているゾーン", system)
        self.assertEqual(client.messages.create_calls[-1]["model"], "claude-opus-5")

    def test_synthesize_is_grounded_in_the_report(self):
        client = FakeClient(text="**いま灯っているところ** …")
        m = InfMind(tmp_path(), api_key="", client=client)
        m.seed()
        out = m.synthesize()
        self.assertIn("いま灯っているところ", out)
        prompt = client.messages.create_calls[-1]["messages"][0]["content"]
        self.assertIn("脳ゾーンの分布", prompt)

    def test_offline_chat_is_refused_but_observation_is_not(self):
        m = InfMind(tmp_path(), api_key="")
        with self.assertRaises(RuntimeError):
            m.converse("話したい")
        self.assertEqual(m.observe("刻みたい").text, "刻みたい")

    def test_reset_clears_everything(self):
        m = InfMind(tmp_path(), api_key="")
        m.seed()
        m.reset()
        self.assertEqual(m.analysis.entries, 0)
        self.assertEqual(m.analysis.concepts, 0)


if __name__ == "__main__":
    unittest.main()
