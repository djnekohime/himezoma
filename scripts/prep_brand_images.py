# -*- coding: utf-8 -*-
"""背景画像・アイコンを web 用に用意する。
引数1: 背景(showroom)の元ファイル
引数2: アイコン(円形バッジ)の元ファイル
出力: static/img/ 配下
"""
import sys
from pathlib import Path
from PIL import Image

bg_src = Path(sys.argv[1])
ic_src = Path(sys.argv[2])
OUT = Path(__file__).resolve().parent.parent / "static" / "img"
OUT.mkdir(parents=True, exist_ok=True)

# --- 背景（トップ以外の固定背景） ---
bg = Image.open(bg_src).convert("RGB")
w = 1080
bg2 = bg.resize((w, round(bg.height * w / bg.width)), Image.LANCZOS)
bg2.save(OUT / "bg-showroom.jpg", "JPEG", quality=78, optimize=True, progressive=True)
print("bg-showroom.jpg", bg2.size, (OUT / "bg-showroom.jpg").stat().st_size // 1024, "KB")

# --- アイコン（円形バッジ・透過PNG） ---
ic = Image.open(ic_src).convert("RGBA")
for size, name in [(512, "icon-512.png"), (192, "icon-192.png"),
                   (180, "favicon-180.png"), (96, "avatar.png"),
                   (32, "favicon-32.png"), (16, "favicon-16.png")]:
    im = ic.resize((size, size), Image.LANCZOS)
    im.save(OUT / name, "PNG", optimize=True)
    print(name, (OUT / name).stat().st_size // 1024, "KB")

# OGP 用（1200x630、バッジを中央に、下地は淡いピンク金）
ogp = Image.new("RGB", (1200, 630), (247, 240, 231))
badge = ic.resize((560, 560), Image.LANCZOS)
ogp.paste(badge, (320, 35), badge)
ogp.save(OUT / "ogp-default.png", "PNG", optimize=True)
print("ogp-default.png", (OUT / "ogp-default.png").stat().st_size // 1024, "KB")
