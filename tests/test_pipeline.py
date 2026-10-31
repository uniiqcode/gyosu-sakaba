"""判定・収集・掲載の確かめ。ネットにはつながない。

使い方: python3 -m unittest discover -s tests
"""
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
import collect  # noqa: E402
import gyosu  # noqa: E402
import publish  # noqa: E402

RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>ブログ</title>
<item><title>【業務スーパー】冷凍赤魚の煮付け</title><link>https://example.hatenablog.com/entry/1?utm_source=rss</link>
<description>材料と作り方</description><pubDate>Wed, 28 Oct 2026 08:00:00 +0900</pubDate></item>
<item><title>業務スーパー購入品紹介</title><link>https://example.hatenablog.com/entry/2</link>
<description>今週買ったもの</description><pubDate>Thu, 29 Oct 2026 08:00:00 +0900</pubDate></item>
<item><title>今日の散歩</title><link>https://example.hatenablog.com/entry/3</link>
<description>公園へ</description><pubDate>Thu, 29 Oct 2026 09:00:00 +0900</pubDate></item>
</channel></rss>"""

ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"><title>note</title>
<entry><title>業スーの姜葱醤で鶏むねの甘辛炒め</title><link href="https://note.com/a/n/n123"/>
<summary>簡単レシピ</summary><published>2026-10-29T12:00:00+09:00</published></entry>
</feed>"""


class Classify(unittest.TestCase):
    def test_accepts_and_sorts(self):
        r = gyosu.classify("【業務スーパー】冷凍から揚げアレンジ！タレ漬けから揚げ", "")
        self.assertEqual((r["section"], r["item_group"], r["kind"], r["hitote"]), ("揚げ物", "冷凍惣菜・加工品", "one", True))

    def test_seasoning_becomes_group_when_nothing_else(self):
        r = gyosu.classify("業務スーパーの姜葱醤レシピ", "")
        self.assertEqual((r["seasoning"], r["item_group"]), ("姜葱醤", "調味料"))

    def test_set(self):
        self.assertEqual(gyosu.classify("業務スーパーの鶏むね肉2kgで7品作り置き", "")["kind"], "set")

    def test_rejects(self):
        self.assertEqual(gyosu.classify("業務スーパー購入品紹介", "レシピ"), "除外の言葉（購入品）")
        self.assertEqual(gyosu.classify("鶏の唐揚げ", "作り方"), "業務スーパーの言葉がない")
        self.assertEqual(gyosu.classify("業務スーパー 唐揚げ", "", "https://cookpad.com/recipe/1"), "対象外のサイト")

    def test_official(self):
        self.assertTrue(gyosu.classify("白身魚の中華甘酢あんかけ｜業務スーパーミラクルレシピ", "")["official"])
        self.assertFalse(gyosu.classify("業務スーパーの豚の角煮", "", channel="業務スーパーマニア")["official"])

    def test_other_store(self):
        self.assertEqual(gyosu.classify("【コストコ】本日の値下げ", "業務スーパーも好き 作り方"), "ほかの店の記事")
        self.assertIsInstance(gyosu.classify("業務スーパーとコストコの鶏むねで唐揚げ", ""), dict)

    def test_recheck_stock(self):
        rules = gyosu.load_toml("rules.toml")
        old = {"title": "【コストコ】新商品続々！", "section": gyosu.UNSORTED}
        self.assertEqual(gyosu.recheck(old, rules), "ほかの店の記事")
        x = {"title": "業務スーパーの明太子で明太子グラタン", "section": gyosu.UNSORTED}
        self.assertEqual(gyosu.recheck(x, rules)["section"], "焼き物")

    def test_normalize_url(self):
        n = gyosu.normalize_url
        self.assertEqual(n("https://www.youtube.com/shorts/abc"), "https://www.youtube.com/watch?v=abc")
        self.assertEqual(n("https://youtu.be/abc"), "https://www.youtube.com/watch?v=abc")
        self.assertEqual(n("https://m.youtube.com/watch?v=abc&pp=x"), "https://www.youtube.com/watch?v=abc")
        self.assertEqual(n("http://b.example.jp/entry/1?utm=x"), "https://b.example.jp/entry/1")

    def test_clean_title(self):
        self.assertEqual(gyosu.clean_title("【業務スーパー】冷凍赤魚の煮付け‼️ - YouTube"), "冷凍赤魚の煮付け")
        self.assertEqual(gyosu.clean_title("【3ステップ】旨辛！もちもちビビン麺｜業務スーパーミラクルレシピ"), "旨辛 もちもちビビン麺")
        self.assertEqual(gyosu.clean_title("鶏皮ぎょうざ｜業務スーパー"), "鶏皮ぎょうざ")
        self.assertEqual(gyosu.clean_title("料理がもっと楽しくなる！業務スーパーの神調味料6選"), "料理がもっと楽しくなる 神調味料6選")
        # 料理名が【】の中にだけあるときは、【】の中を使う
        self.assertEqual(gyosu.clean_title("おかわりしたくなる‼︎【きのこ&ツナの炊き込みごはん】"), "きのこ&ツナの炊き込みごはん")
        # 外に料理名があれば、【】の中は飾りとして消す
        self.assertEqual(gyosu.clean_title("【ワンパン煮込み】業務スーパーの鶏で照り焼き"), "鶏で照り焼き")

    def test_review(self):
        self.assertEqual(gyosu.classify("【業務スーパー】しめじの値段が198円 実際に使ってみた感想", "レシピ"), "商品の感想")
        self.assertIsInstance(gyosu.classify("【業務スーパー】冷凍赤魚の値段が558円 赤魚の煮付け", ""), dict)

    def test_title_needs_gyosu_or_dish(self):
        self.assertEqual(gyosu.classify("海外一人旅 最初に降り立つ国は", "業務スーパー 簡単"), "タイトルに業務スーパーも料理の言葉もない")
        self.assertIsInstance(gyosu.classify("溶ける黄金カルボナーラ【レシピあり】", "業務スーパーの食材で"), dict)


