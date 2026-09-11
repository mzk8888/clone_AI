"""∞Mind — 端末から使う."""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .mind import InfMind

BANNER = f"""\
   ∞Mind  v{__version__}
   A SECOND BRAIN FOR SELF-UNDERSTANDING   —   IUI lab.
"""

HELP = """\
  そのまま入力    対話する（要 ANTHROPIC_API_KEY）
  :note <text>   対話せずに観測だけ刻む
  :map           分析マップを表示
  :synth         統合的な自己理解を書き起こす
  :seed          初回の種を蒔く
  :reset         脳を消す
  :q             終了
"""


def _repl(mind: InfMind) -> int:
    print(BANNER)
    print(f"  Claude: {'接続' if mind.online else '未接続（辞書ベースで動作）'}"
          f"   観測 {mind.analysis.entries} 件\n")
    print(mind.greeting(), "\n")
    print(HELP)
    while True:
        try:
            line = input("∞ ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not line:
            continue
        if line in (":q", ":quit", ":exit"):
            return 0
        if line in (":h", ":help"):
            print(HELP)
        elif line == ":map":
            print(mind.report())
        elif line == ":synth":
            if not mind.online:
                print("  ANTHROPIC_API_KEY が必要です。")
            else:
                print(mind.synthesize())
        elif line == ":seed":
            print(f"  {mind.seed()} 件を刻みました。")
        elif line == ":reset":
            mind.reset()
            print("  消しました。")
        elif line.startswith(":note "):
            e = mind.observe(line[6:].strip(), source="note")
            print(f"  刻みました [{e.zone}] {', '.join(e.concepts[:5])}")
        elif not mind.online:
            print("  Claude 未接続です。:note で観測のみ刻めます。")
        else:
            try:
                print("\n" + mind.converse(line)["reply"] + "\n")
            except Exception as exc:
                print(f"  失敗しました: {exc}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="infmind", description="∞Mind — 第二の脳型 自己理解システム")
    ap.add_argument("--data", help="保存先 JSON（既定 ~/.infmind/mind.json）")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("chat", help="対話する（既定）")
    sub.add_parser("map", help="分析マップを表示して終了")
    sub.add_parser("synth", help="統合的な自己理解を書き起こして終了")
    sub.add_parser("seed", help="初回の種を蒔いて終了")
    srv = sub.add_parser("serve", help="Web UI を起動")
    srv.add_argument("--host", default="127.0.0.1")
    srv.add_argument("--port", type=int, default=8800)
    srv.add_argument("--reload", action="store_true")
    args = ap.parse_args(argv)

    if args.cmd == "serve":
        from .server import run
        print(BANNER)
        print(f"  http://{args.host}:{args.port}\n")
        run(args.host, args.port, args.reload)
        return 0

    mind = InfMind(args.data)
    if args.cmd == "map":
        print(mind.report())
    elif args.cmd == "synth":
        if not mind.online:
            print("ANTHROPIC_API_KEY が必要です。", file=sys.stderr)
            return 1
        print(mind.synthesize())
    elif args.cmd == "seed":
        print(f"{mind.seed()} 件を刻みました。")
    else:
        return _repl(mind)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
