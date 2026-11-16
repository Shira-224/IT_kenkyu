<?php
// POSTデータを安全に取得
$keyword     = isset($_POST['keyword']) ? trim($_POST['keyword']) : '';
$price_range = isset($_POST['price_range']) ? $_POST['price_range'] : '';
$genre       = isset($_POST['genre']) ? $_POST['genre'] : '';
$time_limit  = isset($_POST['time_limit']) ? $_POST['time_limit'] : '';
$page        = isset($_POST['page']) ? max(1, (int)$_POST['page']) : 1;

// 条件バッジ用の日本語ラベルマッピング
$price_labels = [
    'free'       => '無料プレイ',
    'under_1000' => '1,000円以下',
    'under_3000' => '3,000円以下',
    'over_3000'  => '3,000円以上',
];
$genre_labels = [
    'action'   => 'アクション',
    'rpg'      => 'RPG',
    'indie'    => 'インディー',
    'fps'      => 'FPS / シューター',
    'strategy' => 'ストラテジー',
];
$time_labels = [
    'under_5'  => '5時間未満',
    'under_20' => '20時間未満',
    'over_20'  => '20時間以上',
];

$active_conditions = [];
if ($keyword !== '') {
    $active_conditions[] = '🔍 ' . $keyword;
}
if (isset($price_labels[$price_range])) {
    $active_conditions[] = '💰 ' . $price_labels[$price_range];
}
if (isset($genre_labels[$genre])) {
    $active_conditions[] = '🏷️ ' . $genre_labels[$genre];
}
if (isset($time_labels[$time_limit])) {
    $active_conditions[] = '⏱️ ' . $time_labels[$time_limit];
}

$results = [];
$error_message = '';

if (empty($active_conditions)) {
    $error_message = '検索条件を少なくとも1つ以上入力または選択してください。';
} else {
    $url = 'http://127.0.0.1:5000/api/search?' . http_build_query([
        'keyword'     => $keyword,
        'price_range' => $price_range,
        'genre'       => $genre,
        'time_limit'  => $time_limit,
        'page'        => $page,
    ]);

    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 15,
    ]);
    $response  = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($response === false) {
        $error_message = 'APIサーバーに接続できませんでした（Flaskが起動しているか確認してください）。';
    } else {
        $data = json_decode($response, true);
        if (json_last_error() !== JSON_ERROR_NONE) {
            $error_message = 'APIの応答を解析できませんでした。';
        } elseif (($data['status'] ?? '') !== 'success') {
            $error_message = $data['message'] ?? 'APIでエラーが発生しました。';
        } else {
            $results = $data['results'] ?? [];
        }
    }
}

