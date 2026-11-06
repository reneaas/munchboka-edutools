"""Disposable local auth fixture only; never deploy its output. Use a fresh output directory."""
from pathlib import Path
import shutil,re
root=Path(__file__).resolve().parents[1];out=Path('/private/tmp/jeopardy-auth')
shutil.copytree(root/'public',out/'public',dirs_exist_ok=True);shutil.copytree(root/'private',out/'private',dirs_exist_ok=True)
p=out/'public/index.php';s=p.read_text().replace("if (($_SERVER['HTTPS'] ?? '') !== 'on')",'if (false)').replace("session_name('__Host-jeopardy')","session_name('jeopardy-local')").replace("'__Host-jeopardy', ''","'jeopardy-local', ''").replace("'secure' => true","'secure' => false").replace("'/home/zebfxvix/jeopardy-private/app.php'",repr(str(out/'private/app.php')));p.write_text(s)
p=out/'private/app.php';s=p.read_text().replace('function jp_db(): PDO','function jp_original_db(): PDO').replace('function jp_schema(PDO $db): void','function jp_original_schema(PDO $db): void');s+='''
class LocalJeopardyPDO extends PDO {public function prepare(string $q,array $options=[]):PDOStatement|false{return parent::prepare(str_replace([' FOR UPDATE','INSERT IGNORE'],['','INSERT OR IGNORE'],$q),$options);}}
function jp_db():PDO{return new LocalJeopardyPDO('sqlite:/private/tmp/jeopardy-auth/test.sqlite',null,null,[PDO::ATTR_ERRMODE=>PDO::ERRMODE_EXCEPTION,PDO::ATTR_DEFAULT_FETCH_MODE=>PDO::FETCH_ASSOC]);}
function jp_schema(PDO $db):void{}
''';p.write_text(s)
core=(root/'tests/core.php').read_text();sql=re.search(r"\$db->exec\('([\s\S]*?)'\);",core)[1]
(out/'schema.sql').write_text(sql)
(out/'setup.php').write_text("<?php require __DIR__.'/private/app.php';$db=jp_db();$db->exec(file_get_contents(__DIR__.'/schema.sql'));jp_credentials_prepare($db);jp_query($db,'INSERT INTO jp_users (email) VALUES (?)',['browser@osloskolen.no']);jp_query($db,'INSERT INTO lq_credentials (user_id,password_hash,version) VALUES (1,?,1)',[password_hash('Original browser password',jp_password_algorithm())]);")
(out/'public/_test_code.php').write_text("<?php session_name('jeopardy-local');session_start();require __DIR__.'/../private/app.php';$db=jp_db();$email='browser@osloskolen.no';$challenge=bin2hex(random_bytes(32));jp_query($db,'INSERT IGNORE INTO jp_login (email) VALUES (?)',[$email]);jp_query($db,'UPDATE jp_login SET challenge=?,code_hash=?,expires_at=?,attempts=0 WHERE email=?',[$challenge,password_hash('12345678',PASSWORD_DEFAULT),time()+600,$email]);$_SESSION['email_pending']=$email;$_SESSION['challenge']=$challenge;header('Location: /?account=1');")
