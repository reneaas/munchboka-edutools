<?php
declare(strict_types=1);

// Sharing metadata lives in the existing JSON columns; no schema migration needed.
function lq_share(PDO $db, int $uid, string $id, bool $enabled): array {
    if ($uid <= 0) throw new DomainException('Logg inn først.');
    return lq_transaction($db, function () use ($db, $uid, $id, $enabled) {
        $quiz = lq_query($db, 'SELECT * FROM lq_quizzes WHERE id = ? AND owner_id = ? FOR UPDATE', [lq_id($id), $uid])->fetch();
        if (!$quiz) throw new DomainException('Quizen finnes ikke på din konto.');
        $content = json_decode($quiz['content'], true, 32, JSON_THROW_ON_ERROR);
        if ($enabled && lq_is_private($content)) throw new DomainException('Gjør quizen offentlig før du deler den.');
        if ($enabled) $content['_share'] ??= bin2hex(random_bytes(32));
        else unset($content['_share']);
        lq_query($db, 'UPDATE lq_quizzes SET content = ? WHERE id = ?', [json_encode($content, JSON_THROW_ON_ERROR), $id]);
        return ['key' => $content['_share'] ?? null];
    });
}
function lq_shared_quiz(PDO $db, string $id, string $key, bool $lock = false): array {
    if (!preg_match('/^[a-f0-9]{64}$/D', $key)) throw new DomainException('Delingslenken er ugyldig eller slått av.');
    $quiz = lq_query($db, 'SELECT * FROM lq_quizzes WHERE id = ?'.($lock ? ' FOR UPDATE' : ''), [lq_id($id)])->fetch();
    $content = $quiz ? json_decode($quiz['content'], true, 32, JSON_THROW_ON_ERROR) : [];
    if (lq_is_private($content) || !isset($content['_share']) || !hash_equals($content['_share'], $key)) throw new DomainException('Delingslenken er ugyldig eller slått av.');
    return $quiz;
}
function lq_shared_start(PDO $db, string $id, string $key, string $hostToken): array {
    if (!preg_match('/^[a-f0-9]{64}$/D', $hostToken)) throw new DomainException('Ugyldig vertsnøkkel.');
    return lq_transaction($db, function () use ($db, $id, $key, $hostToken) {
        $quiz = lq_shared_quiz($db, $id, $key, true);
        $content = json_decode($quiz['content'], true, 32, JSON_THROW_ON_ERROR);
        $content['_host_hash'] = hash('sha256', $hostToken);
        return lq_insert_room($db, (int)$quiz['owner_id'], $content);
    });
}
function lq_require_host(array $room, int $uid, string $hostToken): void {
    if ($uid > 0 && (int)$room['owner_id'] === $uid) return;
    $content = json_decode($room['content'], true, 32, JSON_THROW_ON_ERROR);
    if (preg_match('/^[a-f0-9]{64}$/D', $hostToken) && isset($content['_host_hash'])
        && hash_equals($content['_host_hash'], hash('sha256', $hostToken))) return;
    throw new DomainException('Ingen tilgang til å styre dette spillet. Åpne delingslenken for å starte ditt eget spill.');
}
