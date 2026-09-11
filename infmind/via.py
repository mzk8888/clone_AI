"""∞Mind — L2 可視化層 / VIA 24の強み.

設計上、24の強みは「脳ゾーンと連動」する。各強みは 1つのゾーンに錨を下ろし、
そのゾーンが発火したとき一緒に活性化する。これが脳ゾーンマップと強みを繋ぐ軸。

2因子マップの座標系（設計図 "VIA 2因子バランスマップ" に準拠）:
    rational : 感情(-1)  ←→  理性(+1)
    intra    : 個人間(-1) ←→  個人内(+1)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class Virtue:
    key: str
    jp: str
    en: str
    color: str
    zone: str   # その徳性が最も強く結びつく脳ゾーン


VIRTUES: Tuple[Virtue, ...] = (
    Virtue("wisdom",        "知恵",   "Wisdom",        "#2792C3", "thought"),
    Virtue("courage",       "勇気",   "Courage",       "#68BE8D", "goals"),
    Virtue("humanity",      "人間性", "Humanity",      "#D05A6E", "emotion"),
    Virtue("justice",       "正義",   "Justice",       "#F8B500", "values"),
    Virtue("temperance",    "節制",   "Temperance",    "#A59ACA", "memory"),
    Virtue("transcendence", "超越性", "Transcendence", "#00A3AF", "ideas"),
)

VIRTUE_BY_KEY: Dict[str, Virtue] = {v.key: v for v in VIRTUES}


@dataclass(frozen=True)
class Strength:
    key: str            # 一文字の象徴（西陣織の紋のように並べる）
    jp: str
    en: str
    virtue: str
    zone: str           # 錨を下ろす脳ゾーン
    rational: float     # -1 感情 .. +1 理性
    intra: float        # -1 個人間 .. +1 個人内
    definition: str
    under: str          # 不足したとき
    over: str           # 過剰になったとき
    related: Tuple[str, ...]
    keywords: Tuple[str, ...]

    def to_dict(self) -> Dict:
        return {
            "key": self.key, "jp": self.jp, "en": self.en,
            "virtue": self.virtue, "zone": self.zone,
            "rational": self.rational, "intra": self.intra,
            "definition": self.definition, "under": self.under, "over": self.over,
            "related": list(self.related),
        }


STRENGTHS: Tuple[Strength, ...] = (
    # ── 知恵 Wisdom ────────────────────────────────────────────────
    Strength("創", "創造性", "Creativity", "wisdom", "ideas", 0.10, 0.60,
             "独自性と実用性を兼ね備えた新しいものを生み出す力。既存の枠に収まらない発想で問題を解く。",
             "守旧・発想の停滞", "奇抜さが独走し実用を失う",
             ("好奇心", "勇敢さ", "大局観", "熱意"),
             ("創", "つくり", "作っ", "発明", "デザイン", "独自", "工夫", "オリジナル", "生み出")),
    Strength("好", "好奇心", "Curiosity", "wisdom", "ideas", 0.15, 0.45,
             "新しい経験・知識・アイデアへ開かれた関心。曖昧さを楽しみ、探索そのものに喜びを見出す。",
             "無関心・退屈", "気が散る・深掘り不足",
             ("創造性", "向学心", "大局観", "熱意"),
             ("気になる", "知りたい", "調べ", "探索", "興味", "面白そう", "なんで", "どうして")),
    Strength("判", "判断力", "Judgment", "wisdom", "thought", 0.85, 0.30,
             "物事を多角的に検討し、証拠に基づいて結論を出す。自分の信念すら検証対象にする。",
             "優柔不断・鵜呑み", "懐疑が過剰で決めきれない",
             ("向学心", "大局観", "誠実さ", "思慮深さ"),
             ("判断", "検証", "根拠", "客観", "だとすると", "見極め", "冷静", "妥当")),
    Strength("向", "向学心", "Love of Learning", "wisdom", "thought", 0.60, 0.62,
             "スキルと知識の習得そのものに情熱を持つ。学ぶ過程が報酬になる。",
             "惰性・機械的作業", "知識の披瀝・実践の欠如",
             ("好奇心", "判断力", "創造性", "誠実さ"),
             ("勉強", "学習", "学ぶ", "習得", "理解した", "読んだ", "インプット", "身につ")),
    Strength("観", "大局観", "Perspective", "wisdom", "memory", 0.62, 0.18,
             "自分と他者の双方にとって意味のある視座を提供する。部分と全体を同時に見る力。",
             "視野の狭さ・短絡", "説教的・上から目線",
             ("判断力", "誠実さ", "向学心", "社会的知性"),
             ("全体", "俯瞰", "長期", "視点", "本質", "つまり", "結局", "文脈")),
    # ── 勇気 Courage ───────────────────────────────────────────────
    Strength("敢", "勇敢さ", "Bravery", "courage", "goals", 0.30, 0.38,
             "脅威・困難・反対に怯まず、正しいと信じることを行う。恐れの不在ではなく、恐れの中での行動。",
             "臆病・回避", "無謀・リスク軽視",
             ("誠実さ", "粘り強さ", "熱意", "大局観"),
             ("挑戦", "怖いけど", "踏み出", "思い切", "立ち向か", "勇気", "リスク")),
    Strength("粘", "粘り強さ", "Perseverance", "courage", "goals", 0.55, 0.35,
             "始めたことを完遂する力。障害があっても軌道修正しながら前進し続ける。",
             "怠惰・途中放棄", "撤退できない・固執",
             ("熱意", "希望", "勇敢さ", "誠実さ"),
             ("続け", "やり切", "諦め", "完遂", "毎日", "継続", "コツコツ", "最後まで")),
    Strength("誠", "誠実さ", "Honesty", "courage", "values", 0.40, 0.10,
             "真実を語り、自分の感情と行動に責任を持つ。演じるのではなく、そのまま在る。",
             "欺瞞・見栄", "無遠慮・配慮の欠如",
             ("勇敢さ", "大局観", "公平さ", "自律"),
             ("正直", "誠実", "本音", "ごまかさ", "責任", "素直", "隠さず")),
    Strength("熱", "熱意", "Zest", "courage", "emotion", -0.25, 0.22,
             "活力をもって人生に取り組む。中途半端にせず、全身で関わる。",
             "無気力・疲弊", "燃え尽き・過活動",
             ("希望", "感謝", "好奇心", "愛情"),
             ("わくわく", "楽しい", "夢中", "テンション", "エネルギ", "没頭", "熱中")),
    # ── 人間性 Humanity ────────────────────────────────────────────
    Strength("愛", "愛情", "Love", "humanity", "emotion", -0.72, -0.62,
             "他者との深い相互的な絆を築き、大切にする。与えることも受け取ることもできる。",
             "孤立・親密さの回避", "依存・境界の消失",
             ("親切心", "感謝", "熱意", "チームワーク"),
             ("大好き", "family", "家族", "恋", "大切な人", "絆", "愛")),
    Strength("親", "親切心", "Kindness", "humanity", "emotion", -0.45, -0.70,
             "見返りを求めず他者のために行動する。思いやりを行為に変える。",
             "冷淡・無関心", "過干渉・自己犠牲",
             ("愛情", "感謝", "公平さ", "チームワーク"),
             ("手伝", "助け", "優しく", "思いやり", "喜んで", "支え", "気づかい")),
    Strength("社", "社会的知性", "Social Intelligence", "humanity", "emotion", -0.35, -0.55,
             "自分と他者の感情や動機を読み取り、場に応じて適切に振る舞う。",
             "場の読めなさ", "読みすぎ・操作的",
             ("大局観", "愛情", "親切心", "寛容さ"),
             ("空気", "察し", "相手の気持ち", "雰囲気", "場の", "汲み取")),
    # ── 正義 Justice ───────────────────────────────────────────────
    Strength("団", "チームワーク", "Teamwork", "justice", "values", 0.15, -0.78,
             "集団の一員として忠実に役割を果たす。自分の成功より共同の成果を優先できる。",
             "個人プレー・非協力", "同調圧力への服従",
             ("公平さ", "リーダーシップ", "親切心", "感謝"),
             ("チーム", "みんなで", "協力", "一緒に", "仲間", "共同", "メンバー")),
    Strength("公", "公平さ", "Fairness", "justice", "values", 0.62, -0.62,
             "すべての人を偏りなく扱う。感情や利害に左右されず原則に基づいて判断する。",
             "えこひいき・偏見", "杓子定規・文脈無視",
             ("チームワーク", "誠実さ", "リーダーシップ", "寛容さ"),
             ("公平", "平等", "偏り", "フェア", "えこひいき", "同じ基準")),
    Strength("導", "リーダーシップ", "Leadership", "justice", "goals", 0.30, -0.70,
             "集団の活動を組織し、メンバーが力を発揮できるよう動かす。良い関係を保ちながら成果を出す。",
             "放任・責任回避", "支配的・統制過多",
             ("公平さ", "チームワーク", "社会的知性", "熱意"),
             ("まとめ", "引っ張", "巻き込", "旗振り", "率い", "リード", "方針")),
    # ── 節制 Temperance ────────────────────────────────────────────
    Strength("寛", "寛容さ", "Forgiveness", "temperance", "memory", -0.30, -0.35,
             "過ちを犯した人を許し、報復を手放す。人は変われると信じる。",
             "恨みの保持・報復", "甘さ・責任の免除",
             ("謙虚さ", "社会的知性", "愛情", "感謝"),
             ("許し", "水に流", "気にしない", "わだかまり", "手放", "受け入れ")),
    Strength("謙", "謙虚さ", "Humility", "temperance", "values", 0.20, -0.15,
             "成果を誇示せず、自分を等身大に見る。自分を低く見るのではなく、自分にこだわらない。",
             "傲慢・自己過信", "自己卑下・過小評価",
             ("寛容さ", "感謝", "思慮深さ", "誠実さ"),
             ("まだまだ", "教えて", "おかげ", "謙虚", "自分なんて", "学ばせ")),
    Strength("慮", "思慮深さ", "Prudence", "temperance", "thought", 0.72, 0.42,
             "選択に慎重で、不要なリスクを避ける。長期の結果を見据えて今を決める。",
             "衝動的・無計画", "慎重すぎて機会を逃す",
             ("自律", "謙虚さ", "判断力", "誠実さ"),
             ("慎重", "リスク", "念のため", "備え", "計画的", "先を見", "様子見")),
    Strength("律", "自律", "Self-Regulation", "temperance", "goals", 0.55, 0.78,
             "感情・欲求・行動を自ら調整する。衝動ではなく選択で動く。",
             "自制の欠如・過剰行動", "禁欲的・硬直",
             ("思慮深さ", "粘り強さ", "誠実さ", "謙虚さ"),
             ("我慢", "自制", "ルーティン", "整え", "節制", "コントロール", "律し")),
    # ── 超越性 Transcendence ───────────────────────────────────────
    Strength("美", "審美眼", "Appreciation of Beauty", "transcendence", "ideas", -0.55, 0.55,
             "自然・芸術・技巧・卓越性に美を見出し、感動する。日常の中の質に気づく。",
             "鑑賞力の鈍麻", "完璧主義・批評家気質",
             ("感謝", "好奇心", "創造性", "希望"),
             ("綺麗", "美し", "デザイン", "見とれ", "感動", "洗練", "美意識")),
    Strength("謝", "感謝", "Gratitude", "transcendence", "memory", -0.48, -0.20,
             "良いことに気づき、それを当然と思わない。受け取ったものを言葉と行動で返す。",
             "不満・当然視", "形式的な感謝の反復",
             ("審美眼", "希望", "愛情", "親切心"),
             ("ありがた", "感謝", "おかげ", "恵まれ", "thank", "嬉しかった")),
    Strength("望", "希望", "Hope", "transcendence", "goals", -0.15, 0.50,
             "良い未来を期待し、それを実現する道筋を描いて動く。楽観と行動が結びついている。",
             "悲観・無力感", "現実を見ない楽観",
             ("熱意", "感謝", "粘り強さ", "勇敢さ"),
             ("きっと", "楽しみ", "未来", "いずれ", "希望", "なんとかなる", "前向き")),
    Strength("笑", "ユーモア", "Humor", "transcendence", "emotion", -0.58, -0.72,
             "遊び心をもって物事に向き合い、他者に笑いをもたらす。緊張を緩める力。",
             "深刻すぎる・硬さ", "茶化し・逃避",
             ("社会的知性", "愛情", "好奇心", "熱意"),
             ("笑", "冗談", "ウケ", "ネタ", "ふざけ", "遊び心", "ツッコミ")),
    Strength("霊", "超越", "Spirituality", "transcendence", "values", -0.30, 0.72,
             "より大きな全体の中での自分の位置を感じ、人生の意味と目的を持つ。",
             "虚無感・意味の喪失", "教条的・現実離れ",
             ("感謝", "審美眼", "希望", "寛容さ"),
             ("意味", "使命", "生き方", "人生", "何のため", "在り方", "祈")),
)

STRENGTH_BY_JP: Dict[str, Strength] = {s.jp: s for s in STRENGTHS}
STRENGTH_BY_KEY: Dict[str, Strength] = {s.key: s for s in STRENGTHS}

# ゾーン → そこに錨を下ろす強み
STRENGTHS_BY_ZONE: Dict[str, List[Strength]] = {}
for _s in STRENGTHS:
    STRENGTHS_BY_ZONE.setdefault(_s.zone, []).append(_s)


def detect(text: str) -> Dict[str, float]:
    """テキストに現れた強みを 強みJP名 -> 確信度(0..1) で返す。"""
    found: Dict[str, float] = {}
    for s in STRENGTHS:
        hits = sum(1 for kw in s.keywords if kw in text)
        if hits:
            found[s.jp] = round(min(1.0, 0.45 + 0.2 * hits), 3)
    return found


def resolve(name: str) -> Strength | None:
    """日本語名・英語名・象徴文字のいずれからでも強みを引く。"""
    if name in STRENGTH_BY_JP:
        return STRENGTH_BY_JP[name]
    if name in STRENGTH_BY_KEY:
        return STRENGTH_BY_KEY[name]
    low = name.strip().lower()
    for s in STRENGTHS:
        if s.en.lower() == low:
            return s
    return None


def catalog() -> Dict:
    """フロントエンドへ渡す静的カタログ。"""
    return {
        "virtues": [
            {"key": v.key, "jp": v.jp, "en": v.en, "color": v.color, "zone": v.zone}
            for v in VIRTUES
        ],
        "strengths": [s.to_dict() for s in STRENGTHS],
    }
