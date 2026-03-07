import json
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

headers = {"User-Agent": "Mozilla/5.0"}
ranking_url = "https://kabutan.jp/warning/?mode=2_1"

res = requests.get(ranking_url, headers=headers, timeout=30)
res.raise_for_status()
soup = BeautifulSoup(res.text, "lxml")

codes = []
for a in soup.select("a[href*='/stock/?code=']"):
    href = a.get("href", "")
    m = re.search(r"code=([0-9A-Z]+)", href)
    if m:
        code = m.group(1)
        if re.fullmatch(r"[0-9A-Z]{4}", code):
            codes.append(code)

codes = list(dict.fromkeys(codes))
codes = [c for c in codes if c not in ["0000", "0950", "0800", "0823"]]

ng_words = [
    "ストップ高／ストップ安", "均衡表", "ボリンジャー", "ゴールデンクロス",
    "デッドクロス", "MACD", "75日線", "25日線", "5日線", "移動平均",
    "引け", "前場", "後場", "本日の【", "レーティング", "市場ニュース",
    "今週の【話題株ダイジェスト】", "前日に動いた銘柄", "成長株特集",
    "第1弾", "テーマ株", "新興市場銘柄ダイジェスト", "本日の注目個別銘柄",
    "上場来高値銘柄", "相場展望"
]

rows = []
now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

for code in codes[:20]:
    url = f"https://kabutan.jp/stock/news?code={code}"
    try:
        res = requests.get(url, headers=headers, timeout=30)
        res.raise_for_status()
    except Exception:
        continue

    soup = BeautifulSoup(res.text, "lxml")

    for a in soup.select("a[href*='&b=n']")[:30]:
        title = a.get_text(strip=True)
        link = "https://kabutan.jp" + a.get("href", "")

        if title and not any(w in title for w in ng_words):
            rows.append({
                "code": code,
                "title": title,
                "url": link,
                "time": now_str,
            })
            break

with open("docs/material.json", "w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False, indent=2)
