<?php
declare(strict_types=1);
if (PHP_SAPI!=='cli') { http_response_code(404); exit; }
require __DIR__.'/app.php';
$count=lq_prune_all_history(jp_db());
if ($count) echo "Livequiz: removed $count old or abandoned game sessions.\n";
