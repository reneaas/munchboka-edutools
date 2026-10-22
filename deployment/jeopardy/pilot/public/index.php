<?php
declare(strict_types=1);
ini_set('display_errors', '0');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');
header('Referrer-Policy: no-referrer');
header('X-Frame-Options: DENY');

header("Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'");
if (($_SERVER['HTTPS'] ?? '') !== 'on') {
    header('Location: https://jeopardy.munchboka.no/', true, 302);
    exit;
}
ini_set('session.use_strict_mode', '1');
ini_set('session.use_only_cookies', '1');
session_name('__Host-jeopardy');
session_set_cookie_params(['lifetime' => 0, 'path' => '/', 'secure' => true, 'httponly' => true, 'samesite' => 'Lax']);
session_start();
if (isset($_SESSION['uid']) && time() - ($_SESSION['authenticated_at'] ?? 0) > 28800) {
    $_SESSION = [];
    session_regenerate_id(true);
}
$_SESSION['csrf'] ??= bin2hex(random_bytes(32));
$api = ($_SERVER['HTTP_X_JEOPARDY_REQUEST'] ?? '') === 'editor';
function json_response(array $data, int $status = 200): never {
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($data, JSON_THROW_ON_ERROR);
    exit;
}
$about = isset($_GET['about']) && $_GET['about'] === '1';
$publicInfo = $_SERVER['REQUEST_METHOD'] === 'GET' && empty($_SESSION['uid'])
    && (empty($_GET) || ($about && count($_GET) === 1));
