# -*- coding: utf-8 -*-
"""日本語Wikipediaの「M月D日」ページ366枚から「記念日・年中行事」節を抽出する。
出力: kinenbi_master.json  (CC-BY-SA / 出典 = 各日付ページ)
"""
import json, re, time, sys, urllib.parse, urllib.request, calendar

API = "https://ja.wikipedia.org/w/api.php"
UA = "himezoma-kinenbi-collector/1.0 (personal project; contact via project owner)"

# よく出る国テンプレ -> 日本語表記（抜けは括弧ごと落とす）
CC = {
 "JPN":"日本","USA":"アメリカ","GBR":"イギリス","FRA":"フランス","DEU":"ドイツ","CHN":"中国",
 "KOR":"韓国","PRK":"北朝鮮","RUS":"ロシア","ITA":"イタリア","ESP":"スペイン","CAN":"カナダ",
 "AUS":"オーストラリア","IND":"インド","BRA":"ブラジル","ARG":"アルゼンチン","MEX":"メキシコ",
 "IDN":"インドネシア","THA":"タイ","VNM":"ベトナム","PHL":"フィリピン","MYS":"マレーシア",
 "SGP":"シンガポール","TUR":"トルコ","EGY":"エジプト","ZAF":"南アフリカ","NGA":"ナイジェリア",
 "KEN":"ケニア","POL":"ポーランド","UKR":"ウクライナ","NLD":"オランダ","BEL":"ベルギー",
 "CHE":"スイス","SWE":"スウェーデン","NOR":"ノルウェー","DNK":"デンマーク","FIN":"フィンランド",
 "AUT":"オーストリア","GRC":"ギリシャ","PRT":"ポルトガル","IRL":"アイルランド","NZL":"ニュージーランド",
 "CUB":"キューバ","CHL":"チリ","PER":"ペルー","COL":"コロンビア","VEN":"ベネズエラ",
 "ISR":"イスラエル","SAU":"サウジアラビア","IRN":"イラン","IRQ":"イラク","PAK":"パキスタン",
 "BGD":"バングラデシュ","LKA":"スリランカ","MMR":"ミャンマー","NPL":"ネパール","MNG":"モンゴル",
 "TWN":"台湾","HKG":"香港","HUN":"ハンガリー","CZE":"チェコ","SVK":"スロバキア","ROU":"ルーマニア",
 "BGR":"ブルガリア","HRV":"クロアチア","SRB":"セルビア","SVN":"スロベニア","LTU":"リトアニア",
 "LVA":"ラトビア","EST":"エストニア","ISL":"アイスランド","LUX":"ルクセンブルク",
 "ROC":"中華民国","VAT":"バチカン","SCO":"スコットランド","WAL":"ウェールズ","ENG":"イングランド",
 "NIR":"北アイルランド","CAT":"カタルーニャ","PSE":"パレスチナ","MAR":"モロッコ","DZA":"アルジェリア",
 "TUN":"チュニジア","LBY":"リビア","ETH":"エチオピア","GHA":"ガーナ","TZA":"タンザニア",
 "UGA":"ウガンダ","ZWE":"ジンバブエ","ZMB":"ザンビア","AGO":"アンゴラ","MOZ":"モザンビーク",
 "SEN":"セネガル","CIV":"コートジボワール","CMR":"カメルーン","COD":"コンゴ民主共和国",
 "COG":"コンゴ共和国","MDG":"マダガスカル","BOL":"ボリビア","PRY":"パラグアイ","URY":"ウルグアイ",
 "ECU":"エクアドル","GTM":"グアテマラ","HND":"ホンジュラス","NIC":"ニカラグア","CRI":"コスタリカ",
 "PAN":"パナマ","DOM":"ドミニカ共和国","JAM":"ジャマイカ","HTI":"ハイチ","BRN":"ブルネイ",
 "KHM":"カンボジア","LAO":"ラオス","BTN":"ブータン","MDV":"モルディブ","AFG":"アフガニスタン",
 "SDN":"スーダン","SSD":"南スーダン","SOM":"ソマリア","YEM":"イエメン","JOR":"ヨルダン",
 "LBN":"レバノン","SYR":"シリア","KWT":"クウェート","ARE":"アラブ首長国連邦","QAT":"カタール",
 "BHR":"バーレーン","OMN":"オマーン","FJI":"フィジー","PNG":"パプアニューギニア","SLB":"ソロモン諸島",
}

