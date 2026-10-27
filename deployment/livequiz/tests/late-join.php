<?php
require __DIR__.'/core.php';
function lateControl(PDO $db,string $id,string $command,array $extra=[]): array {
 $s=lq_state($db,$id,1,'',true);return lq_control($db,1,['room'=>$id,'version'=>$s['version'],'run'=>$s['run'],'command'=>$command]+$extra)['state'];
}
foreach(['regular','lightning','race'] as $kind)foreach(['individual','teams'] as $mode){
 $quiz=lq_save($db,1,['content'=>['title'=>'Late arrivals','questions'=>[$q]]]);$room=lq_create_room($db,1,$quiz['id']);$rid=$room['room'];$tokens=[];
 for($i=0;$i<2;$i++){$tokens[]=bin2hex(random_bytes(32));lq_join($db,$room['pin'],'P'.$i,$tokens[$i]);}
 lateControl($db,$rid,'next',['settings'=>['game'=>$kind==='race'?'race':'regular','mode'=>$mode,'max_team_size'=>2,'lightning'=>['enabled'=>$kind==='lightning','seconds'=>60]]]);
 if($mode==='teams')lateControl($db,$rid,'next');
 if($kind==='lightning'){lq_query($db,"UPDATE lq_rooms SET phase='light_intro' WHERE id=?",[$rid]);lateControl($db,$rid,'next');}
 lq_query($db,'UPDATE lq_rooms SET deadline=? WHERE id=?',[(int)(microtime(true)*1000)-1,$rid]);
 $before=lq_state($db,$rid,1,'',true);$content=json_decode(lq_room($db,$rid)['content'],true);
 $late=bin2hex(random_bytes(32));lq_join($db,$room['pin'],'Late',$late);lq_join($db,$room['pin'],'Same person',$late);
 $after=lq_state($db,$rid,1,'',true);$state=lq_state($db,$rid,0,$late,false);
 check((int)lq_query($db,'SELECT COUNT(*) FROM lq_players WHERE room_id=?',[$rid])->fetchColumn()===3,'retry does not duplicate late entrant');
 check($after['deadline']===$before['deadline'],'joining never extends timer');check($after['teams']===$before['teams'],'joining never changes existing teams');
 if($mode==='teams'){
  check($state['state']==='WAITING_LOBBY'&&!isset($state['question']),'team arrival waits without question');check($after['players']===2&&$after['waiting_count']===1,'waiting player excluded from eligible counts');
  $input=['room'=>$rid,'index'=>0,'answer'=>[1],'run'=>0];
  rejects(fn()=>lq_answer($db,$input,$late),'waiting normal answer denied');rejects(fn()=>lq_lightning_answer($db,$input,$late),'waiting lightning answer denied');rejects(fn()=>lq_race_answer($db,$input,$late),'waiting race answer denied');
 }else{
  check($state['state']===$before['state']&&isset($state['question']),'individual arrival gets current question');check($after['players']===3&&$after['waiting_count']===0,'individual entrant participates immediately');
  if($kind==='race')check($state['progress']===0&&$state['race']['attempt']===0,'late racer starts new independent attempt');
  if($kind==='lightning')check($state['progress']===0,'late lightning player starts their own order');
  $tokens[]=$late;
 }
 foreach($tokens as $token){
  $s=lq_state($db,$rid,0,$token,false);$input=['room'=>$rid,'run'=>0,'index'=>0,'answer'=>[1]];
  if($kind==='race'){
   if($s['state']==='RACE_FINISHED'||!$s['can_answer'])continue;
   lq_race_answer($db,$input+['attempt'=>$s['race']['attempt'],'race_revision'=>$s['race']['revision']],$token);
  }elseif($kind==='lightning')lq_lightning_answer($db,$input,$token);
  else lq_answer($db,$input,$token);
 }
 $end=lq_state($db,$rid,1,'',true);check($end['state']===match($kind){'race'=>'RACE_FINISHED','lightning'=>'LIGHTNING_FINISHED',default=>'QUESTION_RESULTS'},'eligible completions finish without waiting entrant');
 if($kind==='regular'){lateControl($db,$rid,'leaderboard');lateControl($db,$rid,'next');}
 // Joining an ended game waits rather than changing the recorded results.
 $finishedLate=bin2hex(random_bytes(32));lq_join($db,$room['pin'],'After finish',$finishedLate);check(lq_state($db,$rid,0,$finishedLate,false)['state']==='WAITING_LOBBY','finished game arrivals wait');
 lateControl($db,$rid,'restart');$lobby=lq_state($db,$rid,1,'',true);check($lobby['players']===4&&$lobby['waiting_count']===0,'replay admits all waiting players');
 check(lq_state($db,$rid,0,$late,false)['state']==='LOBBY','late participant automatically returns to normal lobby');
 if($mode==='teams'){$teams=lateControl($db,$rid,'next')['teams'];$members=array_merge(...array_column($teams,'members'));check(in_array(lq_player($db,$rid,$late)['id'],array_column($members,'id'),true),'late entrant included in next team allocation');}
}
echo "$checks checks including late arrivals passed\n";
