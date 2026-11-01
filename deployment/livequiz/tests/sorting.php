<?php
require __DIR__.'/quizlet.php';
$sorting=array_replace($q,['type'=>'sort','prompt'=>'Sorter fra minst til størst','options'=>['Tre','En','To'],'correct'=>[1,2,0],'youtube'=>'']);
$validated=lq_validate($db,1,['title'=>'Sorting','questions'=>[$sorting]])['questions'][0];
check($validated['correct']===[1,2,0],'sorting solution preserves order');
check(lq_grade($validated,[1,2,0])===[[1,2,0],1000],'exact order earns full points');
check(lq_grade($validated,[0,1,2])[1]===0,'same items in wrong order earn no points');
foreach([[1,2],[1,2,2],[1,2,0,0],['1',2,0],[1,2,8],[]] as $bad){
 rejects(fn()=>lq_grade($validated,$bad),'invalid sorting submission rejected');
 rejects(fn()=>lq_validate($db,1,['title'=>'Invalid','questions'=>[array_replace($sorting,['correct'=>$bad])]]),'invalid sorting key rejected');
}
$saved=lq_save($db,1,['content'=>['title'=>'Sorting','questions'=>[$sorting]]]);
$room=lq_create_room($db,1,$saved['id']);$id=$room['room'];$t=bin2hex(random_bytes(32));lq_join($db,$room['pin'],'Sorter',$t);
qc($db,$id,'next');expireInitialCountdown($db,$id);
check(!isset(lq_state($db,$id,0,$t,false)['question']['correct']),'sorting solution hidden before reveal');
lq_answer($db,['room'=>$id,'run'=>0,'index'=>0,'answer'=>[1,2,0]],$t);
check(lq_state($db,$id,0,$t,false)['answer']===[1,2,0],'submitted order survives refresh');
$revealed=lq_state($db,$id,1,'',true);
check($revealed['question']['correct']===[1,2,0]&&$revealed['distribution']['correct']===1,'results preserve solution and count full correct answers');
foreach(['race','quizlet'] as $game){
 $room=lq_create_room($db,1,$saved['id']);$id=$room['room'];qc($db,$id,'configure',['game'=>$game,'mode'=>$game==='quizlet'?'teams':'individual','max_team_size'=>2]);$tokens=[];
 for($i=0;$i<2;$i++){$token=bin2hex(random_bytes(32));lq_join($db,$room['pin'],'Sorter '.$i,$token);$tokens[]=$token;}
 qc($db,$id,'next');if($game==='quizlet')qc($db,$id,'next');lq_query($db,'UPDATE lq_rooms SET deadline=1 WHERE id=?',[$id]);
 $state=lq_state($db,$id,0,$tokens[1],false);
 check($state['question']['options']===$sorting['options']&&!isset($state['question']['correct']),'race/Quizlet participants receive full sorting choices without solution');
 $input=['room'=>$id,'run'=>0,'index'=>0,'attempt'=>$state['race']['attempt'],'race_revision'=>$state['race']['revision']];
 $reply=lq_race_answer($db,$input+['answer'=>[1,2,0]],$tokens[1]);check($reply['correct'],'sorting advances race/Quizlet');
 rejects(fn()=>lq_race_answer($db,$input+['answer'=>[1,2,0]],$tokens[1]),'stale sorting submission rejected');
}
// Sorting also uses exact-order grading in the lightning round.
$room=lq_create_room($db,1,$saved['id']);$id=$room['room'];$token=bin2hex(random_bytes(32));lq_join($db,$room['pin'],'Lightning sorter',$token);
qc($db,$id,'configure',['mode'=>'individual','max_team_size'=>3,'lightning'=>['enabled'=>true,'seconds'=>60]]);
qc($db,$id,'next');lq_query($db,"UPDATE lq_rooms SET phase='leaderboard',question_index=0,deadline=0 WHERE id=?",[$id]);
qc($db,$id,'next');qc($db,$id,'next');lq_query($db,'UPDATE lq_rooms SET deadline=1 WHERE id=?',[$id]);
// Use a recent countdown end so the lightning timer remains open.
lq_query($db,'UPDATE lq_rooms SET deadline=? WHERE id=?',[(int)round(microtime(true)*1000)-10,$id]);
$state=lq_state($db,$id,0,$token,false);check($state['question']['type']==='sort'&&!isset($state['question']['correct']),'lightning exposes sorting without solution');
lq_lightning_answer($db,['room'=>$id,'run'=>0,'index'=>0,'answer'=>[1,2,0]],$token);
check((int)lq_state($db,$id,1,'',true)['leaderboard'][0]['score']===1000,'lightning awards exact sorting points');
echo "$checks checks including sorting passed\n";
