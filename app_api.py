from flask import Flask, jsonify, request
import requests

app = Flask(__name__)
app.json.ensure_ascii = False  # 日本語文字化け防止

GENRE_TAGS = {"action": 19, "rpg": 122, "indie": 492, "fps": 1663, "strategy": 9}
PRICE_MAX = {"free": "free", "under_1000": 1000, "under_3000": 3000}

def search_steam(price_range, genre, time_limit):
    """Steamのストア検索を呼び出して、ゲーム一覧を返す"""
    params = {"json": 1, "cc": "jp", "l": "japanese", "count": 20}
    if genre in GENRE_TAGS:
        params["tags"] = GENRE_TAGS[genre]
    if price_range in PRICE_MAX:
        params["maxprice"] = PRICE_MAX[price_range]

    r = requests.get("https://store.steampowered.com/search/results/",
                     params=params, timeout=10)
    r.raise_for_status()
    items = r.json().get("items", [])

    # time_limit（プレイ時間）はSteamだけでは絞り込めないので今は未使用
    return [{"title": i.get("name", "名称不明"), "price": "N/A"} for i in items]


@app.route("/api/search", methods=["GET"])
def search():
    price_range = request.args.get("price_range", "")
    genre = request.args.get("genre", "")
    time_limit = request.args.get("time_limit", "")

    if not (price_range or genre or time_limit):
        return jsonify({"status": "error", "message": "条件が未指定です。"}), 400

    try:
        results = search_steam(price_range, genre, time_limit)
        return jsonify({"status": "success", "results": results})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)