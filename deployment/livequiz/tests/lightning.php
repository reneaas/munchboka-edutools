<?php
require __DIR__.'/core.php';
function lightningFixture(PDO $db, string $mode='individual', int $n=3, string $scoring='fixed'): array {
    global $q,$multi,$typed;
    $quiz=lq_save($db,1,['content'=>['title'=>'Lightning test','scoring'=>$scoring,'questions'=>[$q,$multi,$typed]]]);
    $room=lq_create_room($db,1,$quiz['id']);$id=$room['room'];
    lq_control($db,1,['room'=>$id,'version'=>1,'command'=>'configure','mode'=>$mode,'max_team_size'=>3,'lightning'=>['enabled'=>true,'seconds'=>60]]);
    $tokens=[];
    for($i=0;$i<$n;$i++){$token=bin2hex(random_bytes(32));lq_join($db,$room['pin'],'P'.$i,$token);$tokens[]=$token;}
    lq_control($db,1,['room'=>$id,'version'=>2,'command'=>'next']);
    // Existing core tests cover normal questions; seed the completed regular round.
    foreach($tokens as $token){$player=lq_player($db,$id,$token);lq_query($db,'INSERT INTO lq_answers VALUES (?,?,?,?,?)',[$id,$player['id'],0,'[1]',1000]);}
    lq_query($db,"UPDATE lq_rooms SET phase='leaderboard',question_index=2,deadline=0 WHERE id=?",[$id]);
    $state=lq_state($db,$id,1,'',true);
    lq_control($db,1,['room'=>$id,'version'=>$state['version'],'command'=>'next']);
    check(lq_state($db,$id,1,'',true)['state']==='LIGHTNING_INTRO','enabled final leaderboard enters intro');
    rejects(fn()=>lq_join($db,$room['pin'],'Late',bin2hex(random_bytes(32))),'new lightning participants rejected');
    $intro=lq_state($db,$id,1,'',true);
    rejects(fn()=>lq_control($db,0,['room'=>$id,'version'=>$intro['version'],'command'=>'next']),'participant cannot start lightning');
    lq_control($db,1,['room'=>$id,'version'=>$intro['version'],'command'=>'next']);
    $count=lq_state($db,$id,1,'',true);check($count['state']==='LIGHTNING_COUNTDOWN'&&!isset($count['question']),'countdown has no question');
    rejects(fn()=>lq_lightning_answer($db,['room'=>$id,'index'=>0,'answer'=>[1]],$tokens[0]),'countdown rejects answers');
    $end=microtime(true)-.2;lq_query($db,'UPDATE lq_rooms SET deadline=? WHERE id=?',[(int)round($end*1000),$id]);
    $active=lq_state($db,$id,1,'',true);
    check(abs($active['deadline']-($end+60))<.002,'lightning timer based on countdown end');
    check($active['state']==='LIGHTNING_ACTIVE'&&!isset($active['question']),'host timer-only state');
    return [$id,$tokens];
}
foreach([null,[],['enabled'=>1,'seconds'=>60],['enabled'=>true,'seconds'=>0],['enabled'=>true,'seconds'=>601],['enabled'=>true,'seconds'=>1.5]] as $bad)rejects(fn()=>lq_validate_lightning($bad),'invalid lightning configuration');
foreach(['individual','teams'] as $mode){
 [$lr,$tokens]=lightningFixture($db,$mode,6,'speed');
 $content=json_decode(lq_room($db,$lr)['content'],true);$orders=$content['_lightning']['orders'];
 check(count($orders)===6,'all eligible players have persisted orders');
 foreach($orders as $order){$sorted=$order;sort($sorted);check($sorted===[0,1,2],'each question occurs once');}
 $teamBefore=$content['play']['teams'];
 $first=lq_state($db,$lr,0,$tokens[0],false);
 check(!isset($first['question']['correct'],$first['question']['accepted'],$first['question']['youtube']),'no answer or video leaked');
 $different=($first['index']+1)%3;
 rejects(fn()=>lq_lightning_answer($db,['room'=>$lr,'index'=>$different,'answer'=>[1]],$tokens[0]),'out-of-order answer rejected');
 foreach($tokens as $position=>$token){
  for($j=0;$j<3;$j++){
   $state=lq_state($db,$lr,0,$token,false);$refresh=lq_state($db,$lr,0,$token,false);
   check($state['index']===$refresh['index']&&$state['deadline']===$refresh['deadline'],'refresh preserves progress and deadline');
   check($state['progress']===$j,'independent progress starts at zero for each player');
   $question=$content['questions'][$state['index']];$answer=$question['type']==='text'?'F I R E':$question['correct'];
   $input=['room'=>$lr,'index'=>$state['index'],'answer'=>$answer];
   $reply=lq_lightning_answer($db,$input,$token);
   check(isset($reply['state']),'submission returns current state immediately');
   if($reply['state']['state']==='LIGHTNING_ACTIVE'){
    check($reply['state']['progress']===$j+1,'submission immediately advances one question');
    $retry=lq_lightning_answer($db,array_replace($input,['answer'=>[]]),$token);
    check($retry['state']['progress']===$j+1,'duplicate answer cannot advance twice');
   }
  }
  if($position===0){check($reply['state']['completed']===true&&!isset($reply['state']['question']),'completed player waits');check(lq_state($db,$lr,0,$tokens[1],false)['progress']===0,'other player remains at first question');}
 }
 $final=lq_state($db,$lr,1,'',true);check($final['state']==='LIGHTNING_FINISHED','everyone done ends round');
 check($final['teams']===$teamBefore,'team assignments unchanged');
 foreach($final['leaderboard'] as $row)check((int)$row['score']===($mode==='teams'?12000:4000),'normal and fixed lightning points accumulated');
 rejects(fn()=>lq_lightning_answer($db,['room'=>$lr,'index'=>0,'answer'=>[1]],$tokens[0]),'finished rejects answers');
 lq_control($db,1,['room'=>$lr,'version'=>$final['version'],'command'=>'next']);check(lq_state($db,$lr,1,'',true)['state']==='QUIZ_FINISHED','teacher finishes lightning leaderboard');
}
[$lr,$tokens]=lightningFixture($db);
$before=lq_state($db,$lr,0,$tokens[0],false);
lq_query($db,'UPDATE lq_rooms SET deadline=? WHERE id=?',[(int)floor(microtime(true)*1000)-1,$lr]);
rejects(fn()=>lq_lightning_answer($db,['room'=>$lr,'index'=>$before['index'],'answer'=>[1]],$tokens[0]),'late answer rejected');
check(lq_room($db,$lr)['phase']==='light_done','late submission persists end transition');
check((int)lq_query($db,'SELECT COUNT(*) FROM lq_answers WHERE room_id=? AND question_index<0',[$lr])->fetchColumn()===0,'late submission awards no points');
// Orders are sampled independently; check a larger population to avoid flaky pairwise comparisons.
[$lr,$tokens]=lightningFixture($db,'individual',30);
$orders=json_decode(lq_room($db,$lr)['content'],true)['_lightning']['orders'];
check(count(array_unique(array_map('json_encode',array_values($orders))))>1,'independent random orders across participants');
echo "$checks checks including Lightning Round passed\n";
