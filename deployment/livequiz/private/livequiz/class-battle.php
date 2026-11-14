<?php
declare(strict_types=1);

// Class Battle shares a normal room and its answer/deadline machinery. Only the
// additional entry points need a lookup table; roster and capabilities are locked
// with the room JSON, so joining and starting cannot race each other.
function lq_battle_prepare(PDO $db): void {
    $engine=$db->getAttribute(PDO::ATTR_DRIVER_NAME)==='mysql'?' ENGINE=InnoDB DEFAULT CHARSET=utf8mb4':'';
    $db->exec('CREATE TABLE IF NOT EXISTS lq_class_codes (pin CHAR(8) PRIMARY KEY, room_id CHAR(32) NOT NULL, class_id CHAR(32) NOT NULL)'.$engine);
}
function lq_battle_class(array $content, string $token): string {
    if (!preg_match('/^[a-f0-9]{64}$/D',$token)) throw new DomainException('Ugyldig medvertlenke.');
    foreach ($content['_battle']['classes'] ?? [] as $id=>$class) {
        if (isset($class['host_hash']) && hash_equals($class['host_hash'],hash('sha256','cohost:'.$token))) return (string)$id;
    }
    throw new DomainException('Medvertlenken er utløpt eller klassen er fjernet.');
}
function lq_battle_write(PDO $db,array $room,array $content): void {
    lq_query($db,'UPDATE lq_rooms SET content=?, version=version+1 WHERE id=?',[json_encode($content,JSON_THROW_ON_ERROR),$room['id']]);
}
function lq_battle_manage(PDO $db,int $uid,array $input,string $hostToken,string $cohostToken): array {
    return lq_transaction($db,function()use($db,$uid,$input,$hostToken,$cohostToken){
        $room=lq_room($db,$input['room'] ?? '',true);$content=json_decode($room['content'],true,32,JSON_THROW_ON_ERROR);
        if (lq_game($content)!=='classbattle' || !isset($content['_battle'])) throw new DomainException('Dette er ikke en Class Battle.');
        $cohost=$cohostToken!=='';$class=$cohost?lq_battle_class($content,$cohostToken):'main';
        if(!$cohost)lq_require_host($room,$uid,$hostToken);
        lq_require_run($room,$input);
        if($room['phase']!=='lobby'||$content['_battle']['locked'])throw new DomainException('Klasser og deltakere er låst mens spillet pågår.');
        $action=$input['command'] ?? '';$result=['ok'=>true];
        if($action==='invite'&&!$cohost){
            $content['_battle']['invitation_number'] ??= 0;
            $key=bin2hex(random_bytes(32));$content['_battle']['invites'][hash('sha256',$key)]=null;
            $content['_battle']['invitation_keys'][hash('sha256',$key)]=['key'=>$key,'number'=>++$content['_battle']['invitation_number']];
            $result=['key'=>$key];
        }elseif($action==='revoke'&&!$cohost){
            $hash=hash('sha256',jp_text($input['key'] ?? '',64));
            if(!array_key_exists($hash,$content['_battle']['invites'])||$content['_battle']['invites'][$hash]!==null)throw new DomainException('Bare ubrukte invitasjoner kan trekkes tilbake.');
            unset($content['_battle']['invites'][$hash],$content['_battle']['invitation_keys'][$hash]);
        }elseif($action==='ready'&&$cohost){
            if(!is_bool($input['ready'] ?? null))throw new DomainException('Ugyldig klar-status.');
            $content['_battle']['classes'][$class]['ready']=$input['ready'];
        }elseif($action==='rename'){
            $name=jp_text($input['name'] ?? '',80);if($name==='')throw new DomainException('Skriv et klassenavn.');
            $content['_battle']['classes'][$class]['name']=$name;
        }elseif($action==='kick'){
            $pid=lq_id($input['player'] ?? null);
            if(($content['_battle']['members'][$pid] ?? null)!==$class)throw new DomainException('Du kan bare fjerne deltakere fra din egen klasse.');
            $player=lq_query($db,'SELECT token_hash FROM lq_players WHERE room_id=? AND id=?',[$room['id'],$pid])->fetch();
            if(!$player)throw new DomainException('Deltakeren finnes ikke.');
            $content['_kicked'][]=$player['token_hash'];unset($content['_battle']['members'][$pid]);
            lq_query($db,'DELETE FROM lq_answers WHERE room_id=? AND player_id=?',[$room['id'],$pid]);
            lq_query($db,'DELETE FROM lq_players WHERE room_id=? AND id=?',[$room['id'],$pid]);
        }elseif($action==='leave'&&$cohost){
            foreach($content['_battle']['members'] as $pid=>$cid){
                if($cid!==$class)continue;
                $hash=lq_query($db,'SELECT token_hash FROM lq_players WHERE room_id=? AND id=?',[$room['id'],$pid])->fetchColumn();
                if($hash)$content['_kicked'][]=$hash;
                lq_query($db,'DELETE FROM lq_answers WHERE room_id=? AND player_id=?',[$room['id'],$pid]);
                lq_query($db,'DELETE FROM lq_players WHERE room_id=? AND id=?',[$room['id'],$pid]);
                unset($content['_battle']['members'][$pid]);
            }
            unset($content['_battle']['classes'][$class]);
            foreach($content['_battle']['invites'] as $hash=>$cid)if($cid===$class)unset($content['_battle']['invites'][$hash],$content['_battle']['invitation_keys'][$hash]);
            lq_query($db,'DELETE FROM lq_class_codes WHERE room_id=? AND class_id=?',[$room['id'],$class]);
        }else throw new DomainException('Handlingen er ikke tilgjengelig for denne verten.');
        lq_battle_write($db,$room,$content);return $result;
    });
}
function lq_battle_join_host(PDO $db,array $input): array {
    lq_battle_prepare($db);
    return lq_transaction($db,function()use($db,$input){
        $room=lq_room($db,$input['room'] ?? '',true);$content=json_decode($room['content'],true,32,JSON_THROW_ON_ERROR);
        $key=$input['key'] ?? '';if(!is_string($key)||!preg_match('/^[a-f0-9]{64}$/D',$key))throw new DomainException('Ugyldig invitasjon.');
        $hash=hash('sha256',$key);
        if(!isset($content['_battle'])||!array_key_exists($hash,$content['_battle']['invites']))throw new DomainException('Invitasjonen er ugyldig eller fjernet.');
        // Reopening the same invitation resumes the same class, never duplicates it.
        $id=$content['_battle']['invites'][$hash];
        if($id!==null)return ['room'=>$room['id'],'class'=>$id];
        if($room['phase']!=='lobby'||$content['_battle']['locked'])throw new DomainException('Spillet har startet. Nye klasser kan ikke bli med nå.');
        $name=jp_text($input['name'] ?? '',80);if($name==='')throw new DomainException('Skriv et klassenavn.');
        $id=bin2hex(random_bytes(16));$pin=null;
        for($i=0;$i<10;$i++){
            // Leading zero reserves a disjoint six-digit namespace: main rooms use 100000–999999.
            $candidate=sprintf('%06d',random_int(1,99999));
            try{lq_query($db,'INSERT INTO lq_class_codes (pin,room_id,class_id) VALUES (?,?,?)',[$candidate,$room['id'],$id]);$pin=$candidate;break;}
            catch(PDOException $e){if($e->getCode()!=='23000')throw $e;}
        }
        if($pin===null)throw new DomainException('Kunne ikke opprette klassekode. Prøv igjen.');
        $content['_battle']['classes'][$id]=['name'=>$name,'pin'=>$pin,'host_hash'=>hash('sha256','cohost:'.$key)];
        $content['_battle']['invites'][$hash]=$id;lq_battle_write($db,$room,$content);
        return ['room'=>$room['id'],'class'=>$id];
    });
}
function lq_battle_board(PDO $db,string $room,array $battle): array {
    $players=lq_query($db,'SELECT p.id,p.nickname,COALESCE(SUM(a.points),0) AS score FROM lq_players p LEFT JOIN lq_answers a ON a.player_id=p.id AND a.room_id=p.room_id WHERE p.room_id=? GROUP BY p.id,p.nickname ORDER BY score DESC,p.nickname,p.id',[$room])->fetchAll();
    $rows=[];
    foreach($battle['classes'] as $id=>$class){
        $members=array_values(array_filter($players,fn($p)=>($battle['members'][$p['id']] ?? null)===$id));
        $total=array_sum(array_column($members,'score'));$n=count($members);
        $rows[]=['id'=>$id,'name'=>$class['name'],'ready'=>(bool)($class['ready'] ?? false),'count'=>$n,'total'=>$total,'score'=>$n?$total/$n:null,'individuals'=>$members];
    }
    // Compare rational scores exactly, not their rounded display values.
    usort($rows,function($a,$b){if(!$a['count']||!$b['count'])return ($b['count']>0)<=>($a['count']>0);return ($b['total']*$a['count']<=>$a['total']*$b['count']) ?: strcmp($a['id'],$b['id']);});
    $previous=null;
    foreach($rows as $i=>&$row){
        $row['rank']=$row['count']?($previous && $previous['total']*$row['count']===$row['total']*$previous['count']?$previous['rank']:$i+1):null;
        if($row['count'])$previous=$row;
    }unset($row);return $rows;
}
function lq_battle_payload(PDO $db,array $room,array $state,?array $player,bool $host,?string $class=null): array {
    $content=json_decode($room['content'],true,32,JSON_THROW_ON_ERROR);if(!isset($content['_battle']))return $state;
    $battle=$content['_battle'];$mine=$class ?? ($host?'main':($battle['members'][$player['id']] ?? null));
    $rows=lq_battle_board($db,$room['id'],$battle);$details=[];$mvps=[];
    if($host&&$room['phase']==='finished'){
        foreach($rows as $row)foreach($row['individuals'] as $person)$mvps[]=['id'=>$person['id'],'name'=>$person['nickname'],'class_name'=>$row['name'],'score'=>(int)$person['score']];
        // Equal scores use immutable player IDs, independent of database collation.
        usort($mvps,fn($a,$b)=>($b['score']<=>$a['score'])?:strcmp($a['id'],$b['id']));
        $mvps=array_slice($mvps,0,3);foreach($mvps as $i=>&$mvp)$mvp['rank']=$i+1;unset($mvp);
    }
    foreach($rows as &$row){
        if($host&&($class===null||$row['id']===$mine))$details[]=['name'=>$row['name'],'players'=>$row['individuals']];
        unset($row['individuals']);
    }unset($row);
    $state['battle']=['classes'=>$rows,'class_id'=>$mine,'class_name'=>$battle['classes'][$mine]['name'] ?? '', 'locked'=>$battle['locked'],'cohost'=>$class!==null];
    $state['leaderboard']=$rows;
    if($host){
        $state['battle']['results']=$details;
        if($room['phase']==='finished')$state['battle']['mvps']=$mvps;
        $state['battle']['music']=lq_battle_music($db,$room,$content);
        if($class===null){
            $state['battle']['invitations']=[];
            foreach($battle['invitation_keys'] ?? [] as $hash=>$invitation){
                if(!array_key_exists($hash,$battle['invites']))continue;
                $cid=$battle['invites'][$hash];
                $state['battle']['invitations'][]=$invitation+['accepted'=>$cid!==null,'class_name'=>$cid!==null?($battle['classes'][$cid]['name'] ?? null):null];
            }
        }
        $state['pin']=$battle['classes'][$mine]['pin'] ?? $room['pin'];
        if(isset($state['lobby_players'])){
            $state['lobby_players']=array_values(array_filter($state['lobby_players'],fn($p)=>($battle['members'][$p['id']] ?? null)===$mine));
            $state['roster']=array_column($state['lobby_players'],'nickname');
        }
        if($class!==null)$state['can_switch_quiz']=false;
    }
    return $state;
}
function lq_battle_state(PDO $db,string $room,string $key): array {
    return lq_transaction($db,function()use($db,$room,$key){
        $r=lq_room($db,$room,true);$class=lq_battle_class(json_decode($r['content'],true,32,JSON_THROW_ON_ERROR),$key);
        $r=lq_advance_locked($db,$r);
        return lq_state_payload($db,$r,null,true,$class);
    });
}

