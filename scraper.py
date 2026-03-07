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

IGNORE_CODES = {"0000","0950","0800","0823"}

ng_words = [
    "ストップ高／ストップ安","均衡表","ボリンジャー",
    "ゴールデンクロス","デッドクロス","MACD",
    "75日線","25日線","5日線","移動平均",
    "引け","前場","後場","本日の【",
    "今週の【話題株ダイジェスト】","前日に動いた銘柄",
    "成長株特集","第1弾","テーマ株",
    "市場ニュース","レーティング","相場展望",
    "新興市場銘柄ダイジェスト","本日の注目個別銘柄",
    "上場来高値銘柄"
]

def get_soup(url):
    r = requests.get(url,headers=headers,timeout=20)
    r.raise_for_status()
    return BeautifulSoup(r.text,"lxml")

def normalize_text(t):
    return re.sub(r"\s+"," ",t).strip()

# -----------------------------
# 記事日付取得
# -----------------------------

def extract_article_date_from_link(link):

    m = re.search(r"[?&]b=n(\d{8})\d*",link)

    if m:
        ymd = m.group(1)
        return f"{ymd[0:4]}/{ymd[4:6]}/{ymd[6:8]}"

    return ""

# -----------------------------
# 銘柄名取得
# -----------------------------

def get_stock_name(code):

    url = f"https://kabutan.jp/stock/?code={code}"
    soup = get_soup(url)

    title = soup.title.get_text(strip=True)

    m = re.match(r"(.+?)【"+re.escape(code)+"】",title)

    if m:
        return m.group(1)

    return code

# -----------------------------
# ランキング銘柄取得
# -----------------------------

def extract_ranked_stocks(url,limit=20):

    soup = get_soup(url)

    stocks=[]
    seen=set()

    for a in soup.select("a[href*='/stock/?code=']"):

        href=a.get("href","")

        m=re.search(r"code=([0-9A-Z]+)",href)

        if not m:
            continue

        code=m.group(1)

        if code in IGNORE_CODES:
            continue

        if not re.fullmatch(r"[0-9A-Z]{4}",code):
            continue

        if code in seen:
            continue

        stocks.append({"code":code})

        seen.add(code)

        if len(stocks)>=limit:
            break

    return stocks

# -----------------------------
# 材料取得
# -----------------------------

def pick_materials(code,max_items=3):

    url=f"https://kabutan.jp/stock/news?code={code}"

    soup=get_soup(url)

    materials=[]
    seen=set()

    for a in soup.select("a[href*='&b=n']"):

        title=normalize_text(a.get_text())

        if not title:
            continue

        if title in seen:
            continue

        if any(w in title for w in ng_words):
            continue

        link=urljoin("https://kabutan.jp",a.get("href",""))

        date=extract_article_date_from_link(link)

        materials.append({
            "title":title,
            "url":link,
            "date":date
        })

        seen.add(title)

        if len(materials)>=max_items:
            break

    return materials

# -----------------------------
# 行作成
# -----------------------------

def build_rows(category,ranking_url,limit=10):

    ranked=extract_ranked_stocks(ranking_url,limit)

    rows=[]

    now=datetime.now().strftime("%Y-%m-%d %H:%M")

    for i,stock in enumerate(ranked,start=1):

        code=stock["code"]

        name=get_stock_name(code)

        materials=pick_materials(code,3)

        rows.append({
            "category":category,
            "rank":i,
            "code":code,
            "name":name,
            "news_list_url":f"https://kabutan.jp/stock/news?code={code}",
            "materials":materials,
            "time":now
        })

    return rows


rows=[]

rows+=build_rows("PTS",PTS_URL,10)
rows+=build_rows("S高",STOP_URL,10)

print(json.dumps(rows[:3],ensure_ascii=False,indent=2))
