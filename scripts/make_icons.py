"""site/assets/logo-mark.png（緑の文字だけ・背景は透明）から、アイコンの各サイズを作る。

使い方: python3 scripts/make_icons.py   （Pillow が必要: pip install pillow）
ロゴを差し替えたら、logo-mark.png を置き換えてこれを動かす。
"""
import pathlib

from PIL import Image

ASSETS = pathlib.Path(__file__).resolve().parent.parent / "site/assets"
WHITE = (255, 255, 255, 255)


def icon(mark, size, fill):
    """白の正方形の中央に、一辺の fill 割の大きさで文字を置く。"""
    canvas = Image.new("RGBA", (size, size), WHITE)
    side = round(size * fill)
    scale = side / max(mark.size)
    m = mark.resize((round(mark.width * scale), round(mark.height * scale)), Image.LANCZOS)
    canvas.alpha_composite(m, ((size - m.width) // 2, (size - m.height) // 2))
    return canvas.convert("RGB")


def main():
    mark = Image.open(ASSETS / "logo-mark.png").convert("RGBA")
    # ふつうのアイコン（iPhone・ブラウザのタブ・Android の切り抜かない表示）: 文字は一辺の84%
    for name, size in [("icon-192.png", 192), ("icon-512.png", 512), ("apple-touch-icon.png", 180)]:
        icon(mark, size, 0.84).save(ASSETS / name)
    # Android の丸・角丸に切り抜かれる用: 中心から直径80%の円に文字の四隅まで収める（一辺の56%）
    icon(mark, 512, 0.56).save(ASSETS / "icon-maskable-512.png")
    # ブラウザのタブ用。小さいので文字をできるだけ大きく
    icon(mark, 64, 0.94).save(ASSETS / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    print("site/assets にアイコンを作った")


if __name__ == "__main__":
    main()
