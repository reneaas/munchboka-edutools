<?php
declare(strict_types=1);
// Deployed beside the existing private Jeopardy application, not its credentials.
if (!function_exists('jp_db')) require __DIR__ . '/../app.php';
require_once __DIR__ . '/teams.php';
require_once __DIR__ . '/lightning.php';
function lq_query(PDO $db, string $sql, array $args = []): PDOStatement {
    $s = $db->prepare($sql); $s->execute($args); return $s;
}
function lq_transaction(PDO $db, callable $fn): mixed {
    $db->beginTransaction();
    try { $r = $fn(); $db->commit(); return $r; }
    catch (Throwable $e) { if ($db->inTransaction()) $db->rollBack(); throw $e; }
}
function lq_id(mixed $id): string {
    if (!is_string($id) || !preg_match('/^[a-f0-9]{32}$/D', $id)) throw new DomainException('Ugyldig ID.');
    return $id;
}
function lq_youtube(string $s): string {
    if ($s === '' || preg_match('/^[a-zA-Z0-9_-]{11}$/D', $s)) return $s;
    $u = parse_url($s);
    if (!$u || !in_array($u['scheme'] ?? '', ['https', 'http'], true)) throw new DomainException('Ugyldig YouTube-lenke.');
    $host = strtolower($u['host'] ?? ''); $id = '';
    if ($host === 'youtu.be') $id = trim($u['path'] ?? '', '/');
    if (in_array($host, ['youtube.com', 'www.youtube.com', 'm.youtube.com'], true)) {
        parse_str($u['query'] ?? '', $params);
        $id = $params['v'] ?? '';
        if (preg_match('~^/(?:embed|shorts)/([a-zA-Z0-9_-]{11})/?$~D', $u['path'] ?? '', $m)) $id = $m[1];
    }
    if (!is_string($id) || !preg_match('/^[a-zA-Z0-9_-]{11}$/D', $id)) throw new DomainException('Ugyldig YouTube-lenke.');
    return $id;
}
function lq_code(mixed $value): string {
    jp_text($value, 8000); // Validate type, size and UTF-8 without trimming code.
    return $value;
}
function lq_validate(PDO $db, int $uid, mixed $data): array {
    if (!is_array($data)) throw new DomainException('Ugyldig quiz.');
    $title = jp_text($data['title'] ?? '', 180); $questions = $data['questions'] ?? null;
    if ($title === '' || !is_array($questions) || !array_is_list($questions) || count($questions) < 1 || count($questions) > 50) throw new DomainException('Gi quizen en tittel og 1–50 spørsmål.');
    $scoring = $data['scoring'] ?? 'fixed';
    if (!in_array($scoring, ['fixed', 'speed'], true)) throw new DomainException('Ugyldig poengstil.');
    $out = ['title' => $title, 'scoring' => $scoring, 'questions' => []];
    foreach ($questions as $q) {
        if (!is_array($q) || !in_array($q['type'] ?? '', ['single', 'multi', 'text'], true)) throw new DomainException('Ugyldig spørsmålstype.');
        $c = ['type' => $q['type'], 'prompt' => jp_text($q['prompt'] ?? '', 8000), 'code' => lq_code($q['code'] ?? ''),
            'youtube' => lq_youtube(jp_text($q['youtube'] ?? '', 500)), 'image' => null];
        $seconds = $q['seconds'] ?? 30;
        if (!is_int($seconds) || $seconds < 5 || $seconds > 600) throw new DomainException('Velg 5–600 sekunder.');
        $c['seconds'] = $seconds;
        if (($q['image'] ?? null) !== null) {
            if (!is_array($q['image'])) throw new DomainException('Ugyldig bilde.');
            $id = lq_id($q['image']['id'] ?? null); jp_media($db, $id, $uid, false);
            $alt = jp_text($q['image']['alt'] ?? '', 500);
            $c['image'] = ['id' => $id, 'alt' => $alt];
        }
        if ($c['prompt'] === '' && trim($c['code']) === '' && !$c['image'] && !$c['youtube']) throw new DomainException('Spørsmålet trenger innhold.');
        $c['options'] = []; $c['correct'] = []; $c['accepted'] = [];
        if ($c['type'] === 'text') {
            $a = $q['accepted'] ?? null;
            if (!is_array($a) || !array_is_list($a) || count($a) < 1 || count($a) > 20) throw new DomainException('Legg til 1–20 godkjente svar.');
            foreach ($a as $v) { $v = jp_text($v, 500); if ($v === '') throw new DomainException('Godkjente svar kan ikke være tomme.'); $c['accepted'][] = $v; }
        } else {
            $opts = $q['options'] ?? null; $correct = $q['correct'] ?? null;
            if (!is_array($opts) || !array_is_list($opts) || count($opts) < 2 || count($opts) > 6 || !is_array($correct) || !array_is_list($correct) || !$correct) throw new DomainException('Legg til 2–6 alternativer og marker fasit.');
            foreach ($opts as $v) { $v = jp_text($v, 1000); if ($v === '') throw new DomainException('Svaralternativer kan ikke være tomme.'); $c['options'][] = $v; }
            foreach ($correct as $v) if (!is_int($v) || $v < 0 || $v >= count($opts)) throw new DomainException('Ugyldig fasit.');
            $c['correct'] = array_values(array_unique($correct)); sort($c['correct']);
            if ($c['type'] === 'single' && count($c['correct']) !== 1) throw new DomainException('Velg nøyaktig ett riktig alternativ.');
        }
        $out['questions'][] = $c;
    }
    return $out;
}
function lq_quiz(PDO $db, int $uid, string $id): array {
    $r = lq_query($db, 'SELECT * FROM lq_quizzes WHERE id = ? AND owner_id = ?', [lq_id($id), $uid])->fetch();
    if (!$r) throw new DomainException('Quizen finnes ikke på din konto.');
    return $r;
}
function lq_save(PDO $db, int $uid, array $input): array {
    $content = lq_validate($db, $uid, $input['content'] ?? null);
    if (($input['id'] ?? '') === '' && !empty($input['folder'])) lq_library_prepare($db, $uid);
    return lq_transaction($db, function () use ($db, $uid, $input, $content) {
        $id = $input['id'] ?? ''; $rev = 1; $json = json_encode($content, JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE);
        if ($id === '') {
            $library = !empty($input['folder']) ? lq_library_data($db, $uid, true) : null;
            $folder = $library !== null ? lq_folder_id($library, $input['folder']) : null;
            $id = bin2hex(random_bytes(16));
            lq_query($db, 'INSERT INTO lq_quizzes (id, owner_id, title, content, revision) VALUES (?, ?, ?, ?, 1)', [$id, $uid, $content['title'], $json]);
            if ($folder !== null) { $library['quiz_folders'][$id] = $folder; lq_library_write($db, $uid, $library); }
        } else {
            $r = lq_query($db, 'SELECT revision, content FROM lq_quizzes WHERE id = ? AND owner_id = ? FOR UPDATE', [lq_id($id), $uid])->fetch();
            if ($r === false || (int)$r['revision'] !== ($input['revision'] ?? null)) throw new DomainException('Quizen er endret i en annen fane eller utilgjengelig. Kopier arbeidet ditt før du åpner den på nytt.');
            $rev = (int)$r['revision'] + 1;
            $previous = json_decode($r['content'], true, 32, JSON_THROW_ON_ERROR);
            if (isset($previous['_share'])) $content['_share'] = $previous['_share'];
            $json = json_encode($content, JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE);
            lq_query($db, 'UPDATE lq_quizzes SET title = ?, content = ?, revision = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', [$content['title'], $json, $rev, $id]);
        }
        return ['id' => $id, 'revision' => $rev];
    });
}
function lq_delete(PDO $db, int $uid, array $input): array {
    $id = lq_id($input['id'] ?? '');
    lq_library_prepare($db, $uid);
    return lq_transaction($db, function () use ($db, $uid, $id) {
        $library = lq_library_data($db, $uid, true);
        lq_quiz($db, $uid, $id);
        lq_query($db, 'DELETE FROM lq_quizzes WHERE id = ? AND owner_id = ?', [$id, $uid]);
        unset($library['quiz_folders'][$id]);
        lq_library_write($db, $uid, $library);
        return ['ok' => true];
    });
}
function lq_create_room(PDO $db, int $uid, string $id): array {
    $quiz = lq_quiz($db, $uid, $id);
    $content = json_decode($quiz['content'], true, 32, JSON_THROW_ON_ERROR);
    return lq_insert_room($db, $uid, $content);
}
function lq_insert_room(PDO $db, int $uid, array $content): array {
    unset($content['_share']);
    $content['play'] = lq_validate_play('individual', 3);
    $content['lightning'] = ['enabled'=>false,'seconds'=>60];
    $snapshot = json_encode($content, JSON_THROW_ON_ERROR);
    for ($attempt = 0; $attempt < 10; $attempt++) {
        $room = bin2hex(random_bytes(16)); $pin = (string)random_int(100000, 999999);
        try {
            lq_query($db, 'INSERT INTO lq_rooms (id, pin, owner_id, content, expires_at) VALUES (?, ?, ?, ?, ?)', [$room, $pin, $uid, $snapshot, time() + 21600]);
            return ['room' => $room, 'pin' => $pin];
        } catch (PDOException $e) { if ($e->getCode() !== '23000') throw $e; }
    }
    throw new DomainException('Kunne ikke lage spillkode. Prøv igjen.');
}
function lq_room(PDO $db, string $id, bool $lock = false): array {
    $r = lq_query($db, 'SELECT * FROM lq_rooms WHERE id = ?' . ($lock ? ' FOR UPDATE' : ''), [lq_id($id)])->fetch();
    if (!$r || (int)$r['expires_at'] <= time()) throw new DomainException('Spillet finnes ikke eller er utløpt.');
    return $r;
}
function lq_join(PDO $db, string $pin, string $name, string $token): array {
    if (!preg_match('/^[0-9]{6}$/D', $pin) || !preg_match('/^[a-f0-9]{64}$/D', $token)) throw new DomainException('Skriv en gyldig spillkode.');
    $name = jp_text($name, 80); if ($name === '') throw new DomainException('Skriv et kallenavn.');
    return lq_transaction($db, function () use ($db, $pin, $name, $token) {
        $r = lq_query($db, 'SELECT * FROM lq_rooms WHERE pin = ? FOR UPDATE', [$pin])->fetch();
        if (!$r || (int)$r['expires_at'] <= time()) throw new DomainException('Spillkoden er ugyldig eller utløpt.');
        $old = lq_query($db, 'SELECT id, room_id FROM lq_players WHERE token_hash = ?', [hash('sha256', $token)])->fetch();
        if ($old && $old['room_id'] === $r['id']) return ['room' => $r['id']];
        if (in_array($r['phase'], ['light_intro','light_count','lightning','light_done'], true)) throw new DomainException('Lynrunden er startet. Nye deltakere må vente til neste spill.');
        $play = lq_play_settings(json_decode($r['content'], true, 32, JSON_THROW_ON_ERROR));
        if ($play['mode'] === 'teams' && $r['phase'] !== 'lobby') throw new DomainException('Lagene er allerede fordelt. Nye deltakere må vente til neste spill.');
        if ($old || $r['phase'] === 'finished') throw new DomainException('Spillet er avsluttet. Be læreren starte et nytt spill.');
        if ((int)lq_query($db, 'SELECT COUNT(*) FROM lq_players WHERE room_id = ?', [$r['id']])->fetchColumn() >= 60) throw new DomainException('Spillet er fullt (60 deltakere).');
        lq_query($db, 'INSERT INTO lq_players (id, room_id, nickname, token_hash) VALUES (?, ?, ?, ?)', [bin2hex(random_bytes(16)), $r['id'], $name, hash('sha256', $token)]);
        return ['room' => $r['id']];
    });
}
function lq_player(PDO $db, string $room, string $token): array {
    $r = lq_query($db, 'SELECT * FROM lq_players WHERE room_id = ? AND token_hash = ?', [$room, hash('sha256', $token)])->fetch();
    if (!$r) throw new DomainException('Bli med i spillet først.'); return $r;
}
function lq_control(PDO $db, int $uid, array $input, string $hostToken = ''): array {
    return lq_transaction($db, function () use ($db, $uid, $input, $hostToken) {
        $r = lq_room($db, $input['room'] ?? '', true);
        lq_require_host($r, $uid, $hostToken);
        if ((int)$r['version'] !== ($input['version'] ?? null)) throw new DomainException('Spillet er allerede oppdatert. Prøv igjen.');
        $cmd = $input['command'] ?? ''; $phase = $r['phase']; $index = (int)$r['question_index']; $deadline = 0;
        $content = json_decode($r['content'], true, 32, JSON_THROW_ON_ERROR);
        $qs = $content['questions']; $play = lq_play_settings($content);
        if ($cmd === 'configure' && $phase === 'lobby') {
            $content['play'] = lq_validate_play($input['mode'] ?? null, $input['max_team_size'] ?? null);
            $content['lightning'] = lq_validate_lightning($input['lightning'] ?? lq_lightning_settings($content));
            lq_query($db, 'UPDATE lq_rooms SET content = ? WHERE id = ?', [json_encode($content, JSON_THROW_ON_ERROR), $r['id']]);
        } elseif ($cmd === 'next' && $phase === 'lobby') {
            if ($play['mode'] === 'teams') {
                $roster = lq_query($db, 'SELECT id, nickname FROM lq_players WHERE room_id = ? ORDER BY id', [$r['id']])->fetchAll();
                $play['teams'] = lq_assign_teams($roster, $play['max_team_size']);
                $content['play'] = $play;
                lq_query($db, 'UPDATE lq_rooms SET content = ? WHERE id = ?', [json_encode($content, JSON_THROW_ON_ERROR), $r['id']]);
                $phase = 'teams';
            } else {
                $phase = 'countdown'; $deadline = (int)ceil(microtime(true) * 1000) + 3000;
            }
        } elseif ($cmd === 'next' && $phase === 'teams') {
            $phase = 'countdown'; $deadline = (int)ceil(microtime(true) * 1000) + 3000;
        } elseif ($cmd === 'reveal' && $phase === 'question') { $phase = 'reveal'; }
        elseif ($cmd === 'leaderboard' && $phase === 'reveal') { $phase = 'leaderboard'; }
        elseif ($cmd === 'next' && $phase === 'leaderboard') {
            $phase = $index + 1 < count($qs) ? 'countdown' : (lq_lightning_settings($content)['enabled'] ? 'light_intro' : 'finished');
            if ($phase === 'countdown') $deadline = (int)ceil(microtime(true) * 1000) + 3000;
        }
        elseif ($cmd === 'next' && $phase === 'light_intro') {
            $r = lq_lightning_prepare($db, $r, $content);
            $phase = 'light_count'; $deadline = (int)ceil(microtime(true)*1000)+3000;
        }
        elseif ($cmd === 'next' && $phase === 'light_done') { $phase = 'finished'; }
        elseif ($cmd === 'finish' && $phase !== 'finished') { $phase = 'finished'; }
        else throw new DomainException('Denne handlingen er ikke tilgjengelig nå.');
        lq_transition($db, $r, $phase, $index, $deadline);
        return ['ok' => true];
    });
}
function lq_transition(PDO $db, array $room, string $phase, int $index, int $deadline): array {
    lq_query($db, 'UPDATE lq_rooms SET phase = ?, question_index = ?, deadline = ?, version = version + 1 WHERE id = ?', [$phase, $index, $deadline, $room['id']]);
    return array_replace($room, ['phase' => $phase, 'question_index' => $index, 'deadline' => $deadline, 'version' => (int)$room['version'] + 1]);
}
function lq_deadline(array $room): int|float {
    $deadline = (int)$room['deadline'];
    return $deadline > 1000000000000 ? $deadline / 1000 : $deadline;
}
function lq_advance_locked(PDO $db, array $room): array {
    if (in_array($room['phase'], ['light_count','lightning'], true)) return lq_lightning_advance($db, $room);
    if ($room['phase'] === 'countdown' && microtime(true) >= lq_deadline($room)) {
        $index = (int)$room['question_index'] + 1;
        $questions = json_decode($room['content'], true, 32, JSON_THROW_ON_ERROR)['questions'];
        $room = lq_transition($db, $room, 'question', $index, (int)round((lq_deadline($room) + $questions[$index]['seconds']) * 1000));
    }
    if ($room['phase'] === 'question') {
        $players = (int)lq_query($db, 'SELECT COUNT(*) FROM lq_players WHERE room_id = ?', [$room['id']])->fetchColumn();
        $answers = (int)lq_query($db, 'SELECT COUNT(*) FROM lq_answers WHERE room_id = ? AND question_index = ?', [$room['id'], (int)$room['question_index']])->fetchColumn();
        if (lq_is_done($room, $players, $answers)) $room = lq_transition($db, $room, 'reveal', (int)$room['question_index'], 0);
    }
    return $room;
}
function lq_normalize_answer(string $s): string {
    $s = preg_replace('/[\s\p{Z}]+/u', '', $s);
    $s = function_exists('mb_strtolower') ? mb_strtolower($s, 'UTF-8') : strtolower(strtr($s, ['Æ'=>'æ','Ø'=>'ø','Å'=>'å']));
    // Normalize decimal separators only for a complete numeric answer.
    if (preg_match('/^[+-]?(?:[0-9]+(?:[.,][0-9]+)?|[.,][0-9]+)$/D', $s)) $s = str_replace(',', '.', $s);
    return $s;
}
function lq_grade(array $q, mixed $answer): array {
    if ($q['type'] === 'text') {
        $answer = jp_text($answer, 500);
        if (lq_normalize_answer($answer) === '') throw new DomainException('Skriv et svar.');
        return [$answer, in_array(lq_normalize_answer($answer), array_map('lq_normalize_answer', $q['accepted']), true) ? 1000 : 0];
    }
    if (!is_array($answer) || !array_is_list($answer) || !$answer || count($answer) > 6) throw new DomainException('Velg et svar.');
    foreach ($answer as $v) if (!is_int($v) || $v < 0 || $v >= count($q['options'])) throw new DomainException('Ugyldig svaralternativ.');
    $answer = array_values(array_unique($answer)); sort($answer);
    if ($q['type'] === 'single' && count($answer) !== 1) throw new DomainException('Velg ett alternativ.');
    return [$answer, $answer === $q['correct'] ? 1000 : 0];
}
function lq_points(int $grade, string $scoring, int $seconds, float $remaining, bool $hasVideo = false): int {
    if ($grade === 0) return 0;
    if ($scoring !== 'speed') return 1000;
    // Video questions keep full points for the first four seconds. The answer
    // deadline stays unchanged; the remaining interval decays linearly to zero.
    $scoredSeconds = max(1, $seconds - ($hasVideo ? 4 : 0));
    return (int)round(1000 * max(0.0, min(1.0, $remaining / $scoredSeconds)));
}
function lq_answer(PDO $db, array $input, string $token): array {
    return lq_transaction($db, function () use ($db, $input, $token) {
        $r = lq_room($db, $input['room'] ?? '', true); $p = lq_player($db, $r['id'], $token);
        $index = $input['index'] ?? null;
        if (!is_int($index) || $index < 0) throw new DomainException('Ugyldig spørsmål.');
        // Retries return the original acknowledgement, without leaking points before reveal.
        if (lq_query($db, 'SELECT 1 FROM lq_answers WHERE room_id = ? AND player_id = ? AND question_index = ?', [$r['id'], $p['id'], $index])->fetchColumn()) return ['accepted' => true];
        $receivedAt = microtime(true);
        if ($r['phase'] !== 'question' || $index !== (int)$r['question_index'] || $receivedAt >= lq_deadline($r)) throw new DomainException('Spørsmålet er stengt.');
        $content = json_decode($r['content'], true, 32, JSON_THROW_ON_ERROR);
        $q = $content['questions'][$index];
        [$answer, $grade] = lq_grade($q, $input['answer'] ?? null);
        $points = lq_points($grade, $content['scoring'] ?? 'fixed', $q['seconds'], lq_deadline($r) - $receivedAt, !empty($q['youtube']));
        lq_query($db, 'INSERT INTO lq_answers (room_id, player_id, question_index, answer, points) VALUES (?, ?, ?, ?, ?)', [$r['id'], $p['id'], $index, json_encode($answer, JSON_THROW_ON_ERROR), $points]);
        lq_advance_locked($db, $r);
        return ['accepted' => true];
    });
}
function lq_is_done(array $r, int $players, int $answers): bool {
    if ($r['phase'] !== 'question') return false;
    return microtime(true) >= lq_deadline($r) || ($players > 0 && $answers >= $players);
}
function lq_state(PDO $db, string $room, int $uid, string $token, bool $host, string $hostToken = ''): array {
    return lq_transaction($db, function () use ($db, $room, $uid, $token, $host, $hostToken) {
    $r = lq_room($db, $room, true);
    if ($host) lq_require_host($r, $uid, $hostToken);
    $p = $host ? null : lq_player($db, $room, $token);
    $r = lq_advance_locked($db, $r);
    return lq_state_payload($db, $r, $p, $host);
    });
}
function lq_state_payload(PDO $db, array $r, ?array $p, bool $host): array {
    $room = $r['id'];
    $content = json_decode($r['content'], true, 32, JSON_THROW_ON_ERROR);
    $index = (int)$r['question_index'];
    $players = (int)lq_query($db, 'SELECT COUNT(*) FROM lq_players WHERE room_id = ?', [$room])->fetchColumn();
    $answers = (int)lq_query($db, 'SELECT COUNT(*) FROM lq_answers WHERE room_id = ? AND question_index = ?', [$room, $index])->fetchColumn();
    $revealed = in_array($r['phase'], ['reveal', 'leaderboard', 'countdown', 'finished'], true);
    $states = ['lobby' => 'LOBBY', 'teams' => 'TEAM_OVERVIEW', 'question' => 'QUESTION_ACTIVE', 'reveal' => 'QUESTION_RESULTS', 'leaderboard' => 'LEADERBOARD', 'countdown' => 'COUNTDOWN', 'finished' => 'QUIZ_FINISHED', 'light_intro'=>'LIGHTNING_INTRO', 'light_count'=>'LIGHTNING_COUNTDOWN', 'lightning'=>'LIGHTNING_ACTIVE', 'light_done'=>'LIGHTNING_FINISHED'];
    $state = ['room' => $room, 'title' => $content['title'], 'phase' => $r['phase'], 'index' => $index,
        'scoring' => $content['scoring'] ?? 'fixed',
        'state' => $states[$r['phase']], 'countdown_end' => in_array($r['phase'], ['countdown','light_count'], true) ? lq_deadline($r) : null,
        'version' => (int)$r['version'], 'deadline' => lq_deadline($r), 'now' => microtime(true), 'total' => count($content['questions']),
        'players' => $players, 'answers' => $answers];
    $play = lq_play_settings($content);
    $state['mode'] = $play['mode']; $state['max_team_size'] = $play['max_team_size'];
    $state['teams'] = $play['teams']; $state['my_team'] = null;
    if ($p) foreach ($play['teams'] as $team) {
        if (in_array($p['id'], array_column($team['members'], 'id'), true)) $state['my_team'] = $team['id'];
    }
    $state['lightning'] = lq_lightning_settings($content);
    if ($host) $state['pin'] = $r['pin'];
    if (in_array($r['phase'], ['light_intro','light_count','lightning','light_done'], true)) return lq_lightning_state($db,$r,$p,$state,$content);
    if (isset($content['questions'][$index]) && $r['phase'] !== 'finished') {
        $q = $content['questions'][$index];
        if (!$revealed) unset($q['correct'], $q['accepted']);
        // Only the host receives image metadata and the video ID, including on results.
        if (!$host) unset($q['youtube'], $q['image']);
        $state['question'] = $q;
    }
    if ($p) {
        $a = lq_query($db, 'SELECT answer, points FROM lq_answers WHERE room_id = ? AND player_id = ? AND question_index = ?', [$room, $p['id'], $index])->fetch();
        $state['submitted'] = (bool)$a;
        if ($a) $state['answer'] = json_decode($a['answer'], true, 8, JSON_THROW_ON_ERROR);
        if ($a && $revealed) $state['points'] = (int)$a['points'];
    }
    if ($host && $r['phase'] === 'lobby') $state['roster'] = lq_query($db, 'SELECT nickname FROM lq_players WHERE room_id = ? ORDER BY nickname', [$room])->fetchAll(PDO::FETCH_COLUMN);
    if ($revealed) $state['leaderboard'] = lq_leaderboard($db, $room, $content);
    if ($host && $r['phase'] === 'reveal' && isset($content['questions'][$index])) {
        $cq = $content['questions'][$index]; $counts = array_fill(0, count($cq['options']), 0); $correct = 0;
        $rows = lq_query($db, 'SELECT answer, points FROM lq_answers WHERE room_id = ? AND question_index = ?', [$room, $index])->fetchAll();
        foreach ($rows as $row) {
            $submitted = json_decode($row['answer'], true, 8, JSON_THROW_ON_ERROR);
            if (lq_grade($cq, $submitted)[1] > 0) $correct++;
            if ($cq['type'] === 'text') continue;
            foreach ($submitted as $i) if (isset($counts[$i])) $counts[$i]++;
        }
        $state['distribution'] = ['counts' => $counts, 'correct' => $correct, 'answered' => count($rows)];
    }
    return $state;
}
function lq_room_media(PDO $db, string $room, int $uid, string $token, bool $host, string $image, string $hostToken = ''): array {
    $r = lq_room($db, $room);
    if (!$host && $r['phase']==='lightning' && microtime(true)<lq_deadline($r)) {
        $player=lq_player($db,$room,$token);
        $progress=lq_lightning_progress($db,$r,$player['id']);
        $content=json_decode($r['content'],true,32,JSON_THROW_ON_ERROR);
        $question=$progress['index'] !== null ? $content['questions'][$progress['index']] : null;
        if (($question['image']['id'] ?? '') !== $image) throw new DomainException('Bildet er ikke tilgjengelig.');
        return jp_media($db,lq_id($image),(int)$r['owner_id']);
    }
    if (!$host) throw new DomainException('Bilder vises bare på lærerskjermen.');
    lq_require_host($r, $uid, $hostToken);
    $content = json_decode($r['content'], true, 32, JSON_THROW_ON_ERROR);
    $q = $content['questions'][(int)$r['question_index']] ?? null;
    if (!in_array($r['phase'], ['question','reveal','leaderboard'], true) || ($q['image']['id'] ?? '') !== $image) throw new DomainException('Bildet er ikke tilgjengelig.');
    return jp_media($db, lq_id($image), (int)$r['owner_id']);
}

require_once __DIR__ . '/library.php';
require_once __DIR__ . '/sharing.php';
require_once __DIR__ . '/auth.php';
