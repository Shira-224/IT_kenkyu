import re
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request
from howlongtobeatpy import HowLongToBeat

app = Flask(__name__)
app.json.ensure_ascii = False  # 日本語文字化け防止

GENRE_TAGS = {"action": 19, "rpg": 122, "indie": 492, "fps": 1663, "strategy": 9}
PRICE_MAX = {"free": "free", "under_1000": 1000, "under_3000": 3000}


def extract_hours_from_entry(entry):
    """HowLongToBeatEntry から利用可能なプレイ時間を抽出する"""
    attributes_to_check = [
        "game_time",
        "main_story",
        "gameplay_main",
        "comp_main",
        "all_styles",
    ]
    for attr in attributes_to_check:
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
    """HLTB検索成功率を高めるためのタイトル整形"""
    return re.sub(r"[^\w\s]", "", title).strip().lower()


def extract_review_summary(target_row):
    """検索一覧HTML内のsearch_review_summaryから評価ラベルと好評率を抽出する"""
    review_elem = target_row.find("span", class_="search_review_summary")
    if not review_elem:
        return "評価なし"

    tooltip = review_elem.get("data-tooltip-html", "")
    if tooltip:
        summary_text = tooltip.split("<br>")[0].strip()
        percent_match = re.search(r"(\d+%)", tooltip)
        if percent_match:
            return f"{summary_text} ({percent_match.group(1)})"
        return summary_text

    classes = review_elem.get("class", [])
    if "positive" in classes:
        return "好評"
    elif "mixed" in classes:
        return "賛否両論"
    elif "negative" in classes:
        return "不評"

    return "評価なし"


def evaluate_rank(price, cost_per_hour, review_label):
    """価格・単価・レビューラベルを組み合わせてランクを判定する"""
    if price == 0:
        if "圧倒的に好評" in review_label or "非常に好評" in review_label:
            return "SSS", "SSS (神無料ゲー)"
        elif "好評" in review_label:
            return "A", "A (無料・良作)"
        else:
            return "B", "B (無料・お試し)"

    ranks = ["S", "A", "B", "C"]
    if cost_per_hour <= 50:
        idx = 0
    elif cost_per_hour <= 150:
        idx = 1
    elif cost_per_hour <= 300:
        idx = 2
    else:
        idx = 3

    note = ""
    if "圧倒的に好評" in review_label:
        idx = max(0, idx - 1)
        note = "・超高評価"
    elif "賛否両論" in review_label or "不評" in review_label:
        idx = min(3, idx + 1)
        note = "・賛否あり"

    final_code = ranks[idx]
    labels = {
        "S": f"S (神コスパ{note})",
        "A": f"A (良コスパ{note})",
        "B": f"B (標準{note})",
        "C": f"C (贅沢{note})",
    }
    return final_code, labels[final_code]


def search_steam(keyword, price_range, genre, time_limit, page=1):
    """Steamストア検索ページから指定ページ分を取得し、HLTB時間＆一覧レビューでコスパ判定を行う"""
    params = {
        "l": "japanese",
        "cc": "jp",
        "page": page,
    }

    if keyword:
        params["term"] = keyword

    if price_range in PRICE_MAX:
        params["maxprice"] = PRICE_MAX[price_range]

    if genre in GENRE_TAGS:
        params["tags"] = GENRE_TAGS[genre]

    steam_url = "https://store.steampowered.com/search/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    }

    results_list = []
    fallback_list = []
    ignore_keywords = [
        "soundtrack",
        "artbook",
        "pack",
        "pass",
        "hollows",
        "dlc",
        "expansion",
    ]

    try:
        res = requests.get(steam_url, params=params, headers=headers, timeout=5)
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")
        results = soup.find_all("a", class_="search_result_row")

        if not results:
            return []

        targets = results[:12]

        for target_row in targets:
            title_elem = target_row.find("span", class_="title")
            if not title_elem:
                continue
            title = title_elem.get_text(strip=True)

            # 非ゲームコンテンツの除外
            if any(kw in title.lower() for kw in ignore_keywords):
                continue

            # Steamストア直リンクURL
            store_url = target_row.get("href", "")

            # 画像取得
            img_elem = target_row.find("div", class_="search_capsule")
            img_url = ""
            if img_elem and img_elem.find("img"):
                img_url = img_elem.find("img").get("src", "")

            # 価格取得
            price_elem = target_row.find("div", class_="discount_final_price")
            if not price_elem:
                price_elem = target_row.find("div", class_="search_price")

            price_text = price_elem.get_text(strip=True) if price_elem else "¥ 0"
            numbers = re.findall(r"\d+", price_text.replace(",", ""))

            if "無料" in price_text or "Free" in price_text:
                price = 0
            elif numbers:
                price = int(numbers[0])
            else:
                price = 0

            if price_range == "over_3000" and price < 3000:
                continue

            # HLTBから時間取得
            main_hours = 0.0
            search_query = clean_title_for_hltb(title)

            if search_query:
                try:
                    hltb_results = HowLongToBeat().search(search_query)
                    if hltb_results and len(hltb_results) > 0:
                        extracted = extract_hours_from_entry(hltb_results[0])
                        if extracted > 0:
                            main_hours = extracted
                except Exception:
                    pass

            if main_hours == 0.0:
                main_hours = 10.0

            # レビュー評価テキスト抽出
            review_label = extract_review_summary(target_row)

            # コスパ計算 ＆ 総合ランク判定
            cost_per_hour = round(price / main_hours) if main_hours > 0 else price
            rank_code, rank_label = evaluate_rank(price, cost_per_hour, review_label)

            item_data = {
                "title": title,
                "url": store_url,
                "image": img_url,
                "price_display": price_text,
                "price": price,
                "play_hours": main_hours,
                "cost_per_hour": cost_per_hour,
                "review_summary": review_label,
                "rank_code": rank_code,
                "rank": rank_label,
            }

            fallback_list.append(item_data)

            # プレイ時間上限フィルタリング
            if time_limit == "under_5" and main_hours >= 5:
                continue
            elif time_limit == "under_20" and main_hours >= 20:
                continue
            elif time_limit == "over_20" and main_hours < 20:
                continue

            results_list.append(item_data)

            if len(results_list) >= 5:
                break

    except Exception:
        return []

    if not results_list:
        return fallback_list[:5]

    return results_list


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
        return (
            jsonify({"status": "error", "message": "条件が未指定です。"}),
            400,
        )

    try:
        results = search_steam(keyword, price_range, genre, time_limit, page)
        return jsonify({
            "status": "success",
            "page": page,
            "results": results,
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=False, port=5000)