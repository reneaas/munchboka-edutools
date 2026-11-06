<?php
declare(strict_types=1);

// Shared with Livequiz: retain lq_credentials and lq_auth_limits table names.
// Additive migration: credentials belong to existing shared user IDs.
function jp_credentials_prepare(PDO $db): void {
    foreach ([
        'lq_credentials' => 'user_id BIGINT UNSIGNED PRIMARY KEY, password_hash VARCHAR(255) NULL, version INT NOT NULL DEFAULT 0',
        'lq_auth_limits' => 'bucket CHAR(64) PRIMARY KEY, window_at BIGINT NOT NULL, attempts INT NOT NULL'
    ] as $table=>$columns) {
        try { $db->query("SELECT 1 FROM $table LIMIT 1"); }
        catch (PDOException $e) {
            if (!in_array((string)$e->getCode(),['42S02','HY000'],true)) throw $e;
            $sql="CREATE TABLE IF NOT EXISTS $table ($columns)";
            if ($db->getAttribute(PDO::ATTR_DRIVER_NAME)==='mysql') $sql.=' ENGINE=InnoDB DEFAULT CHARSET=utf8mb4';
            $db->exec($sql);
        }
    }
}
function jp_credentials_version(PDO $db,int $uid): int {
    return (int)jp_query($db,'SELECT version FROM lq_credentials WHERE user_id = ?',[$uid])->fetchColumn();
}
function jp_auth_session(int $uid,string $email,int $version,bool $verifiedEmail=false): void {
    session_regenerate_id(true);
    $_SESSION=['uid'=>$uid,'email'=>$email,'authenticated_at'=>time(),'credential_version'=>$version,'csrf'=>bin2hex(random_bytes(32))];
    if ($verifiedEmail) $_SESSION['email_verified_at']=time();
}
function jp_password_algorithm(): string|int {
    return in_array('argon2id',password_algos(),true) ? PASSWORD_ARGON2ID : PASSWORD_DEFAULT;
}
function jp_password_value(mixed $value): string {
    if (!is_string($value) || strlen($value)>1024 || str_contains($value,"\0")) throw new DomainException('Ugyldig passord.');
    return $value; // Never trim or normalize passwords.
}
function jp_password_limit(PDO $db,string $email,string $ip): void {
    $db->beginTransaction();
    try {
        foreach (['email:'.$email=>10,'ip:'.$ip=>50] as $key=>$maximum) {
            $bucket=hash('sha256',$key);
            jp_query($db,'INSERT IGNORE INTO lq_auth_limits (bucket,window_at,attempts) VALUES (?, ?, 0)',[$bucket,time()]);
            $row=jp_query($db,'SELECT * FROM lq_auth_limits WHERE bucket = ? FOR UPDATE',[$bucket])->fetch();
            $fresh=time()-(int)$row['window_at']>=900;
            $count=$fresh?0:(int)$row['attempts'];
            if ($count>=$maximum) throw new DomainException('For mange innloggingsforsøk. Vent 15 minutter og prøv igjen.');
            jp_query($db,'UPDATE lq_auth_limits SET window_at = ?, attempts = ? WHERE bucket = ?',[$fresh?time():$row['window_at'],$count+1,$bucket]);
        }
        $db->commit();
    } catch (Throwable $e) { if ($db->inTransaction()) $db->rollBack(); throw $e; }
}
function jp_password_login(PDO $db,string $email,mixed $password,string $ip): void {
    $email=strtolower(trim($email));$password=jp_password_value($password);
    jp_credentials_prepare($db);jp_password_limit($db,$email,$ip);
    $row=jp_query($db,'SELECT u.id, c.password_hash, c.version FROM jp_users u JOIN lq_credentials c ON c.user_id = u.id WHERE u.email = ?',[$email])->fetch();
    $dummy=in_array('argon2id',password_algos(),true) ? '$argon2id$v=19$m=65536,t=4,p=1$QzFKS282T0llQlJSMzBsdw$6Hq3jdVcRBHm3Ippm+1x/00qR9/V7FyBdQtvhOiVSnw' : '$2y$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2uheWG/igi.';
    if (!in_array('argon2id',password_algos(),true)) $dummy=substr_replace($dummy,sprintf('%02d',PASSWORD_BCRYPT_DEFAULT_COST),4,2);
    $valid=password_verify($password,$row['password_hash'] ?? $dummy);
    if ($row && str_starts_with($row['password_hash'] ?? '', '$2') && strlen($password)>72) $valid=false;
    if (!$valid || !$row || !$row['password_hash'] || !jp_allowed_email($email)) throw new DomainException('Feil e-post eller passord.');
    // A concurrent password reset invalidates this session through its old version.
    if (password_needs_rehash($row['password_hash'],jp_password_algorithm())) {
        jp_query($db,'UPDATE lq_credentials SET password_hash = ? WHERE user_id = ? AND version = ? AND password_hash = ?',
            [password_hash($password,jp_password_algorithm()),$row['id'],$row['version'],$row['password_hash']]);
    }
    jp_auth_session((int)$row['id'],$email,(int)$row['version']);
}
function jp_set_password(PDO $db,mixed $password): void {
    $uid=(int)($_SESSION['uid'] ?? 0);
    if (!$uid || time()-(int)($_SESSION['email_verified_at'] ?? 0)>600) throw new DomainException('Bekreft e-posten med en ny engangskode før du setter passord.');
    $password=jp_password_value($password);
    $length=preg_match_all('/[\s\S]/u',$password);
    if ($length===false || $length<15) throw new DomainException('Bruk minst 15 tegn i passordet.');
    if (jp_password_algorithm()===PASSWORD_BCRYPT && strlen($password)>72) throw new DomainException('Denne serveren støtter passord på maksimalt 72 byte.');
    $hash=password_hash($password,jp_password_algorithm());
    jp_credentials_prepare($db);
    $db->beginTransaction();
    try {
        jp_query($db,'INSERT IGNORE INTO lq_credentials (user_id,version) VALUES (?,0)',[$uid]);
        $version=(int)jp_query($db,'SELECT version FROM lq_credentials WHERE user_id = ? FOR UPDATE',[$uid])->fetchColumn();
        if ($version!==(int)($_SESSION['credential_version'] ?? 0)) throw new DomainException('Logg inn igjen før du setter passord.');
        jp_query($db,'UPDATE lq_credentials SET password_hash = ?, version = version + 1 WHERE user_id = ?',[$hash,$uid]);
        $db->commit();
    } catch (Throwable $e) { if ($db->inTransaction()) $db->rollBack(); throw $e; }
    jp_auth_session($uid,$_SESSION['email'],$version+1);
}

function jp_query(PDO $db,string $sql,array $params=[]): PDOStatement {
    $stmt=$db->prepare($sql);$stmt->execute($params);return $stmt;
}
function jp_check_credentials(PDO $db): void {
    if (empty($_SESSION['uid'])) return;
    jp_credentials_prepare($db);
    if (jp_credentials_version($db,(int)$_SESSION['uid']) !== (int)($_SESSION['credential_version'] ?? 0)) {
        session_regenerate_id(true);
        $_SESSION=['csrf'=>bin2hex(random_bytes(32))];
    }
}
