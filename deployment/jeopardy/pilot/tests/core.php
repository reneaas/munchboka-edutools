<?php
declare(strict_types=1);
require __DIR__ . '/../private/app.php';
function jp_sample(): array
{
    return ['title' => 'Mitt første Jeopardy', 'category' => 'Matematikk', 'tiles' => [
        ['value' => 100, 'question' => 'Hva er 7 + 8?', 'answer' => '15'],
        ['value' => 200, 'question' => 'Løs likningen 2x + 3 = 11.', 'answer' => 'x = 4'],
        ['value' => 300, 'question' => 'Et rektangel har sider på 4 cm og 6 cm. Hva er arealet?', 'answer' => '24 cm²'],
    ]];
}

const TEST_EMAIL = 'teacher@osloskolen.no';
session_save_path('/tmp');
session_start();
if (session_status() !== PHP_SESSION_ACTIVE) throw new RuntimeException('Test session did not start');
// Exercise the actual application functions with a real in-memory database.
// MySQL row locks and deployment DDL still require hosting integration checks.
class TestDatabase extends PDO {
    public function prepare(string $query, array $options = []): PDOStatement|false {
        return parent::prepare(str_replace([' FOR UPDATE', 'INSERT IGNORE'], ['', 'INSERT OR IGNORE'], $query), $options);
    }
}
$db = new TestDatabase('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
$db->exec('CREATE TABLE jp_users (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE);
CREATE TABLE jp_games (id TEXT PRIMARY KEY, owner_id INTEGER, title TEXT, content TEXT, revision INTEGER, updated_at TEXT);
CREATE TABLE jp_revisions (game_id TEXT, revision INTEGER, content TEXT, PRIMARY KEY(game_id, revision));
CREATE TABLE jp_media (id TEXT PRIMARY KEY, owner_id INTEGER, mime TEXT, size INTEGER, width INTEGER, height INTEGER, bytes BLOB);
CREATE TABLE jp_shares (game_id TEXT PRIMARY KEY, token TEXT UNIQUE, content TEXT, revision INTEGER);
CREATE TABLE jp_mail_budget (id INTEGER PRIMARY KEY, window_at INTEGER DEFAULT 0, send_count INTEGER DEFAULT 0);
CREATE TABLE jp_login (email TEXT PRIMARY KEY, challenge TEXT, code_hash TEXT, expires_at INTEGER, attempts INTEGER DEFAULT 0, sent_at INTEGER DEFAULT 0, window_at INTEGER DEFAULT 0, send_count INTEGER DEFAULT 0)');
$checks = 0;
function check(bool $condition, string $label): void {
    global $checks;
    if (!$condition) throw new RuntimeException('FAILED: ' . $label);
    $checks++;
}
function rejects(callable $fn, string $label): void {
    try { $fn(); } catch (DomainException $e) { check(true, $label); return; }
    throw new RuntimeException('FAILED to reject: ' . $label);
}
$_POST = ['id' => '', 'revision' => '0', 'title' => 'Lagringstest', 'category' => 'Matematikk'];
for ($i = 0; $i < 3; $i++) { $_POST['question' . $i] = 'Spørsmål ' . $i; $_POST['answer' . $i] = 'Svar ' . $i; }
$id = jp_save($db, 10);
$game = jp_game($db, $id, 10);
check((int) $game['revision'] === 1, 'new game revision');
check(json_decode($game['content'], true)['categories'][0]['tiles'][2]['answer'] === 'Svar 2', 'question content round trip');
rejects(fn() => jp_game($db, $id, 11), 'other user cannot read');
$_POST['id'] = $id; $_POST['revision'] = '1'; $_POST['title'] = 'Oppdatert';
jp_save($db, 10);
check((int) jp_game($db, $id, 10)['revision'] === 2, 'revision increment');
check((int) $db->query('SELECT COUNT(*) FROM jp_revisions')->fetchColumn() === 2, 'revision history retained');
rejects(fn() => jp_save($db, 10), 'stale save rejected');
check(jp_game($db, $id, 10)['title'] === 'Oppdatert', 'stale save did not overwrite');
$_POST['revision'] = '2';
rejects(fn() => jp_save($db, 11), 'other user cannot write');
check((int) $db->query('SELECT COUNT(*) FROM jp_revisions')->fetchColumn() === 2, 'failed saves do not create revisions');
$_POST['question0'] = '';
rejects(fn() => jp_save($db, 10), 'incomplete content rejected');
check(jp_h('<script>alert(1)</script>') === '&lt;script&gt;alert(1)&lt;/script&gt;', 'player content escaped');
$_POST['title'] = ['bad']; rejects(fn() => jp_input('title', 180), 'array field rejected');
rejects(fn() => jp_send_code($db, 'user@example.com'), 'outside domain rejected before email');
check(jp_allowed_email('teacher@osloskolen.no'), 'teacher domain accepted');
check(jp_allowed_email('student@osloskolen.no'), 'student domain accepted');
check(jp_allowed_email('TEACHER@OSLOSKOLEN.NO'), 'domain case insensitive');
foreach (['user@osloskolen.no.evil.test', 'user@sub.osloskolen.no', 'osloskolen.no', 'user@example.com', "user@osloskolen.no\r\nBcc: a@example.com"] as $email) {
    check(!jp_allowed_email($email), 'invalid or lookalike email rejected');
}
$db->beginTransaction(); jp_mail_budget($db, 10000); $db->commit();
check((int) $db->query('SELECT send_count FROM jp_mail_budget')->fetchColumn() === 1, 'global mail count incremented');
$db->exec('UPDATE jp_mail_budget SET send_count = 500');
$db->beginTransaction(); rejects(fn() => jp_mail_budget($db, 10001), 'global mail limit enforced'); $db->rollBack();
$db->beginTransaction(); jp_mail_budget($db, 13600); $db->commit();
check((int) $db->query('SELECT send_count FROM jp_mail_budget')->fetchColumn() === 1, 'global mail window resets');

function seedCode(PDO $db, int $expires, int $attempts = 0, string $email = TEST_EMAIL): void {
    $db->exec('DELETE FROM jp_login');
    $challenge = str_repeat('a', 64);
    $db->prepare('INSERT INTO jp_login (email, challenge, code_hash, expires_at, attempts) VALUES (?, ?, ?, ?, ?)')
        ->execute([$email, $challenge, password_hash('12345678', PASSWORD_DEFAULT), $expires, $attempts]);
    $_SESSION = ['email_pending' => $email, 'challenge' => $challenge];
}
seedCode($db, time() + 600);
rejects(fn() => jp_verify($db, '00000000'), 'wrong code rejected');
check((int) $db->query('SELECT attempts FROM jp_login')->fetchColumn() === 1, 'failed attempts persist');
$_SESSION['challenge'] = str_repeat('b', 64);
rejects(fn() => jp_verify($db, '12345678'), 'code bound to requesting session');
seedCode($db, time() - 1);
rejects(fn() => jp_verify($db, '12345678'), 'expired code rejected');
seedCode($db, time() + 600, 5);
rejects(fn() => jp_verify($db, '12345678'), 'attempt limit enforced');
seedCode($db, time() + 600);
jp_verify($db, '12345678');
check(isset($_SESSION['uid']) && $_SESSION['email'] === TEST_EMAIL, 'successful code creates authenticated session');
check($db->query('SELECT code_hash FROM jp_login')->fetchColumn() === null, 'successful code consumed');
$_SESSION = ['email_pending' => TEST_EMAIL, 'challenge' => str_repeat('a', 64)];
rejects(fn() => jp_verify($db, '12345678'), 'consumed code cannot be reused');
$teacherId = (int) $db->query("SELECT id FROM jp_users WHERE email = 'teacher@osloskolen.no'")->fetchColumn();

seedCode($db, time() + 600, 0, 'student@osloskolen.no');
jp_verify($db, '12345678');
$studentId = (int) $_SESSION['uid'];
check($studentId !== $teacherId && $_SESSION['email'] === 'student@osloskolen.no', 'new student gets distinct account');
$_POST = ['id' => '', 'revision' => '0', 'content' => json_encode(jp_normalize(jp_sample()))];
$studentGame = jp_save($db, $studentId);
check((int) jp_game($db, $studentGame, $studentId)['owner_id'] === $studentId, 'new student can save own game');
rejects(fn() => jp_game($db, $studentGame, $teacherId), 'teacher cannot read student game');
$_POST['id'] = $studentGame; $_POST['revision'] = '1';
rejects(fn() => jp_save($db, $teacherId), 'teacher cannot overwrite student game');
seedCode($db, time() + 600, 0, 'student@osloskolen.no');
jp_verify($db, '12345678');
check((int) $_SESSION['uid'] === $studentId, 'repeat login retains same account');
check(jp_game($db, $studentGame, $studentId)['id'] === $studentGame, 'game persists across student logins');
$sample = jp_normalize(jp_sample());
check(count($sample['categories']) === 1, 'legacy content normalized');
$sample['categories'][] = $sample['categories'][0];
$sample['categories'][1]['name'] = 'Algebra';
$sample['categories'][1]['tiles'][0]['question'] = 'Løs $x^2 = 9$';
$valid = jp_validate_content($db, 10, $sample);
check($valid['categories'][1]['tiles'][0]['question'] === 'Løs $x^2 = 9$', 'LaTeX preserved exactly');
$_POST = ['id' => '', 'revision' => '0', 'content' => json_encode($valid)];
$richId = jp_save($db, 10);
check(count(json_decode(jp_game($db, $richId, 10)['content'], true)['categories']) === 2, 'multiple categories round trip');
$sample['categories'][1]['tiles'][0]['value'] = 999;
rejects(fn() => jp_validate_content($db, 10, $sample), 'inconsistent rows rejected');
$sample = $valid;
$sample['categories'][0]['tiles'][1]['value'] = 100;
rejects(fn() => jp_validate_content($db, 10, $sample), 'duplicate points rejected');
$sample = $valid;
$sample['categories'][0]['tiles'][0]['value'] = 1.5;
rejects(fn() => jp_validate_content($db, 10, $sample), 'fractional points rejected');
$sample = $valid;
$sample['categories'] = array_fill(0, 9, $sample['categories'][0]);
rejects(fn() => jp_validate_content($db, 10, $sample), 'category limit enforced');
$imageId = str_repeat('c', 32);
$db->prepare('INSERT INTO jp_media (id, owner_id, mime, size, bytes) VALUES (?, ?, ?, ?, ?)')->execute([$imageId, 10, 'image/png', 3, 'png']);
rejects(fn() => jp_media($db, $imageId, 11), 'other account cannot read image');
$sample = $valid;
$sample['categories'][0]['tiles'][0]['questionImage'] = ['id' => $imageId, 'alt' => 'En trekant'];
$sample['categories'][0]['tiles'][0]['question'] = '';
check(jp_validate_content($db, 10, $sample)['categories'][0]['tiles'][0]['question'] === '', 'image-only question accepted');
rejects(fn() => jp_validate_content($db, 11, $sample), 'other account cannot attach image');
$sample['categories'][0]['tiles'][0]['questionImage']['alt'] = '';
rejects(fn() => jp_validate_content($db, 10, $sample), 'missing alt text rejected');
$sample['categories'][0]['tiles'][0]['questionImage']['id'] = '../../database.php';
rejects(fn() => jp_validate_content($db, 10, $sample), 'invalid media id rejected');
$markup = jp_side_html(['question' => '<script>alert(1)</script> $x^2$', 'questionImage' => ['id' => $imageId, 'alt' => '" onerror="alert(1)']], 'question');
check(!str_contains($markup, '<script>') && str_contains($markup, '&quot;'), 'text and image attributes escaped');
rejects(fn() => jp_image_info('<svg xmlns="http://www.w3.org/2000/svg"></svg>'), 'SVG rejected');
rejects(fn() => jp_image_info('<?php echo 1; ?>'), 'PHP file rejected');
rejects(fn() => jp_image_info(str_repeat('x', 2 * 1024 * 1024 + 1)), 'oversize image rejected');
rejects(fn() => jp_upload($db, 10, ['error' => UPLOAD_ERR_OK, 'tmp_name' => __FILE__]), 'non-upload file rejected');
$png = base64_decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jO1sAAAAASUVORK5CYII=');
check(jp_image_info($png)['mime'] === 'image/png', 'valid PNG accepted');
check(jp_new_game() === ['title' => '', 'categories' => []], 'new game starts completely blank');
$_POST = ['id' => '', 'revision' => '0', 'content' => json_encode(['title' => 'Tomt utkast', 'categories' => []])];
$emptyId = jp_save($db, 10);
check(json_decode(jp_game($db, $emptyId, 10)['content'], true)['categories'] === [], 'empty draft can be saved and reopened');
$_POST = ['id' => $richId, 'revision' => '1', 'content' => json_encode(['title' => 'Alle kategorier fjernet', 'categories' => []])];
jp_save($db, 10);
check(json_decode(jp_game($db, $richId, 10)['content'], true)['categories'] === [], 'last category removal persists');

$_POST = ['id' => '', 'revision' => '0', 'content' => json_encode(jp_normalize(jp_sample()))];
$shareGameId = jp_save($db, 10);
rejects(fn() => jp_share($db, 11, $shareGameId, 1), 'other owner cannot share');
rejects(fn() => jp_share($db, 10, $emptyId, 1), 'empty draft cannot be shared');
rejects(fn() => jp_share($db, 10, $shareGameId, 2), 'stale share request rejected');
$share = jp_share($db, 10, $shareGameId, 1);
check(strlen($share['token']) === 64, 'share uses random 256-bit token');
check(jp_shared_game($db, $share['token'])['id'] === $shareGameId, 'public read accepts active token without login');
rejects(fn() => jp_shared_game($db, $shareGameId), 'game id does not grant public read');
rejects(fn() => jp_shared_game($db, ['bad']), 'array share token rejected');
rejects(fn() => jp_unshare($db, 11, $shareGameId), 'other owner cannot revoke share');
rejects(fn() => jp_shared_media($db, $share['token'], $imageId), 'share cannot read unrelated owner image');
$sharedContent = jp_normalize(jp_sample());
$sharedContent['title'] = 'Updated private draft';
$sharedContent['categories'][0]['tiles'][0]['questionImage'] = ['id' => $imageId, 'alt' => 'Trekant'];
$_POST = ['id' => $shareGameId, 'revision' => '1', 'content' => json_encode($sharedContent)];
jp_save($db, 10);
check((int) jp_shared_game($db, $share['token'])['revision'] === 1, 'later edits remain private until explicitly shared');
$updated = jp_share($db, 10, $shareGameId, 2);
check($updated['token'] === $share['token'] && (int) jp_shared_game($db, $share['token'])['revision'] === 2, 'update keeps link and publishes chosen revision');
check(jp_shared_media($db, $share['token'], $imageId)['id'] === $imageId, 'shared image accessible only when in shared snapshot');
$config = jp_player_config($sharedContent, $share['token']);
check(str_contains($config['categories'][0]['tiles'][0]['question'], '&amp;share=' . $share['token']), 'public player images use scoped token');
jp_unshare($db, 10, $shareGameId);
rejects(fn() => jp_shared_game($db, $share['token']), 'revoked link rejects public read');
rejects(fn() => jp_shared_media($db, $share['token'], $imageId), 'revoked link rejects image read');
$reshare = jp_share($db, 10, $shareGameId, 2);
check($reshare['token'] !== $share['token'], 'resharing creates new token');
rejects(fn() => jp_shared_game($db, $share['token']), 'old token remains invalid after resharing');
// Delete only an owned game; revoke its shares and remove dependent revisions.
rejects(fn() => jp_delete($db, 11, $shareGameId), 'other owner cannot delete');
check(jp_shared_game($db, $reshare['token'])['id'] === $shareGameId, 'denied delete preserves sharing');
rejects(fn() => jp_delete($db, 10, 'bad-id'), 'invalid delete id rejected');
$mediaBefore = (int) $db->query('SELECT COUNT(*) FROM jp_media')->fetchColumn();
$otherBefore = jp_game($db, $id, 10);
// A database failure must roll back share/revision removal too.
$db->exec("CREATE TRIGGER prevent_delete BEFORE DELETE ON jp_games BEGIN SELECT RAISE(ABORT, 'test failure'); END");
try { jp_delete($db, 10, $shareGameId); throw new RuntimeException('Expected delete failure'); }
catch (PDOException $e) { check(true, 'delete failure propagated'); }
check(jp_shared_game($db, $reshare['token'])['id'] === $shareGameId, 'failed delete rolls back share removal');
$stmt = $db->prepare('SELECT COUNT(*) FROM jp_revisions WHERE game_id = ?');
$stmt->execute([$shareGameId]); check((int) $stmt->fetchColumn() === 2, 'failed delete rolls back revisions');
$db->exec('DROP TRIGGER prevent_delete');
jp_delete($db, 10, $shareGameId);
rejects(fn() => jp_game($db, $shareGameId, 10), 'deleted game unavailable');
rejects(fn() => jp_shared_game($db, $reshare['token']), 'deleted game sharing revoked');
$stmt->execute([$shareGameId]); check((int) $stmt->fetchColumn() === 0, 'deleted game revisions removed');
check((int) $db->query('SELECT COUNT(*) FROM jp_media')->fetchColumn() === $mediaBefore, 'shared media retained');
check(jp_game($db, $id, 10) === $otherBefore, 'other games preserved');
rejects(fn() => jp_delete($db, 10, $shareGameId), 'repeated delete rejected safely');
echo $checks . " core checks passed.\n";
