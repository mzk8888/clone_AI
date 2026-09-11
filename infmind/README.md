# ∞Mind — 第二の脳型 自己理解システム

思考・感情・目標などを脳ゾーンとして可視化し、VIAの24の強みと連動。
AIチャットと分析マップで、思考傾向・価値観・強みを統合的に把握する。

> IUI lab. / MZK Inc. — 設計: Notion「IUI lab. / Case Studies / ∞Mind」

---

## システム構造（4層 ＋ ループ）

```
  壱 入力 ── AIチャット           対話で思考・感情・目標を言語化する
      │                          agent.py  ·  extract.py
      ▼
  弐 可視化 ─ 脳ゾーンマップ + VIA24  6つのゾーンとして表示し、24の強みと連動させる
      │                          zones.py  ·  via.py  ·  web/brain.js  ·  web/via.js
      ▼
  参 分析 ── 分析マップ            思考傾向・価値観・強みを抽出する
      │                          analysis.py
      ▼
  肆 統合 ── 第二の脳             統合的な自己理解へ
      │                          store.py  ·  mind.py
      └──── ↻ 継続更新 ─────┘   対話を重ねるほど自己理解が深まる
```

ループは `InfMind.observe()` の一回で一周する。刻まれた状態は次の対話の
システムプロンプトへ戻され、文脈が厚くなる。これが ↻ の実体。

---

## 6つの脳ゾーン

配色は京都の伝統色（西陣織の糸目）から取った。

| ゾーン | 領域 | 京都伝統色 | 何を受け取るか |
|---|---|---|---|
| 思考 Thought | 前頭前野 PREFRONTAL | 縹色 `#2792C3` | 筋道を立てて考え、比べ、意味づける |
| 感情 Emotion | 大脳辺縁系 LIMBIC | 今様色 `#D05A6E` | 心が動いた瞬間を受け取る |
| 目標 Goals | 頭頂葉 PARIETAL | 若竹色 `#68BE8D` | 行き先を定め、進み続ける |
| 価値観 Values | 前帯状皮質 CINGULATE | 山吹色 `#F8B500` | 譲れないものが立ち上がる |
| 記憶 Memory | 海馬 HIPPOCAMPUS | 藤紫 `#A59ACA` | 過去を呼び戻し、いま結び直す |
| アイデア Ideas | 側頭葉 TEMPORAL | 浅葱色 `#00A3AF` | まだ形のないものが芽吹く |

## VIA 24の強みとの連動

24の強みはそれぞれ**1つのゾーンに錨を下ろす**。そのゾーンが灯ると、錨を下ろす
強みも一緒に活性化する。これが「脳ゾーンマップと強みの連動」の実装。

- 6徳性（知恵・勇気・人間性・正義・節制・超越性）にも重心が出る
- 2因子マップ: 理性⇄感情 × 個人内⇄個人間 に24の強みを散らし、活性の重心を打つ
- 強みスコアは新しい発話ほど重い（半減期 40 件）。いまの自分を映すため

---

## 使う

```bash
pip install -r infmind/requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...      # 無くても全層が動く（後述）

python3 -m infmind.cli serve             # Web UI  → http://127.0.0.1:8800
python3 -m infmind.cli                   # 端末で対話
python3 -m infmind.cli map               # 分析マップを表示
python3 -m infmind.cli synth             # 統合的な自己理解を書き起こす
```

Python から：

```python
from infmind import InfMind

mind = InfMind()
mind.converse("第二の脳を作りたい。自分の思考が自分で見えるようにしたい。")
print(mind.report())
print(mind.synthesize())
```

### API キーが無いときの挙動

対話（L1）だけが止まり、**他の3層はすべて動く**。送った言葉は辞書ベースで
解析され、脳ゾーン・24の強み・分析マップに反映される。UI では「送る」が
観測だけを刻む経路に切り替わる。

| | Claude 接続 | 未接続 |
|---|---|---|
| 発話の構造化 | 意味で読む | 辞書で読む |
| 脳ゾーンマップ | ○ | ○ |
| VIA 24 / 2因子 | ○ | ○ |
| 分析マップ | ○ | ○ |
| AIチャット | ○ | × |
| 統合（語り） | ○ | × |

---

## HTTP API

| | | |
|---|---|---|
| `GET` | `/api/state` | ゾーン・VIAカタログ・分析マップ・直近の観測 |
| `GET` | `/api/analysis` | 分析マップのみ |
| `GET` | `/api/report` | 分析マップを読める文章表で |
| `GET` | `/api/greeting` | 時刻と脳の状態に応じた挨拶 |
| `POST` | `/api/chat` | 対話1往復。刻んで分析マップまで返す |
| `POST` | `/api/observe` | 対話せず観測だけ刻む（キー不要） |
| `POST` | `/api/synthesize` | 統合的な自己理解を書き起こす |
| `POST` | `/api/connect` | 実行中に API キーを渡す |
| `DELETE` | `/api/brain` | 脳を消す |

API キーはサーバに留まり、ブラウザへは渡さない。

---

## 保存先

既定 `~/.infmind/mind.json`（`INFMIND_DATA` で変更可）。書き込みは
一時ファイル＋`os.replace` の原子的置換。壊れたファイルは
`.corrupt.json` へ退避して起動は止めない。

`INFMIND_SEED=0` を渡すと、空の脳に初回の種を蒔かない。

---

## 構成

```
infmind/
  zones.py      L2  6つの脳ゾーン・京都の配色・日本語トークナイザ
  via.py        L2  VIA 24の強み / 6徳性 / ゾーンへの錨 / 2因子座標
  extract.py    L1→L2  発話の構造化（Claude ↔ 辞書、同じ Signal を返す）
  agent.py      L1  対話・挨拶・統合の語り
  analysis.py   L3  分析マップ（分布・強み・徳性・2因子・傾向・深度）
  store.py      L4  Entry の永続化と概念グラフ
  mind.py       ↻   4層を束ねるループ本体
  server.py         FastAPI + 静的配信
  cli.py            端末から
  web/              index.html · style.css · app.js · brain.js · via.js
```

## テスト

```bash
python3 -m unittest discover -s tests -v
```

Claude を呼ぶ経路はモッククライアントで検証するので、API キー無しで全件通る。
