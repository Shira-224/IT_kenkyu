import json
import os
import re
import requests
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request
from howlongtobeatpy import HowLongToBeat

app = Flask(__name__)
app.json.ensure_ascii = False

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "games.json")
PAGE_SIZE = 5
MAX_RESULTS = 5
HLTB_WORKERS = 8
HLTB_CACHE = {}

GENRE_TAGS = {
    "action": 19, "rpg": 122, "fps": 1663, "strategy": 9,
    "simulation": 599, "adventure": 21,
    "sports_racing": 701, "sports/racing": 701, "sports": 701, "racing": 699,
    "puzzle": 1664, "casual": 597, "horror": 1667, "indie": 492,
    "パズル": 1664, "スポーツ": 701, "レーシング": 699, "スポーツ/レーシング": 701
}

STEAM_URL = "https://store.steampowered.com/search/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
}


# ---------------- 共通の関数 ----------------
def extract_hours_from_entry(entry):
    for attr in ["game_time", "main_story", "gameplay_main", "comp_main", "all_styles"]:
        if hasattr(entry, attr):
            val = getattr(entry, attr)
            if isinstance(val, (int, float)) and val > 0:
                return round(float(val), 1)
            elif isinstance(val, str):
                numbers = re.findall(r"[\d\.]+", val)
                if numbers:
                    return round(float(numbers[0]), 1)
    return 0.0


def clean_title_for_hltb(title):
    return re.sub(r"[^\w\s]", "", title).strip().lower()


def lookup_hours(query):
    if not query:
        return 0.0
    if query in HLTB_CACHE:
        return HLTB_CACHE[query]
    try:
        res = HowLongToBeat().search(query)
        if res:
            hours = extract_hours_from_entry(res[0])
            if hours > 0:
                HLTB_CACHE[query] = hours
                return hours
    except Exception:
        pass
    return 0.0


def match_time(hours, time_limit):
    if time_limit == "under_1":
        return hours < 1
    if time_limit == "over_10":
        return hours >= 10
    parts = time_limit.split("_")
    if len(parts) == 2:
        try:
            return float(parts[0]) <= hours < float(parts[1])
        except ValueError:
            return True
    return True


def match_price(price, price_range):
    if not price_range:
        return True
    if price_range == "free":
        return price == 0
    if price_range == "over_10000":
        return price >= 10000
    parts = price_range.split("_")
    if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
        return int(parts[0]) <= price <= int(parts[1])
    return True


def extract_review_summary(target_row):
    review_elem = target_row.find("span", class_="search_review_summary")
    if not review_elem:
        return "評価なし"
    tooltip = review_elem.get("data-tooltip-html", "")
    if tooltip:
        summary_text = tooltip.split("<br>")[0].strip()
        m = re.search(r"(\d+%)", tooltip)
        return f"{summary_text} ({m.group(1)})" if m else summary_text
    classes = review_elem.get("class", [])
    if "positive" in classes: return "好評"
    elif "mixed" in classes: return "賛否両論"
    elif "negative" in classes: return "不評"
    return "評価なし"


def evaluate_rank(price, cost_per_hour, review_label):
    if price == 0:
        if "圧倒的に好評" in review_label or "非常に好評" in review_label:
            return "SSS", "SSS (神無料ゲー)"
        elif "好評" in review_label:
            return "A", "A (無料・良作)"
        else:
            return "B", "B (無料・お試し)"
    ranks = ["S", "A", "B", "C"]
    if cost_per_hour <= 50: idx = 0
    elif cost_per_hour <= 150: idx = 1
    elif cost_per_hour <= 300: idx = 2
    else: idx = 3

    note = ""
    if "圧倒的に好評" in review_label:
        idx = max(0, idx - 1)
        note = "・超高評価"
    elif "賛否両論" in review_label or "不評" in review_label:
        idx = min(3, idx + 1)
        note = "・賛否あり"

    final_code = ranks[idx]
    labels = {
        "S": f"S (神コスパ{note})", "A": f"A (良コスパ{note})",
        "B": f"B (標準{note})", "C": f"C (贅沢{note})",
    }
    return final_code, labels[final_code]


def build_item(title, url, image, price_display, price, hours, review_label):
    cost_per_hour = round(price / hours) if hours > 0 else price
    rank_code, rank_label = evaluate_rank(price, cost_per_hour, review_label)
    return {
        "title": title, "url": url, "image": image,
        "price_display": price_display, "price": price,
        "play_hours": hours, "cost_per_hour": cost_per_hour,
        "review_summary": review_label, "rank_code": rank_code, "rank": rank_label,
    }


