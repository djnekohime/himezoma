#!/usr/bin/env python3
"""
愚痴聞き猫：SNS投稿用カード（1080×1080）を data/guchi.json から生成する。

    .venv\Scripts\python.exe scripts\make_guchi_card.py          # 全件
    .venv\Scripts\python.exe scripts\make_guchi_card.py 0 2      # 0番目と2番目だけ

出力: OUT_DIR/愚痴カード_{連番}.png
entries[].pen（ペンネーム・任意）、kind='sample' の場合は「例」表示が入る。
※ SNSに出してよいのは、フォームで「SNSでも取り上げてOK」を選んだものだけ。
"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = Path(r"C:/Users/himic/HIMEKA避難所/愚痴カード")  # ※Dドライブ不在中の暫定
FONTS = Path(r"C:/Windows/Fonts")
W = H = 1080
PINK = (204, 79, 136)
INK = (42, 32, 41)
MUTED = (120, 95, 108)

def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)

def wrap(d, text, fnt, max_w):
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur); cur = ""; continue
        if d.textlength(cur + ch, font=fnt) <= max_w or not cur:
            cur += ch
        else:
            lines.append(cur); cur = ch
    if cur:
        lines.append(cur)
    return lines

def fit(d, text, name, max_w, max_h, sizes, lh=1.5):
    for s in sizes:
        f = font(name, s)
        lines = wrap(d, text, f, max_w)
        if len(lines) * s * lh <= max_h:
            return f, lines, s
    f = font(name, sizes[-1])
    return f, wrap(d, text, f, max_w), sizes[-1]

def bg():
    top, bot = (255, 246, 236), (255, 222, 236)
    im = Image.new("RGB", (W, H))
    px = im.load()
    for y in range(H):
        t = y / (H - 1)
        c = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
        for x in range(W):
            px[x, y] = c
    return im

def circle_avatar(path, size):
    a = Image.open(path).convert("RGB").resize((size, size), Image.LANCZOS)
    m = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(m).ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=255)
    m = m.resize((size, size), Image.LANCZOS)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(a, (0, 0), m)
    return out

def rounded(im, box, r, fill, outline=None, width=0):
    d = ImageDraw.Draw(im, "RGBA")
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)

def make(entry, out):
    im = bg().convert("RGBA")
    d = ImageDraw.Draw(im, "RGBA")
    M = 60
    # ヘッダー
    f_pill = font("NotoSansJP-Bold.otf", 34)
    label = "愚痴聞き猫"
    tw = d.textlength(label, font=f_pill)
    rounded(im, (M, 50, M + tw + 56, 112), 31, PINK + (255,))
    d.text((M + 28, 60), label, font=f_pill, fill=(255, 255, 255))
    if entry.get("kind") == "sample":
        d.text((W - M - 130, 66), "※例です", font=font("NotoSansJP-Medium.otf", 28), fill=MUTED)

    # 愚痴カード
    pen = (entry.get("pen") or "").strip()
    who = f"— {pen} さん" if pen else "— 匿名さん"
    card_top, card_bot = 140, 470
    rounded(im, (M, card_top, W - M, card_bot), 34, (255, 255, 255, 235))
    inner_w = W - 2 * M - 80
    f, lines, s = fit(d, entry["text"], "NotoSansJP-Bold.otf", inner_w, card_bot - card_top - 130,
                      [54, 50, 46, 42, 38, 34, 30])
    y = card_top + 36
    d.text((M + 40, y - 6), "“", font=font("NotoSansJP-Bold.otf", 70), fill=PINK)
    y += 34
    for ln in lines:
        d.text((M + 40, y), ln, font=f, fill=INK)
        y += int(s * 1.5)
    d.text((W - M - 40 - d.textlength(who, font=font("NotoSansJP-Medium.otf", 28)), card_bot - 58),
           who, font=font("NotoSansJP-Medium.otf", 28), fill=MUTED)

    # 返事（吹き出し）
    av = 150
    replies = [("ひめか", entry["himeka"], "guchi-himeka.webp", "left"),
               ("ゾーマ", entry["zoma"], "guchi-zoma.webp", "right")]
    y = card_bot + 26
    box_h = 190
    for name, text, img, side in replies:
        avatar = circle_avatar(ROOT / "static/img" / img, av)
        bw = W - 2 * M - av - 24
        if side == "left":
            ax, bx = M, M + av + 24
        else:
            ax, bx = W - M - av, M
        ring = Image.new("RGBA", (av + 12, av + 12), (0, 0, 0, 0))
        ImageDraw.Draw(ring).ellipse((0, 0, av + 11, av + 11), fill=(255, 255, 255, 255))
        im.alpha_composite(ring, (ax - 6, y + 6))
        im.alpha_composite(avatar, (ax, y + 12))
        rounded(im, (bx, y, bx + bw, y + box_h), 30,
                (255, 255, 255, 235) if side == "left" else (255, 240, 246, 240))
        d.text((bx + 28, y + 12), name, font=font("NotoSansJP-Bold.otf", 26), fill=PINK)
        f2, l2, s2 = fit(d, text, "NotoSansJP-Medium.otf", bw - 56, box_h - 62, [34, 32, 30, 28, 26, 24, 22], lh=1.45)
        ty = y + 50
        for ln in l2:
            d.text((bx + 28, ty), ln, font=f2, fill=INK)
            ty += int(s2 * 1.45)
        y += box_h + 20

    # フッター
    f1 = font("NotoSansJP-Bold.otf", 30)
    d.text((M, H - 92), "愚痴・お悩み、匿名で受付中 → himezoma.pro/guchi", font=f1, fill=PINK)
    d.text((M, H - 52), "返事は猫キャラのことば（AI補助・管理人が確認）", font=font("NotoSansJP-Regular.otf", 22), fill=MUTED)
    im.convert("RGB").save(out, quality=95)

def main():
    data = json.loads((ROOT / "data/guchi.json").read_text(encoding="utf-8"))
    entries = data["entries"]
    idx = [int(a) for a in sys.argv[1:]] or range(len(entries))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for i in idx:
        out = OUT_DIR / f"愚痴カード_{i+1:02d}.png"
        make(entries[i], out)
        print("saved:", out)

if __name__ == "__main__":
    main()
