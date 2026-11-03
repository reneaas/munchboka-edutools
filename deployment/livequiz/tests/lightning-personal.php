<?php
require __DIR__.'/lightning.php';
foreach(['individual','teams'] as $mode){
 [$id,$tokens]=lightningFixture($db,$mode,3);
 foreach($tokens as $token)check(!isset(lq_state($db,$id,0,$token,false)['lightning_result']),'personal summary hidden during round');
 $content=json_decode(lq_room($db,$id)['content'],true);
 foreach([[0,true],[0,false],[1,false]] as [$who,$correct]){
  $s=lq_state($db,$id,0,$tokens[$who],false);$q=$content['questions'][$s['index']];
  $answer=$q['type']==='text'?($correct?$q['accepted'][0]:'wrong'):($correct?$q['correct']:[count($q['options'])-1]);
  lq_lightning_answer($db,['room'=>$id,'run'=>0,'index'=>$s['index'],'answer'=>$answer],$tokens[$who]);
 }
 lq_query($db,'UPDATE lq_rooms SET deadline=1 WHERE id=?',[$id]);
 $host=lq_state($db,$id,1,'',true);check($host['state']==='LIGHTNING_FINISHED'&&!isset($host['lightning_result']),'host receives no personal summary');
 $expected=[['correct'=>1,'answered'=>2,'total'=>3,'wrong'=>1,'unanswered'=>1],['correct'=>0,'answered'=>1,'total'=>3,'wrong'=>1,'unanswered'=>2],['correct'=>0,'answered'=>0,'total'=>3,'wrong'=>0,'unanswered'=>3]];
 foreach($tokens as $i=>$token){$s=lq_state($db,$id,0,$token,false);check($s['lightning_result']===$expected[$i],'only own correct/wrong/unanswered counts, excluding regular-round scores');check(lq_state($db,$id,0,$token,false)['lightning_result']===$expected[$i],'refresh retains summary');}
 lq_control($db,1,['room'=>$id,'run'=>0,'version'=>$host['version'],'command'=>'next']);
 foreach($tokens as $i=>$token)check(lq_state($db,$id,0,$token,false)['lightning_result']===$expected[$i],'private summary retained after final results');
 $finished=lq_state($db,$id,1,'',true);check(!isset($finished['lightning_result']),'no host summary in final results');
 lq_control($db,1,['room'=>$id,'run'=>0,'version'=>$finished['version'],'command'=>'restart']);
 check(!isset(lq_state($db,$id,0,$tokens[0],false)['lightning_result']),'replay removes previous summary');
}
echo "$checks checks including private lightning results passed\n";
