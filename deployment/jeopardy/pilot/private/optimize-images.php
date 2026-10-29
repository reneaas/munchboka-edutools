<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
require __DIR__.'/app.php';
// Keep a durable cursor outside the deployment checkout; process at most ten per cron run.
$progress = fopen(__DIR__.'/.image-optimization-v1', 'c+');
if (!$progress) throw new RuntimeException('Cannot open image optimization progress.');
if (!flock($progress, LOCK_EX | LOCK_NB)) exit;
$cursor = trim(stream_get_contents($progress));
if ($cursor !== '' && !preg_match('/^[a-f0-9]{32}$/D', $cursor)) throw new RuntimeException('Invalid image optimization cursor.');
$db = jp_db();
$stmt = $db->prepare("SELECT id, owner_id FROM jp_media WHERE id > ? AND mime = 'image/png' ORDER BY id LIMIT 10");
$stmt->execute([$cursor]);
$rows = $stmt->fetchAll(); $saved = 0;
foreach ($rows as $row) {
    $image = jp_media($db, $row['id'], (int)$row['owner_id']);
    $optimized = jp_optimize_image($image['bytes']);
    if (strlen($optimized) < strlen($image['bytes'])) {
        $info = jp_image_info($optimized);
        // Preserve IDs and all references, and avoid overwriting a concurrent change.
        $update = $db->prepare('UPDATE jp_media SET bytes = ?, size = ?, mime = ?, width = ?, height = ? WHERE id = ? AND bytes = ?');
        $update->execute([$optimized, strlen($optimized), $info['mime'], $info['width'], $info['height'], $row['id'], $image['bytes']]);
        if ($update->rowCount()) $saved += strlen($image['bytes']) - strlen($optimized);
    }
    rewind($progress); ftruncate($progress, 0); fwrite($progress, $row['id']); fflush($progress);
}
flock($progress, LOCK_UN); fclose($progress);
if ($rows) echo 'Images: checked '.count($rows).", saved $saved bytes (lossless).\n";
