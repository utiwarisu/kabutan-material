import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime
from urllib.parse import urljoin

headers = {
    "User-Agent": "Mozilla/5.0"
}

PTS_URL = "https://kabutan.jp/warning/pts_night_price_increase"
STOP_URL = "https://kabutan.jp/warning/?mode=3_1"

IGNORE_CODES = {"0000", "0950", "0800", "0823"}

ng_words = [
    "ストップ高／ストップ安", "均衡表", "ボリンジャー",
    "ゴールデンクロス", "デッドクロス", "MACD",
    "75日線", "25日線", "5日線", "移動平均",
    "引け", "前場", "後場", "本日の【",
    "今週の【話題株ダイジェスト】", "前日に動いた銘柄",
    "成長株特集", "第1弾", "テーマ株",
    "市場ニュース", "レーティング", "相場展望",
    "新興市場銘柄ダイジェスト", "本日の注目個別銘柄",
    "上場来高値銘柄"
]

def get_soup(url: str) -> BeautifulSoup:
    res = requests.get(url, headers=headers, timeout=20)
    res.raise_for_status()
    return BeautifulSoup(res.text, "lxml")

def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def extract_ranked_stocks(url: str, limit: int = 20) -> list[dict]:
    soup = get_soup(url)
    stocks = []
    seen = set()

    # ランキングページ内の個別銘柄リンクを順番に拾う
    for a in soup.select("a[href*='/stock/?code=']"):
        href = a.get("href", "")
        m = re.search(r"code=([0-9A-Z]+)", href)
        if not m:
            continue

        code = m.group(1)
        if code in IGNORE_CODES:
            continue
        if not re.fullmatch(r"[0-9A-Z]{4}", code):
            continue
        if code in seen:
            continue

        name = normalize_text(a.get_text())
        if not name:
            continue

        stocks.append({
            "code": code,
            "name": name
        })
        seen.add(code)

        if len(stocks) >= limit:
            break

    return stocks

def extract_article_date(text: str) -> str:
    text = normalize_text(text)

    m = re.search(r"(\d{2}/\d{2}\s+\d{2}:\d{2})", text)
    if m:
        return m.group(1)

    m = re.search(r"(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2})", text)
    if m:
        return m.group(1)

    return ""

def pick_materials(code: str, max_items: int = 3) -> list[dict]:
    url = f"https://kabutan.jp/stock/news?code={code}"
    soup = get_soup(url)

    materials = []
    seen_titles = set()

    # まずニュースリンクを直接拾う
    for a in soup.select("a[href*='&b=n']"):
        title = normalize_text(a.get_text())
        if not title:
            continue
        if title in seen_titles:
            continue
        if any(word in title for word in ng_words):
            continue

        link = urljoin("https://kabutan.jp", a.get("href", ""))

        # 親要素の文字列から日付を拾う
        parent_text = ""
        if a.parent:
            parent_text = normalize_text(a.parent.get_text(" "))
        if not parent_text and a.parent and a.parent.parent:
            parent_text = normalize_text(a.parent.parent.get_text(" "))

        article_date = extract_article_date(parent_text)

        materials.append({
            "title": title,
            "url": link,
            "date": article_date
        })
        seen_titles.add(title)

        if len(materials) >= max_items:
            break

    return materials

def build_rows(category: str, ranking_url: str, limit: int = 20) -> list[dict]:
    ranked = extract_ranked_stocks(ranking_url, limit=limit)
    rows = []
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    for idx, stock in enumerate(ranked, start=1):
        code = stock["code"]
        name = stock["name"]
        news_list_url = f"https://kabutan.jp/stock/news?code={code}"
        materials = pick_materials(code, max_items=3)

        rows.append({
            "category": category,
            "rank": idx,
            "code": code,
            "name": name,
            "news_list_url": news_list_url,
            "materials": materials,
            "time": now_str
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