# ---------------- 時間条件あり：games.json から検索 ----------------
def search_db(keyword, price_range, genre, time_limit, page):
    if not os.path.exists(DB_FILE):
        return None
    with open(DB_FILE, encoding="utf-8") as f:
        games = json.load(f)

    kw = keyword.lower().strip()
    matched = []
    for g in games:
        if kw and kw not in g["title"].lower() and kw not in g.get("title_en", "").lower():
            continue
        if genre and genre not in g.get("genres", []):
            continue
        if not match_price(g["price"], price_range):
            continue
        if not match_time(g["play_hours"], time_limit):
            continue
        matched.append(g)

    start = (page - 1) * PAGE_SIZE
    return [
        build_item(g["title"], g["url"], g["image"], g["price_display"],
                   g["price"], g["play_hours"], g["review_summary"])
        for g in matched[start:start + PAGE_SIZE]
    ]


# ---------------- 時間条件なし：Steamを直接検索 ----------------
def get_english_titles(params):
    try:
        en_params = dict(params)
        en_params["l"] = "english"
        res = requests.get(STEAM_URL, params=en_params, headers=HEADERS, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        mapping = {}
        for row in soup.find_all("a", class_="search_result_row"):
            appid = row.get("data-ds-appid")
            t = row.find("span", class_="title")
            if appid and t:
                mapping[appid] = t.get_text(strip=True)
        return mapping
    except Exception:
        return {}


def search_live(keyword, price_range, genre, page):
    params = {"l": "japanese", "cc": "jp", "page": page}
    if keyword:
        params["term"] = keyword
    if genre and genre.lower() in GENRE_TAGS:
        params["tags"] = GENRE_TAGS[genre.lower()]
    if price_range == "free":
        params["maxprice"] = "free"
    elif price_range and price_range != "over_10000":
        parts = price_range.split("_")
        if len(parts) == 2 and parts[1].isdigit():
            params["maxprice"] = parts[1]

    ignore_keywords = ["soundtrack", "artbook", "pack", "pass", "hollows", "dlc", "expansion"]

    try:
        res = requests.get(STEAM_URL, params=params, headers=HEADERS, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        rows = soup.find_all("a", class_="search_result_row")
        if not rows:
            return []

        en_titles = get_english_titles(params)

        candidates = []
        for row in rows:
            t = row.find("span", class_="title")
            if not t:
                continue
            title = t.get_text(strip=True)
            if any(kw in title.lower() for kw in ignore_keywords):
                continue

            price_elem = row.find("div", class_="discount_final_price") or row.find("div", class_="search_price")
            price_text = price_elem.get_text(strip=True) if price_elem else "¥ 0"
            numbers = re.findall(r"\d+", price_text.replace(",", ""))
            if "無料" in price_text or "Free" in price_text:
                price = 0
            elif numbers:
                price = int(numbers[0])
            else:
                price = 0
            if not match_price(price, price_range):
                continue

            img = row.find("div", class_="search_capsule")
            img_url = img.find("img").get("src", "") if img and img.find("img") else ""
            appid = row.get("data-ds-appid", "")
            candidates.append({
                "row": row, "title": title, "url": row.get("href", ""),
                "image": img_url, "price_text": price_text, "price": price,
                "hltb_query": clean_title_for_hltb(en_titles.get(appid, title)),
            })
            if len(candidates) >= MAX_RESULTS:
                break

        if not candidates:
            return []

        with ThreadPoolExecutor(max_workers=HLTB_WORKERS) as ex:
            hours_list = list(ex.map(lambda c: lookup_hours(c["hltb_query"]), candidates))

        results = []
        for c, hours in zip(candidates, hours_list):
            if hours <= 0:
                hours = 10.0  # 取得できなかったときの仮置き
            results.append(build_item(
                c["title"], c["url"], c["image"], c["price_text"], c["price"],
                hours, extract_review_summary(c["row"])))
        return results

    except Exception:
        return []


# ---------------- API ----------------
@app.route("/api/search", methods=["GET"])
def search():
    keyword = request.args.get("keyword", "")
    price_range = request.args.get("price_range", "")
    genre = request.args.get("genre", "")
    time_limit = request.args.get("time_limit", "")

    try:
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        page = 1

    if not (keyword or price_range or genre or time_limit):
        return jsonify({"status": "error", "message": "条件が未指定です。"}), 400

    try:
        if time_limit:
            results = search_db(keyword, price_range, genre, time_limit, page)
            if results is None:
                return jsonify({"status": "error",
                                "message": "games.json がありません。先に build_db.py を実行してください。"}), 500
        else:
            results = search_live(keyword, price_range, genre, page)
        return jsonify({"status": "success", "page": page, "results": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=False, port=5000)