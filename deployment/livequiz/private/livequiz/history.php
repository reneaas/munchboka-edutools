<?php
declare(strict_types=1);

// Keep saved quizzes/media separate from disposable game sessions.
function lq_prune_history(PDO $db, int $owner): int {
    return lq_transaction($db, function () use ($db,$owner) {
        $now=time();
        // Lock candidates in a stable order. A concurrent restart must either finish
        // before this query (and be excluded), or wait until cleanup commits.
        $rows=lq_query($db,"SELECT id, phase, content, expires_at FROM lq_rooms WHERE owner_id = ? AND (phase IN ('finished','race_done','light_done') OR expires_at <= ?) ORDER BY id FOR UPDATE",[$owner,$now])->fetchAll();
        $finished=[];$remove=[];
        foreach ($rows as $row) {
            if (!in_array($row['phase'],['finished','race_done','light_done'],true)) {$remove[]=$row['id'];continue;}
            $content=json_decode($row['content'],true,32,JSON_THROW_ON_ERROR);
            // Legacy rooms have no completion timestamp; their expiry provides
            // a stable approximation of age without extending their lifetime.
            $row['finished_at']=(float)($content['_finished_at'] ?? ((int)$row['expires_at']-21600));
            $finished[]=$row;
        }
        usort($finished,fn($a,$b)=>($b['finished_at']<=>$a['finished_at']) ?: strcmp($b['id'],$a['id']));
        foreach (array_slice($finished,5) as $row) $remove[]=$row['id'];
        foreach ($remove as $id) {
            lq_query($db,'DELETE FROM lq_answers WHERE room_id = ?',[$id]);
            lq_query($db,'DELETE FROM lq_players WHERE room_id = ?',[$id]);
            lq_query($db,'DELETE FROM lq_rooms WHERE id = ? AND owner_id = ?',[$id,$owner]);
        }
        return count($remove);
    });
}
function lq_prune_all_history(PDO $db): int {
    $count=0;
    foreach (lq_query($db,'SELECT DISTINCT owner_id FROM lq_rooms')->fetchAll(PDO::FETCH_COLUMN) as $owner) $count+=lq_prune_history($db,(int)$owner);
    return $count;
}
