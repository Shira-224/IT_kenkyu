from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
app.json.ensure_ascii = False  # ← この行を追加（日本語文字化け防止）

def analyze_phone_number(phone_number):
    """telnavi.jp をスクレイピングしてリスク判定を行う"""
    url = f"https://www.telnavi.jp/phone/{phone_number}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")
        text_content = soup.get_text()

        # 危険キーワードの検出
        risk_keywords = ["詐欺", "悪質", "迷惑", "架空請求", "アポ電", "セールス", "営業", "しつこい"]
        keyword_count = sum(text_content.count(kw) for kw in risk_keywords)

        # 危険度判定
        if keyword_count >= 3:
            risk_level = "HIGH"
            message = "🚨 危険：詐欺や悪質な連絡の報告が多数見つかりました！"
        elif keyword_count >= 1:
            risk_level = "MEDIUM"
            message = "⚠️ 注意：迷惑電話や営業電話の報告があります。"
        else:
            risk_level = "LOW"
            message = "✅ 安全：目立った被害報告は見つかりませんでした。"

        return {
            "status": "success",
            "source": "telnavi.jp",
            "phone_number": phone_number,
            "risk_level": risk_level,
            "keyword_count": keyword_count,
            "message": message
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"解析中にエラーが発生しました: {str(e)}"
        }

@app.route("/api/check", methods=["GET"])
def check_number():
    phone_number = request.args.get("number")
    
    if not phone_number:
        return jsonify({"status": "error", "message": "電話番号が指定されていません。"}), 400

    result = analyze_phone_number(phone_number)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True, port=5000)