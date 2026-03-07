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

def extract_article_date_from_link(link: str) -> str:
    m = re.search(r"n(\d{4})(\d{2})(\d{2})", link)
    if m:
        return f"{m.group(1)}/{m.group(2)}/{m.group(3)}"
    return ""

def get_stock_name(code: str) -> str:
    url = f"https://kabutan.jp/stock/?code={code}"
    soup = get_soup(url)

    title = soup.title.get_text(strip=True) if soup.title else ""
    # 例: ブレインズテクノロジー【4075】｜ニュース｜株探（かぶたん）
    m = re.match(r"(.+?)【" + re.escape(code) + r"】", title)
    if m:
        return m.group(1).strip()

    # 保険
    h2 = soup.select_one("h2")
    if h2:
        txt = normalize_text(h2.get_text())
        if txt and txt != code:
            return txt

    return code

def extract_ranked_stocks(url: str, limit: int = 20) -> list[dict]:
    soup = get_soup(url)
    stocks = []
    seen = set()

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

        stocks.append({
            "code": code
        })
        seen.add(code)

        if len(stocks) >= limit:
            break

    return stocks

def pick_materials(code: str, max_items: int = 3) -> list[dict]:
    url = f"https://kabutan.jp/stock/news?code={code}"
    soup = get_soup(url)

    materials = []
    seen_titles = set()

    for a in soup.select("a[href*='&b=n']"):
        title = normalize_text(a.get_text())
        if not title:
            continue
        if title in seen_titles:
            continue
        if any(word in title for word in ng_words):
            continue

        link = urljoin("https://kabutan.jp", a.get("href", ""))
        article_date = extract_article_date_from_link(link)

        materials.append({
            "title": title,
            "url": link,
            "date": article_date
        })
        seen_titles.add(title)

        if len(materials) >= max_items:
            break

    return materials

def build_rows(category: str, ranking_url: str, limit: int = 10) -> list[dict]:
    ranked = extract_ranked_stocks(ranking_url, limit=limit)
    rows = []
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    for idx, stock in enumerate(ranked, start=1):
        code = stock["code"]
        name = get_stock_name(code)
        materials = pick_materials(code, max_items=3)

        rows.append({
            "category": category,
            "rank": idx,
            "code": code,
            "name": name,
            "news_list_url": f"https://kabutan.jp/stock/news?code={code}",
            "materials": materials,
            "time": now_str
        })

    return rows

rows = []
rows += build_rows("PTS", PTS_URL, limit=10)
rows += build_rows("S高", STOP_URL, limit=10)

print(json.dumps(rows[:3], ensure_ascii=False, indent=2))
