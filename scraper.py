import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime

headers = {"User-Agent": "Mozilla/5.0"}

PTS_URL = "https://kabutan.jp/warning/pts_night_price_increase"
STOP_URL = "https://kabutan.jp/warning/?mode=3_1"

ng_words = [
    "ストップ高／ストップ安", "均衡表", "ボリンジャー",
    "ゴールデンクロス", "デッドクロス", "MACD",
    "75日線", "25日線", "5日線", "移動平均",
    "引け", "前場", "後場", "本日の【",
    "今週の【話題株ダイジェスト】", "前日に動いた銘柄",
    "成長株特集", "第1弾", "テーマ株",
    "市場ニュース", "レーティング", "相場展望"
]

IGNORE_CODES = {"0000", "0950", "0800", "0823"}

def get_soup(url: str) -> BeautifulSoup:
    res = requests.get(url, headers=headers, timeout=20)
    res.raise_for_status()
    return BeautifulSoup(res.text, "lxml")

def extract_codes_from_ranking(url: str, limit: int = 20) -> list[str]:
    soup = get_soup(url)
    codes = []

    for a in soup.select("a[href*='/stock/?code=']"):
        href = a.get("href", "")
        m = re.search(r"code=([0-9A-Z]+)", href)
        if not m:
            continue
        code = m.group(1)
        if re.fullmatch(r"[0-9A-Z]{4}", code) and code not in IGNORE_CODES:
            codes.append(code)

    codes = list(dict.fromkeys(codes))
    return codes[:limit]

def pick_material(code: str) -> tuple[str, str]:
    url = f"https://kabutan.jp/stock/news?code={code}"
    soup = get_soup(url)

    for a in soup.select("a[href*='&b=n']")[:40]:
        title = a.get_text(strip=True)
        link = "https://kabutan.jp" + a["href"]

        if not any(word in title for word in ng_words):
            return title, link

    return "", ""

def build_rows(label: str, ranking_url: str, limit: int = 20) -> list[dict]:
    rows = []
    codes = extract_codes_from_ranking(ranking_url, limit=limit)

    for rank, code in enumerate(codes, start=1):
        title, link = pick_material(code)
        rows.append({
            "category": label,   # "PTS" or "S高"
            "rank": rank,
            "code": code,
            "title": title,
            "url": link,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M")
        })

    return rows

def main():
    rows = []
    rows += build_rows("PTS", PTS_URL, limit=20)
    rows += build_rows("S高", STOP_URL, limit=20)

    with open("docs/material.json", "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
