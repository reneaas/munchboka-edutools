<?php
declare(strict_types=1);

function lq_lightning_settings(array $content): array {
    return $content['lightning'] ?? ['enabled'=>false,'seconds'=>60];
}
function lq_validate_lightning(mixed $settings): array {
    if (!is_array($settings) || !is_bool($settings['enabled'] ?? null)
        || !is_int($settings['seconds'] ?? null) || $settings['seconds'] < 5 || $settings['seconds'] > 600) {
        throw new DomainException('Velg 5–600 hele sekunder for lynrunden.');
    }
    return ['enabled'=>$settings['enabled'],'seconds'=>$settings['seconds']];
}
function lq_lightning_prepare(PDO $db, array $room, array $content): array {
    $players = lq_query($db,'SELECT id FROM lq_players WHERE room_id = ? ORDER BY id',[$room['id']])->fetchAll(PDO::FETCH_COLUMN);
    if (!$players) throw new DomainException('Lynrunden trenger minst én deltaker.');
    $players=array_values(array_diff($players,$content['_waiting'] ?? []));
    $orders = [];
    foreach ($players as $player) {
        $order = range(0,count($content['questions'])-1);
        for ($i=count($order)-1;$i>0;$i--) { $j=random_int(0,$i); [$order[$i],$order[$j]]=[$order[$j],$order[$i]]; }
        $orders[$player] = $order;
    }
    $content['_lightning'] = ['orders'=>$orders];
    lq_query($db,'UPDATE lq_rooms SET content = ? WHERE id = ?',[json_encode($content,JSON_THROW_ON_ERROR),$room['id']]);
    return array_replace($room,['content'=>json_encode($content,JSON_THROW_ON_ERROR)]);
}
function lq_lightning_progress(PDO $db, array $room, string $player): array {
    $content=json_decode($room['content'],true,32,JSON_THROW_ON_ERROR);
    $order=$content['_lightning']['orders'][$player] ?? [];
    $position=(int)lq_query($db,'SELECT COUNT(*) FROM lq_answers WHERE room_id = ? AND player_id = ? AND question_index < 0',[$room['id'],$player])->fetchColumn();
    return ['position'=>$position,'index'=>$order[$position] ?? null,'total'=>count($order),'done'=>$position>=count($order)];
}
function lq_lightning_advance(PDO $db, array $room): array {
    $content=json_decode($room['content'],true,32,JSON_THROW_ON_ERROR);
    if ($room['phase']==='light_count' && microtime(true)>=lq_deadline($room)) {
        $deadline=(int)round((lq_deadline($room)+lq_lightning_settings($content)['seconds'])*1000);
        $room=lq_transition($db,$room,'lightning',(int)$room['question_index'],$deadline);
    }
    if ($room['phase']==='lightning') {
        $expected=count($content['_lightning']['orders'] ?? [])*count($content['questions']);
        $answered=(int)lq_query($db,'SELECT COUNT(*) FROM lq_answers WHERE room_id = ? AND question_index < 0',[$room['id']])->fetchColumn();
        if (microtime(true)>=lq_deadline($room) || ($expected>0 && $answered>=$expected)) {
            $room=lq_transition($db,$room,'light_done',(int)$room['question_index'],0);
        }
    }
    return $room;
}
function lq_lightning_state(PDO $db, array $room, ?array $player, array $state, array $content): array {
    $state['lightning']=lq_lightning_settings($content);
    if ($room['phase']==='light_done') {
        $state['leaderboard']=lq_leaderboard($db,$room['id'],$content);
        return $state;
    }
    if ($room['phase']!=='lightning' || !$player) return $state;
    $progress=lq_lightning_progress($db,$room,$player['id']);
    $state['progress']=$progress['position'];$state['completed']=$progress['done'];
    $state['index']=$progress['index'];$state['submitted']=false;
    if (!$progress['done']) {
        $question=$content['questions'][$progress['index']];
        unset($question['correct'],$question['accepted'],$question['youtube']);
        $state['question']=$question;
    }
    return $state;
}
function lq_lightning_answer(PDO $db, array $input, string $token): array {
    // Returning the state inside this same room lock makes progression atomic.
    $result=lq_transaction($db,function () use ($db,$input,$token) {
        $room=lq_room($db,$input['room'] ?? '',true);
        $player=lq_player($db,$room['id'],$token);
        lq_require_run($room,$input);lq_require_eligible($room,$player);
        $room=lq_lightning_advance($db,$room);
        if ($room['phase']!=='lightning' || microtime(true)>=lq_deadline($room)) return ['closed'=>true];
        $index=$input['index'] ?? null;
        if (!is_int($index) || $index<0) throw new DomainException('Ugyldig spørsmål.');
        $content=json_decode($room['content'],true,32,JSON_THROW_ON_ERROR);
        if (!isset($content['questions'][$index])) throw new DomainException('Ugyldig spørsmål.');
        // Negative indices reserve a separate answer key space for this round.
        $key=-1-$index;
        if (!lq_query($db,'SELECT 1 FROM lq_answers WHERE room_id = ? AND player_id = ? AND question_index = ?',[$room['id'],$player['id'],$key])->fetchColumn()) {
            $progress=lq_lightning_progress($db,$room,$player['id']);
            if ($progress['done'] || $progress['index']!==$index) throw new DomainException('Dette er ikke ditt gjeldende spørsmål.');
            [$answer,$points]=lq_grade($content['questions'][$index],$input['answer'] ?? null);
            lq_query($db,'INSERT INTO lq_answers (room_id,player_id,question_index,answer,points) VALUES (?,?,?,?,?)',[$room['id'],$player['id'],$key,json_encode($answer,JSON_THROW_ON_ERROR),$points]);
        }
        $room=lq_lightning_advance($db,$room);
        return ['accepted'=>true,'state'=>lq_state_payload($db,$room,$player,false)];
    });
    if (isset($result['closed'])) throw new DomainException('Lynrunden er avsluttet.');
    return $result;
}
function lq_leaderboard(PDO $db,string $room,array $content): array {
    $rows=lq_query($db,'SELECT p.id, p.nickname, COALESCE(SUM(a.points), 0) AS score FROM lq_players p LEFT JOIN lq_answers a ON a.player_id = p.id AND a.room_id = p.room_id WHERE p.room_id = ? GROUP BY p.id, p.nickname ORDER BY score DESC, p.nickname, p.id LIMIT 60',[$room])->fetchAll();
    $rows=array_values(array_filter($rows,fn($row)=>!in_array($row['id'],$content['_waiting'] ?? [],true)));
    $play=lq_play_settings($content);
    return $play['mode']==='teams' ? lq_team_leaderboard($play['teams'],$rows) : $rows;
}
