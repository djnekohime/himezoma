# ひめかとゾーマの今日は何の日 (himezoma.pro)

白猫ひめか＆黒猫ゾーマ（HIMEZOMA / DJ猫姫・DJ猫）の「今日は何の日」図鑑。

## ビルド
```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python build.py --serve   # http://localhost:8001
```

## データ
- `data/kinenbi_master.json` … 記念日・年中行事 366日（日本語Wikipedia「M月D日」から自動抽出。scripts/extract_kinenbi.py）出典 CC BY-SA
- `data/birthflower.json` … 誕生花・花言葉・誕生石・石言葉・今日のひとこと 366日
- `data/today.json` … （未）ひめか＆ゾーマの語り・ラッキー・ことわざ等。ChatGPTエクスポートから合流予定
- `data/site.json` … サイト設定

## 状態
v0（図鑑パート）: 記念日＋誕生花＋ひとこと を日別表示。キャラ層・音楽・リンクハブは未完。
