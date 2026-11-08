# 検索対策（SEO）

2026-11-08。`uniiqcode/claude-skills` の `seo-uniiqcode` スキルの手順に沿って入れた。正式な URL は **https://uniiqcode.com/gyosu-sakaba/**。

## 入れたもの

| スキルの手順 | 中身 | 場所 |
|---|---|---|
| 1. 正式な URL | `https://uniiqcode.com/gyosu-sakaba/`（canonical・OGP・サイトマップ・構造化データはすべてこれ） | `site/template.html`、`scripts/build_site.py` の `SITE_URL` |
| 2. 中身を HTML に | 今日の一品と「すべての品書き」（区分ごとのリンクの一覧）を、ページを作る時に HTML に書き込む。作った日（日本時間）までに載せた品だけ | `scripts/build_site.py` |
| 3. 基本の META | title「業スー酒場｜居酒屋の一品ネタ帳」、description（約90文字）、canonical、`<html lang="ja">`、h1（見た目は隠す）、絵の alt・大きさ | `site/template.html` |
| 4. 共有した時の表示 | OGP と X のカード。絵は夜の路地の絵から切り出した 1200×630（`og.jpg`） | `site/template.html`、`site/assets/og.jpg` |
| 5. サイトマップ | `sitemap.xml`（日付は作った日）。robots.txt は置かない（アプリのリポジトリでは効かないため） | `scripts/build_site.py` |
| 6. 構造化データ | `ItemList`（料理名とレシピのリンク）。レシピ本文は載せていないので `Recipe` 型は使わない | `scripts/build_site.py` の `json_ld` |
| 7. 速さ | ページ上部の絵を WebP にし、`preload` で先に読む | `site/assets/hero-*.webp`、`site/template.html` |

ホーム画面に追加した時の名前（「業スー酒場」）と説明（「居酒屋の一品ネタ帳」）は、manifest と `apple-mobile-web-app-title` に残してある。ページの description だけを検索用の長い文にした。

## 業スー酒場だけの工夫

- 品は載せる日が来た朝に JavaScript で表に出す。HTML に書き込む一覧は作った日までの品だけなので、**ページを毎日 0:05（日本時間）に作り直す**（`.github/workflows/pages.yml` の `schedule`）。作り直しが遅れても、表の表示は JavaScript が載せる日に合わせる

## 公開後に人がすること（スキルの手順8）

1. **Google Search Console**（https://search.google.com/search-console ）で、「ドメイン」プロパティとして `uniiqcode.com` を登録する（一度だけ。DNS に TXT レコードを足す。uniiqcode.com は Cloudflare で管理している）
2. 「サイトマップ」で `https://uniiqcode.com/gyosu-sakaba/sitemap.xml` を送信する
3. 「URL 検査」で `https://uniiqcode.com/gyosu-sakaba/` を調べ、「インデックス登録をリクエスト」
4. **Bing Webmaster Tools**（https://www.bing.com/webmasters ）は、Search Console から取り込める

## 確かめ方

- X の投稿画面や LINE に URL を貼り、夜の路地の絵とタイトルが出る
- Google の「リッチリザルト テスト」（https://search.google.com/test/rich-results ）に URL を入れて、エラーがない
- PageSpeed Insights（https://pagespeed.web.dev/ ）でスマホの LCP が 2.5 秒以内

## 訪問者数のカウンター（2026-11-08）

- 数えるのは **GoatCounter**（無料、Cookie を使わない）。サイトのコードは `gyosusakaba`（コンビニ24Hと同じアカウントの2つ目のサイト）
- ページに計測用のコード（`https://gc.zgo.at/count.js`、`data-goatcounter="https://gyosusakaba.goatcounter.com/count"`）を入れた
- 毎日0:05のページの作り直しの時に、GoatCounter の API（`/api/v0/stats/total`）から、数え始めた日（2026-11-08）から前日までの訪問者数を受け取り、ページの最後に「訪問者数 ○○人（○月○日時点）」と書く。受け取れなかった日は書かない
- API のトークンは GitHub の Secrets `GOATCOUNTER_TOKEN`（権限は Read statistics だけ、サイトは gyosusakaba だけ）。ページには出さない
- ページの最後に「訪問者数は GoatCounter で数えています（個人を特定する情報は保存しません）」と書いた