// Called under the room transaction. Track selection is persisted once per run/phase.
function lq_battle_music(PDO $db,array $room,array $content): ?array {
    if(!in_array($room['phase'],['lobby','question'],true))return null;
    $phase=$room['phase'];$key=($content['_run'] ?? 0).':'.$phase.':'.($phase==='lobby'?-1:$room['question_index']);
    if(($content['_battle']['music']['key'] ?? null)===$key)return $content['_battle']['music'];
    $public=defined('LQ_MUSIC_PUBLIC_DIR')?LQ_MUSIC_PUBLIC_DIR:dirname(__DIR__,2).'/public';
    require_once $public.'/music-catalog.php';
    $folder=$phase==='lobby'?'lobby_music':'music';
    $tracks=lq_music_tracks($public.'/'.$folder,$folder);
    $start=$phase==='question'?lq_deadline($room)-$content['questions'][(int)$room['question_index']]['seconds']:microtime(true);
    $music=['key'=>$key,'phase'=>$phase,'track'=>$tracks?$tracks[random_int(0,count($tracks)-1)]:null,'started_at'=>$start];
    $content['_battle']['music']=$music;
    // Music does not change gameplay version or invalidate host control requests.
    lq_query($db,'UPDATE lq_rooms SET content=? WHERE id=?',[json_encode($content,JSON_THROW_ON_ERROR),$room['id']]);
    return $music;
}
