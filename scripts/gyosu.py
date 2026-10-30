"""業スー酒場の共通部分: データの読み書きと、キーワードによる判定・分類。"""
import datetime
import hashlib
import json
import pathlib
import re
import tomllib
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
RECIPES = ROOT / "data/recipes.json"   # ページに載せたもの
STOCK = ROOT / "data/stock.json"       # 集めたが、まだ載せていないもの
SEEN = ROOT / "data/seen.tsv"          # 一度でも見た URL（載せなかったものも）
CONFIG = ROOT / "config"

UNSORTED = "未分類"


def today():
    """日本時間の今日（YYYY-MM-DD）。"""
    jst = datetime.timezone(datetime.timedelta(hours=9))
    return datetime.datetime.now(jst).date().isoformat()


def load_toml(name):
    with open(CONFIG / name, "rb") as f:
        return tomllib.load(f)


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def load_seen():
    if not SEEN.exists():
        return set()
    return {line.split("\t")[1] for line in SEEN.read_text(encoding="utf-8").splitlines() if "\t" in line}


def append_seen(rows):
    """rows: (日付, URL, 結果) のリスト。追記のみ。"""
    with open(SEEN, "a", encoding="utf-8") as f:
        for r in rows:
            f.write("\t".join(r) + "\n")


def normalize_url(url):
    """同じページを二重に載せないよう、URL をそろえる。"""
    u = urllib.parse.urlsplit(url.strip())
    host = u.netloc.lower().removeprefix("m.")
    if host in ("youtu.be",):
        return f"https://www.youtube.com/watch?v={u.path.strip('/')}"
    if host.endswith("youtube.com"):
        if u.path.startswith("/shorts/"):
            return f"https://www.youtube.com/watch?v={u.path.split('/')[2]}"
        vid = urllib.parse.parse_qs(u.query).get("v", [""])[0]
        if vid:
            return f"https://www.youtube.com/watch?v={vid}"
    # ブログは問い合わせ部分（?以降）を落とす
    return urllib.parse.urlunsplit(("https", host, u.path, "", ""))


def item_id(url):
    return hashlib.sha1(normalize_url(url).encode()).hexdigest()[:10]


def _first(rules, text):
    """[[section]] などの表から、最初に当たった name と当たった言葉を返す。"""
    for r in rules:
        for w in r["words"]:
            if w in text:
                return r["name"], w
    return None, None


def clean_title(title):
    """タイトルから料理名の候補を作る。人が PR で直す前提の下書き。"""
    t = re.sub(r"\s*[-|｜]\s*YouTube\s*$", "", title)
    # 「料理名｜業務スーパーミラクルレシピ」のような、｜の後ろのチャンネル名・シリーズ名を落とす
    parts = [s for s in re.split(r"[|｜]", t) if s.strip()]
    if len(parts) > 1:
        t = max(parts[:-1], key=len) if re.search(r"業務用?スーパー|業スー", parts[-1]) else t
    t = re.sub(r"[【\[［〔(（][^】\]］〕)）]*[】\]］〕)）]", " ", t)
    t = re.sub(r"#\S+", " ", t)
    t = re.sub(r"業務用?スーパー|業スー|の?(簡単|激うま|絶品|最強|節約)?レシピ", " ", t)
    t = re.sub(r"[^\w\sぁ-んァ-ヶー一-龠々〆・&＆]", " ", t)  # 絵文字や記号を消す
    t = re.sub(r"\s+", " ", t).strip(" ・")
    t = re.sub(r"^(の|で|を|は)\s*", "", t)   # 「業スーの〇〇」の「の」など
    return t[:30] or title[:30]


def title_reject(title, rules):
    """タイトルだけで載せないと決められるなら、その理由を返す。"""
    if any(w in title for w in rules["reject"]["other_stores"]) and not any(w in title for w in rules["accept"]["gyosu"]):
        return "ほかの店の記事"
    bad = [w for w in rules["reject"]["title"] if w in title]
    if bad:
        return f"除外の言葉（{bad[0]}）"
    if any(w in title for w in rules["reject"]["review"]) and _first(rules["section"], title)[0] is None:
        return "商品の感想"
    return None


def recheck(item, rules):
    """ストックの1件を今のルールで見直す。外すなら理由の文字列、残すなら直した item を返す。
    ストックには説明文を残していない（元のページの文章を写さないため）ので、タイトルだけで見る。"""
    title = item["title"]
    reason = title_reject(title, rules)
    if reason:
        return reason
    section, _ = _first(rules["section"], title)
    if section is None and not any(w in title for w in rules["accept"]["gyosu"]):
        return "タイトルに業務スーパーも料理の言葉もない"
    if item["section"] == UNSORTED and section:
        item = {**item, "section": section}
    return {**item, "dish": clean_title(title)} if "dish" in item else item


def classify(title, description="", url="", channel="", rules=None):
    """載せるなら分類の結果（dict）を、載せないなら理由の文字列を返す。"""
    rules = rules or load_toml("rules.toml")
    text = f"{title}\n{description}"
    host = urllib.parse.urlsplit(url).netloc.lower()
    if any(host == d or host.endswith("." + d) for d in rules["reject"]["domains"]):
        return "対象外のサイト"
    if not any(w in text for w in rules["accept"]["gyosu"]):
        return "業務スーパーの言葉がない"
    reason = title_reject(title, rules)
    if reason:
        return reason
    # 区分と札は、まずタイトルで決め、だめなら説明文も見る
    section, _ = _first(rules["section"], title)
    # 業務スーパーの言葉が説明文にしかないなら、タイトルに料理の言葉があることを条件にする
    if section is None and not any(w in title for w in rules["accept"]["gyosu"]):
        return "タイトルに業務スーパーも料理の言葉もない"
    kind = "set" if any(re.search(p, title) for p in rules["set"]["patterns"]) else "one"
    # 料理の言葉（煮・炒め・唐揚げなど）や「〇品」「作り置き」がタイトルにあれば、それもレシピの目印にする
    if section is None and kind == "one" and not any(w in text for w in rules["accept"]["recipe"]):
        return "レシピの目印がない"
    group, item = _first(rules["group"], title)
    seasoning, s_word = _first(rules["seasoning"], title)
    if group is None:
        group, item = _first(rules["group"], text)
    if seasoning is None:
        seasoning, s_word = _first(rules["seasoning"], text)
    if group is None and seasoning:
        group, item = "調味料", s_word
    off = rules["official"]
    official = (any(w in title for w in off["title_contains"])
                or any(title.endswith(w) for w in off["title_endswith"])
                or channel in off["channels"])
    return {
        "dish": clean_title(title),
        "section": section or UNSORTED,
        "item_group": group or "いろいろ",
        "gyosu_item": item or "",
        "seasoning": seasoning,
        "kind": kind,
        "hitote": group == "冷凍惣菜・加工品",
        "official": official,
    }


def source_of(url):
    host = urllib.parse.urlsplit(url).netloc
    if "youtube.com" in host:
        return "youtube"
    if any(b in host for b in ("ameblo.jp", "note.com", "hatenablog", "hateblo.jp", "livedoor.blog", "fc2.com")):
        return "blog"
    return "web"
