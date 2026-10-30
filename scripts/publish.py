"""ストックから今日の1品（とまとめ1件）を選び、ページに載せる。毎日の PR の説明文も作る。

使い方: python3 scripts/publish.py
選び方: 投稿日が新しいものを最優先（古い動画・記事の商品は、もう売っていないかもしれないため）。
同じ投稿日なら区分が決まっているものを先に。古いものしかなければ古いものを載せる。
"""
import json
import sys

import gyosu


def pick(stock, kind):
    cands = [x for x in stock if x["kind"] == kind]
    # 投稿日が新しいもの → 区分が決まっているもの → 早く見つけたもの（投稿日が不明なものは最後）
    cands.sort(key=lambda x: (x.get("posted") or "", x["section"] != gyosu.UNSORTED, x["found"]), reverse=True)
    return cands[0] if cands else None


def line(x):
    tags = [x["section"], x["item_group"]] + ([x["seasoning"]] if x["seasoning"] else []) + (["ひと手間"] if x["hitote"] else [])
    return f"- **{x['dish']}**（{' / '.join(tags)}）\n  - [{x['title']}]({x['url']})　投稿日 {x.get('posted') or '不明'}"


def main():
    recipes = gyosu.load_json(gyosu.RECIPES)
    stock = gyosu.load_json(gyosu.STOCK)
    day = gyosu.today()
    # 今日の1品が載せてあっても、集めた結果（ストック・見た URL）を残すため PR の説明は作る
    done = any(r["added"] == day and r["kind"] == "one" for r in recipes)
    chosen = [] if done else [x for x in (pick(stock, "one"), pick(stock, "set")) if x]
    for x in chosen:
        stock.remove(x)
        recipes.append({**x, "added": day})
    gyosu.save_json(gyosu.RECIPES, recipes)
    gyosu.save_json(gyosu.STOCK, stock)

    collect = json.loads((gyosu.ROOT / "data/last_collect.json").read_text(encoding="utf-8")) \
        if (gyosu.ROOT / "data/last_collect.json").exists() else {}
    body = [f"{day} の更新です。内容を確かめてマージしてください。", "", "## 今日載せるもの"]
    if done:
        body += ["- 今日の1品はもう載せてあるので、今日は集めた結果だけを記録します"]
    else:
        body += [line(x) for x in chosen] or ["- ストックが空なので、今日は載せるものがありません"]
    if any(x["section"] == gyosu.UNSORTED for x in chosen):
        body += ["", "⚠ 区分が「未分類」です。`data/recipes.json` の `section` を焼き物・揚げ物・煮物・炒め物・小鉢・〆 のどれかに直してください。"]
    year_ago = str(int(day[:4]) - 1) + day[4:]
    if any((x.get("posted") or "") < year_ago for x in chosen):
        body += ["", "⚠ 投稿が1年以上前（または不明）のものがあります。新しいものがストックにないため選びました。業務スーパーで今も売っている商品か確かめてください。"]
    body += ["", "料理名（`dish`）や区分が違っていたら、この PR の `data/recipes.json` を直してからマージしてください。"]
    body += ["", "## 集めた結果",
             f"- 見つけた: {collect.get('found', '-')}件 / 初めて見た: {collect.get('new', '-')}件 / ストックに入れた: {collect.get('stocked', '-')}件",
             f"- 今のルールでストックから外した: {collect.get('removed', 0)}件",
             f"- ストックの残り: 1品 {sum(x['kind'] == 'one' for x in stock)}件（未分類 {sum(x['kind'] == 'one' and x['section'] == gyosu.UNSORTED for x in stock)}件）・まとめ {sum(x['kind'] == 'set' for x in stock)}件"]
    if collect.get("errors"):
        body += ["", "## うまく取れなかったところ"] + [f"- {e}" for e in collect["errors"]]
    (gyosu.ROOT / "pr_body.md").write_text("\n".join(body) + "\n", encoding="utf-8")
    print("\n".join(body))
    return 0


if __name__ == "__main__":
    sys.exit(main())