class Pick(unittest.TestCase):
    def test_newest_first_even_if_unsorted(self):
        stock = [
            {"kind": "one", "section": "焼き物", "posted": "2024-05-01", "found": "2026-10-30"},
            {"kind": "one", "section": gyosu.UNSORTED, "posted": "2026-10-28", "found": "2026-10-30"},
            {"kind": "one", "section": "煮物", "posted": "", "found": "2026-10-30"},
        ]
        self.assertEqual(publish.pick(stock, "one")["posted"], "2026-10-28")

    def test_same_day_prefers_sorted(self):
        stock = [
            {"kind": "one", "section": gyosu.UNSORTED, "posted": "2026-10-28", "found": "2026-10-30"},
            {"kind": "one", "section": "揚げ物", "posted": "2026-10-28", "found": "2026-10-30"},
        ]
        self.assertEqual(publish.pick(stock, "one")["section"], "揚げ物")

    def test_old_only_is_still_picked(self):
        stock = [{"kind": "one", "section": "焼き物", "posted": "2021-01-01", "found": "2026-10-30"}]
        self.assertEqual(publish.pick(stock, "one")["posted"], "2021-01-01")


class Pipeline(unittest.TestCase):
    """一時フォルダの上で、収集 → 掲載 を通す。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = pathlib.Path(self.tmp.name)
        (d / "data").mkdir()
        self.saved = (gyosu.ROOT, gyosu.RECIPES, gyosu.STOCK, gyosu.SEEN, gyosu.load_toml, gyosu.today, collect.get)
        real_load = gyosu.load_toml
        # 情報源は手元の2つのフィードだけにする。判定のルールは本物を使う
        gyosu.load_toml = lambda name: {"youtube": {}, "rss": {"feeds": ["a", "b"]}} if name == "sources.toml" else real_load(name)
        gyosu.ROOT = d
        gyosu.RECIPES, gyosu.STOCK, gyosu.SEEN = d / "data/recipes.json", d / "data/stock.json", d / "data/seen.tsv"
        gyosu.today = lambda: "2026-10-30"
        feeds = {"a": RSS, "b": ATOM}
        collect.get = lambda url: feeds[url].encode()

    def tearDown(self):
        gyosu.ROOT, gyosu.RECIPES, gyosu.STOCK, gyosu.SEEN, gyosu.load_toml, gyosu.today, collect.get = self.saved
        self.tmp.cleanup()

    def test_collect_then_publish(self):
        collect.main()
        stock = gyosu.load_json(gyosu.STOCK)
        self.assertEqual(sorted(x["dish"] for x in stock), ["冷凍赤魚の煮付け", "姜葱醤で鶏むねの甘辛炒め"])
        self.assertEqual(len(gyosu.load_seen()), 4)   # 載せなかった購入品と散歩の記事も記録する

        # 2回目は同じものを拾わない
        collect.main()
        self.assertEqual(len(gyosu.load_json(gyosu.STOCK)), 2)

        publish.main()
        recipes = gyosu.load_json(gyosu.RECIPES)
        self.assertEqual(len(recipes), 1)
        self.assertEqual(recipes[0]["dish"], "姜葱醤で鶏むねの甘辛炒め")   # 投稿日が新しい方
        self.assertEqual(recipes[0]["added"], "2026-10-30")
        self.assertIn("姜葱醤で鶏むねの甘辛炒め", (gyosu.ROOT / "pr_body.md").read_text(encoding="utf-8"))

        # 同じ日に2回動いても、2品目は載せない。PR の説明は作る
        (gyosu.ROOT / "pr_body.md").unlink()
        publish.main()
        self.assertEqual(len(gyosu.load_json(gyosu.RECIPES)), 1)
        self.assertIn("もう載せてある", (gyosu.ROOT / "pr_body.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
