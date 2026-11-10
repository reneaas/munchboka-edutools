<?php
declare(strict_types=1);
// Existing games retain their privacy until their owner explicitly publishes them.
function jp_is_private(array $content): bool { return ($content['private'] ?? true) !== false; }
function jp_public_game(PDO $db, mixed $id, bool $lock = false): array {
    if (!is_string($id) || !preg_match('/^[a-f0-9]{32}$/D', $id)) throw new DomainException('Spillet er ikke offentlig eller finnes ikke.');
    $stmt = $db->prepare('SELECT * FROM jp_games WHERE id = ?' . ($lock ? ' FOR UPDATE' : ''));
    $stmt->execute([$id]); $game = $stmt->fetch();
    if (!$game || jp_is_private(json_decode($game['content'], true, 32, JSON_THROW_ON_ERROR))) throw new DomainException('Spillet er ikke offentlig eller finnes ikke.');
    return $game;
}
function jp_discover(PDO $db, string $search, int $page = 0): array {
    if ($page < 0 || $page > 500) throw new DomainException('Ugyldig side.');
    $search = jp_text($search, 180);
    $visibility = $db->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql'
        ? "JSON_UNQUOTE(JSON_EXTRACT(content, '$.private')) = 'false'"
        : "JSON_TYPE(content, '$.private') = 'false'";
    $pattern = '%' . str_replace(['!', '%', '_'], ['!!', '!%', '!_'], $search) . '%';
    $stmt = $db->prepare("SELECT id,title FROM jp_games WHERE $visibility AND title LIKE ? ESCAPE '!' ORDER BY updated_at DESC,id DESC LIMIT 21 OFFSET " . ($page * 20));
    $stmt->execute([$pattern]); $rows = $stmt->fetchAll();
    return ['items' => array_slice($rows, 0, 20), 'more' => count($rows) > 20];
}
function jp_public_media(PDO $db, mixed $id, string $image): array {
    $game = jp_public_game($db, $id);
    $content = jp_normalize(json_decode($game['content'], true, 32, JSON_THROW_ON_ERROR));
    foreach ($content['categories'] as $category) foreach ($category['tiles'] as $tile) {
        foreach (['questionImage','answerImage'] as $side) {
            if (($tile[$side]['id'] ?? null) === $image) return jp_media($db, $image, (int)$game['owner_id']);
        }
    }
    throw new DomainException('Bildet finnes ikke i dette offentlige spillet.');
}
function jp_copy_public(PDO $db, int $uid, string $id): string {
    if ($uid <= 0) throw new DomainException('Logg inn for å lagre en kopi.');
    $db->beginTransaction();
    try {
        $original = jp_public_game($db, $id, true);
        $stmt = $db->prepare('SELECT id FROM jp_users WHERE id = ? FOR UPDATE'); $stmt->execute([$uid]);
        if (!$stmt->fetchColumn()) throw new DomainException('Logg inn på nytt.');
        $content = jp_normalize(json_decode($original['content'], true, 32, JSON_THROW_ON_ERROR));
        $stmt = $db->prepare('SELECT COALESCE(SUM(size),0) FROM jp_media WHERE owner_id = ?'); $stmt->execute([$uid]);
        $used = (int)$stmt->fetchColumn(); $images = [];
        foreach ($content['categories'] as &$category) foreach ($category['tiles'] as &$tile) {
            foreach (['questionImage','answerImage'] as $side) {
                if (empty($tile[$side])) continue;
                $image = $tile[$side]['id'];
                if (!isset($images[$image])) {
                    $media = jp_media($db, $image, (int)$original['owner_id']);
                    $images[$image] = $image;
                    if ((int)$original['owner_id'] !== $uid) {
                        $used += (int)$media['size'];
                        if ($used > 50*1024*1024) throw new DomainException('Kopien får ikke plass i bildelageret ditt (50 MB).');
                        $images[$image] = bin2hex(random_bytes(16));
                        $db->prepare('INSERT INTO jp_media (id,owner_id,mime,size,width,height,bytes) VALUES (?,?,?,?,?,?,?)')->execute([$images[$image],$uid,$media['mime'],$media['size'],$media['width'],$media['height'],$media['bytes']]);
                    }
                }
                $tile[$side]['id'] = $images[$image];
            }
        }
        unset($tile, $category);
        while (strlen($content['title']) > 173) $content['title'] = preg_replace('/.$/us', '', $content['title']);
        $content['title'] .= ' (kopi)'; $content['private'] = false;
        $content = jp_validate_content($db, $uid, $content);
        $json = json_encode($content, JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR);
        $copy = bin2hex(random_bytes(16));
        $db->prepare('INSERT INTO jp_games (id,owner_id,title,content,revision) VALUES (?,?,?,?,1)')->execute([$copy,$uid,$content['title'],$json]);
        $db->commit(); return $copy;
    } catch (Throwable $e) { if ($db->inTransaction()) $db->rollBack(); throw $e; }
}
