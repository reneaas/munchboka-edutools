<?php
declare(strict_types=1);

function lq_game(array $content): string { return $content['game'] ?? 'regular'; }
function lq_race_order(int $count): array {
    $order=range(0,$count-1);
    for($i=$count-1;$i>0;$i--){$j=random_int(0,$i);[$order[$i],$order[$j]]=[$order[$j],$order[$i]];}
    return $order;
}
function lq_race_store(PDO $db,array $room,array $content): array {
    $json=json_encode($content,JSON_THROW_ON_ERROR);
    lq_query($db,'UPDATE lq_rooms SET content=? WHERE id=?',[$json,$room['id']]);
    return array_replace($room,['content'=>$json]);
}
function lq_race_new_entry(array $group,int $count): array {
    return ['id'=>'r'.$group['id'],'name'=>$group['name'],'members'=>$group['members'],'attempt'=>0,'start'=>0,
        'order'=>lq_race_order($count),'progress'=>0,'revision'=>0,'completed'=>false,'completed_at'=>null,'reset_at'=>null,'updated_at'=>microtime(true)];
}
function lq_race_prepare(PDO $db,array $room,array $content): array {
    $play=lq_play_settings($content);
    $players=lq_query($db,'SELECT id,nickname FROM lq_players WHERE room_id=? ORDER BY id',[$room['id']])->fetchAll();
    if(!$players)throw new DomainException('Vent til minst én deltaker har blitt med.');
    $groups=$play['mode']==='teams' ? $play['teams'] : array_map(fn($p)=>['id'=>$p['id'],'name'=>$p['nickname'],'members'=>[$p]],$players);
    $entries=[];
    foreach($groups as $group){
        $entry=lq_race_new_entry($group,count($content['questions']));$entries[$entry['id']]=$entry;
    }
    $content['_race']=['entries'=>$entries,'winner'=>null];
    return lq_race_store($db,$room,$content);
}
function lq_race_entry(array $content,string $player): array {
    foreach($content['_race']['entries'] ?? [] as $entry)if(in_array($player,array_column($entry['members'],'id'),true))return $entry;
    throw new DomainException('Du er ikke med i dette løpet.');
}
function lq_race_active(array $entry): array {
    return $entry['members'][($entry['start']+$entry['progress'])%count($entry['members'])];
}
function lq_race_state(array $room,?array $player,array $state,array $content): array {
    $race=$content['_race'];$state['winner']=$race['winner'];
    // Never expose other competitors' orders, questions or correct answers.
    $state['race_board']=array_values(array_map(fn($e)=>array_intersect_key($e,array_flip(['id','name','progress','attempt','completed','completed_at'])),$race['entries']));
    usort($state['race_board'],fn($a,$b)=>($b['completed']<=>$a['completed']) ?: ($b['progress']<=>$a['progress']) ?: strcmp($a['name'],$b['name']));
    if($room['phase']!=='race' || !$player)return $state;
    $entry=lq_race_entry($content,$player['id']);$active=lq_race_active($entry);
    $state['race']=array_intersect_key($entry,array_flip(['id','attempt','start','progress','revision','members','updated_at','reset_at']));
    $state['race']['active']=$active;$state['race']['starting']=$entry['members'][$entry['start']];
    $state['can_answer']=$active['id']===$player['id'];$state['progress']=$entry['progress'];$state['submitted']=false;
    if($state['can_answer']){
        $state['index']=$entry['order'][$entry['progress']];
        $question=$content['questions'][$state['index']];unset($question['correct'],$question['accepted'],$question['youtube']);
        $state['question']=$question;
    }else $state['index']=null;
    return $state;
}
function lq_race_answer(PDO $db,array $input,string $token): array {
    return lq_transaction($db,function()use($db,$input,$token){
        $room=lq_room($db,$input['room'] ?? '',true);$player=lq_player($db,$room['id'],$token);
        lq_require_run($room,$input);lq_require_eligible($room,$player);
        $room=lq_advance_locked($db,$room);
        if($room['phase']!=='race')throw new DomainException('Løpet er ikke aktivt.');
        $content=json_decode($room['content'],true,32,JSON_THROW_ON_ERROR);$entry=lq_race_entry($content,$player['id']);
        if(lq_race_active($entry)['id']!==$player['id'])throw new DomainException('Det er ikke din tur.');
        // A revision binds the submission to exactly one turn in one attempt.
        if(($input['attempt'] ?? null)!==$entry['attempt'] || ($input['race_revision'] ?? null)!==$entry['revision']
            || ($input['index'] ?? null)!==$entry['order'][$entry['progress']])throw new DomainException('Dette svaret tilhører en tidligere tur.');
        [, $points]=lq_grade($content['questions'][$input['index']],$input['answer'] ?? null);
        $correct=$points>0;
        if($correct){
            $entry['progress']++;
            if($entry['progress']===count($entry['order'])){
                $entry['completed']=true;$entry['completed_at']=microtime(true);$content['_race']['winner']=$entry['id'];
            }
        }else{
            $entry['reset_at']=microtime(true);$entry['progress']=0;$entry['attempt']++;$entry['start']=($entry['start']+1)%count($entry['members']);
            $entry['order']=lq_race_order(count($content['questions']));
        }
        $entry['revision']++;$entry['updated_at']=microtime(true);$content['_race']['entries'][$entry['id']]=$entry;
        $room=lq_race_store($db,$room,$content);
        // The room lock serializes winning submissions and makes resets/retries atomic.
        $room=lq_transition($db,$room,$entry['completed']?'race_done':'race',-1,0);
        return ['accepted'=>true,'correct'=>$correct,'state'=>lq_state_payload($db,$room,$player,false)];
    });
}
