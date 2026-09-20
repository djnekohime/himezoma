#!/usr/bin/env python3
r"""
愚痴聞き猫：ひめか(Kuon)・ゾーマ(Otani) の返事を ElevenLabs で音声化する。

準備（1回だけ）: ElevenLabs の API キーを環境変数 ELEVENLABS_API_KEY に入れる
  （または C:\Users\himic\.elevenlabs_key というテキストファイルに1行で保存。リポジトリの外）。
  ※キーはチャットに貼らない・リポジトリに入れない。

    .venv\Scripts\python.exe scripts\make_guchi_voice.py --list          # 声の名前とIDを確認
    .venv\Scripts\python.exe scripts\make_guchi_voice.py                 # 全件
    .venv\Scripts\python.exe scripts\make_guchi_voice.py 0 2             # 0番目と2番目だけ

入力: data/guchi.json の entries[].himeka / zoma
出力: OUT_DIR/愚痴NN_ひめか.mp3, 愚痴NN_ゾーマ.mp3
設定: さくらが使っている既存の設定に合わせる（stability .5 / similarity .75 / speed 1.0、モデル v3）。
"""
import json, os, sys, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = Path(r"C:/Users/himic/HIMEKA避難所/愚痴カード/音声")  # ※Dドライブ不在中の暫定
KEY_FILE = Path(r"C:/Users/himic/.elevenlabs_key")
VOICES = {"ひめか": "kuon", "ゾーマ": "otani"}  # ElevenLabs 上の声の名前（大文字小文字は無視）
MODEL = "eleven_v3"
SETTINGS = {"stability": 0.5, "similarity_boost": 0.75, "speed": 1.0}
API = "https://api.elevenlabs.io/v1"


def api_key():
    k = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not k and KEY_FILE.exists():
        k = KEY_FILE.read_text(encoding="utf-8").strip()
    if not k:
        sys.exit("ELEVENLABS_API_KEY が見つかりません。環境変数か %s に入れてください。" % KEY_FILE)
    return k


def call(method, path, key, body=None):
    req = urllib.request.Request(API + path, method=method,
                                 data=json.dumps(body).encode() if body else None,
                                 headers={"xi-api-key": key, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        sys.exit("ElevenLabs エラー %s: %s" % (e.code, e.read().decode("utf-8", "ignore")[:300]))


def voice_ids(key):
    data = json.loads(call("GET", "/voices", key))
    return {v["name"].lower(): v["voice_id"] for v in data.get("voices", [])}, data.get("voices", [])


def main():
    key = api_key()
    ids, voices = voice_ids(key)
    if "--list" in sys.argv:
        for v in voices:
            print(v["name"], v["voice_id"])
        return
    need = {}
    for who, name in VOICES.items():
        match = [vid for n, vid in ids.items() if name in n]
        if not match:
            sys.exit("声が見つかりません: %s（--list で名前を確認して、VOICES を直してください）" % name)
        need[who] = match[0]
    entries = json.loads((ROOT / "data/guchi.json").read_text(encoding="utf-8"))["entries"]
    idx = [int(a) for a in sys.argv[1:] if a.isdigit()] or range(len(entries))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for i in idx:
        for who, field in (("ひめか", "himeka"), ("ゾーマ", "zoma")):
            audio = call("POST", "/text-to-speech/%s?output_format=mp3_44100_128" % need[who], key,
                         {"text": entries[i][field], "model_id": MODEL,
                          "language_code": "ja", "voice_settings": SETTINGS})
            out = OUT_DIR / ("愚痴%02d_%s.mp3" % (i + 1, who))
            out.write_bytes(audio)
            print("saved:", out)


if __name__ == "__main__":
    main()
