"""data/sample_links.csv から試作の画面 prototype/index.html を作る。

使い方: python3 prototype/build.py
公開日は並べ方を見るための仮の日付（2026-10-30 から1日1品ずつ遡る）。
"""
import csv, datetime, itertools, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SEASONINGS = [("姜葱醤", "姜葱醤"), ("トムヤム", "トムヤム"), ("甘酢あん", "中華甘酢あん"),
              ("青のにんにく", "青のにんにく"), ("豆板醤", "豆板醤")]
SECTION_NAMES = {"ご飯・麺": "〆", "小鉢・冷菜": "小鉢"}

rows = [r for r in csv.DictReader(open(ROOT / "data/sample_links.csv", encoding="utf-8")) if r["fit"] != "△"]
for r in rows:
    r.pop("fit")
    r["kind"] = "set" if r["section"] == "まとめ" else "one"
    r["section"] = SECTION_NAMES.get(r["section"], r["section"])
    r["seasoning"] = next((n for k, n in SEASONINGS if k in r["gyosu_item"]), None)
    r["hitote"] = r["item_group"] == "冷凍惣菜・加工品"
    r["official"] = "ミラクルレシピ" in r["title"] or r["title"].endswith("｜業務スーパー")
    if r["item_group"] == "その他":
        r["item_group"] = "いろいろ"
    r["date"] = ""

# 品書きが偏らないよう、区分を順番に回して並べる
groups = {}
for r in rows:
    if r["kind"] == "one":
        groups.setdefault(r["section"], []).append(r)
ones = [r for t in itertools.zip_longest(*groups.values()) for r in t if r]
today = datetime.date(2026, 10, 30)
for i, r in enumerate(ones):
    r["date"] = str(today - datetime.timedelta(days=i))

items = ones + [r for r in rows if r["kind"] == "set"]
template = (ROOT / "prototype/template.html").read_text(encoding="utf-8")
(ROOT / "prototype/index.html").write_text(template.replace("__DATA__", json.dumps(items, ensure_ascii=False)), encoding="utf-8")
print(f"{len(ones)}品 + まとめ{len(items) - len(ones)}件")
