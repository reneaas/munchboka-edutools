<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
require __DIR__ . '/app.php';
// Bounded batches avoid a long transaction on accounts with a large backlog.
// Current game rows, revision counters, shared snapshots and media are untouched.
$db = jp_db();
$removed = 0;
for ($batch = 0; $batch < 10; $batch++) {
    $count = $db->exec('DELETE FROM jp_revisions LIMIT 1000');
    $removed += $count;
    if ($count < 1000) break;
}
if ($removed) echo "Jeopardy: removed $removed unused historical revisions.\n";
