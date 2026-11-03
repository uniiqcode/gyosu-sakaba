"""予定に入っている、明日以降の1品の日数を数えて出す（お知らせの判断に使う）。

使い方: python3 scripts/remaining.py   → 例: 2
"""
import sys

import gyosu


def remaining(recipes, today):
    return len({r["added"] for r in recipes if r["kind"] == "one" and r["added"] > today})


if __name__ == "__main__":
    print(remaining(gyosu.load_json(gyosu.RECIPES), gyosu.today()))
    sys.exit(0)