def fetch_wikitext(page):
    return fetch_many([page])[page]

def fetch_many(pages):
    """action=query で最大50ページのwikitextを一括取得。{page: wikitext} を返す。"""
    q = urllib.parse.urlencode({
        "action":"query","prop":"revisions","rvprop":"content","rvslots":"main",
        "titles":"|".join(pages),"format":"json","formatversion":"2","redirects":"1"})
    req = urllib.request.Request(API+"?"+q, headers={"User-Agent":UA, "Api-User-Agent":UA})
    last = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                d = json.load(r)
            break
        except Exception as e:
            last = e
            time.sleep(5 * (attempt+1))
    else:
        raise last
    # redirects/normalized で返りタイトルが変わるので元タイトルへ寄せ直す
    norm = {n["from"]: n["to"] for n in d.get("query",{}).get("normalized",[])}
    redir = {r["from"]: r["to"] for r in d.get("query",{}).get("redirects",[])}
    by_title = {}
    for pg in d.get("query",{}).get("pages",[]):
        t = pg.get("title","")
        wt = ""
        try:
            wt = pg["revisions"][0]["slots"]["main"]["content"]
        except Exception:
            wt = ""
        by_title[t] = wt
    out = {}
    for p in pages:
        t = redir.get(norm.get(p, p), norm.get(p, p))
        out[p] = by_title.get(t, "")
    return out

def strip_refs(s):
    s = re.sub(r"<ref[^>]*/>", "", s)
    s = re.sub(r"<ref[^>]*>.*?</ref>", "", s, flags=re.S)
    return s

def clean_templates(s):
    # {{仮リンク|表示|...}} / {{ill|...}} -> 表示（label= があれば優先、無ければ第1引数）
    def il(m):
        body = m.group(1)
        parts = [p.strip() for p in body.split("|")]
        for p in parts:
            if p.startswith("label="):
                return p.split("=",1)[1].strip()
        return parts[0] if parts else ""
    for _ in range(3):
        s = re.sub(r"\{\{(?:仮リンク|Link-interwiki|ill|Ill|interlang)\|([^{}]*)\}\}", il, s)
    # 国テンプレ {{JPN}} など
    def cc(m):
        code = m.group(1).strip().upper()
        return CC.get(code, "")
    s = re.sub(r"\{\{([A-Za-z]{2,4})\}\}", cc, s)
    # 和暦・Cite・その他テンプレは丸ごと除去（ネスト対応で数回）
    for _ in range(6):
        s2 = re.sub(r"\{\{[^{}]*\}\}", "", s)
        if s2 == s: break
        s = s2
    return s

def clean_links(s):
    s = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"\[\[([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"\[https?://[^\s\]]+\s+([^\]]*)\]", r"\1", s)
    s = re.sub(r"\[https?://[^\s\]]+\]", "", s)
    return s

def clean_all(s):
    s = strip_refs(s)
    s = clean_templates(s)
    s = clean_links(s)
    s = s.replace("'''","").replace("''","")
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"[ \t　]+", " ", s)
    return s.strip(" 　:：-—・\n")

KNOWN_COUNTRIES = set(CC.values()) | {
 "日本","中華民国","中華人民共和国","朝鮮","ソ連","西ドイツ","東ドイツ","EU","欧州連合",
 "国連","スコットランド","ウェールズ","北アイルランド","イングランド","カタルーニャ",
 "ベラルーシ","カザフスタン","ウズベキスタン","ジョージア","アルメニア","アゼルバイジャン",
 "モルドバ","北マケドニア","ボスニア・ヘルツェゴビナ","モンテネグロ","コソボ","キプロス",
 "マルタ","モナコ","リヒテンシュタイン","アンドラ","サンマリノ","バチカン",
}

