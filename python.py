from openai import OpenAI

# 1. APIへの接続準備（"sk-"から始まる自分のAPIキーに書き換えてください）
client = OpenAI(api_key="sk-ここにあなたのAPIキーを貼り付けてください")

print("AIに通信をリクエストしています...")

try:
    # 2. AIへ簡単なメッセージを送信してテスト
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # コストが安く賢い最新モデル
        messages=[
            {"role": "user", "content": "こんにちは！APIのテスト通信です。短い挨拶を返してください。"}
        ]
    )

    # 3. AIからの返信を画面に表示
    print("\n通信成功！AIからの返信:")
    print(response.choices[0].message.content)

except Exception as e:
    print(f"\nエラーが発生しました。APIキーが間違っていないか等を確認してください: {e}")