import json
import os
import re
import time
from collections import Counter

import requests
from bs4 import BeautifulSoup
from howlongtobeatpy import HowLongToBeat

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "games.json")
PAGES_PER_TAG = 6      # 1ジャンルあたり取得するページ数（1ページ約25件）
SLEEP_SEC = 1.0        # Steamへの連続アクセスの間隔
HLTB_SLEEP = 0.5       # HLTBへの連続アクセスの間隔
HLTB_RETRY = 3         # HLTB失敗時のやり直し回数

TAGS = {
    "action": 19, "rpg": 122, "fps": 1663, "strategy": 9,
    "simulation": 599, "adventure": 21, "sports_racing": 701,
    "puzzle": 1664, "casual": 597, "horror": 1667, "indie": 492,
}

STEAM_URL = "https://store.steampowered.com/search/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
}


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


def extract_review_summary(row):
    review_elem = row.find("span", class_="search_review_summary")
    if not review_elem:
        return "評価なし"
    tooltip = review_elem.get("data-tooltip-html", "")
    if tooltip:
        summary_text = tooltip.split("<br>")[0].strip()
        m = re.search(r"(\d+%)", tooltip)
        return f"{summary_text} ({m.group(1)})" if m else summary_text
    classes = review_elem.get("class", [])
    if "positive" in classes: return "好評"
    if "mixed" in classes: return "賛否両論"
    if "negative" in classes: return "不評"
    return "評価なし"


def fetch_rows(params):
    """Steam検索を1ページ取得。失敗時は少し待って最大3回試す"""
    last_err = None
    for attempt in range(3):
        try:
            res = requests.get(STEAM_URL, params=params, headers=HEADERS, timeout=15)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")
            return soup.find_all("a", class_="search_result_row")
        except Exception as e:
            last_err = e
            time.sleep(2 * (attempt + 1))
    raise last_err


def parse_price(row):
    price_elem = row.find("div", class_="discount_final_price") or row.find("div", class_="search_price")
    text = price_elem.get_text(strip=True) if price_elem else ""
    if "無料" in text or "Free" in text:
        return 0, text or "無料"
    numbers = re.findall(r"\d+", text.replace(",", ""))
    if numbers:
        return int(numbers[0]), text
    return None, text  # 価格不明（未発売など）


def collect_steam_games():
    games = {}
    fail_count = 0
    for tag_key, tag_id in TAGS.items():
        for page in range(1, PAGES_PER_TAG + 1):
            base = {"cc": "jp", "page": page, "tags": tag_id,
                    "category1": 998, "sort_by": "Reviews_DESC"}
            try:
                ja_rows = fetch_rows({**base, "l": "japanese"})
                time.sleep(SLEEP_SEC)
                en_rows = fetch_rows({**base, "l": "english"})
                time.sleep(SLEEP_SEC)
            except Exception as e:
                fail_count += 1
                print(f"  [{tag_key} p{page}] 取得失敗: {repr(e)[:150]}")
                continue

            en_map = {}
            for r in en_rows:
                appid = r.get("data-ds-appid")
                t = r.find("span", class_="title")
                if appid and t:
                    en_map[appid] = t.get_text(strip=True)

            before = len(games)
            for row in ja_rows:
                appid = row.get("data-ds-appid", "")
                if not appid or "," in appid:   # バンドルは除外
                    continue
                t = row.find("span", class_="title")
                if not t:
                    continue
                if appid in games:
                    if tag_key not in games[appid]["genres"]:
                        games[appid]["genres"].append(tag_key)
                    continue
                price, price_text = parse_price(row)
                if price is None:
                    continue
                img = row.find("div", class_="search_capsule")
                img_url = img.find("img").get("src", "") if img and img.find("img") else ""
                title = t.get_text(strip=True)
                games[appid] = {
                    "appid": appid,
                    "title": title,
                    "title_en": en_map.get(appid, ""),
                    "url": row.get("href", ""),
                    "image": img_url,
                    "price": price,
                    "price_display": price_text,
                    "review_summary": extract_review_summary(row),
                    "genres": [tag_key],
                }
            print(f"  [{tag_key} p{page}] 取得行数 {len(ja_rows)} / 新規 {len(games) - before} / 累計 {len(games)}")
    print(f"Steam取得失敗ページ数: {fail_count}")
    return games


def search_hltb(query):
    """HLTBを検索。(時間, エラー内容) を返す。失敗時は時間0.0"""
    if not query:
        return 0.0, "空のタイトル"
    last_err = "結果なし"
    for attempt in range(HLTB_RETRY):
        try:
            res = HowLongToBeat().search(query)
            if res:
                hours = extract_hours_from_entry(res[0])
                if hours > 0:
                    return hours, ""
                last_err = "時間が0"
                break  # 見つかったが時間が無いのでやり直しても無駄
            last_err = "結果なし"
            break      # 結果なしもやり直しても無駄
        except Exception as e:
            last_err = repr(e)[:120]
            time.sleep(2 * (attempt + 1))
    return 0.0, last_err


def lookup_hours(game):
    """英語名→日本語名の順にHLTBを検索"""
    queries = []
    if game.get("title_en"):
        queries.append(clean_title_for_hltb(game["title_en"]))
    queries.append(clean_title_for_hltb(game["title"]))
    last_err = ""
    for q in dict.fromkeys(queries):   # 重複を除く
        hours, err = search_hltb(q)
        if hours > 0:
            return hours, ""
        last_err = err
        time.sleep(HLTB_SLEEP)
    return 0.0, last_err


def main():
    # 前回取得できた時間があれば再利用する
    old_hours = {}
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, encoding="utf-8") as f:
                for g in json.load(f):
                    old_hours[g["appid"]] = g.get("play_hours", 0)
        except Exception:
            pass

    print("① Steamからゲーム一覧を取得中...")
    games = collect_steam_games()
    print(f"→ {len(games)} 件\n")

    print("② HLTBからプレイ時間を取得中（1本ずつ順番に）...")
    items = list(games.values())
    for g in items:
        g["play_hours"] = old_hours.get(g["appid"], 0)
    need = [g for g in items if g["play_hours"] <= 0]

    errors = Counter()
    samples = []
    for i, g in enumerate(need, 1):
        hours, err = lookup_hours(g)
        g["play_hours"] = hours
        if hours <= 0:
            errors[err] += 1
            if len(samples) < 10:
                samples.append(f"{g['title_en'] or g['title']} -> {err}")
        time.sleep(HLTB_SLEEP)
        if i % 25 == 0:
            ok = sum(1 for x in need[:i] if x["play_hours"] > 0)
            print(f"  {i}/{len(need)}（成功 {ok}）")

    final = [g for g in items if g["play_hours"] > 0]
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False)

    print(f"\n完了: 時間が取れた {len(final)} 件を {DB_FILE} に保存しました（取得できず除外 {len(items) - len(final)} 件）")
    if errors:
        print("\n【HLTB失敗の内訳】")
        for e, n in errors.most_common():
            print(f"  {n}件: {e}")
        print("\n【失敗例】")
        for s in samples:
            print("  ", s)


if __name__ == "__main__":
    main()