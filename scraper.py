import csv
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

JST = timezone(timedelta(hours=9))
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
}
RANKING_URL = "https://kabutan.jp/warning/?mode=2_1"
EXCLUDED_CODES = {"0000", "0950", "0800", "0823"}
NG_WORDS = [
    "ストップ高／ストップ安", "均衡表", "ボリンジャー", "ゴールデンクロス",
    "デッドクロス", "MACD", "75日線", "25日線", "5日線", "移動平均",
    "引け", "前場", "後場", "本日の【", "レーティング", "市場ニュース",
    "今週の【話題株ダイジェスト】", "前日に動いた銘柄", "成長株特集",
    "第1弾", "テーマ株", "新興市場銘柄ダイジェスト", "本日の注目個別銘柄",
    "上場来高値銘柄", "相場展望",
]
WEAK_WORDS = [
    "大量保有報告書", "変更報告書", "保有割合が減少", "保有割合が5％を超えた",
]


def get_soup(url: str) -> BeautifulSoup:
    res = requests.get(url, headers=HEADERS, timeout=30)
    res.raise_for_status()
    return BeautifulSoup(res.text, "lxml")


def fetch_ranking_codes(limit: int = 20) -> list[str]:
    soup = get_soup(RANKING_URL)
    codes: list[str] = []
    for a in soup.select("a[href*='/stock/?code=']"):
        href = a.get("href", "")
        m = re.search(r"code=([0-9A-Z]+)", href)
        if not m:
            continue
        code = m.group(1)
        if re.fullmatch(r"[0-9A-Z]{4}", code) and code not in EXCLUDED_CODES:
            codes.append(code)
    deduped = list(dict.fromkeys(codes))
    return deduped[:limit]


def parse_news_items(code: str, max_items: int = 40) -> list[dict]:
    soup = get_soup(f"https://kabutan.jp/stock/news?code={code}")
    items = []
    for a in soup.select("a[href*='&b=n']")[:max_items]:
        title = a.get_text(strip=True)
        href = a.get("href", "")
        if not title or not href:
            continue
        items.append({
            "title": title,
            "url": f"https://kabutan.jp{href}",
        })
    return items


def choose_material(items: list[dict]) -> dict:
    if not items:
        return {"title": "", "url": "", "source": "kabutan", "quality": "none"}

    strong = [i for i in items if not any(word in i["title"] for word in NG_WORDS + WEAK_WORDS)]
    if strong:
        chosen = strong[0].copy()
        chosen.update({"source": "kabutan", "quality": "strong"})
        return chosen

    medium = [i for i in items if not any(word in i["title"] for word in NG_WORDS)]
    if medium:
        chosen = medium[0].copy()
        chosen.update({"source": "kabutan", "quality": "medium"})
        return chosen

    chosen = items[0].copy()
    chosen.update({"source": "kabutan", "quality": "fallback"})
    return chosen


def build_rows(limit: int = 20) -> list[dict]:
    rows = []
    fetched_at = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S JST")
    for code in fetch_ranking_codes(limit=limit):
        items = parse_news_items(code)
        chosen = choose_material(items)
        rows.append({
            "code": code,
            "title": chosen["title"],
            "url": chosen["url"],
            "source": chosen["source"],
            "quality": chosen["quality"],
            "fetched_at": fetched_at,
        })
    return rows


def write_outputs(rows: list[dict]) -> None:
    docs = Path("docs")
    docs.mkdir(exist_ok=True)

    payload = {
        "updated_at": datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S JST"),
        "count": len(rows),
        "items": rows,
        "notes": [
            "source=kabutan は株探ベース",
            "quality=strong は個別材料寄り、medium/fallback はまとめ記事や保有報告を含む可能性あり",
            "TDnet/Yahoo補完は今後追加しやすいよう source/quality を残しています",
        ],
    }
    (docs / "material.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    with (docs / "material.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["code", "title", "url", "source", "quality", "fetched_at"])
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    rows = build_rows(limit=20)
    write_outputs(rows)
    print(f"done: {len(rows)} rows")
