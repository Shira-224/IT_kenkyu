import requests
from bs4 import BeautifulSoup
import time

# 1. 警察庁のトップページにアクセス
url = "https://www.npa.go.jp/"
response = requests.get(url)
time.sleep(1) # サーバーへの配慮（1秒待機）

# 2. ページ全体をBeautifulSoupで読み込みやすくする
soup = BeautifulSoup(response.content, "html.parser")

# 3. ページの中から「タイトル（titleタグ）」だけを抜き出して出力！
print("▼ スクレイピングの出力結果 ▼")
print(soup.title.text)