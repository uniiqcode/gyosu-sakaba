"""YouTube と RSS から新しい動画・記事を探し、条件に合うものをストックに入れる。

使い方: YOUTUBE_API_KEY=... python3 scripts/collect.py
キーがなければ YouTube は飛ばす。1つの情報源が失敗しても、ほかは続ける。
"""
import datetime
import email.utils
import json
import os
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

import gyosu

UA = {"User-Agent": "gyosu-sakaba/1.0 (+https://github.com/uniiqcode/gyosu-sakaba)"}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def youtube(cfg, key):
    """検索で動画 ID を集め、videos.list で概要欄まで取る。"""
    after = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=cfg["days"])).strftime("%Y-%m-%dT%H:%M:%SZ")
    ids = []
    for q in cfg["queries"]:
        for order in ("date", "relevance"):
            params = {"part": "id", "type": "video", "q": q, "order": order, "maxResults": cfg["max_results"],
                      "publishedAfter": after, "regionCode": "JP", "relevanceLanguage": "ja", "key": key}
            data = json.loads(get("https://www.googleapis.com/youtube/v3/search?" + urllib.parse.urlencode(params)))
            ids += [it["id"]["videoId"] for it in data.get("items", []) if it["id"].get("videoId")]
    ids = list(dict.fromkeys(ids))
    out = []
    for i in range(0, len(ids), 50):
        params = {"part": "snippet", "id": ",".join(ids[i:i + 50]), "key": key}
        data = json.loads(get("https://www.googleapis.com/youtube/v3/videos?" + urllib.parse.urlencode(params)))
        for v in data.get("items", []):
            s = v["snippet"]
            out.append({"url": f"https://www.youtube.com/watch?v={v['id']}", "title": s["title"],
                        "description": s.get("description", ""), "channel": s.get("channelTitle", ""),
                        "posted": s.get("publishedAt", "")[:10]})
    return out


def _date(text):
    if not text:
        return ""
    try:
        return email.utils.parsedate_to_datetime(text).date().isoformat()   # RSS 2.0
    except (TypeError, ValueError):
        return text[:10]                                                     # Atom / RDF (ISO 8601)


def rss(url):
    """RSS 2.0・RSS 1.0（RDF）・Atom を読む。"""
    root = ET.fromstring(get(url))
    out = []
    for el in root.iter():
        tag = el.tag.rsplit("}", 1)[-1]
        if tag not in ("item", "entry"):
            continue
        f = {c.tag.rsplit("}", 1)[-1]: c for c in el}
        link = f.get("link")
        href = (link.get("href") or link.text or "").strip() if link is not None else ""
        title = (f["title"].text or "").strip() if "title" in f else ""
        desc = next(((f[k].text or "") for k in ("description", "summary", "content", "encoded") if k in f), "")
        posted = next((_date(f[k].text) for k in ("pubDate", "published", "updated", "date") if k in f), "")
        if href and title:
            out.append({"url": href, "title": title, "description": desc, "channel": "", "posted": posted})
    return out


def main():
    sources = gyosu.load_toml("sources.toml")
    rules = gyosu.load_toml("rules.toml")
    found, errors = [], []
    key = os.environ.get("YOUTUBE_API_KEY")
    if key:
        try:
            found += youtube(sources["youtube"], key)
        except Exception as e:  # noqa: BLE001  失敗しても RSS は続ける
            errors.append(f"YouTube: {e}")
    else:
        errors.append("YouTube: YOUTUBE_API_KEY がないので飛ばした")
    for url in sources["rss"]["feeds"]:
        try:
            found += rss(url)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{url}: {e}")

    seen = gyosu.load_seen()
    seen |= {gyosu.normalize_url(x["url"]) for x in gyosu.load_json(gyosu.RECIPES) + gyosu.load_json(gyosu.STOCK)}
    stock = gyosu.load_json(gyosu.STOCK)
    day = gyosu.today()
    log, added = [], []
    for x in found:
        url = gyosu.normalize_url(x["url"])
        if url in seen:
            continue
        seen.add(url)
        result = gyosu.classify(x["title"], x["description"], url, x["channel"], rules)
        if isinstance(result, str):
            log.append((day, url, result))
            continue
        item = {"id": gyosu.item_id(url), "url": url, "title": x["title"], "source": gyosu.source_of(url),
                "channel": x["channel"], "posted": x["posted"], "found": day, **result}
        stock.append(item)
        added.append(item)
        log.append((day, url, "ストック"))
    gyosu.save_json(gyosu.STOCK, stock)
    gyosu.append_seen(log)

    summary = {"found": len(found), "new": len(log), "stocked": len(added), "errors": errors}
    (gyosu.ROOT / "data/last_collect.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
