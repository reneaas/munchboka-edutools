"""Disposable loopback MySQL fixture. Requires an already running isolated server.
Never deploy the output. Usage: python3 prepare-concurrency.py /private/tmp/lq-test 33079
The database lq_simulation must not already exist.
"""
from pathlib import Path
import subprocess
import shutil
import sys
out = Path(sys.argv[1]).resolve()
port = int(sys.argv[2])
assert str(out).startswith('/private/tmp/')
root = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(root/'tests/prepare-local.py'), str(out)], check=True)
shutil.copy(root.parent/'jeopardy/pilot/private/app.php', out/'private/app.php')
shutil.copy(root/'private/livequiz/schema.sql', out/'schema.sql')
(out/'private/database.php').write_text(
    "<?php return ['host'=>'127.0.0.1','port'=>%d,'name'=>'lq_simulation','user'=>'root','password'=>''];" % port)
(out/'setup.php').write_text("""<?php
$db=new PDO('mysql:host=127.0.0.1;port=%d','root','');
$db->exec('CREATE DATABASE lq_simulation');$db->exec('USE lq_simulation');
$db->exec(file_get_contents(__DIR__.'/schema.sql'));
$db->exec("CREATE TABLE jp_users (id BIGINT UNSIGNED PRIMARY KEY, email VARCHAR(254)); INSERT INTO jp_users VALUES (1,'test@osloskolen.no'); CREATE TABLE jp_media (id CHAR(32) PRIMARY KEY,owner_id BIGINT,mime VARCHAR(100),size INT,width INT,height INT,bytes LONGBLOB)");
""" % port)
(out/'public/_simulation.php').write_text(
    "<?php header('Content-Type: application/json'); echo json_encode(['fixture'=>'isolated-mysql-concurrency','pid'=>getmypid()]);")
subprocess.run(['php', str(out/'setup.php')], check=True)
