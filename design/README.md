# デザインの素材

| ファイル | 中身 |
|---|---|
| `chochin-reference.png` | 提灯に書く文字の見本（縦書き）。ロゴの文字を並べ、「スー」を小さく、「ー」を縦棒にした。ChatGPT に添付する |
| `chochin-prompt.md` | 提灯の絵を ChatGPT に頼むプロンプト |
| `chochin-chatgpt-original.png` | ChatGPT が作った提灯の絵（2026-10-31）。採用。「スー」は縦中横（横並び）、背景は黒（夜に灯っている表現） |
| `alley-prompt.md` | 夜の路地の絵（ページ上部の背景）を ChatGPT に頼むプロンプト |
| `alley-chatgpt-original.png` | ChatGPT が作った夜の路地の絵（2026-10-31）。採用。ページ上部の背景にした（`site/assets/hero-768.jpg`・`hero-1536.jpg` は縮めて軽くしたもの）。文字を重ねる下の方の暗いグラデーションはページ側（`site/template.html` の `.hero`）でかけている |
| `logo-chatgpt-original.webp` | ChatGPT が作ったロゴの元の画像（2026-10-30）。文字以外の緑（円・マスの線）があったので、Claude が消して `site/assets/logo-mark.png` にした。アイコン（タブ・ホーム画面）に使う。ページ上部は夜の路地の絵にしたので、ページには出していない |

## ロゴの決まり

- 文字は緑 `#0B6E4F`、背景は白 `#FFFFFF` の2色だけ
- 配置: 正方形を4つに分け、左上「業」・右上の下半分に小さく「スー」・左下「酒」・右下「場」
- 字体は居酒屋の看板のような太い筆文字。業務スーパーのロゴの書体や色（#009662）はまねない（公式と誤解されないため）

## アイコンの作り直し

`site/assets/logo-mark.png`（緑の文字だけ・背景は透明）を差し替えて、`python3 scripts/make_icons.py` を動かす（Pillow が必要）。

| 作られるもの | 用途 |
|---|---|
| `icon-192.png`、`icon-512.png` | Android のホーム画面（切り抜かない表示） |
| `icon-maskable-512.png` | Android の丸・角丸の切り抜き用。文字を直径80%の円に収めるため小さめ |
| `apple-touch-icon.png` | iPhone のホーム画面 |
| `favicon.ico` | ブラウザのタブ |

## 短冊のフォント

`strip-font-samples.png` は、短冊のフォント候補を縦書きで並べた見本（2026-10-31）。どれも Google Fonts で無料で使える。Darumadrop One は縦書きで文字が重なるので使えない。

**Yusei Magic に決定**（2026-10-31）。短冊（今日の一品・新着の縦書きの札）の料理名だけに使う。文字の大きさは `site/template.html` の `stripName()` で短冊ごとに決める（2行は幅いっぱい、1行は大きめ）。ドラフトは `strip-draft-yusei-magic.png`。

## 短冊の「新」の印

赤い油性マジック（`#D3261C`）で手書きした二重丸。画像ではなく `site/template.html` の `newMark()` で SVG として描く。短冊ごとに傾き（−6〜−18度）と丸のゆがみを変え、スタンプのように同じ形が並ばないようにしている（同じ短冊はいつも同じ形）。ドラフトは `strip-draft-new-mark.png`。
