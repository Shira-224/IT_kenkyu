<?php
// POSTデータを安全に取得（3つの絞り込み条件のみ）
$price_range = isset($_POST['price_range']) ? $_POST['price_range'] : '';
$genre       = isset($_POST['genre']) ? $_POST['genre'] : '';
$time_limit  = isset($_POST['time_limit']) ? $_POST['time_limit'] : '';

$results = [];
$error_message = '';

// すべて「指定なし」になっていないかチェック
if ($price_range === '' && $genre === '' && $time_limit === '') {
    $error_message = '検索条件を少なくとも1つ以上選択してください。';
} else {
    // 1. Pythonスクリプトのパス
    $python_script = 'scraper.py';
    
    // 2. 引数を3つ（価格帯、ジャンル、時間上限）に調整してPythonに渡す
    $cmd = sprintf(
        'python3 %s %s %s %s',
        escapeshellarg($python_script),
        escapeshellarg($price_range),
        escapeshellarg($genre),
        escapeshellarg($time_limit)
    );

    // 3. Pythonを実行し、結果を受け取る
    $output = shell_exec($cmd);

    if ($output === null) {
        $error_message = 'Pythonスクリプトの実行に失敗しました（サーバー環境を確認してください）。';
    } else {
        $results = json_decode($output, true);
        
        if (json_last_error() !== JSON_ERROR_NONE) {
            $results = [];
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