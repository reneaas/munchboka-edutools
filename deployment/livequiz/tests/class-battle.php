<?php
require __DIR__.'/core.php';
function battleControl(PDO $db,string $room,string $command,array $extra=[]):array {
    $state=lq_state($db,$room,1,'',true);
    return lq_control($db,1,['room'=>$room,'run'=>$state['run'],'version'=>$state['version'],'command'=>$command]+$extra);
}
$quiz=lq_save($db,1,['content'=>['title'=>'Three class competition','questions'=>[array_replace($q,['youtube'=>'','seconds'=>60,'image'=>['id'=>$img,'alt'=>'Class image']]),array_replace($q,['youtube'=>'','seconds'=>60])]]]);
$room=lq_create_room($db,1,$quiz['id']);$rid=$room['room'];
battleControl($db,$rid,'configure',['game'=>'classbattle','mode'=>'individual','max_team_size'=>3]);
rejects(fn()=>battleControl($db,$rid,'next'),'cannot start with only one class');
$manage=fn($command,$extra=[])=>lq_battle_manage($db,1,['room'=>$rid,'command'=>$command]+$extra,'','');
$inviteB=$manage('invite')['key'];$inviteC=$manage('invite')['key'];$inviteEmpty=$manage('invite')['key'];
$b=lq_battle_join_host($db,['room'=>$rid,'key'=>$inviteB,'name'=>'Class B']);
$c=lq_battle_join_host($db,['room'=>$rid,'key'=>$inviteC,'name'=>'Class C']);
$empty=lq_battle_join_host($db,['room'=>$rid,'key'=>$inviteEmpty,'name'=>'Empty']);
check(lq_battle_join_host($db,['room'=>$rid,'key'=>$inviteB,'name'=>'Duplicate'])===$b,'invitation replay resumes same class');
rejects(fn()=>battleControl($db,$rid,'next'),'cannot start without students');
$manage('rename',['name'=>'Renamed A']);check(lq_state($db,$rid,1,'',true)['battle']['class_name']==='Renamed A','main class can be named');$manage('rename',['name'=>'Class A']);
$bs=lq_battle_state($db,$rid,$inviteB);$cs=lq_battle_state($db,$rid,$inviteC);
check($bs['pin']!==$cs['pin']&&strlen($bs['pin'])===8,'co-host codes are separate');
rejects(fn()=>lq_battle_join_host($db,['room'=>$rid,'key'=>str_repeat('0',64),'name'=>'Unauthorized']),'invalid invitation rejected');
rejects(fn()=>lq_join($db,$inviteB,'Host link as code',bin2hex(random_bytes(32))),'invitation is not a student code');
rejects(fn()=>lq_state($db,$rid,0,'',true,$inviteB),'co-host key cannot authorize main-host control');
rejects(fn()=>lq_battle_manage($db,0,['room'=>$rid,'command'=>'invite'],'',$inviteB),'co-host cannot invite more hosts');
$tokens=[];$pids=[];
foreach([[$room['pin'],3,'A'],[$bs['pin'],2,'B'],[$cs['pin'],1,'C']] as [$pin,$n,$class]){
 for($i=0;$i<$n;$i++){$token=bin2hex(random_bytes(32));lq_join($db,$pin,$class.$i,$token);$tokens[$class][]=$token;$pids[$class][]=lq_player($db,$rid,$token)['id'];}
}
$foreign=$pids['A'][0];
rejects(fn()=>lq_battle_state($db,$rid,$tokens['A'][0]),'student token grants no co-host privileges');
rejects(fn()=>lq_battle_manage($db,0,['room'=>$rid,'command'=>'kick','player'=>$foreign],'',$inviteB),'co-host cannot kick another class');
rejects(fn()=>lq_join($db,$bs['pin'],'Switch class',$tokens['A'][0]),'student cannot change class');
$extra=bin2hex(random_bytes(32));lq_join($db,$bs['pin'],'Wrong student',$extra);$extraId=lq_player($db,$rid,$extra)['id'];
lq_battle_manage($db,0,['room'=>$rid,'command'=>'kick','player'=>$extraId],'',$inviteB);
rejects(fn()=>lq_join($db,$bs['pin'],'Return after kick',$extra),'kicked participant cannot rejoin');
check(count(lq_battle_state($db,$rid,$inviteB)['lobby_players'])===2,'co-host sees only own roster');
check(count(lq_battle_state($db,$rid,$inviteB)['battle']['results'])===1,'co-host individual results limited to own class');
$leaveKey=$manage('invite')['key'];lq_battle_join_host($db,['room'=>$rid,'key'=>$leaveKey,'name'=>'Leaving class']);
$leavePin=lq_battle_state($db,$rid,$leaveKey)['pin'];$leaveToken=bin2hex(random_bytes(32));lq_join($db,$leavePin,'Leaving student',$leaveToken);
lq_battle_manage($db,0,['room'=>$rid,'command'=>'leave'],'',$leaveKey);
rejects(fn()=>lq_join($db,$leavePin,'Invalid code',bin2hex(random_bytes(32))),'leaving removes class entry code');
rejects(fn()=>lq_player($db,$rid,$leaveToken),'leaving removes class students from roster');
$unused=$manage('invite')['key'];
battleControl($db,$rid,'next');
rejects(fn()=>lq_join($db,$bs['pin'],'Late student',bin2hex(random_bytes(32))),'late join rejected after roster lock');
rejects(fn()=>lq_battle_join_host($db,['room'=>$rid,'key'=>$unused,'name'=>'Late class']),'class registration locked');
rejects(fn()=>lq_battle_manage($db,0,['room'=>$rid,'command'=>'leave'],'',$inviteB),'cannot change denominator by leaving mid-game');
check(lq_join($db,$bs['pin'],'Reconnect',$tokens['B'][0])['room']===$rid,'existing student reconnects with frozen membership');
check(lq_battle_join_host($db,['room'=>$rid,'key'=>$inviteB,'name'=>''])===$b,'co-host invitation reconnects mid-game');
expireInitialCountdown($db,$rid);
$state=lq_battle_state($db,$rid,$inviteB);
check($state['state']==='QUESTION_ACTIVE'&&$state['index']===0,'co-host follows main room');
check(lq_room_media($db,$rid,0,'',true,$img,'',$inviteB)['bytes']==='PNG','co-host can load current classroom image');
rejects(fn()=>lq_room_media($db,$rid,0,'',true,$img,'',str_repeat('0',64)),'invalid co-host cannot load image');
check(!isset($state['question']['correct'])&&!isset($state['question']['accepted']),'co-host cannot see unrevealed answer key');
foreach($tokens as $class=>$list)foreach($list as $i=>$token){
 $correct=($class==='B'||($class==='A'&&$i<2));
 $input=['room'=>$rid,'run'=>0,'index'=>0,'answer'=>$correct?[1]:[0]];
 lq_answer($db,$input,$token);lq_answer($db,$input,$token);
}
$state=lq_state($db,$rid,1,'',true);$rows=$state['battle']['classes'];$byName=array_column($rows,null,'name');
check($byName['Class B']['rank']===1&&$byName['Class B']['score']==1000,'smaller class can win by average');
check(abs($byName['Class A']['score']-2000/3)<1e-10,'fractional means are not rounded internally');
check($byName['Empty']['rank']===null&&$byName['Empty']['score']===null,'empty class is unranked');
check((int)lq_query($db,'SELECT COUNT(*) FROM lq_answers WHERE room_id=?',[$rid])->fetchColumn()===6,'duplicate submissions are idempotent');
check(lq_battle_state($db,$rid,$inviteC)['battle']['classes']===$rows,'all classrooms see identical standings');
check($state['state']==='QUESTION_RESULTS','normal answer completion advances shared state');
battleControl($db,$rid,'leaderboard');battleControl($db,$rid,'next');
lq_query($db,'UPDATE lq_rooms SET deadline=? WHERE id=?',[(int)round((microtime(true)-0.01)*1000),$rid]);
check(lq_state($db,$rid,1,'',true)['index']===1,'all classes advance to second question');
foreach($tokens as $list)foreach($list as $token)lq_answer($db,['room'=>$rid,'run'=>0,'index'=>1,'answer'=>[1]],$token);
battleControl($db,$rid,'leaderboard');battleControl($db,$rid,'next');
check(lq_battle_state($db,$rid,$inviteB)['state']==='QUIZ_FINISHED','shared final state');
// Exact tie and rounding-near-tie checks use real persisted cumulative scores.
lq_query($db,'UPDATE lq_answers SET points=0 WHERE room_id=?',[$rid]);
lq_query($db,'UPDATE lq_answers SET points=1 WHERE room_id=? AND player_id=? AND question_index=0',[$rid,$pids['A'][0]]);
lq_query($db,'UPDATE lq_answers SET points=1 WHERE room_id=? AND player_id=? AND question_index=0',[$rid,$pids['B'][0]]);
$rows=lq_state($db,$rid,1,'',true)['battle']['classes'];$byName=array_column($rows,null,'name');
check($byName['Class B']['rank']<$byName['Class A']['rank'],'ranking uses exact fractions even when rounded display might tie');
lq_query($db,'UPDATE lq_answers SET points=0 WHERE room_id=?',[$rid]);
$rows=lq_state($db,$rid,1,'',true)['battle']['classes'];check(count(array_filter($rows,fn($r)=>$r['rank']===1))===3,'all tied populated classes share rank');
battleControl($db,$rid,'restart');
check(!lq_state($db,$rid,1,'',true)['battle']['locked'],'replay reopens lobby and retains classes');
battleControl($db,$rid,'switch-quiz',['quiz'=>$quiz['id']]);
check(lq_battle_state($db,$rid,$inviteB)['pin']===$bs['pin']&&lq_state($db,$rid,1,'',true)['game']==='classbattle','switch quiz retains class battle and entry codes');
rejects(fn()=>lq_battle_manage($db,0,['room'=>$rid,'command'=>'kick','player'=>$pids['B'][0],'run'=>0],'',$inviteB),'stale lobby action cannot affect a new run');
lq_battle_manage($db,0,['room'=>$rid,'run'=>lq_state($db,$rid,1,'',true)['run'],'command'=>'leave'],'',$inviteEmpty);
rejects(fn()=>lq_battle_state($db,$rid,$inviteEmpty),'leaving revokes co-host capability');
// More than the existing room's 60-player limit, across independently assigned classes.
for($i=0;$i<61;$i++)lq_join($db,$cs['pin'],'Additional '.$i,bin2hex(random_bytes(32)));
check(lq_state($db,$rid,1,'',true)['players']===67,'class battle supports several full classes');
$encoded=json_encode(lq_battle_state($db,$rid,$inviteB));
check(!str_contains($encoded,$inviteB)&&!str_contains($encoded,'host_hash')&&!str_contains($encoded,'invites'),'state never leaks invitation or capability hashes');
lq_query($db,'UPDATE lq_rooms SET expires_at=? WHERE id=?',[time()-1,$rid]);
rejects(fn()=>lq_join($db,$cs['pin'],'Expired',bin2hex(random_bytes(32))),'expired class code rejected');
rejects(fn()=>lq_battle_state($db,$rid,$inviteC),'expired co-host room rejected');
echo "$checks checks including Class Battle passed\n";
