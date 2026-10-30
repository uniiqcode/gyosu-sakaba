"""data/recipes.json と site/template.html から、公開するページ _site/index.html を作る。

使い方: python3 scripts/build_site.py
"""
import json
import shutil
import sys

import gyosu

FIELDS = ["id", "url", "title", "source", "dish", "section", "item_group", "gyosu_item",
          "seasoning", "kind", "hitote", "official", "added"]


def main():
    recipes = gyosu.load_json(gyosu.RECIPES)
    # 載せた順（新しいものが後ろ）。ページ側では後ろから「今日の一品」「新着」にする
    items = [{k: r.get(k) for k in FIELDS} for r in recipes]
    template = (gyosu.ROOT / "site/template.html").read_text(encoding="utf-8")
    html = "<!doctype html>\n<html lang=\"ja\">\n<head>\n<meta charset=\"utf-8\">\n" \
           "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n" + \
           template.replace("__DATA__", json.dumps(items, ensure_ascii=False))
    out = gyosu.ROOT / "_site"
    out.mkdir(exist_ok=True)
    (out / "index.html").write_text(html, encoding="utf-8")
    # ロゴ・アイコン・ホーム画面用の設定を、ページと同じ場所に置く
    for f in (gyosu.ROOT / "site/assets").iterdir():
        shutil.copy(f, out / f.name)
    shutil.copy(gyosu.ROOT / "site/manifest.webmanifest", out / "manifest.webmanifest")
    print(f"_site/index.html を作った（{len(items)}件）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
