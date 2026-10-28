<?php
declare(strict_types=1);
require_once __DIR__ . '/passwords.php';
// Separate challenges, shared users and global mail budget. Uses the existing verified sender.
function lq_send_code(PDO $db, string $email): void
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
        $db->prepare('INSERT IGNORE INTO lq_login (email) VALUES (?)')->execute([$email]);
        $stmt = $db->prepare('SELECT * FROM lq_login WHERE email = ? FOR UPDATE');
        $stmt->execute([$email]);
        $row = $stmt->fetch();
        if ($now - (int) $row['sent_at'] < 60) {
            throw new DomainException('Vent ett minutt før du ber om en ny kode.');
        }
        $freshWindow = $now - (int) $row['window_at'] >= 3600;
        $count = $freshWindow ? 0 : (int) $row['send_count'];
        if ($count >= 5) throw new DomainException('For mange kodeforespørsler. Prøv igjen om en time.');
        $db->prepare('UPDATE lq_login SET challenge = ?, code_hash = ?, expires_at = ?, attempts = 0, sent_at = ?, window_at = ?, send_count = ? WHERE email = ?')
            ->execute([$challenge, password_hash($code, PASSWORD_DEFAULT), $now + 600,
                $now, $freshWindow ? $now : $row['window_at'], $count + 1, $email]);
        $db->commit();
    } catch (Throwable $e) {
        if ($db->inTransaction()) $db->rollBack();
        throw $e;
    }
    $body = "Din innloggingskode til Munchboka Livequiz er:\r\n\r\n" . $code
        . "\r\n\r\nKoden gjelder i 10 minutter og kan brukes en gang.\r\n"
        . "Skriv den inn i nettleseren der du ba om koden:\r\n" . 'https://quiz.munchboka.no/?login=1'
        . "\r\n\r\nHvis du ikke ba om denne koden, kan du ignorere meldingen.\r\n";
    $accepted = mail($email, 'Innloggingskode til Munchboka Livequiz', $body, [
        'From' => 'Munchboka Livequiz <' . JP_SENDER . '>',
        'MIME-Version' => '1.0',
        'Content-Type' => 'text/plain; charset=UTF-8',
    ], '-f' . JP_SENDER);
    if (!$accepted) {
        $db->prepare('UPDATE lq_login SET code_hash = NULL WHERE email = ? AND challenge = ?')->execute([$email, $challenge]);
        throw new DomainException('E-posttjenesten kunne ikke sende koden. Prøv igjen senere.');
    }
    $_SESSION['challenge'] = $challenge;
    $_SESSION['email_pending'] = $email;
    $_SESSION['flash'] = 'Koden er sendt til e-posttjenesten. Se etter meldingen i innboksen og søppelpost.';
}

function lq_verify(PDO $db, string $code): void
{
    $email = $_SESSION['email_pending'] ?? '';
    $challenge = $_SESSION['challenge'] ?? '';
    if (!is_string($email) || !jp_allowed_email($email) || !is_string($challenge) || strlen($challenge) !== 64) {
        throw new DomainException('Be om en ny kode først.');
    }
    lq_credentials_prepare($db);
    $db->beginTransaction();
    try {
        $stmt = $db->prepare('SELECT * FROM lq_login WHERE email = ? FOR UPDATE');
        $stmt->execute([$email]);
        $row = $stmt->fetch();
        if (!$row || !$row['code_hash'] || !hash_equals((string) $row['challenge'], $challenge)
            || (int) $row['expires_at'] < time() || (int) $row['attempts'] >= 5) {
            throw new DomainException('Koden er utløpt eller brukt opp. Be om en ny kode.');
        }
        $db->prepare('UPDATE lq_login SET attempts = attempts + 1 WHERE email = ?')->execute([$email]);
        if (!preg_match('/^[0-9]{8}$/D', $code) || !password_verify($code, $row['code_hash'])) {
            $db->commit(); // Failed attempts must persist.
            throw new DomainException('Feil kode. Kontroller de åtte sifrene og prøv igjen.');
        }
        $db->prepare('UPDATE lq_login SET code_hash = NULL, challenge = NULL WHERE email = ?')->execute([$email]);
        $db->prepare('INSERT IGNORE INTO jp_users (email) VALUES (?)')->execute([$email]);
        $stmt = $db->prepare('SELECT id FROM jp_users WHERE email = ?');
        $stmt->execute([$email]);
        $uid = (int) $stmt->fetchColumn();
        $version=lq_credentials_version($db,$uid);
        $db->commit();
        lq_auth_session($uid,$email,$version,true);
    } catch (Throwable $e) {
        if ($db->inTransaction()) $db->rollBack();
        throw $e;
    }
}

