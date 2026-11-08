"""data/recipes.json と site/template.html から、公開するページ _site/ を作る。

使い方: python3 scripts/build_site.py
- 検索エンジンが読めるよう、作った日（日本時間）までに載せた品を HTML に書き込む（今日の一品・すべての品書き・
  構造化データ）。予定の品（載せる日がまだ来ていないもの）は書き込まない。ページは毎日作り直す（pages.yml）
- JavaScript 用のデータには予定の品も入れる（作り直しが遅れても、載せる日の朝に表に出るように）
- sitemap.xml も作る（日付は作った日）
"""
import html
import json
import shutil
import sys

import gyosu

FIELDS = ["id", "url", "title", "source", "dish", "section", "item_group", "gyosu_item",
          "seasoning", "kind", "hitote", "official", "added"]
SITE_URL = "https://uniiqcode.com/gyosu-sakaba/"   # 正式な URL（seo-uniiqcode スキル）
SECTIONS = ["焼き物", "揚げ物", "煮物", "炒め物", "小鉢", "〆"]


def plain(dish):
    return dish.replace("／", "")   # 「／」は短冊の改行の印なので、ほかでは消す


def static_today(item):
    """JavaScript が動く前（と検索エンジン）に見せる、今日の一品。"""
    e = html.escape
    return (f'<div class="info"><p class="dish"><a href="{e(item["url"])}" target="_blank" rel="noopener">'
            f'{e(plain(item["dish"]))}</a></p><div class="orig">{e(item["title"])}</div></div>')


def all_list(published):
    """すべての品書き: 区分ごとに、新しい順のリンクの一覧。"""
    e = html.escape
    newest = list(reversed(published))
    groups = [(s, [x for x in newest if x["kind"] == "one" and x["section"] == s]) for s in SECTIONS]
    groups.append(("調味料が主役", [x for x in newest if x.get("seasoning")]))
    groups.append(("まとめて見る", [x for x in newest if x["kind"] == "set"]))
    parts = []
    for name, xs in groups:
        if xs:
            lis = "".join(f'<li><a href="{e(x["url"])}" target="_blank" rel="noopener">{e(plain(x["dish"]))}</a></li>' for x in xs)
            parts.append(f"<h3>{e(name)}（{len(xs)}）</h3><ul>{lis}</ul>")
    return "\n      ".join(parts)


def json_ld(published):
    """構造化データ。レシピ本文は載せていないので Recipe 型は使わず、リンク集（ItemList）にする。"""
    newest = list(reversed(published))
    data = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "業スー酒場｜居酒屋の一品ネタ帳",
        "url": SITE_URL,
        "numberOfItems": len(newest),
        "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": plain(x["dish"]), "url": x["url"]}
                            for i, x in enumerate(newest)],
    }
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def sitemap(day):
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"  <url><loc>{SITE_URL}</loc><lastmod>{day}</lastmod></url>\n"
            "</urlset>\n")


def main():
    recipes = gyosu.load_json(gyosu.RECIPES)
    day = gyosu.today()
    # 載せた順（新しいものが後ろ）。ページ側では後ろから「今日の一品」「新着」にする
    items = [{k: r.get(k) for k in FIELDS} for r in recipes]
    published = [x for x in items if not x["added"] or x["added"] <= day]
    ones = [x for x in published if x["kind"] == "one"]
    template = (gyosu.ROOT / "site/template.html").read_text(encoding="utf-8")
    page = (template
            .replace("__JSONLD__", json_ld(published))
            .replace("__STATIC_TODAY__", static_today(ones[-1]) if ones else "")
            .replace("__ALL_COUNT__", str(len(published)))
            .replace("__ALL_LIST__", all_list(published))
            .replace("__DATA__", json.dumps(items, ensure_ascii=False)))
    out_html = "<!doctype html>\n<html lang=\"ja\">\n<head>\n<meta charset=\"utf-8\">\n" \
               "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n" + page
    out = gyosu.ROOT / "_site"
    out.mkdir(exist_ok=True)
    (out / "index.html").write_text(out_html, encoding="utf-8")
    (out / "sitemap.xml").write_text(sitemap(day), encoding="utf-8")
    # ロゴ・アイコン・絵・ホーム画面用の設定を、ページと同じ場所に置く
    for f in (gyosu.ROOT / "site/assets").iterdir():
        shutil.copy(f, out / f.name)
    shutil.copy(gyosu.ROOT / "site/manifest.webmanifest", out / "manifest.webmanifest")
    print(f"_site/index.html を作った（{day} までに載せた {len(published)}件、予定を含め {len(items)}件）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
