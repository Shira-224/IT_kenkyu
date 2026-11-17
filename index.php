<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Steam情報取得ツール</title>
    <link rel="stylesheet" href="style/style.css">
</head>
<body>
    <h1>Steamゲーム情報検索</h1>
    
    <!-- データを送信するためのフォーム（receive.phpへ送信） -->
    <form action="receive.php" method="POST">
        <!-- ゲーム名の検索ボックス -->
        <div>
            <label for="keyword">ゲーム名:</label>
            <input type="text" id="keyword" name="keyword" maxlength="100">
        </div>

        <!-- 価格帯のプルダウン -->
        <div>
            <label for="price_range">価格帯:</label>
            <select id="price_range" name="price_range">
                <option value="">指定なし</option>
                <option value="free">無料 (Free)</option>
                <option value="1_2000">1〜2,000円</option>
                <option value="2001_4000">2,001〜4,000円</option>
                <option value="4001_6000">4,001〜6,000円</option>
                <option value="6001_8000">6,001〜8,000円</option>
                <option value="8001_10000">8,001〜10,000円</option>
                <option value="over_10000">10,000円以上</option>
            </select>
        </div>

        <!-- ジャンルのプルダウン -->
        <div>
            <label for="genre">ジャンル:</label>
            <select id="genre" name="genre">
                <option value="">指定なし</option>
                <option value="action">アクション</option>
                <option value="rpg">RPG</option>
                <option value="fps">FPS / シューター</option>
                <option value="strategy">ストラテジー</option>
                <option value="simulation">シミュレーション</option>
                <option value="adventure">アドベンチャー</option>
                <option value="sports_racing">スポーツ / レーシング</option>
                <option value="puzzle">パズル</option>
                <option value="casual">カジュアル</option>
                <option value="horror">ホラー</option>
                <option value="indie">インディー</option>
            </select>
        </div>

        <!-- 時間上限のプルダウン -->
        <div>
            <label for="time_limit">プレイ時間:</label>
            <select id="time_limit" name="time_limit">
                <option value="">指定なし</option>
                <option value="1_2">1〜2時間</option>
                <option value="2_4">2〜4時間</option>
                <option value="4_6">4〜6時間</option>
                <option value="6_8">6〜8時間</option>
                <option value="8_10">8〜10時間</option>
                <option value="over_10">10時間以上</option>
            </select>
        </div>

        <button type="submit">検索する</button>
    </form>
</body>
</html>