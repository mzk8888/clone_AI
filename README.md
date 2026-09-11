# Inf-Mind

**∞Mind** — 第二の脳型 自己理解システム。および、そこへ至るまでの制作物。

IUI lab. / MZK Inc.

---

## ∞Mind — [`infmind/`](infmind/)

思考・感情・目標などを脳ゾーンとして可視化し、VIAの24の強みと連動。
AIチャットと分析マップで、思考傾向・価値観・強みを統合的に把握する。

```
壱 入力 → 弐 可視化 → 参 分析 → 肆 統合 ─┐
  AIチャット  脳ゾーン+VIA24  分析マップ  第二の脳 │
  └──────────── ↻ 継続更新 ──────────────┘
```

```bash
pip install -r infmind/requirements.txt
python3 -m infmind.cli serve       # → http://127.0.0.1:8800
```

詳細は [infmind/README.md](infmind/README.md)。

---

## その他の制作物

| | |
|---|---|
| [`mizuki_clone/`](mizuki_clone/) | ∞Mind の前身。Streamlit + Claude API の第二の脳プロトタイプ |
| [`neural.html`](neural.html) | 単体で動く脳ビジュアライザ。点群の神経網・音声オーブ・VIA24 |
| [`othello/`](othello/) | AIオセロ。ミニマックス + α-β 枝刈り（Streamlit） |
| [`ai-speech-labeling/`](ai-speech-labeling/) | Whisper 音声認識 + Label Studio ラベリング |
| [`GPT-API_LLM/`](GPT-API_LLM/) | GPT API のチャットアプリ（Streamlit） |

`mizuki_clone/` と `neural.html` は ∞Mind の原型にあたる試作で、そのまま残してある。
現行の実装は `infmind/`。
