import sys
import re
import json
import requests
from bs4 import BeautifulSoup
from howlongtobeatpy import HowLongToBeat

def extract_hours_from_entry(entry):
    """ HowLongToBeatEntry から利用可能な時間を安全に抽出する """
    attributes_to_check = ['game_time', 'main_story', 'gameplay_main', 'comp_main', 'all_styles']
    for attr in attributes_to_check:
        if hasattr(entry, attr):
            val = getattr(entry, attr)
            if isinstance(val, (int, float)) and val > 0:
                return round(float(val), 1)
            elif isinstance(val, str):
                numbers = re.findall(r'[\d\.]+', val)
                if numbers:
                    return round(float(numbers[0]), 1)
    return 0.0

def fetch_games_info(game_title):
    steam_url = f"https://store.steampowered.com/search/?term={requests.utils.quote(game_title)}&l=japanese"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    results_list = []
    ignore_keywords = ['soundtrack', 'artbook', 'pack', 'pass']

    try:
        res = requests.get(steam_url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        results = soup.find_all('a', class_='search_result_row')
        if not results:
            return []

        for target_row in results:
            title = target_row.find('span', class_='title').get_text(strip=True)
            
            # 除外キーワードチェック
            if any(kw in title.lower() for kw in ignore_keywords):
                continue

            # 画像取得
            img_elem = target_row.find('div', class_='search_capsule').find('img') if target_row.find('div', class_='search_capsule') else None
            img_url = img_elem['src'] if img_elem and 'src' in img_elem.attrs else ''

            # 価格取得
            price_elem = target_row.find('div', class_='discount_final_price')
            if not price_elem:
                price_elem = target_row.find('div', class_='search_price')
                
            price_text = price_elem.get_text(strip=True) if price_elem else "¥ 0"
            numbers = re.findall(r'\d+', price_text.replace(',', ''))
            price = int(numbers[0]) if (numbers and "無料" not in price_text and "Free" not in price_text) else 0

            # ---------------------------------------------------------
            # 各個別タイトル（title）でHLTBを検索
            # ---------------------------------------------------------
            main_hours = 0.0
            try:
                # まず個別のタイトル名で検索
                hltb_results = HowLongToBeat().search(title)
                if not hltb_results:
                    # ヒットしない場合は元の検索キーワードで再試行
                    hltb_results = HowLongToBeat().search(game_title)
                    
                if hltb_results and len(hltb_results) > 0:
                    main_hours = extract_hours_from_entry(hltb_results[0])
            except Exception:
                pass

            # どうしても時間が取れなかった場合のみデフォルト10時間
            if main_hours == 0.0:
                main_hours = 10.0

            # コスパ計算 ＆ ランク判定
            cost_per_hour = round(price / main_hours) if main_hours > 0 else price
            
            if price == 0:
                rank_code, rank_label = "SSS", "SSS (無料)"
            elif cost_per_hour <= 50:
                rank_code, rank_label = "S", "S (神コスパ)"
            elif cost_per_hour <= 150:
                rank_code, rank_label = "A", "A (良コスパ)"
            elif cost_per_hour <= 300:
                rank_code, rank_label = "B", "B (標準)"
            else:
                rank_code, rank_label = "C", "C (贅沢)"

            results_list.append({
                "title": title,
                "image": img_url,
                "price_display": price_text,
                "play_hours": main_hours,
                "cost_per_hour": cost_per_hour,
                "rank_code": rank_code,
                "rank": rank_label
            })

            if len(results_list) >= 3:
                break

    except Exception:
        pass

    return results_list

if __name__ == '__main__':
    keyword = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].strip() != '' else 'Elden Ring'
    data = fetch_games_info(keyword)
    print(json.dumps(data, ensure_ascii=False))