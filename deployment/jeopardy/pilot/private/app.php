<?php
declare(strict_types=1);

// Private application code. database.php lives beside this file, never in Git.
const JP_ORIGIN = 'https://jeopardy.munchboka.no';
const JP_SENDER = 'noreply@jeopardy.munchboka.no';

function jp_db(): PDO
{
    static $db;
    if ($db instanceof PDO) return $db;
    $c = require __DIR__ . '/database.php';
    $db = new PDO(sprintf('mysql:host=%s;port=%d;dbname=%s;charset=utf8mb4',
        $c['host'], $c['port'], $c['name']), $c['user'], $c['password'], [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_EMULATE_PREPARES => false,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    ]);
    $db->exec("SET time_zone = '+00:00'");
    return $db;
}

function jp_schema(PDO $db): void
{
    // Additive first-run schema for this pilot. Never drops or alters existing data.
    foreach (explode(';', file_get_contents(__DIR__ . '/schema.sql')) as $sql) {
        if (trim($sql) !== '') $db->exec($sql);
    }
}

function jp_h(string $s): string
{
    return htmlspecialchars($s, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function jp_input(string $key, int $limit): string
{
    $value = $_POST[$key] ?? '';
    if (!is_string($value) || strlen($value) > $limit || !preg_match('//u', $value)) {
        throw new DomainException('Et felt er for langt eller har ugyldig innhold.');
    }
    return trim($value);
}

function jp_redirect(string $query = ''): never
{
    header('Location: /' . $query, true, 303);
    exit;
}

function jp_allowed_email(string $email): bool
{
    return strlen($email) <= 254 && filter_var($email, FILTER_VALIDATE_EMAIL) !== false
        && str_ends_with(strtolower($email), '@osloskolen.no');
}

// Called within the login transaction; one shared lock caps total outbound mail.
function jp_mail_budget(PDO $db, int $now): void
{
    $db->prepare('INSERT IGNORE INTO jp_mail_budget (id) VALUES (?)')->execute([1]);
    $stmt = $db->prepare('SELECT * FROM jp_mail_budget WHERE id = ? FOR UPDATE');
    $stmt->execute([1]);
    $row = $stmt->fetch();
    $fresh = $now - (int) $row['window_at'] >= 3600;
    $count = $fresh ? 0 : (int) $row['send_count'];
    if ($count >= 500) throw new DomainException('Mange ber om kode akkurat nå. Prøv igjen senere.');
    $db->prepare('UPDATE jp_mail_budget SET window_at = ?, send_count = ? WHERE id = ?')
        ->execute([$fresh ? $now : $row['window_at'], $count + 1, 1]);
}

function jp_send_code(PDO $db, string $email): void
{
    $email = strtolower(trim($email));
    if (!jp_allowed_email($email)) {
        throw new DomainException('Bruk en e-postadresse som slutter på @osloskolen.no.');
    }
    $code = (string) random_int(10000000, 99999999);
    $challenge = bin2hex(random_bytes(32));
    $now = time();
    $db->beginTransaction();
    try {
        jp_mail_budget($db, $now);
        $db->prepare('INSERT IGNORE INTO jp_login (email) VALUES (?)')->execute([$email]);
        $stmt = $db->prepare('SELECT * FROM jp_login WHERE email = ? FOR UPDATE');
        $stmt->execute([$email]);
        $row = $stmt->fetch();
        if ($now - (int) $row['sent_at'] < 60) {
            throw new DomainException('Vent ett minutt før du ber om en ny kode.');
        }
        $freshWindow = $now - (int) $row['window_at'] >= 3600;
        $count = $freshWindow ? 0 : (int) $row['send_count'];
        if ($count >= 5) throw new DomainException('For mange kodeforespørsler. Prøv igjen om en time.');
        $db->prepare('UPDATE jp_login SET challenge = ?, code_hash = ?, expires_at = ?, attempts = 0, sent_at = ?, window_at = ?, send_count = ? WHERE email = ?')
            ->execute([$challenge, password_hash($code, PASSWORD_DEFAULT), $now + 600,
                $now, $freshWindow ? $now : $row['window_at'], $count + 1, $email]);
        $db->commit();
    } catch (Throwable $e) {
        if ($db->inTransaction()) $db->rollBack();
        throw $e;
    }
    $body = "Din innloggingskode til Munchboka Jeopardy er:\r\n\r\n" . $code
        . "\r\n\r\nKoden gjelder i 10 minutter og kan brukes en gang.\r\n"
        . "Skriv den inn i nettleseren der du ba om koden:\r\n" . JP_ORIGIN
        . "\r\n\r\nHvis du ikke ba om denne koden, kan du ignorere meldingen.\r\n";
    $accepted = mail($email, 'Innloggingskode til Munchboka Jeopardy', $body, [
        'From' => 'Munchboka Jeopardy <' . JP_SENDER . '>',
        'MIME-Version' => '1.0',
        'Content-Type' => 'text/plain; charset=UTF-8',
    ], '-f' . JP_SENDER);
    if (!$accepted) {
        $db->prepare('UPDATE jp_login SET code_hash = NULL WHERE email = ? AND challenge = ?')->execute([$email, $challenge]);
        throw new DomainException('E-posttjenesten kunne ikke sende koden. Prøv igjen senere.');
    }
    $_SESSION['challenge'] = $challenge;
    $_SESSION['email_pending'] = $email;
    $_SESSION['flash'] = 'Koden er sendt til e-posttjenesten. Se etter meldingen i innboksen og søppelpost.';
}

function jp_verify(PDO $db, string $code): void
{
    $email = $_SESSION['email_pending'] ?? '';
    $challenge = $_SESSION['challenge'] ?? '';
    if (!is_string($email) || !jp_allowed_email($email) || !is_string($challenge) || strlen($challenge) !== 64) {
        throw new DomainException('Be om en ny kode først.');
    }
    $db->beginTransaction();
    try {
        $stmt = $db->prepare('SELECT * FROM jp_login WHERE email = ? FOR UPDATE');
        $stmt->execute([$email]);
        $row = $stmt->fetch();
        if (!$row || !$row['code_hash'] || !hash_equals((string) $row['challenge'], $challenge)
            || (int) $row['expires_at'] < time() || (int) $row['attempts'] >= 5) {
            throw new DomainException('Koden er utløpt eller brukt opp. Be om en ny kode.');
        }
        $db->prepare('UPDATE jp_login SET attempts = attempts + 1 WHERE email = ?')->execute([$email]);
        if (!preg_match('/^[0-9]{8}$/D', $code) || !password_verify($code, $row['code_hash'])) {
            $db->commit(); // Failed attempts must persist.
            throw new DomainException('Feil kode. Kontroller de åtte sifrene og prøv igjen.');
        }
        $db->prepare('UPDATE jp_login SET code_hash = NULL, challenge = NULL WHERE email = ?')->execute([$email]);
        $db->prepare('INSERT IGNORE INTO jp_users (email) VALUES (?)')->execute([$email]);
        $stmt = $db->prepare('SELECT id FROM jp_users WHERE email = ?');
        $stmt->execute([$email]);
        $uid = (int) $stmt->fetchColumn();
        $db->commit();
        session_regenerate_id(true);
        $_SESSION = ['uid' => $uid, 'email' => $email, 'authenticated_at' => time(),
            'csrf' => bin2hex(random_bytes(32)), 'flash' => 'Du er logget inn.'];
    } catch (Throwable $e) {
        if ($db->inTransaction()) $db->rollBack();
        throw $e;
    }
}

function jp_new_game(): array
{
    return ['title' => '', 'categories' => []];
}

function jp_game(PDO $db, string $id, int $uid): array
{
    $stmt = $db->prepare('SELECT * FROM jp_games WHERE id = ? AND owner_id = ?');
    $stmt->execute([$id, $uid]);
    $game = $stmt->fetch();
    if (!$game) throw new DomainException('Spillet finnes ikke eller tilhører en annen konto.');
    return $game;
}

function jp_delete(PDO $db, int $uid, string $id): void
{
    if (!preg_match('/^[a-f0-9]{32}$/D', $id)) throw new DomainException('Ugyldig spill.');
    $db->beginTransaction();
    try {
        $stmt = $db->prepare('SELECT id FROM jp_games WHERE id = ? AND owner_id = ? FOR UPDATE');
        $stmt->execute([$id, $uid]);
        if (!$stmt->fetchColumn()) throw new DomainException('Spillet finnes ikke eller tilhører en annen konto.');
        $db->prepare('DELETE FROM jp_shares WHERE game_id = ?')->execute([$id]);
        $db->prepare('DELETE FROM jp_revisions WHERE game_id = ?')->execute([$id]);
        $db->prepare('DELETE FROM jp_games WHERE id = ? AND owner_id = ?')->execute([$id, $uid]);
        // Media may also belong to other Jeopardy games or Livequiz snapshots.
        $db->commit();
    } catch (Throwable $e) {
        if ($db->inTransaction()) $db->rollBack();
        throw $e;
    }
}

function jp_save(PDO $db, int $uid): string
{
    $id = jp_input('id', 32);
    if ($id !== '' && !preg_match('/^[a-f0-9]{32}$/D', $id)) throw new DomainException('Ugyldig spill.');
    $raw = jp_input('content', 1100000);
    if ($raw !== '') {
        try { $data = json_decode($raw, true, 32, JSON_THROW_ON_ERROR); }
        catch (JsonException $e) { throw new DomainException('Spillet har ugyldig innhold.'); }
        $game = jp_validate_content($db, $uid, $data);
    } else {
        // Accept the original pilot form during deployment; old saved games remain readable.
        $legacy = ['title' => jp_input('title', 180), 'category' => jp_input('category', 180), 'tiles' => []];
        for ($i = 0; $i < 3; $i++) $legacy['tiles'][] = ['value' => ($i + 1) * 100,
            'question' => jp_input('question' . $i, 8000), 'answer' => jp_input('answer' . $i, 8000)];
        $game = jp_validate_content($db, $uid, jp_normalize($legacy));
    }
    $json = json_encode($game, JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR);
    $revision = 1;
    $db->beginTransaction();
    try {
        if ($id === '') {
            $id = bin2hex(random_bytes(16));
            $db->prepare('INSERT INTO jp_games (id, owner_id, title, content, revision) VALUES (?, ?, ?, ?, 1)')
                ->execute([$id, $uid, $game['title'], $json]);
        } else {
            $stmt = $db->prepare('SELECT revision FROM jp_games WHERE id = ? AND owner_id = ? FOR UPDATE');
            $stmt->execute([$id, $uid]);
            $current = $stmt->fetchColumn();
            if ($current === false) throw new DomainException('Spillet finnes ikke eller tilhører en annen konto.');
            if ((int) $current !== (int) jp_input('revision', 12)) {
                throw new DomainException('Spillet er endret i en annen fane. Kopier endringene dine før du åpner den nyeste versjonen.');
            }
            $revision = (int) $current + 1;
            $db->prepare('UPDATE jp_games SET title = ?, content = ?, revision = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND owner_id = ?')
                ->execute([$game['title'], $json, $revision, $id, $uid]);
        }
        $db->prepare('INSERT INTO jp_revisions (game_id, revision, content) VALUES (?, ?, ?)')->execute([$id, $revision, $json]);
        $db->commit();
        return $id;
    } catch (Throwable $e) {
        if ($db->inTransaction()) $db->rollBack();
        throw $e;
    }
}


// Upgrade original one-category games in memory, without modifying stored revisions.
function jp_normalize(array $game): array
{
    if (!isset($game['categories'])) {
        $game['categories'] = [['name' => $game['category'], 'tiles' => $game['tiles']]];
        unset($game['category'], $game['tiles']);
    }
    return $game;
}

function jp_text(mixed $value, int $limit): string
{
    if (!is_string($value) || strlen($value) > $limit || !preg_match('//u', $value)) {
        throw new DomainException('Et tekstfelt er for langt eller ugyldig.');
    }
    return trim($value);
}

function jp_validate_content(PDO $db, int $uid, mixed $data): array
{
    if (!is_array($data)) throw new DomainException('Ugyldig spill.');
    $title = jp_text($data['title'] ?? '', 180);
    $categories = $data['categories'] ?? null;
    if ($title === '' || !is_array($categories) || !array_is_list($categories) || count($categories) > 8) {
        throw new DomainException('Fyll inn en tittel. Spillet kan ha opptil åtte kategorier.');
    }
    $out = ['title' => $title, 'categories' => []];
    $values = null;
    foreach ($categories as $category) {
        if (!is_array($category)) throw new DomainException('Ugyldig kategori.');
        $name = jp_text($category['name'] ?? '', 180);
        $tiles = $category['tiles'] ?? null;
        if ($name === '' || !is_array($tiles) || !array_is_list($tiles) || count($tiles) < 1 || count($tiles) > 8) {
            throw new DomainException('Hver kategori må ha et navn og én til åtte ruter.');
        }
        $clean = ['name' => $name, 'tiles' => []];
        $rowValues = [];
        foreach ($tiles as $tile) {
            if (!is_array($tile) || !is_int($tile['value'] ?? null) || $tile['value'] < 1 || $tile['value'] > 10000) {
                throw new DomainException('Poeng må være hele tall fra 1 til 10000.');
            }
            $rowValues[] = $tile['value'];
            $t = ['value' => $tile['value']];
            foreach (['question', 'answer'] as $side) {
                $t[$side] = jp_text($tile[$side] ?? '', 8000);
                $image = $tile[$side . 'Image'] ?? null;
                $t[$side . 'Image'] = null;
                if ($image !== null) {
                    if (!is_array($image) || !is_string($image['id'] ?? null) || !preg_match('/^[a-f0-9]{32}$/D', $image['id'])) {
                        throw new DomainException('Ugyldig bildereferanse.');
                    }
                    jp_media($db, $image['id'], $uid, false);
                    $alt = jp_text($image['alt'] ?? '', 500);
                    if ($alt === '') throw new DomainException('Legg til en kort bildebeskrivelse.');
                    $t[$side . 'Image'] = ['id' => $image['id'], 'alt' => $alt];
                }
                if ($t[$side] === '' && $image === null) throw new DomainException('Hvert spørsmål og svar trenger tekst eller et bilde.');
            }
            $clean['tiles'][] = $t;
        }
        if (count(array_unique($rowValues)) !== count($rowValues) || ($values !== null && $values !== $rowValues)) {
            throw new DomainException('Kategoriene må ha like poengrader, uten gjentatte poengverdier.');
        }
        $values = $rowValues;
        $out['categories'][] = $clean;
    }
    return $out;
}

function jp_media(PDO $db, string $id, int $uid, bool $includeBytes = true): array
{
    $fields = $includeBytes ? '*' : 'id, mime, size';
    $stmt = $db->prepare("SELECT $fields FROM jp_media WHERE id = ? AND owner_id = ?");
    $stmt->execute([$id, $uid]);
    $row = $stmt->fetch();
    if (!$row) throw new DomainException('Bildet finnes ikke eller tilhører en annen konto.');
    return $row;
}

function jp_image_info(string $bytes): array
{
    if (strlen($bytes) > 2 * 1024 * 1024 || $bytes === '') throw new DomainException('Bildet må være mindre enn 2 MB.');
    $mime = (new finfo(FILEINFO_MIME_TYPE))->buffer($bytes);
    $info = @getimagesizefromstring($bytes);
    if (!in_array($mime, ['image/png', 'image/jpeg', 'image/webp'], true) || !$info || $info['mime'] !== $mime) {
        throw new DomainException('Velg et PNG-, JPEG- eller WebP-bilde.');
    }
    if ($info[0] < 1 || $info[1] < 1 || $info[0] > 8000 || $info[1] > 8000 || $info[0] * $info[1] > 16000000) {
        throw new DomainException('Bildet er for stort. Bruk maks 16 megapiksler og 8000 piksler per side.');
    }
    return ['mime' => $mime, 'width' => $info[0], 'height' => $info[1]];
}

// Lossless only: preserve diagram resolution, animation and colour metadata.
function jp_optimize_image(string $bytes): string
{
    $info = jp_image_info($bytes);
    if ($info['mime'] !== 'image/png') return $bytes;
    $chunks = []; $compressed = ''; $webpSafe = true;
    for ($offset = 8; $offset + 12 <= strlen($bytes);) {
        $length = unpack('N', substr($bytes, $offset, 4))[1];
        if ($length > strlen($bytes) - $offset - 12) return $bytes;
        $type = substr($bytes, $offset + 4, 4);
        $data = substr($bytes, $offset + 8, $length);
        $chunks[] = [$type, substr($bytes, $offset, $length + 12)];
        if ($type === 'IDAT') $compressed .= $data;
        if ($type === 'acTL') return $bytes; // Never flatten animated PNGs.
        if ($type === 'IHDR' && ($length !== 13 || ord($data[8]) !== 8 || !in_array(ord($data[9]), [0,2,3], true))) $webpSafe = false;
        if (!in_array($type, ['IHDR','PLTE','IDAT','IEND'], true)) $webpSafe = false;
        $offset += $length + 12;
        if ($type === 'IEND') break;
    }
    if ($offset !== strlen($bytes) || !$chunks || end($chunks)[0] !== 'IEND') return $bytes;
    $best = $bytes;
    // Preserve every non-IDAT chunk, including full precision alpha and profiles.
    $raw = @gzuncompress($compressed, 32 * 1024 * 1024);
    if ($raw !== false) {
        $packed = gzcompress($raw, 9); unset($raw);
        if ($packed !== false && strlen($packed) < strlen($compressed)) {
            $candidate = substr($bytes, 0, 8); $written = false;
            foreach ($chunks as [$type,$chunk]) {
                if ($type !== 'IDAT') { $candidate .= $chunk; continue; }
                if (!$written) { $candidate .= pack('N',strlen($packed)).'IDAT'.$packed.pack('N',crc32('IDAT'.$packed)); $written = true; }
            }
            if (strlen($candidate) < strlen($best)) $best = $candidate;
        }
    }
    // GD reduces alpha precision; use lossless WebP only for opaque, unprofiled 8-bit PNGs.
    if ($webpSafe && $info['width'] * $info['height'] <= 4000000 && function_exists('imagewebp') && defined('IMG_WEBP_LOSSLESS')) {
        $image = @imagecreatefromstring($bytes);
        if ($image !== false) {
            if (!imageistruecolor($image)) imagepalettetotruecolor($image);
            ob_start();
            try { $ok = imagewebp($image, null, IMG_WEBP_LOSSLESS); $candidate = ob_get_contents(); }
            finally { ob_end_clean(); }
            unset($image);
            if ($ok && is_string($candidate) && $candidate !== '' && strlen($candidate) < strlen($best)) $best = $candidate;
        }
    }
    $check = jp_image_info($best);
    return $check['width'] === $info['width'] && $check['height'] === $info['height'] ? $best : $bytes;
}

// Called while holding the account lock, before quota checks.
function jp_duplicate_image(PDO $db, int $uid, string $bytes): ?string
{
    $stmt = $db->prepare('SELECT id, bytes FROM jp_media WHERE owner_id = ? AND size = ?');
    $stmt->execute([$uid, strlen($bytes)]);
    while ($row = $stmt->fetch()) if ($row['bytes'] === $bytes) return $row['id'];
    return null;
}

function jp_upload(PDO $db, int $uid, array $file): array
{
    if (($file['error'] ?? UPLOAD_ERR_NO_FILE) !== UPLOAD_ERR_OK || !is_string($file['tmp_name'] ?? null) || !is_uploaded_file($file['tmp_name'])) {
        throw new DomainException('Opplastingen mislyktes. Velg et bilde under 2 MB og prøv igjen.');
    }
    if (filesize($file['tmp_name']) > 2 * 1024 * 1024) throw new DomainException('Bildet må være mindre enn 2 MB.');
    $bytes = jp_optimize_image(file_get_contents($file['tmp_name']));
    $info = jp_image_info($bytes);
    $id = bin2hex(random_bytes(16));
    $db->beginTransaction();
    try {
        // Serialize per-account uploads so concurrent requests cannot bypass the quota.
        $lock = $db->prepare('SELECT id FROM jp_users WHERE id = ? FOR UPDATE');
        $lock->execute([$uid]);
        if (!$lock->fetchColumn()) throw new DomainException('Logg inn på nytt.');
        $existing = jp_duplicate_image($db, $uid, $bytes);
        if ($existing !== null) { $db->commit(); return ['id'=>$existing, 'alt'=>'']; }
        $sum = $db->prepare('SELECT COALESCE(SUM(size), 0) FROM jp_media WHERE owner_id = ?');
        $sum->execute([$uid]);
        if ((int) $sum->fetchColumn() + strlen($bytes) > 50 * 1024 * 1024) throw new DomainException('Bildelageret ditt er fullt (50 MB).');
        $stmt = $db->prepare('INSERT INTO jp_media (id, owner_id, mime, size, width, height, bytes) VALUES (?, ?, ?, ?, ?, ?, ?)');
        $stmt->execute([$id, $uid, $info['mime'], strlen($bytes), $info['width'], $info['height'], $bytes]);
        $db->commit();
    } catch (Throwable $e) {
        if ($db->inTransaction()) $db->rollBack();
        throw $e;
    }
    return ['id' => $id, 'alt' => ''];
}

function jp_side_html(array $tile, string $side, string $shareToken = ''): string
{
    $html = '<div class="jp-text">' . jp_h($tile[$side]) . '</div>';
    $image = $tile[$side . 'Image'] ?? null;
    if ($image) $html .= '<img class="jp-content-image" src="/?media=' . jp_h($image['id']) . ($shareToken !== '' ? '&amp;share=' . jp_h($shareToken) : '') . '" alt="' . jp_h($image['alt']) . '">';
    return $html;
}

function jp_share(PDO $db, int $uid, string $id, int $revision): array
{
    $db->beginTransaction();
    try {
        $stmt = $db->prepare('SELECT * FROM jp_games WHERE id = ? AND owner_id = ? FOR UPDATE');
        $stmt->execute([$id, $uid]);
        $game = $stmt->fetch();
        if (!$game) throw new DomainException('Spillet finnes ikke eller tilhører en annen konto.');
        if ((int) $game['revision'] !== $revision) throw new DomainException('Spillet er endret i en annen fane. Åpne den nyeste versjonen før du deler.');
        $content = jp_normalize(json_decode($game['content'], true, 32, JSON_THROW_ON_ERROR));
        if (!$content['categories']) throw new DomainException('Legg til en kategori og lagre før du deler spillet.');
        $stmt = $db->prepare('SELECT token FROM jp_shares WHERE game_id = ?');
        $stmt->execute([$id]);
        $token = $stmt->fetchColumn();
        if ($token === false) {
            $token = bin2hex(random_bytes(32));
            $db->prepare('INSERT INTO jp_shares (game_id, token, content, revision) VALUES (?, ?, ?, ?)')->execute([$id, $token, $game['content'], $revision]);
        } else {
            $db->prepare('UPDATE jp_shares SET content = ?, revision = ? WHERE game_id = ?')->execute([$game['content'], $revision, $id]);
        }
        $db->commit();
        return ['token' => $token, 'revision' => $revision];
    } catch (Throwable $e) {
        if ($db->inTransaction()) $db->rollBack();
        throw $e;
    }
}

function jp_unshare(PDO $db, int $uid, string $id): void
{
    $db->beginTransaction();
    try {
        $stmt = $db->prepare('SELECT id FROM jp_games WHERE id = ? AND owner_id = ? FOR UPDATE');
        $stmt->execute([$id, $uid]);
        if (!$stmt->fetchColumn()) throw new DomainException('Spillet finnes ikke eller tilhører en annen konto.');
        $db->prepare('DELETE FROM jp_shares WHERE game_id = ?')->execute([$id]);
        $db->commit();
    } catch (Throwable $e) {
        if ($db->inTransaction()) $db->rollBack();
        throw $e;
    }
}

function jp_shared_game(PDO $db, mixed $token): array
{
    if (!is_string($token) || !preg_match('/^[a-f0-9]{64}$/D', $token)) throw new DomainException('Delingslenken er ugyldig eller delingen er stoppet.');
    $stmt = $db->prepare('SELECT s.game_id AS id, s.content, s.revision, g.owner_id FROM jp_shares s JOIN jp_games g ON g.id = s.game_id WHERE s.token = ?');
    $stmt->execute([$token]);
    $game = $stmt->fetch();
    if (!$game) throw new DomainException('Delingslenken er ugyldig eller delingen er stoppet.');
    return $game;
}

function jp_shared_media(PDO $db, mixed $token, string $imageId): array
{
    $game = jp_shared_game($db, $token);
    $content = jp_normalize(json_decode($game['content'], true, 32, JSON_THROW_ON_ERROR));
    foreach ($content['categories'] as $category) foreach ($category['tiles'] as $tile) {
        foreach (['questionImage', 'answerImage'] as $side) {
            if (($tile[$side]['id'] ?? null) === $imageId) return jp_media($db, $imageId, (int) $game['owner_id']);
        }
    }
    throw new DomainException('Bildet finnes ikke i dette delte spillet.');
}

function jp_player_config(array $content, string $shareToken = ''): array
{
    $cfg = ['teams' => 2, 'values' => array_column($content['categories'][0]['tiles'], 'value'), 'categories' => []];
    foreach ($content['categories'] as $category) {
        $cfg['categories'][] = ['name' => $category['name'], 'tiles' => array_map(static fn(array $tile): array => [
            'value' => $tile['value'], 'question' => jp_side_html($tile, 'question', $shareToken), 'answer' => jp_side_html($tile, 'answer', $shareToken)], $category['tiles'])];
    }
    return $cfg;
}
