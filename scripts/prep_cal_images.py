# -*- coding: utf-8 -*-
"""月別カレンダー画像を web 用にリサイズ・WebP 化する。
入力: scratchpad の cal2026 / cal2027（zip 展開済み）
割り当て: 1〜8月 = 2027年版 / 9〜12月 = 2026年版
出力: static/img/cal/01.webp 〜 12.webp
"""
from PIL import Image
from pathlib import Path
import sys

SP = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
OUT = Path(__file__).resolve().parent.parent / "static" / "img" / "cal"
OUT.mkdir(parents=True, exist_ok=True)

MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]

src = {}
for m in range(1, 9):
    src[m] = SP / "cal2027" / "cal_2027" / f"2027_{m:02d}_{MONTHS[m-1]}.png"
for m in range(9, 13):
    src[m] = SP / "cal2026" / "cal_2026" / f"2026_{m:02d}_{MONTHS[m-1]}.png"

W = 560
total = 0
for m, p in src.items():
    im = Image.open(p).convert("RGB")
    ratio = W / im.width
    im2 = im.resize((W, round(im.height * ratio)), Image.LANCZOS)
    out = OUT / f"{m:02d}.webp"
    im2.save(out, "WEBP", quality=82, method=6)
    kb = out.stat().st_size // 1024
    total += kb
    print(f"{m:02d}  <- {p.name}  ->  {out.name}  {im2.width}x{im2.height}  {kb}KB")
print(f"total {total} KB")
