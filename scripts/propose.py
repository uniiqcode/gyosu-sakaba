"""ストックから7日分の候補を選び、載せる日を付けて data/recipes.json に足す。PR の説明文も作る。

使い方: python3 scripts/propose.py [日数]   （日数を省くと7日分）
- 載せる日は、すでに予定に入っている最後の日の翌日から。今日の1品がまだなければ今日から
- 1日に1品（あれば、まとめも1件）
- 選び方（1品）: 区分がばらけることを優先する（balanced）。
  1日ずつ、ページに載っている数（予定も含む）がいちばん少ない区分を選び、前の日と同じ区分はなるべく続けない。
  区分の中では投稿日が新しいものから（古い動画・記事の商品は、もう売っていないかもしれないため）。
  「未分類」は、ほかの区分のストックがない時だけ使う
- 選び方（まとめ）: 投稿日が新しいものから
- ストック（data/stock.json）は変えない。マージして載せた品は、次の収集の時にストックから外れる
"""
import datetime
import json
import sys

import gyosu


def ranked(stock, kind):
    cands = [x for x in stock if x["kind"] == kind]
    # 投稿日が新しいもの → 区分が決まっているもの → 早く見つけたもの（投稿日が不明なものは最後）
    cands.sort(key=lambda x: (x.get("posted") or "", x["section"] != gyosu.UNSORTED, x["found"]), reverse=True)
    return cands


def balanced(stock, recipes, days):
    """区分がばらけるように1品を days 件選ぶ。"""
    pools = {}
    for x in ranked(stock, "one"):   # 区分ごとに、新しい順
        pools.setdefault(x["section"], []).append(x)
    unsorted = pools.pop(gyosu.UNSORTED, [])
    count = {}
    for r in recipes:
        if r["kind"] == "one":
            count[r["section"]] = count.get(r["section"], 0) + 1
    chosen, prev = [], None
    for _ in range(days):
        live = [s for s in pools if pools[s]]
        if not live:
            if not unsorted:
                break
            chosen.append(unsorted.pop(0))
            continue
        # 少ない区分 → 前の日と違う区分。それでも並んだら、いちばん新しい品がある区分
        first = min((count.get(s, 0), s == prev) for s in live)
        tied = [s for s in live if (count.get(s, 0), s == prev) == first]
        best = max(tied, key=lambda s: pools[s][0].get("posted") or "")
        x = pools[best].pop(0)
        chosen.append(x)
        count[best] = count.get(best, 0) + 1
        prev = best
    return chosen


def pick(stock, kind):
    cands = ranked(stock, kind)
    return cands[0] if cands else None


def first_day(recipes, today):
    """新しい予定を始める日: 予定の最後の日の翌日。ただし今日の1品がまだなければ今日から。"""
    last = max((r["added"] for r in recipes if r["kind"] == "one"), default=None)
    t = datetime.date.fromisoformat(today)
    if last is None:
        return t
    return max(datetime.date.fromisoformat(last) + datetime.timedelta(days=1), t)


def tags(x):
    return [x["section"], x["item_group"]] + ([x["seasoning"]] if x["seasoning"] else []) + (["ひと手間"] if x["hitote"] else [])


def main(days=7):
    recipes = gyosu.load_json(gyosu.RECIPES)
    stock = gyosu.load_json(gyosu.STOCK)
    today = gyosu.today()
    published = {gyosu.normalize_url(r["url"]) for r in recipes}
    stock = [x for x in stock if gyosu.normalize_url(x["url"]) not in published]
    ones, sets = balanced(stock, recipes, days), ranked(stock, "set")[:days]
    start = first_day(recipes, today)

    plan = []
    for i, x in enumerate(ones):
        day = (start + datetime.timedelta(days=i)).isoformat()
        plan.append((day, x, sets[i] if i < len(sets) else None))
        recipes.append({**x, "added": day})
        if i < len(sets):
            recipes.append({**sets[i], "added": day})
    gyosu.save_json(gyosu.RECIPES, recipes)

    year_ago = str(int(today[:4]) - 1) + today[4:]
    body = [f"{len(plan)}日分の候補です（{plan[0][0]} 〜 {plan[-1][0]}）。確かめてマージしてください。" if plan
            else "ストックが空なので、候補を出せませんでした。", ""]
    for day, x, s in plan:
        d = datetime.date.fromisoformat(day)
        body += [f"### {d.month}月{d.day}日（{'月火水木金土日'[d.weekday()]}）",
                 f"- **{x['dish']}**（{' / '.join(tags(x))}）",
                 f"  - [{x['title']}]({x['url']})　投稿日 {x.get('posted') or '不明'}"]
        if x["section"] == gyosu.UNSORTED:
            body.append("  - ⚠ 区分が「未分類」。焼き物・揚げ物・煮物・炒め物・小鉢・〆 のどれかに直す")
        if (x.get("posted") or "") < year_ago:
            body.append("  - ⚠ 投稿が1年以上前（または不明）。業務スーパーで今も売っている商品か確かめる")
        if s:
            body.append(f"- まとめ: [{s['title']}]({s['url']})")
        body.append("")
    body += ["## 直し方",
             "- 料理名（`dish`）や区分（`section`）は、この PR の `data/recipes.json` で直す",
             "- 載せたくない品は、その行を消す。消した品はストックに残り、次の候補にまた出ることがある",
             "- 品を消すとその日は空く（ページは前の日の品を「今日の一品」として出したまま）。日付（`added`）を詰めてもよい",
             "", f"ストックの残り: 1品 {len(ranked(stock, 'one')) - len(ones)}件・まとめ {len(ranked(stock, 'set')) - min(len(sets), len(ones))}件"]
    (gyosu.ROOT / "pr_body.md").write_text("\n".join(body) + "\n", encoding="utf-8")
    print("\n".join(body))
    return 0


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 7))
