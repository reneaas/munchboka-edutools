<?php
declare(strict_types=1);
ini_set('display_errors', '0');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');
header('Referrer-Policy: strict-origin-when-cross-origin');
header('X-Frame-Options: DENY');
header('X-Robots-Tag: noindex, nofollow');
header("Content-Security-Policy: default-src 'self'; script-src 'self' https://www.youtube.com/iframe_api https://www.youtube.com/s/player/; style-src 'self' 'unsafe-inline'; img-src 'self' blob: data:; frame-src https://www.youtube-nocookie.com; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'");
$local = PHP_SAPI === 'cli-server' && getenv('LIVEQUIZ_LOCAL') === '1';
if (!$local && ($_SERVER['HTTPS'] ?? '') !== 'on') { header('Location: https://quiz.munchboka.no/', true, 302); exit; }
ini_set('session.use_strict_mode', '1');
ini_set('session.use_only_cookies', '1');
session_name($local ? 'livequiz-local' : '__Host-livequiz');
session_set_cookie_params(['lifetime'=>0, 'path'=>'/', 'secure'=>!$local, 'httponly'=>true, 'samesite'=>'Lax']);
session_start();
if (isset($_SESSION['uid']) && time() - ($_SESSION['authenticated_at'] ?? 0) > 28800) { $_SESSION = []; session_regenerate_id(true); }
$_SESSION['csrf'] ??= bin2hex(random_bytes(32));
$uid = (int)($_SESSION['uid'] ?? 0); $csrf = $_SESSION['csrf'];
function lq_response(array $data, int $status = 200): never {
    http_response_code($status); header('Content-Type: application/json; charset=utf-8'); echo json_encode($data, JSON_THROW_ON_ERROR); exit;
}
$action = $_GET['api'] ?? null;
if ($action !== null) {
    try {
        if (!is_string($action)) throw new DomainException('Ugyldig forespørsel.');
        $post = $_SERVER['REQUEST_METHOD'] === 'POST';
        $mutations = ['save','create','join','control','answer','upload','send','verify','logout','delete','share','shared-start'];
        if (in_array($action, $mutations, true) !== $post) throw new DomainException('Ugyldig metode.');
        if ($post && !hash_equals($csrf, $_SERVER['HTTP_X_CSRF_TOKEN'] ?? '')) lq_response(['error'=>'Siden er utløpt. Åpne en ny fane og logg inn igjen. Behold denne fanen med arbeidet ditt.'], 403);
        if (in_array($action, ['join','shared-start'], true)) {
            if (time() < ($_SESSION['lq_join_after'] ?? 0)) lq_response(['error'=>'Vent to sekunder og prøv igjen.'], 429);
            $_SESSION['lq_join_after'] = time() + 2;
        }
        // Release PHP's session lock before polling queries, uploads or room locks.
        if (!in_array($action, ['send','verify','logout'], true)) session_write_close();
        if ($action === 'bootstrap') lq_response(['uid'=>$uid, 'csrf'=>$csrf, 'pending'=>isset($_SESSION['email_pending'])]);
        $teacherActions = ['library','quiz','save','create','upload','delete','share'];
        if (in_array($action, $teacherActions, true) && !$uid) lq_response(['error'=>'Logg inn på quiz.munchboka.no i en ny fane først.'], 401);
        require getenv('LIVEQUIZ_PRIVATE') ?: '/home/zebfxvix/jeopardy-private/livequiz/app.php';
        $db = jp_db();
        $input = [];
        if ($post && $action !== 'upload') {
            $raw = file_get_contents('php://input', false, null, 0, 1100001);
            if (strlen($raw) > 1100000) throw new DomainException('Forespørselen er for stor.');
            $input = json_decode($raw, true, 32, JSON_THROW_ON_ERROR);
            if (!is_array($input)) throw new DomainException('Ugyldig forespørsel.');
        }
        $hostToken = $_SERVER['HTTP_X_HOST_TOKEN'] ?? '';
        if (strlen($hostToken) > 64) throw new DomainException('Ugyldig vertsnøkkel.');
        $token = $_SERVER['HTTP_X_PLAYER_TOKEN'] ?? '';
        if (strlen($token) > 64) throw new DomainException('Ugyldig deltaker.');
        $room = $_GET['room'] ?? ''; $host = ($_GET['host'] ?? '') === '1';
        if (!is_string($room)) throw new DomainException('Ugyldig spill.');
        switch ($action) {
            case 'send': lq_send_code($db, jp_text($input['email'] ?? '', 254)); lq_response(['ok'=>true]);
            case 'verify': lq_verify($db, jp_text($input['code'] ?? '', 8)); lq_response(['ok'=>true]);
            case 'logout':
                $_SESSION = []; session_destroy();
                setcookie(session_name(), '', ['expires'=>time()-3600, 'path'=>'/', 'secure'=>!$local, 'httponly'=>true, 'samesite'=>'Lax']);
                lq_response(['ok'=>true]);
            case 'library': lq_response(['quizzes'=>lq_query($db, 'SELECT id, title, revision FROM lq_quizzes WHERE owner_id = ? ORDER BY updated_at DESC', [$uid])->fetchAll(), 'rooms'=>lq_query($db, 'SELECT id, pin, phase FROM lq_rooms WHERE owner_id = ? AND expires_at > ? ORDER BY expires_at DESC LIMIT 20', [$uid,time()])->fetchAll()]);
            case 'quiz': $q = lq_quiz($db, $uid, jp_text($_GET['id'] ?? '', 32)); lq_response(['id'=>$q['id'], 'revision'=>(int)$q['revision'], 'content'=>json_decode($q['content'], true, 32, JSON_THROW_ON_ERROR)]);
            case 'save': lq_response(lq_save($db, $uid, $input));
            case 'delete': lq_response(lq_delete($db, $uid, $input));
            case 'share':
                if (!is_bool($input['enabled'] ?? null)) throw new DomainException('Ugyldig delingsvalg.');
                lq_response(lq_share($db, $uid, jp_text($input['id'] ?? '', 32), $input['enabled']));
            case 'shared':
                $shared = lq_shared_quiz($db, jp_text($_GET['id'] ?? '', 32), jp_text($_SERVER['HTTP_X_QUIZ_SHARE'] ?? '', 64));
                $content = json_decode($shared['content'], true, 32, JSON_THROW_ON_ERROR);
                lq_response(['title'=>$shared['title'], 'total'=>count($content['questions'])]);
            case 'shared-start': lq_response(lq_shared_start($db, jp_text($input['id'] ?? '', 32), jp_text($input['key'] ?? '', 64), jp_text($input['host_token'] ?? '', 64)));
            case 'create': lq_response(lq_create_room($db, $uid, jp_text($input['id'] ?? '', 32)));
            case 'join': lq_response(lq_join($db, jp_text($input['pin'] ?? '', 6), jp_text($input['name'] ?? '', 80), $token));
            case 'control': lq_response(lq_control($db, $uid, $input, $hostToken));
            case 'answer': lq_response(lq_answer($db, $input, $token));
            case 'state': lq_response(lq_state($db, $room, $uid, $token, $host, $hostToken));
            case 'upload': lq_response(['image'=>jp_upload($db, $uid, $_FILES['image'] ?? [])]);
            case 'media':
                $image = lq_id($_GET['image'] ?? null);
                if ($room !== '') $m = lq_room_media($db, $room, $uid, $token, $host, $image, $hostToken);
                elseif ($uid) $m = jp_media($db, $image, $uid);
                else throw new DomainException('Ingen tilgang.');
                header('Content-Type: '.$m['mime']); header('Content-Length: '.strlen($m['bytes'])); echo $m['bytes']; exit;
            default: lq_response(['error'=>'Ukjent handling.'], 404);
        }
    } catch (DomainException|JsonException $e) { lq_response(['error'=>$e instanceof JsonException ? 'Ugyldig JSON.' : $e->getMessage()], 422); }
    catch (Throwable $e) { error_log('Livequiz: '.get_class($e).' '.$e->getCode()); lq_response(['error'=>'Tjenesten er utilgjengelig. Ingen lagring er bekreftet. Prøv igjen.'], 503); }
}
session_write_close();
?>
<!doctype html>
<html lang="nb"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Livequiz · Munchboka</title>
<link rel="stylesheet" href="vendor/katex/katex.min.css"><link rel="stylesheet" href="vendor/codemirror/lib/codemirror.min.css"><link rel="stylesheet" href="app.css?v=<?= filemtime(__DIR__.'/app.css') ?>">
<script defer src="vendor/katex/katex.min.js"></script><script defer src="math.js"></script><script defer src="vendor/qrcode.js"></script><script defer src="vendor/codemirror/lib/codemirror.min.js"></script><script defer src="vendor/codemirror/mode/python/python.min.js"></script><script defer src="code.js"></script><script defer src="youtube.js?v=<?= filemtime(__DIR__.'/youtube.js') ?>"></script><script defer src="music.js?v=<?= filemtime(__DIR__.'/music.js') ?>"></script><script defer src="app.js?v=<?= filemtime(__DIR__.'/app.js') ?>"></script></head>
<body><header><a class="brand" href="./">Munchboka <strong>Livequiz</strong></a><span class="badge">Utprøving</span><nav><a href="?teacher=1">Lag en quiz</a><a id="account-link" href="?login=1">Logg inn</a></nav></header>
<main><div id="notice" role="alert" hidden></div><div id="app"><p>Laster …</p></div></main><footer>Spørsmål, samtale og læring · En klasse om gangen</footer></body></html>
