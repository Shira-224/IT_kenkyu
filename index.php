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
        <!-- 価格帯のプルダウン -->
        <div>
            <label for="price_range">価格帯:</label>
            <select id="price_range" name="price_range">
                <option value="">指定なし</option>
                <option value="free">無料 (Free)</option>
                <option value="under_1000">1,000円未満</option>
                <option value="under_3000">3,000円未満</option>
                <option value="over_3000">3,000円以上</option>
            </select>
        </div>

        <!-- ジャンルのプルダウン -->
        <div>
            <label for="genre">ジャンル:</label>
            <select id="genre" name="genre">
                <option value="">指定なし</option>
                <option value="action">アクション</option>
                <option value="rpg">RPG</option>
                <option value="indie">インディー</option>
                <option value="fps">FPS / シューター</option>
                <option value="strategy">ストラテジー</option>
            </select>
        </div>

        <!-- 時間上限のプルダウン -->
        <div>
            <label for="time_limit">プレイ時間上限:</label>
            <select id="time_limit" name="time_limit">
                <option value="">指定なし</option>
                <option value="under_5">5時間未満（サクッと）</option>
                <option value="under_20">20時間未満（ボリューム普通）</option>
                <option value="over_20">20時間以上（やり込み）</option>
            </select>
        </div>

        <button type="submit">検索する</button>
    </form>
</body>
</html>