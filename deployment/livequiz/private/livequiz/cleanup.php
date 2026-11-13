<?php
declare(strict_types=1);
if (PHP_SAPI!=='cli') { http_response_code(404); exit; }
require __DIR__.'/app.php';
$db=jp_db();$count=lq_prune_all_history($db);
lq_battle_prepare($db);
lq_query($db,'DELETE FROM lq_class_codes WHERE NOT EXISTS (SELECT 1 FROM lq_rooms WHERE lq_rooms.id=lq_class_codes.room_id)');
if ($count) echo "Livequiz: removed $count old or abandoned game sessions.\n";