def split_country(head):
    """見出し末尾の（…）を分離。国名っぽければ country、そうでなければ note に。"""
    head = strip_refs(head).rstrip()
    cm = re.search(r"[（(]\s*([^（）()]*?)\s*[)）]\s*$", head)
    if not cm:
        return head, "", ""
    inside_raw = cm.group(1)
    had_cc_tpl = bool(re.search(r"\{\{[A-Za-z]{2,4}\}\}", inside_raw))
    inside = clean_all(inside_raw)
    rest = head[:cm.start()].rstrip()
    if not inside:
        return rest, "", ""
    # 「日本、1966年」「{{JPN}} 秋田県」等 → 国名部分と残り(note)に割る
    m2 = re.match(r"^(" + "|".join(map(re.escape, sorted(KNOWN_COUNTRIES, key=len, reverse=True))) + r")(?:[ 　、,](.*))?$", inside)
    if had_cc_tpl:
        if m2:
            return rest, m2.group(1), (m2.group(2) or "").strip()
        return rest, inside, ""
    if inside in KNOWN_COUNTRIES and not re.search(r"[0-9。．]", inside):
        return rest, inside, ""
    if m2 and not re.search(r"[0-9。．]", m2.group(1)):
        return rest, m2.group(1), (m2.group(2) or "").strip()
    return rest, "", inside  # note

def parse_section(wt):
    m = re.search(r"==\s*記念日(?:・年中行事)?\s*==(.*?)(?=\n==[^=]|\Z)", wt, re.S)
    if not m:
        return []
    body = strip_refs(m.group(1))
    items = []
    cur = None
    for raw in body.splitlines():
        line = raw.rstrip()
        if re.match(r"^\*:", line):            # 説明行
            desc = clean_all(re.sub(r"^\*:\s*", "", line))
            if cur is not None:
                cur["description"] = (cur.get("description","") + desc).strip()
            continue
        if re.match(r"^\*[^:*]", line) or re.match(r"^\*\s", line):  # 見出し行
            if cur: items.append(cur)
            head = re.sub(r"^\*+\s*", "", line)
            notes = []
            country = ""
            for _ in range(2):  # 「名称（英名）（国）」を2段はがす
                head, c, n = split_country(head)
                if c and not country: country = c
                if n: notes.append(n)
                if not c and not n: break
            note = " / ".join(dict.fromkeys(notes))
            title = clean_all(head)
            title = re.sub(r"[（(]\s*[)）]", "", title).strip(" 　")
            # 記念日名ではなくリード文（長い＋句点）は除外
            if title and not (len(title) > 32 and "。" in title):
                cur = {"title": title, "country": country, "note": note, "description": ""}
            else:
                cur = None
            continue
        # サブ箇条書き等は無視
    if cur: items.append(cur)
    # 空説明も残す（あとで手当てできるよう）
    return items

def main():
    # 全366ページ名
    dates = []
    for month in range(1, 13):
        for day in range(1, calendar.monthrange(2024, month)[1]+1):
            dates.append((month, day, f"{month}月{day}日"))
    out = []
    total = 0
    for i in range(0, len(dates), 40):
        chunk = dates[i:i+40]
        wtmap = fetch_many([c[2] for c in chunk])
        for month, day, page in chunk:
            wt = wtmap.get(page, "")
            items = parse_section(wt) if wt else []
            total += len(items)
            out.append({
                "date": f"{month:02d}-{day:02d}",
                "source": f"https://ja.wikipedia.org/wiki/{urllib.parse.quote(page)}",
                "items": items,
            })
            print(f"{page}: {len(items)}件" + ("  <<EMPTY WIKITEXT>>" if not wt else ""))
        time.sleep(1)
    with open("kinenbi_master.json","w",encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    empties = [o["date"] for o in out if not o["items"]]
    print(f"\n=== 完了: {len(out)}日 / 記念日 合計 {total}件 -> kinenbi_master.json ===")
    print(f"0件の日: {empties}")

if __name__ == "__main__":
    main()
