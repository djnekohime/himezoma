#!/usr/bin/env python3
"""
ひめかとゾーマの今日は何の日 — 静的サイトジェネレーター（v0：図鑑パート）

使い方:
    python build.py            # dist/ に書き出し
    python build.py --serve    # ビルドしてローカルプレビュー (http://localhost:8001)

データの流れ:
    data/kinenbi_master.json … 366日ぶんの記念日（日本語Wikipedia「M月D日」から自動抽出・出典つき）
    data/today.json          … （後日）ひめか＆ゾーマの語り・ラッキー・ことわざ等（ChatGPTエクスポートから合流）
    data/site.json           … サイト名・SNS・ドメイン
        ↓ build.py が読み込んで
    dist/                    … 完成HTML一式（GitHub Pages 等にそのまま置ける）

方針: 依存は Jinja2 だけ。1年後に読んで直せる素朴な作り。
      「骨（記念日データ）」＝この v0 で表示。「皮（キャラの語り）」＝today.json が来たら各日ページに合流。
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).parent
DATA = ROOT / "data"
DIST = ROOT / "dist"
STATIC = ROOT / "static"
TEMPLATES = ROOT / "templates"

MONTH_LABELS = ["1月", "2月", "3月", "4月", "5月", "6月",
                "7月", "8月", "9月", "10月", "11月", "12月"]

# 角度（切り口）— kinenbi_master には角度タグが無いので説明文から推定する
ANGLES = [
    ("gororo", "語呂合わせの日"),
    ("world", "世界の国の記念日"),
    ("koyomi", "暦・季節（二十四節気など）"),
    ("seitei", "制定された記念日"),
    ("gyoji", "年中行事・お祭り・その他"),
]
ANGLE_LABEL = dict(ANGLES)

_SEKKI = set("立春 雨水 啓蟄 春分 清明 穀雨 立夏 小満 芒種 夏至 小暑 大暑 "
             "立秋 処暑 白露 秋分 寒露 霜降 立冬 小雪 大雪 冬至 小寒 大寒".split())


def guess_angle(item: dict) -> str:
    title = item.get("title", "")
    desc = item.get("description", "")
    country = item.get("country", "")
    text = title + " " + desc
    if title in _SEKKI or "二十四節気" in desc:
        return "koyomi"
    if re.search(r"語呂合(わ)?せ|の語呂|と読む", desc):
        return "gororo"
    if re.search(r"独立記念日|建国記念|革命記念|国慶|ナショナルデー|解放記念日", title) or (
        country and country not in ("日本", "") and re.search(r"\d{3,4}年", desc)):
        return "world"
    if re.search(r"制定|協会|委員会|連合会|株式会社|日本記念日協会|が定め", desc):
        return "seitei"
    return "gyoji"


def load_json(name: str, default):
    p = DATA / name
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def make_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    return env


def write(path_from_dist: str, html: str) -> None:
    out = DIST / path_from_dist.lstrip("/")
    if out.suffix != ".html":
        out = out / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")


def write_raw(path_from_dist: str, text: str) -> None:
    out = DIST / path_from_dist.lstrip("/")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")


def build(serve: bool = False) -> None:
    site = load_json("site.json", {})
    kinenbi = load_json("kinenbi_master.json", [])
    today_layer = {d["date"]: d for d in load_json("today.json", [])}  # 後日合流用
    flower_by_date = {d["date"]: d for d in load_json("birthflower.json", [])}  # 誕生花・誕生石・ひとこと
    base = f"https://{site.get('domain', 'example.com')}"
    env = make_env()

    # 日付ごとに整形（角度を付与、キャラ層があれば合流）
    days = []
    for rec in kinenbi:
        date = rec["date"]                       # "MM-DD"
        m, d = int(date[:2]), int(date[3:])
        items = []
        for it in rec.get("items", []):
            it = dict(it)
            it["angle"] = guess_angle(it)
            items.append(it)
        layer = today_layer.get(date, {})
        days.append({
            "date": date,
            "month": m,
            "day": d,
            "slug": f"/today/{date}/",
            "label": f"{m}月{d}日",
            "source": rec.get("source", ""),
            "items": items,
            "count": len(items),
            "layer": layer,          # theme_line / story / lucky_item ... （無ければ {}）
            "flower": flower_by_date.get(date, {}),   # 誕生花・誕生石・今日のひとこと
        })
    days.sort(key=lambda x: (x["month"], x["day"]))
    by_date = {x["date"]: x for x in days}
    by_month = {mo: [x for x in days if x["month"] == mo] for mo in range(1, 13)}

    # 角度別（全日から該当項目を集める）
    by_angle = {key: [] for key, _ in ANGLES}
    for x in days:
        for it in x["items"]:
            by_angle[it["angle"]].append({"day": x, "item": it})

    ctx = dict(site=site, month_labels=MONTH_LABELS, angles=ANGLES,
               angle_label=ANGLE_LABEL, base=base)

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    if STATIC.exists():
        shutil.copytree(STATIC, DIST / "static")
    for name in ("robots.txt", "favicon.ico", "CNAME", "ads.txt"):
        src = ROOT / name
        if src.exists():
            shutil.copy2(src, DIST / name)

    total_items = sum(x["count"] for x in days)

    # --- トップ ---
    write("/index.html", env.get_template("home.html").render(
        **ctx,
        breadcrumbs=[],
        total_items=total_items,
        by_month=by_month,
    ))

    # --- 今日は何の日 図鑑トップ（12か月） ---
    write("/today/index.html", env.get_template("today_index.html").render(
        **ctx,
        breadcrumbs=[("ホーム", "/"), ("今日は何の日", None)],
        by_month=by_month,
        total_items=total_items,
        og_title="今日は何の日 図鑑（366日）",
        og_url=base + "/today/",
    ))

    # --- 月ごと ---
    tmpl_month = env.get_template("today_month.html")
    for mo in range(1, 13):
        ds = by_month[mo]
        write(f"/today/{mo:02d}/", tmpl_month.render(
            **ctx,
            breadcrumbs=[("ホーム", "/"), ("今日は何の日", "/today/"),
                         (MONTH_LABELS[mo - 1], None)],
            month=mo, month_label=MONTH_LABELS[mo - 1], days=ds,
            month_items=sum(x["count"] for x in ds),
            prev_m=(mo - 1 or 12), next_m=(mo % 12 + 1),
            og_title=f"{MONTH_LABELS[mo-1]}は何の日？ 記念日・年中行事一覧",
            og_url=base + f"/today/{mo:02d}/",
        ))

    # --- 1日ごと（366ページ） ---
    tmpl_day = env.get_template("today_day.html")
    for i, x in enumerate(days):
        prev_d = days[i - 1] if i > 0 else days[-1]
        next_d = days[i + 1] if i < len(days) - 1 else days[0]
        by_angle_here = {}
        for it in x["items"]:
            by_angle_here.setdefault(it["angle"], []).append(it)
        ordered = [(k, ANGLE_LABEL[k], by_angle_here[k]) for k, _ in ANGLES if k in by_angle_here]
        head_names = "・".join(it["title"] for it in x["items"][:3])
        write(x["slug"], tmpl_day.render(
            **ctx,
            breadcrumbs=[("ホーム", "/"), ("今日は何の日", "/today/"),
                         (MONTH_LABELS[x["month"] - 1], f"/today/{x['month']:02d}/"),
                         (x["label"], None)],
            d=x, groups=ordered, prev_d=prev_d, next_d=next_d,
            og_title=f"{x['label']}は何の日？（{x['count']}件）",
            og_description=f"{x['label']}の記念日・年中行事：{head_names} ほか。由来つきで{x['count']}件。",
            og_url=base + x["slug"],
        ))

    # --- 角度（切り口）ごと ---
    tmpl_angle = env.get_template("angle.html")
    write("/kirikuchi/index.html", env.get_template("angle_index.html").render(
        **ctx,
        breadcrumbs=[("ホーム", "/"), ("切り口から探す", None)],
        counts={k: len(by_angle[k]) for k, _ in ANGLES},
    ))
    for key, label in ANGLES:
        rows = by_angle[key]
        write(f"/kirikuchi/{key}/", tmpl_angle.render(
            **ctx,
            breadcrumbs=[("ホーム", "/"), ("切り口から探す", "/kirikuchi/"), (label, None)],
            angle_key=key, angle_title=label, rows=rows, total=len(rows),
            og_title=f"{label}｜今日は何の日", og_url=base + f"/kirikuchi/{key}/",
        ))

    # --- リンク / 音楽（スタブ） ---
    write("/links/index.html", env.get_template("links.html").render(
        **ctx, breadcrumbs=[("ホーム", "/"), ("リンク", None)]))
    write("/music/index.html", env.get_template("music.html").render(
        **ctx, breadcrumbs=[("ホーム", "/"), ("HIMEZOMA / 音楽", None)]))
    write("/about/index.html", env.get_template("about.html").render(
        **ctx, breadcrumbs=[("ホーム", "/"), ("このサイトについて", None)]))
    write("/404.html", env.get_template("404.html").render(**ctx, breadcrumbs=[]))

    # --- sitemap / robots ---
    locs = []
    for f in sorted(DIST.rglob("*.html")):
        rel = f.relative_to(DIST).as_posix()
        if rel == "404.html":
            continue
        path = rel[:-len("index.html")] if rel.endswith("index.html") else rel
        locs.append(f"  <url><loc>{base}/{path}</loc></url>")
    write_raw("/sitemap.xml",
              '<?xml version="1.0" encoding="UTF-8"?>\n'
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
              + "\n".join(locs) + "\n</urlset>\n")
    if not (ROOT / "robots.txt").exists():
        write_raw("/robots.txt", f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n")

    pages = sum(1 for _ in DIST.rglob("*.html"))
    filled = sum(1 for x in days if x["layer"])
    fl = sum(1 for x in days if x["flower"])
    print(f"[OK] ビルド完了: {pages} ページ / 記念日 {total_items} 件 / "
          f"誕生花 {fl}/366 日 / キャラ層 {filled}/366 日 / 出力 {DIST}")
    if serve:
        _serve()


def _serve(port: int = 8001) -> None:
    import functools, http.server, socketserver
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DIST))
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"プレビュー: http://localhost:{port}  (Ctrl+C で停止)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n停止しました。")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--serve", action="store_true")
    args = ap.parse_args()
    build(serve=args.serve)