// ソート用のランク数値化マップ
$rank_weights = ['SSS' => 1, 'S' => 2, 'A' => 3, 'B' => 4, 'C' => 5];
?>
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Steam コスパ検索結果 (<?php echo $page; ?>ページ目)</title>
    <link rel="stylesheet" href="style/style.css">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #1b2838;
            color: #fff;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
        }
        h1 {
            color: #66c0f4;
            margin-bottom: 12px;
        }
        .container {
            width: 100%;
            max-width: 650px;
        }
        /* 条件バッジ表示エリア */
        .condition-bar {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 8px;
            margin-bottom: 16px;
        }
        .condition-badge {
            background-color: #2a475e;
            color: #66c0f4;
            border: 1px solid #417a9b;
            padding: 4px 12px;
            border-radius: 16px;
            font-size: 0.85rem;
            font-weight: bold;
        }
        /* コントロールバー（ページ表示＆ソート） */
        .control-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 14px;
            padding: 8px 12px;
            background-color: #171a21;
            border-radius: 6px;
            font-size: 0.9rem;
        }
        .page-indicator {
            color: #8f98a0;
        }
        .sort-select {
            background-color: #2a475e;
            color: #fff;
            border: 1px solid #417a9b;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 0.85rem;
            cursor: pointer;
        }
        /* ゲームカード */
        .card {
            background-color: #2a475e;
            padding: 18px;
            margin-bottom: 16px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
            display: flex;
            gap: 16px;
            align-items: center;
            border-left: 5px solid #66c0f4;
        }
        .card-img {
            width: 120px;
            height: 56px;
            object-fit: cover;
            border-radius: 4px;
            background-color: #171a21;
            flex-shrink: 0;
        }
        .card-info {
            flex: 1;
        }
        .card-title {
            color: #ffffff;
            font-size: 1.15rem;
            font-weight: bold;
            margin-bottom: 8px;
        }
        .card-title a {
            color: #ffffff;
            text-decoration: none;
        }
        .card-title a:hover {
            color: #66c0f4;
            text-decoration: underline;
        }
        .card-details {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 6px;
            font-size: 0.9rem;
            color: #c7d5e0;
        }
        .card-unit-price {
            grid-column: span 2;
            margin-top: 2px;
            color: #e5c545;
            font-weight: bold;
        }
        .card-review {
            grid-column: span 2;
            font-size: 0.85rem;
            color: #66c0f4;
        }
        .rank-badge {
            display: inline-block;
            margin-top: 10px;
            padding: 4px 10px;
            border-radius: 12px;
            font-weight: bold;
            font-size: 0.85rem;
        }
        .rank-SSS { background: #ffd700; color: #000; }
        .rank-S   { background: #5cbe4a; color: #fff; }
        .rank-A   { background: #29b6f6; color: #fff; }
        .rank-B   { background: #ffa726; color: #fff; }
        .rank-C   { background: #ef5350; color: #fff; }

        /* ページネーションボタン */
        .pagination {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin: 24px 0;
        }
        .btn-page {
            background-color: #2a475e;
            color: #66c0f4;
            border: 1px solid #66c0f4;
            padding: 10px 20px;
            border-radius: 6px;
            font-size: 0.95rem;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-page:hover {
            background-color: #66c0f4;
            color: #1b2838;
        }
        .btn-next {
            background-color: #5cbe4a;
            color: #fff;
            border: none;
        }
        .btn-next:hover {
            background-color: #4ea83e;
            color: #fff;
        }
    </style>
</head>
<body>
    <h1>🎮 Steam コスパ検索結果</h1>

    <div class="container">
        <!-- 現在の検索条件バッジ -->
        <?php if (!empty($active_conditions)): ?>
            <div class="condition-bar">
                <?php foreach ($active_conditions as $cond): ?>
                    <span class="condition-badge"><?php echo htmlspecialchars($cond, ENT_QUOTES, 'UTF-8'); ?></span>
                <?php endforeach; ?>
            </div>
        <?php endif; ?>

        <?php if (!empty($error_message)): ?>
            <div style="background-color: #2a475e; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #ff6b6b;">
                <p style="color: #ff6b6b; margin: 0;"><?php echo htmlspecialchars($error_message, ENT_QUOTES, 'UTF-8'); ?></p>
            </div>
        <?php elseif (empty($results)): ?>
            <div style="background-color: #2a475e; padding: 20px; border-radius: 8px; margin-bottom: 20px; text-align: center;">
                <p style="margin: 0; color: #c7d5e0;">このページには一致するゲームが見つかりませんでした。</p>
            </div>
        <?php else: ?>
            <!-- ページ表示＆ソート選択バー -->
            <div class="control-bar">
                <div class="page-indicator">現在 <strong><?php echo $page; ?></strong> ページ目を表示中</div>
                <div>
                    <label for="sort-select" style="color: #8f98a0; margin-right: 4px;">並び替え:</label>
                    <select id="sort-select" class="sort-select" onchange="sortCards()">
                        <option value="default">Steamおすすめ順</option>
                        <option value="rank">コスパランク順 (SSS〜C)</option>
                        <option value="unit_asc">コスパ単価が安い順</option>
                        <option value="hours_desc">プレイ時間が長い順</option>
                        <option value="price_asc">価格が安い順</option>
                    </select>
                </div>
            </div>

            <!-- 検索結果カード一覧 -->
            <div id="results-list" style="margin-bottom: 20px;">
                <?php foreach ($results as $index => $item): ?>
                    <?php
                        $r_code   = $item['rank_code'] ?? 'C';
                        $r_weight = $rank_weights[$r_code] ?? 99;
                        $c_hour   = (float)($item['cost_per_hour'] ?? 999999);
                        $p_hours  = (float)($item['play_hours'] ?? 0);
                        $p_val    = (int)($item['price'] ?? 999999);
                    ?>
                    <div class="card"
                         data-index="<?php echo $index; ?>"
                         data-rank="<?php echo $r_weight; ?>"
                         data-unit="<?php echo $c_hour; ?>"
                         data-hours="<?php echo $p_hours; ?>"
                         data-price="<?php echo $p_val; ?>">
                        
                        <?php if (!empty($item['image'])): ?>
                            <img src="<?php echo htmlspecialchars($item['image'], ENT_QUOTES, 'UTF-8'); ?>" alt="Header" class="card-img">
                        <?php endif; ?>
                        
                        <div class="card-info">
                            <div class="card-title">
                                <?php if (!empty($item['url'])): ?>
                                    <a href="<?php echo htmlspecialchars($item['url'], ENT_QUOTES, 'UTF-8'); ?>" target="_blank" rel="noopener noreferrer">
                                        <?php echo htmlspecialchars($item['title'] ?? '名称不明', ENT_QUOTES, 'UTF-8'); ?> ↗
                                    </a>
                                <?php else: ?>
                                    <?php echo htmlspecialchars($item['title'] ?? '名称不明', ENT_QUOTES, 'UTF-8'); ?>
                                <?php endif; ?>
                            </div>
                            
                            <div class="card-details">
                                <div>💰 価格: <strong><?php echo htmlspecialchars($item['price_display'] ?? ($item['price'] ?? 'N/A'), ENT_QUOTES, 'UTF-8'); ?></strong></div>
                                <div>⏱️ 時間: <strong><?php echo htmlspecialchars($item['play_hours'] ?? '-', ENT_QUOTES, 'UTF-8'); ?> 時間</strong></div>
                                
                                <?php if (isset($item['cost_per_hour'])): ?>
                                    <div class="card-unit-price">
                                        ⏳ 単価: 約 ¥<?php echo htmlspecialchars($item['cost_per_hour'], ENT_QUOTES, 'UTF-8'); ?> / 時間
                                    </div>
                                <?php endif; ?>

                                <?php if (!empty($item['review_summary'])): ?>
                                    <div class="card-review">
                                        💬 評価: <strong><?php echo htmlspecialchars($item['review_summary'], ENT_QUOTES, 'UTF-8'); ?></strong>
                                    </div>
                                <?php endif; ?>
                            </div>

                            <?php if (!empty($item['rank_code'])): ?>
                                <span class="rank-badge rank-<?php echo htmlspecialchars($item['rank_code'], ENT_QUOTES, 'UTF-8'); ?>">
                                    判定: <?php echo htmlspecialchars($item['rank'] ?? '', ENT_QUOTES, 'UTF-8'); ?>
                                </span>
                            <?php endif; ?>
                        </div>
                    </div>
                <?php endforeach; ?>
            </div>
        <?php endif; ?>

        <!-- ページ送りボタンエリア -->
        <?php if (empty($error_message)): ?>
            <div class="pagination">
                <?php if ($page > 1): ?>
                    <form method="POST" action="receive.php" style="margin: 0;">
                        <input type="hidden" name="keyword" value="<?php echo htmlspecialchars($keyword, ENT_QUOTES, 'UTF-8'); ?>">
                        <input type="hidden" name="price_range" value="<?php echo htmlspecialchars($price_range, ENT_QUOTES, 'UTF-8'); ?>">
                        <input type="hidden" name="genre" value="<?php echo htmlspecialchars($genre, ENT_QUOTES, 'UTF-8'); ?>">
                        <input type="hidden" name="time_limit" value="<?php echo htmlspecialchars($time_limit, ENT_QUOTES, 'UTF-8'); ?>">
                        <input type="hidden" name="page" value="<?php echo $page - 1; ?>">
                        <button type="submit" class="btn-page">&laquo; 前のページ</button>
                    </form>
                <?php endif; ?>

                <?php if (!empty($results)): ?>
                    <form method="POST" action="receive.php" style="margin: 0;">
                        <input type="hidden" name="keyword" value="<?php echo htmlspecialchars($keyword, ENT_QUOTES, 'UTF-8'); ?>">
                        <input type="hidden" name="price_range" value="<?php echo htmlspecialchars($price_range, ENT_QUOTES, 'UTF-8'); ?>">
                        <input type="hidden" name="genre" value="<?php echo htmlspecialchars($genre, ENT_QUOTES, 'UTF-8'); ?>">
                        <input type="hidden" name="time_limit" value="<?php echo htmlspecialchars($time_limit, ENT_QUOTES, 'UTF-8'); ?>">
                        <input type="hidden" name="page" value="<?php echo $page + 1; ?>">
                        <button type="submit" class="btn-page btn-next">次のページ（もっと見る） &raquo;</button>
                    </form>
                <?php endif; ?>
            </div>
        <?php endif; ?>

        <div style="text-align: center; margin-top: 15px;">
            <a href="index.php" style="color: #66c0f4; text-decoration: none; font-weight: bold; font-size: 0.95rem;">
                &laquo; 検索条件を変更する
            </a>
        </div>
    </div>

    <script>
        function sortCards() {
            const list = document.getElementById('results-list');
            if (!list) return;

            const sortBy = document.getElementById('sort-select').value;
            const cards = Array.from(list.getElementsByClassName('card'));

            cards.sort((a, b) => {
                if (sortBy === 'rank') {
                    return parseFloat(a.dataset.rank) - parseFloat(b.dataset.rank);
                } else if (sortBy === 'unit_asc') {
                    return parseFloat(a.dataset.unit) - parseFloat(b.dataset.unit);
                } else if (sortBy === 'hours_desc') {
                    return parseFloat(b.dataset.hours) - parseFloat(a.dataset.hours);
                } else if (sortBy === 'price_asc') {
                    return parseFloat(a.dataset.price) - parseFloat(b.dataset.price);
                } else {
                    return parseInt(a.dataset.index) - parseInt(b.dataset.index);
                }
            });

            cards.forEach(card => list.appendChild(card));
        }
    </script>
</body>
</html>