"""∞Mind — 第二の脳型 自己理解システム (IUI lab. / MZK Inc.)

思考・感情・目標などを脳ゾーンとして可視化し、VIAの24の強みと連動させる。
AIチャットと分析マップで、思考傾向・価値観・強みを統合的に把握する。

    L1 入力   : AIチャット          → agent.py
    L2 可視化 : 脳ゾーン + VIA24     → zones.py / via.py
    L3 分析   : 分析マップ            → analysis.py
    L4 統合   : 第二の脳             → store.py / mind.py
    ↻  継続更新: 対話を重ねるほど深まる → mind.InfMind.observe
"""

from .mind import InfMind

__all__ = ["InfMind"]
__version__ = "0.1.0"
