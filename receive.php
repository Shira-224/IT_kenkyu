<?php
// POSTデータを安全に取得（3つの絞り込み条件のみ）
$keyword     = isset($_POST['keyword']) ? trim($_POST['keyword']) : '';
$price_range = isset($_POST['price_range']) ? $_POST['price_range'] : '';
$genre       = isset($_POST['genre']) ? $_POST['genre'] : '';
$time_limit  = isset($_POST['time_limit']) ? $_POST['time_limit'] : '';

$results = [];
$error_message = '';

// すべて「指定なし」になっていないかチェック
if ($keyword === '' && $price_range === '' && $genre === '' && $time_limit === '') {
    $error_message = '検索条件を少なくとも1つ以上選択してください。';
} else {
    $url = 'http://127.0.0.1:5000/api/search?' . http_build_query([
        'keyword'     => $keyword,
        'price_range' => $price_range,
        'genre'       => $genre,
        'time_limit'  => $time_limit,
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
?>
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Steam検索結果</title>
    <link rel="stylesheet" href="style/style.css">
</head>
<body>
    <h1>Steam検索結果</h1>

    <div style="width: 100%; max-width: 500px;">
        <?php if (!empty($error_message)): ?>
            <!-- エラー時の表示 -->
            <div style="background-color: #2a475e; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #ff6b6b;">
                <p style="color: #ff6b6b; margin: 0;"><?php echo htmlspecialchars($error_message, ENT_QUOTES, 'UTF-8'); ?></p>
            </div>
        <?php elseif (empty($results)): ?>
            <!-- 該当データなしの表示 -->
            <div style="background-color: #2a475e; padding: 20px; border-radius: 8px; margin-bottom: 20px; text-align: center;">
                <p style="margin: 0; color: #c7d5e0;">一致するゲームが見つかりませんでした。</p>
            </div>
        <?php else: ?>
            <!-- 検索結果のリスト表示 -->
            <ul style="list-style: none; padding: 0; margin-bottom: 20px;">
                <?php foreach ($results as $item): ?>
                    <li style="background-color: #2a475e; padding: 15px; margin-bottom: 12px; border-radius: 6px; box-shadow: 0 4px 8px rgba(0,0,0,0.3);">
                        <strong style="color: #66c0f4; font-size: 1.1rem; display: block; margin-bottom: 6px;">
                            <?php echo htmlspecialchars($item['title'] ?? '名称不明', ENT_QUOTES, 'UTF-8'); ?>
                        </strong>
                        <span style="color: #c7d5e0; font-size: 0.95rem;">
                            価格: <?php echo htmlspecialchars($item['price'] ?? 'N/A', ENT_QUOTES, 'UTF-8'); ?>
                        </span>
                    </li>
                <?php endforeach; ?>
            </ul>
        <?php endif; ?>

        <!-- 戻るリンク -->
        <div style="text-align: center;">
            <a href="index.php" style="color: #66c0f4; text-decoration: none; font-weight: bold; font-size: 0.95rem;">
                &laquo; 検索画面に戻る
            </a>
        </div>
    </div>
</body>
</html>