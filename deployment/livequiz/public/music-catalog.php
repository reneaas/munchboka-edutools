<?php
declare(strict_types=1);

function lq_music_tracks(string $directory): array {
    $tracks = [];
    foreach (is_dir($directory) ? scandir($directory) : [] as $name) {
        if ($name[0] === '.' || !is_file($directory.'/'.$name) || is_link($directory.'/'.$name)) continue;
        if (!in_array(strtolower(pathinfo($name, PATHINFO_EXTENSION)), ['mp3','m4a','ogg','wav'], true)) continue;
        $tracks[] = 'music/'.rawurlencode($name);
    }
    return $tracks;
}