header('X-Robots-Tag: ' . ($publicInfo ? 'index, follow' : 'noindex, nofollow'));
$error = '';
$flash = $_SESSION['flash'] ?? '';
unset($_SESSION['flash']);
$db = null;
try {
    require '/home/zebfxvix/jeopardy-private/app.php';
    $db = jp_db();
    jp_schema($db);
    if (isset($_GET['media'])) {
        if (!is_string($_GET['media']) || !preg_match('/^[a-f0-9]{32}$/D', $_GET['media'])) {
            http_response_code(404); exit;
        }
        try {
            if (isset($_GET['share'])) $media = jp_shared_media($db, $_GET['share'], $_GET['media']);
            elseif (isset($_SESSION['uid'])) $media = jp_media($db, $_GET['media'], (int) $_SESSION['uid']);
            else { http_response_code(404); exit; }
        }
        catch (DomainException $e) { http_response_code(404); exit; }
        header('Content-Type: ' . $media['mime']);
        header('Content-Disposition: inline');
        header('Content-Length: ' . strlen($media['bytes']));
        echo $media['bytes']; exit;
    }
    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        if (!is_string($_POST['csrf'] ?? null) || !hash_equals($_SESSION['csrf'], $_POST['csrf'])) {
            throw new DomainException('Siden er utløpt. Last inn på nytt og prøv igjen.');
        }
        $action = jp_input('action', 20);
        if ($action === 'send') {
            jp_send_code($db, jp_input('email', 254));
            jp_redirect();
        } elseif ($action === 'verify') {
            jp_verify($db, jp_input('code', 40));
            jp_redirect();
        } elseif ($action === 'logout') {
            $_SESSION = [];
            session_destroy();
            setcookie('__Host-jeopardy', '', ['expires' => time() - 3600, 'path' => '/', 'secure' => true, 'httponly' => true, 'samesite' => 'Lax']);
            jp_redirect();
        } elseif (($action === 'share' || $action === 'unshare') && isset($_SESSION['uid'])) {
            $id = jp_input('id', 32);
            if ($action === 'share') json_response(['share' => jp_share($db, (int) $_SESSION['uid'], $id, (int) jp_input('revision', 12))]);
            jp_unshare($db, (int) $_SESSION['uid'], $id);
            json_response(['share' => null]);
        } elseif ($action === 'upload' && isset($_SESSION['uid'])) {
            $image = jp_upload($db, (int) $_SESSION['uid'], $_FILES['image'] ?? []);
            json_response(['image' => $image]);
        } elseif ($action === 'save' && isset($_SESSION['uid'])) {
            $savedId = jp_save($db, (int) $_SESSION['uid']);
            if ($api) {
                $saved = jp_game($db, $savedId, (int) $_SESSION['uid']);
                json_response(['id' => $savedId, 'revision' => (int) $saved['revision']]);
            }
            $_SESSION['flash'] = 'Spillet er lagret på nett. Du kan åpne det igjen fra Mine quizer.';
            jp_redirect('?edit=' . $savedId);
        } else {
            throw new DomainException('Logg inn for å lagre spill.');
        }
    }
} catch (DomainException $e) {
    $error = $e->getMessage();
} catch (Throwable $e) {
    http_response_code(503);
    $error = 'Tjenesten er midlertidig utilgjengelig. Ingen lagring er bekreftet. Prøv igjen senere.';
    // Log only exception class and SQLSTATE, never credentials, email codes or SQL data.
    error_log('Jeopardy pilot error: ' . get_class($e) . ' code=' . (string) $e->getCode());
}
if ($api) json_response(['error' => $error ?: 'Ugyldig forespørsel.'], isset($_SESSION['uid']) ? 422 : 401);
$uid = (int) ($_SESSION['uid'] ?? 0);
$shared = isset($_GET['share']);
$editing = !$about && !$shared && (isset($_GET['new']) || isset($_GET['edit']));
$playing = $shared || isset($_GET['play']);
$shareInfo = null;
$game = null;
$content = null;
$games = [];
try {
    if ($shared && $db) {
        $game = jp_shared_game($db, $_GET['share']);
        $content = jp_normalize(json_decode($game['content'], true, 32, JSON_THROW_ON_ERROR));
    } elseif ($uid && $db) {
        $stmt = $db->prepare('SELECT g.id, g.title, g.revision, g.updated_at, s.token AS share_token FROM jp_games g LEFT JOIN jp_shares s ON s.game_id = g.id WHERE g.owner_id = ? ORDER BY g.updated_at DESC');
        $stmt->execute([$uid]);
        $games = $stmt->fetchAll();
        if ($editing || $playing) {
            if (isset($_GET['new'])) {
                $game = ['id' => '', 'revision' => 0];
                $content = jp_new_game();
            } else {
                $id = $playing ? $_GET['play'] : $_GET['edit'];
                if (!is_string($id) || !preg_match('/^[a-f0-9]{32}$/D', $id)) throw new DomainException('Ugyldig spill.');
                $game = jp_game($db, $id, $uid);
                $stmt = $db->prepare('SELECT token, revision FROM jp_shares WHERE game_id = ?');
                $stmt->execute([$id]);
                $shareInfo = $stmt->fetch() ?: null;
                $content = jp_normalize(json_decode($game['content'], true, 32, JSON_THROW_ON_ERROR));
            }

        }
    }
} catch (DomainException $e) {
    if ($shared) http_response_code(404);
    $error = $e->getMessage();
    $game = null;
} catch (Throwable $e) {
    $error = 'Spillene kunne ikke lastes. Prøv igjen senere.';
}
function h(string $s): string { return htmlspecialchars($s, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8'); }
function csrf(): void { echo '<input type="hidden" name="csrf" value="' . h($_SESSION['csrf']) . '">'; }
?>
<!doctype html>
<html lang="nb"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Jeopardy · Munchboka – for lærere og elever</title>
<meta name="description" content="Lag faglige undervisningsquizer til repetisjon, begrepstrening og samarbeid i klasserommet. Et Jeopardy-verktøy for lærere og elever, med matematikk, bilder og deling av oppgaver.">
<meta property="og:title" content="Jeopardy · Munchboka – for lærere og elever">
<meta property="og:description" content="Et digitalt undervisningsverktøy for faglig repetisjon og samarbeid. Lag egne spørsmål og svar med matematikk og bilder, og bruk dem i klasserommet.">
<meta property="og:type" content="website"><meta property="og:locale" content="nb_NO">
<?php if ($publicInfo): ?><link rel="canonical" href="https://jeopardy.munchboka.no/<?= $about ? '?about=1' : '' ?>"><?php endif; ?><script src="/theme.js?v=3"></script><link rel="stylesheet" href="/pilot.css?v=3">
<link rel="stylesheet" href="/vendor/katex/katex.min.css"><script defer src="/vendor/katex/katex.min.js"></script><script defer src="/math.js?v=2"></script>
<?php if ($editing && $game): ?><script defer src="/editor.js?v=5"></script><?php endif; ?>
<?php if ($playing && $game): ?><link rel="stylesheet" href="/jeopardy.css"><script defer src="/jeopardy.js?v=2"></script><?php endif; ?>
</head><body><header><a class="brand" href="/">Munchboka <strong>Jeopardy</strong></a><label class="theme-control" for="theme">Utseende<select id="theme"><option value="system">Følg systemet</option><option value="light">Lyst</option><option value="dark">Mørkt</option></select></label></header>
<main>
<?php if ($flash): ?><div class="notice" role="status"><?= h($flash) ?></div><?php endif; ?>
<?php if ($error): ?><div class="error" role="alert"><?= h($error) ?></div><?php endif; ?>
<?php if ($about): ?>
<section class="intro"><p class="eyebrow">DIGITALE LÆRINGSRESSURSER</p><h1>Et verktøy for undervisning og repetisjon</h1>
<p>Munchboka Jeopardy lar lærere og elever lage egne faglige spørsmål og svar i et Jeopardy-format: et oppgavebrett med kategorier og poengverdier.</p></section>
<section class="card"><h2>Slik kan verktøyet brukes i timen</h2>
<ul><li>Repetere fagstoff og hente frem tidligere kunnskap.</li><li>Øve på begreper, forklare fremgangsmåter og diskutere svar i grupper.</li><li>La elever lage spørsmål til hverandre som del av arbeidet med et tema.</li></ul>
<p>Kategorier og oppgaver bestemmes av den som lager quizen. Verktøyet kan brukes på tvers av fag, og støtter formler med LaTeX og opplastede bilder.</p></section>
<section class="card"><h2>Laget for lærere og elever</h2>
<p>For å opprette og lagre quizer må brukeren bekrefte en e-postadresse som slutter på @osloskolen.no. Dette er et selvstendig Munchboka-verktøy, ikke en offisiell innloggingstjeneste fra Osloskolen eller Feide.</p>
<p>Innholdet lages av brukerne. Eieren velger om en lagret versjon skal deles via lenke. Mottakere kan gjennomføre den delte aktiviteten uten innlogging, men kan ikke redigere originalen.</p>
<p>Poeng og lag brukes som ramme for aktiviteten i klasserommet. Nettstedet har ingen pengespill, kjøp av spillvaluta eller annonser.</p></section>
<p><a class="button" href="/">Til undervisningsquizene</a></p>
<?php elseif ($shared): ?>
<?php if ($game && $content): ?>
<p class="eyebrow">DELT UNDERVISNINGSQUIZ</p><h1><?= h($content['title']) ?></h1>
<p>Faglig quiz til repetisjon og samarbeid. Du kan gjennomføre aktiviteten uten innlogging. Poeng og fremdrift gjelder bare i denne nettleseren.</p>
<?php $cfg = jp_player_config($content, $_GET['share']); ?>
<div class="jeopardy-container" id="shared-<?= h($game['id']) ?>-<?= (int) $game['revision'] ?>" data-config="<?= h(json_encode($cfg, JSON_THROW_ON_ERROR)) ?>"></div>
<?php else: ?><p>Be eieren om en ny delingslenke.</p><?php endif; ?>
<p><a href="/">Lag din egen undervisningsquiz</a></p>
<?php elseif (!$uid): ?>
<section class="intro"><p class="eyebrow">FAGLIG REPETISJON OG SAMARBEID</p><h1>Jeopardy</h1>
<p>Lag egne spørsmål og svar til faglig repetisjon, begrepstrening og samarbeid. Organiser oppgavene i et Jeopardy-brett med kategorier, og bruk tekst, matematiske formler og bilder i undervisningen.</p><p>Lærere og elever kan lagre quizene på nett og dele en valgt versjon med klassen. <a href="/?about=1">Les om undervisningsverktøyet</a>.</p></section>
<section class="card login"><h2>Logg inn eller opprett konto</h2><p>For lærere og elever med @osloskolen.no. Du får en engangskode på e-post og trenger ikke et eget passord.</p>
<?php if (isset($_SESSION['challenge'])): ?>
<form method="post" action="/"><?php csrf(); ?><input type="hidden" name="action" value="verify">
<label for="code">Kode sendt til <?= h($_SESSION['email_pending']) ?></label>
<input id="code" name="code" inputmode="numeric" autocomplete="one-time-code" pattern="[0-9]{8}" maxlength="8" required placeholder="8 sifre">
<button>Logg inn</button><p class="hint">Koden gjelder i 10 minutter. Sjekk også søppelpost.</p></form>
<details><summary>Trenger du en ny kode?</summary>
<?php endif; ?>
<form method="post" action="/"><?php csrf(); ?><input type="hidden" name="action" value="send">
<label for="email">E-post i Osloskolen</label><input id="email" name="email" type="email" autocomplete="email" maxlength="254" required placeholder="navn@osloskolen.no">
<button>Send innloggingskode</button></form>
<?php if (isset($_SESSION['challenge'])): ?></details><?php endif; ?>
<p class="hint">Kontoen opprettes når du bekrefter e-postadressen første gang. E-postadressen brukes til innlogging og eierskap. Quizer og bilder er private til du velger å dele en quiz med en lenke.</p></section>
<?php else: ?>
<nav><a href="/">Mine quizer</a><span><?= h($_SESSION['email']) ?></span><form method="post" action="/"><?php csrf(); ?><input type="hidden" name="action" value="logout"><button class="quiet">Logg ut</button></form></nav>
<?php if ($playing && $game && $content && !$content['categories']): ?>
<h1><?= h($content['title']) ?></h1><p>Dette spillet har ingen kategorier ennå.</p>
<a class="button" href="/?edit=<?= h($game['id']) ?>">Legg til din første kategori</a>
<?php elseif ($playing && $game && $content): ?>
<h1><?= h($content['title']) ?></h1><p><a href="/?edit=<?= h($game['id']) ?>">Tilbake til redigering</a></p>
<?php
    $cfg = jp_player_config($content);
?>
<div class="jeopardy-container" id="pilot-<?= h($game['id']) ?>-<?= (int) $game['revision'] ?>" data-config="<?= h(json_encode($cfg, JSON_THROW_ON_ERROR)) ?>"></div>
<?php elseif ($editing && $game && $content): ?>
<h1><?= $game['id'] ? 'Rediger undervisningsquizen' : 'Lag en undervisningsquiz' ?></h1>
<p>Skriv matematikk med <code>$x^2$</code> eller <code>$$\frac{1}{2}$$</code>. Legg til bilder i spørsmål og svar.</p>
<div id="editor" data-share="<?= h(json_encode($shareInfo, JSON_THROW_ON_ERROR)) ?>" data-game="<?= h(json_encode($content, JSON_THROW_ON_ERROR)) ?>" data-id="<?= h($game['id']) ?>" data-revision="<?= (int) $game['revision'] ?>" data-csrf="<?= h($_SESSION['csrf']) ?>">
<noscript>Slå på JavaScript for å bruke spillverkstedet.</noscript></div>
<?php else: ?>
<p class="eyebrow">DINE UNDERVISNINGSQUIZER</p><h1>Mine quizer</h1><p>Quizene er knyttet til kontoen din og lagret på nett.</p><a class="button" href="/?new=1">Opprett quiz</a>
<?php if (!$games): ?><section class="card"><h2>Plass til din første undervisningsquiz</h2><p>Lag kategorier, fyll inn spørsmål og svar, og lagre quizen til neste time.</p></section><?php endif; ?>
<div class="library"><?php foreach ($games as $item): ?><article class="card"><h2><?= h($item['title']) ?></h2><p class="hint">Versjon <?= (int) $item['revision'] ?> · <?= $item['share_token'] ? 'Delt med lenke' : 'Privat' ?></p><div class="actions"><a href="/?edit=<?= h($item['id']) ?>">Rediger</a><a href="/?play=<?= h($item['id']) ?>">Start quiz</a></div></article><?php endforeach; ?></div>
<?php endif; endif; ?>
</main><footer>Munchboka · Digitale læringsressurser · <a href="/?about=1">Om undervisningsverktøyet</a></footer></body></html>
