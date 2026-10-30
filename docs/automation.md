# 自動更新のしくみ

毎朝、プログラムが新しい動画・記事を集めて、今日の1品を選び、PR を作る。人は PR を確かめてマージするだけ。マージすると、ページが自動で更新される。

## 毎日の流れ

```
5:10（日本時間）  GitHub Actions「毎日の更新」が動く
  1. 集める        YouTube（API）と RSS から新しい動画・記事を探す           scripts/collect.py
                   → config/rules.toml のキーワードで「載せるか」「どこに分けるか」を決める
                   → 載せるものは「ストック」（data/stock.json）に入れる
  2. 今日の1品     ストックから1品（とまとめ1件）を選び、data/recipes.json に移す  scripts/publish.py
                   選び方: 区分が決まっているもの → 投稿日が新しいもの
  3. PR を作る     「毎日の更新 2026-11-01」という PR が届く
人                 PR を確かめてマージ（料理名・区分が違っていたら直してからマージ）
マージしたら       GitHub Actions「ページの公開」が動き、ページが更新される     scripts/build_site.py
```

- 一度見た URL は `data/seen.tsv` に記録して、二度と見ない（載せなかったものも、理由と一緒に記録する）
- PR をマージしないまま次の朝になると、その PR は次の日の内容で置き換わる。その日の1品はストックに戻り、また選ばれる
- 収集は無料の範囲だけ（YouTube の API は1日10,000の無料枠のうち約1,600を使う。AI の API は使わない）

## PR で見るところ

PR の説明に、今日載せるもの（料理名・区分・札・元のタイトルとリンク）と、集めた件数が書いてある。

- **料理名（`dish`）**: 元のタイトルから自動で作った下書き。おかしければ `data/recipes.json` の該当する行を直す
- **区分（`section`）**: 「未分類」なら、焼き物・揚げ物・煮物・炒め物・小鉢・〆 のどれかに直す
- **載せたくない**: その行を `data/recipes.json` から消してマージする（`data/seen.tsv` に残るので、二度と拾わない）

直し方がわからなければ、PR の URL を Claude に渡して「この PR の料理名を〇〇に直して」と頼めばよい。

## 最初に人がすること（1回だけ）

### 1. YouTube の API キーを作る

1. https://console.cloud.google.com/ を開き、プロジェクトを作る（名前は `gyosu-sakaba` など）
2. 「API とサービス」→「ライブラリ」で **YouTube Data API v3** を探して「有効にする」
3. 「API とサービス」→「認証情報」→「認証情報を作成」→「API キー」
4. できたキーの「キーを制限」で、「API の制限」を **YouTube Data API v3 だけ** にする
5. キーをコピーする（チャットやファイルには貼らない）

### 2. キーを GitHub に登録する

1. https://github.com/uniiqcode/gyosu-sakaba/settings/secrets/actions を開く
2. 「New repository secret」
3. Name に `YOUTUBE_API_KEY`、Secret にコピーしたキーを貼って保存

### 3. Actions が PR を作れるようにする

1. https://github.com/uniiqcode/gyosu-sakaba/settings/actions を開く
2. 一番下の「Workflow permissions」で **Read and write permissions** を選ぶ
3. **Allow GitHub Actions to create and approve pull requests** にチェックを入れて保存

### 4. GitHub Pages を有効にする

1. https://github.com/uniiqcode/gyosu-sakaba/settings/pages を開く
2. 「Build and deployment」の Source を **GitHub Actions** にする

### 5. 初回を手で動かす

1. https://github.com/uniiqcode/gyosu-sakaba/actions を開く
2. 「ページの公開」→「Run workflow」で、最初の101件のページを公開する（URL は `https://uniiqcode.github.io/gyosu-sakaba/`）
3. 「毎日の更新」→「Run workflow」で、1回目の収集を試す。PR が届けば完了。PR の「うまく取れなかったところ」に何か出ていたら、Claude に見せる

## 直したいとき

| 直したいこと | ファイル |
|---|---|
| 載せる・載せないの言葉、区分・札・調味料の言葉 | `config/rules.toml` |
| YouTube の検索語、RSS のフィード | `config/sources.toml` |
| 動く時刻 | `.github/workflows/daily.yml` の `cron`（UTC で書く。日本時間 −9時間） |
| ページの見た目 | `site/template.html` |

ルールを変えたら `python3 -m unittest discover -s tests` で確かめる（GitHub Actions でも毎朝確かめている）。
