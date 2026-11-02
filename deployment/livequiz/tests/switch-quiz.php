<?php
require __DIR__.'/core.php';
function switchControl(PDO $db,string $id,string $command,array $extra=[]): array {
 $s=lq_state($db,$id,1,'',true);return lq_control($db,1,['room'=>$id,'run'=>$s['run'],'version'=>$s['version'],'command'=>$command]+$extra);
}
$next=lq_save($db,1,['content'=>['title'=>'Next quiz','questions'=>[array_replace($q,['prompt'=>'A new question','image'=>['id'=>$img,'alt'=>'Next image']])]]]);
$foreign=lq_save($db,2,['content'=>['title'=>'Someone else','questions'=>[$q]]]);
foreach(['lobby','finished','race_done','light_done'] as $phase){
 $room=lq_create_room($db,1,$next['id']);$id=$room['room'];$token=bin2hex(random_bytes(32));lq_join($db,$room['pin'],'Same player',$token);$player=lq_player($db,$id,$token);
 $snapshot=json_decode(lq_room($db,$id)['content'],true);$snapshot['title']='Previous quiz';$snapshot['_run']=3;$snapshot['_waiting']=[$player['id']];$snapshot['_finished_at']=1;
 lq_query($db,'UPDATE lq_rooms SET phase=?,content=? WHERE id=?',[$phase,json_encode($snapshot),$id]);
 lq_query($db,'INSERT INTO lq_answers VALUES (?,?,?,?,?)',[$id,$player['id'],0,'[1]',1000]);
 $before=lq_room($db,$id);$input=['room'=>$id,'run'=>3,'version'=>(int)$before['version'],'command'=>'switch-quiz','quiz'=>$next['id']];
 rejects(fn()=>lq_control($db,2,$input),'another user cannot switch room');
 rejects(fn()=>lq_control($db,1,array_replace($input,['quiz'=>$foreign['id']])),'another owners quiz rejected');
 rejects(fn()=>lq_control($db,1,array_replace($input,['quiz'=>str_repeat('f',32)])),'missing target rejected');
 check(lq_room($db,$id)['content']===$before['content'],'failed switches leave game unchanged');
 $reply=lq_control($db,1,$input);$s=$reply['state'];
 check($s['state']==='LOBBY'&&$s['title']==='Next quiz'&&$s['run']===4&&$s['index']===-1,'switch starts fresh lobby with new snapshot');
 check($s['pin']===$room['pin']&&$s['players']===1&&$s['roster']===['Same player'],'PIN and player roster retained including waiting players');
 check($s['game']==='regular'&&$s['mode']==='individual'&&$s['teams']===[]&&!$s['lightning']['enabled'],'new quiz starts with fresh settings');
 check(lq_player($db,$id,$token)['id']===$player['id'],'same player token still works');
 check(lq_state($db,$id,0,$token,false)['state']==='LOBBY','participant automatically returns to lobby');
 check((int)lq_query($db,'SELECT COUNT(*) FROM lq_answers WHERE room_id=?',[$id])->fetchColumn()===0,'old answers and scores cleared');
 rejects(fn()=>lq_control($db,1,$input),'duplicate switch cannot reset twice');
 $latest=lq_state($db,$id,1,'',true);
 rejects(fn()=>lq_control($db,1,array_replace($input,['version'=>$latest['version']])),'stale run cannot switch a newer quiz');
 switchControl($db,$id,'next');expireInitialCountdown($db,$id);
 check(lq_state($db,$id,0,$token,false)['question']['prompt']==='A new question','same player receives new quiz');
 check(lq_room_media($db,$id,0,$token,false,$img)['bytes']==='PNG','new quiz image accessible');
 rejects(fn()=>lq_answer($db,['room'=>$id,'run'=>3,'index'=>0,'answer'=>[1]],$token),'old quiz answer cannot score in new quiz');
 rejects(fn()=>switchControl($db,$id,'switch-quiz',['quiz'=>$next['id']]),'switching active question rejected');
 lq_answer($db,['room'=>$id,'run'=>4,'index'=>0,'answer'=>[1]],$token);
 check(lq_state($db,$id,0,$token,false)['points']===1000,'new quiz can be played with existing token');
}
// Guest host credentials do not grant access to the owner's private library.
$hostKey=bin2hex(random_bytes(32));$snapshot=['title'=>'Guest room','questions'=>[$q],'_host_hash'=>hash('sha256',$hostKey)];
$room=lq_insert_room($db,1,$snapshot);$r=lq_room($db,$room['room']);
check(!lq_state($db,$r['id'],0,'',true,$hostKey)['can_switch_quiz'],'guest host does not get switch UI');
rejects(fn()=>lq_control($db,0,['room'=>$r['id'],'run'=>0,'version'=>1,'command'=>'switch-quiz','quiz'=>$next['id']],$hostKey),'guest host cannot replace owner snapshot');
echo "$checks checks including switching quiz passed\n";
