<?php
require __DIR__.'/core.php';
function replayControl(PDO $db,string $id,string $command,array $extra=[]): void {
 $s=lq_state($db,$id,1,'',true);lq_control($db,1,['room'=>$id,'version'=>$s['version'],'command'=>$command]+$extra);
}
function replayActivate(PDO $db,string $id): void {
 $s=lq_state($db,$id,1,'',true);
 if($s['state']==='LOBBY')replayControl($db,$id,'next');
 $s=lq_state($db,$id,1,'',true);
 if($s['state']==='TEAM_OVERVIEW')replayControl($db,$id,'next');
 lq_query($db,'UPDATE lq_rooms SET deadline=? WHERE id=?',[(int)(microtime(true)*1000)-1,$id]);
 lq_state($db,$id,1,'',true);
}
function replayComplete(PDO $db,string $id,array $tokens,array $old=[]): array {
 $s=lq_state($db,$id,1,'',true);$inputs=[];
 if($s['game']==='race'){
  foreach($tokens as $token){$p=lq_state($db,$id,0,$token,false);if(!$p['can_answer'])continue;
   $input=['room'=>$id,'run'=>$p['run'],'index'=>$p['index'],'attempt'=>$p['race']['attempt'],'race_revision'=>$p['race']['revision'],'answer'=>[1]];
   if($old)rejects(fn()=>lq_race_answer($db,$old[0][1],$old[0][0]),'previous race cannot answer new attempt');
   lq_race_answer($db,$input,$token);$inputs[]=[$token,$input];break;
  }
 }else{
  foreach($tokens as $token){$p=lq_state($db,$id,0,$token,false);$input=['room'=>$id,'run'=>$p['run'],'index'=>0,'answer'=>[1]];
   if($old)rejects(fn()=>lq_answer($db,$old[0][1],$old[0][0]),'previous normal answer rejected');
   lq_answer($db,$input,$token);$inputs[]=[$token,$input];
  }
  replayControl($db,$id,'leaderboard');replayControl($db,$id,'next');
  if(lq_state($db,$id,1,'',true)['state']==='LIGHTNING_INTRO'){
   replayControl($db,$id,'next');replayActivate($db,$id);
   foreach($tokens as $token){$p=lq_state($db,$id,0,$token,false);$input=['room'=>$id,'run'=>$p['run'],'index'=>0,'answer'=>[1]];
    if($old)rejects(fn()=>lq_lightning_answer($db,$old[0][1],$old[0][0]),'previous lightning answer rejected');
    lq_lightning_answer($db,$input,$token);
   }
  }
 }
 return $inputs;
}
foreach(['regular','lightning','race'] as $kind)foreach(['individual','teams'] as $mode){
 $quiz=lq_save($db,1,['content'=>['title'=>'Replay','questions'=>[$q]]]);$r=lq_create_room($db,1,$quiz['id']);$id=$r['room'];
 replayControl($db,$id,'configure',['game'=>$kind==='race'?'race':'regular','mode'=>$mode,'max_team_size'=>2,'lightning'=>['enabled'=>$kind==='lightning','seconds'=>60]]);
 $tokens=[bin2hex(random_bytes(32)),bin2hex(random_bytes(32))];foreach($tokens as $i=>$t)lq_join($db,$r['pin'],'P'.$i,$t);
 $players=lq_query($db,'SELECT * FROM lq_players WHERE room_id=? ORDER BY id',[$id])->fetchAll();
 rejects(fn()=>replayControl($db,$id,'restart'),'cannot restart lobby');replayActivate($db,$id);
 rejects(fn()=>replayControl($db,$id,'restart'),'cannot restart active game');
 $old=replayComplete($db,$id,$tokens);$end=lq_state($db,$id,1,'',true);$oldControl=['room'=>$id,'version'=>$end['version'],'command'=>'restart'];
 rejects(fn()=>lq_control($db,0,$oldControl),'only host may restart');
 lq_control($db,1,$oldControl);rejects(fn()=>lq_control($db,1,$oldControl),'duplicate restart rejected');
 $lobby=lq_state($db,$id,1,'',true);check($lobby['state']==='LOBBY'&&$lobby['run']===1&&$lobby['index']===-1&&$lobby['deadline']===0,'fresh lobby run');
 check($lobby['pin']===$r['pin']&&$lobby['mode']===$mode&&$lobby['max_team_size']===2,'PIN and settings retained');
 check($lobby['lightning']['enabled']===($kind==='lightning'),'lightning preference retained');
 check($lobby['teams']===[],'previous team assignments cleared');
 check(lq_query($db,'SELECT * FROM lq_players WHERE room_id=? ORDER BY id',[$id])->fetchAll()===$players,'same roster and tokens retained');
 $content=json_decode(lq_room($db,$id)['content'],true);check(!isset($content['_race'],$content['_lightning']),'race and lightning state cleared');
 check((int)lq_query($db,'SELECT COUNT(*) FROM lq_answers WHERE room_id=?',[$id])->fetchColumn()===0,'all previous answers and points cleared');
 foreach($tokens as $t){check(lq_state($db,$id,0,$t,false)['state']==='LOBBY','old player token enters lobby');check(lq_join($db,$r['pin'],'Existing',$t)['room']===$id,'existing player reconnects');}
 replayActivate($db,$id);replayComplete($db,$id,$tokens,$old);
 // Return through the final screen as well, then switch to the other variant/mode.
 if(lq_state($db,$id,1,'',true)['state']!=='QUIZ_FINISHED')replayControl($db,$id,'next');
 replayControl($db,$id,'restart');check(lq_state($db,$id,1,'',true)['run']===2,'repeated replay increments run');
 replayControl($db,$id,'configure',['game'=>$kind==='race'?'regular':'race','mode'=>$mode==='teams'?'individual':'teams','max_team_size'=>2,'lightning'=>['enabled'=>false,'seconds'=>60]]);
 replayActivate($db,$id);replayComplete($db,$id,$tokens);
 check(lq_query($db,'SELECT * FROM lq_players WHERE room_id=? ORDER BY id',[$id])->fetchAll()===$players,'mode switch retains players');
}
$share=lq_share($db,1,$quiz['id'],true);$hostToken=bin2hex(random_bytes(32));$r=lq_shared_start($db,$quiz['id'],$share['key'],$hostToken);
lq_control($db,0,['room'=>$r['room'],'version'=>1,'command'=>'finish'],$hostToken);
lq_control($db,0,['room'=>$r['room'],'version'=>2,'command'=>'restart'],$hostToken);
check(lq_state($db,$r['room'],0,'',true,$hostToken)['state']==='LOBBY','shared host credential survives replay');
echo "$checks checks including replay passed\n";
