"""Create an isolated SQLite/browser fixture in /tmp; never deploy this directory."""
from pathlib import Path
import shutil
import re
import sys
root = Path(__file__).resolve().parents[1]
out = Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp/livequiz-browser')
out.mkdir(parents=True, exist_ok=True)
shutil.copytree(root / 'public', out / 'public', dirs_exist_ok=True)
legacy = root.parent / 'jeopardy/pilot'
shutil.copytree(legacy / 'public/vendor', out / 'public/vendor', dirs_exist_ok=True)
shutil.copy(legacy / 'public/math.js', out / 'public/math.js')
shutil.copytree(root / 'private', out / 'private', dirs_exist_ok=True)
app = (legacy / 'private/app.php').read_text().replace('function jp_db(): PDO', 'function jp_unused_original_db(): PDO')
app += '''
class LocalQuizPDO extends PDO {
 public function prepare(string $q, array $options = []): PDOStatement|false {
  return parent::prepare(str_replace([' FOR UPDATE', 'INSERT IGNORE'], ['', 'INSERT OR IGNORE'], $q), $options);
 }
}
function jp_db(): PDO {
 return new LocalQuizPDO('sqlite:''' + str(out / 'test.sqlite') + '''', null, null, [PDO::ATTR_ERRMODE=>PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE=>PDO::FETCH_ASSOC]);
}
'''
(out / 'private/app.php').write_text(app)
sql = (root / 'private/livequiz/schema.sql').read_text()
sql = re.sub(r' CHARACTER SET ascii| COLLATE ascii_bin| ENGINE=InnoDB DEFAULT CHARSET=utf8mb4', '', sql)
sql = re.sub(r',\s*INDEX [^\n]+', '', sql)
(out / 'schema.sql').write_text(sql)
(out / 'setup.php').write_text("<?php require __DIR__.'/private/app.php'; $db=jp_db(); $db->exec(file_get_contents(__DIR__.'/schema.sql')); $db->exec('CREATE TABLE IF NOT EXISTS jp_users (id INTEGER PRIMARY KEY, email TEXT); INSERT OR IGNORE INTO jp_users VALUES (1,\"test@osloskolen.no\"); CREATE TABLE IF NOT EXISTS jp_media (id TEXT PRIMARY KEY, owner_id INTEGER, mime TEXT, size INTEGER, width INTEGER, height INTEGER, bytes BLOB)');")
(out / 'public/_test_login.php').write_text("<?php session_name('livequiz-local'); session_start(); $_SESSION=['uid'=>1,'email'=>'test@osloskolen.no','authenticated_at'=>time(),'csrf'=>bin2hex(random_bytes(32))]; header('Location: /?teacher=1');")
print(out)
