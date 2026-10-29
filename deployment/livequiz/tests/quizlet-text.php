<?php
require __DIR__.'/quizlet.php';
$text=array_replace($typed,['accepted'=>['Right left','0.25'],'image'=>['id'=>$img,'alt'=>'']]);
foreach([[$text,$text],[$q,$multi,$text]] as $questions){
 $saved=lq_save($db,1,['content'=>['title'=>'Typed team','questions'=>$questions]]);$room=lq_create_room($db,1,$saved['id']);$id=$room['room'];
 qc($db,$id,'configure',$settings);$tokens=[];
 for($i=0;$i<6;$i++){$t=bin2hex(random_bytes(32));lq_join($db,$room['pin'],'P'.$i,$t);$tokens[lq_player($db,$id,$t)['id']]=$t;}
 qc($db,$id,'next');qc($db,$id,'next');lq_query($db,'UPDATE lq_rooms SET deadline=1 WHERE id=?',[$id]);lq_state($db,$id,1,'',true);
 $entry=reset(contentOf($db,$id)['_race']['entries']);$key=$entry['id'];$failed=false;$texts=0;
 while(true){
  $content=contentOf($db,$id);$entry=$content['_race']['entries'][$key];if($entry['completed'])break;
  $index=$entry['order'][$entry['progress']];$current=$content['questions'][$index];
  $input=['room'=>$id,'run'=>0,'index'=>$index,'attempt'=>$entry['attempt'],'race_revision'=>$entry['revision']];
  if($current['type']==='text'){
   foreach($entry['members'] as $m){
    $s=lq_state($db,$id,0,$tokens[$m['id']],false);
    check($s['can_answer']&&$s['question']['type']==='text'&&$s['index']===$index,'all teammates get same text question');
    check(!isset($s['question']['accepted'])&&!isset($s['question']['correct']),'accepted text answers stay hidden');
    check(lq_room_media($db,$id,0,$tokens[$m['id']],false,$img)['bytes']==='PNG','text image available to every teammate');
   }
   check($entry['choices']===[]&&$entry['confirmed']===[],'text questions clear choice state');
   $member=$entry['members'][1]; // Not the rotating starting player.
   $wrong=!$failed;$answer=$wrong?'wrong':($texts%2?'0,25':' R I G H T  lEfT ');
   $reply=lq_race_answer($db,$input+['answer'=>$answer],$tokens[$member['id']]);
   check($reply['correct']===!$wrong,'reuse text normalization and decimal matching');
   $updated=contentOf($db,$id)['_race']['entries'][$key];
   check($updated['progress']===($wrong?0:$entry['progress']+1),'first text submission resets or advances whole team');
   if($wrong){check($updated['attempt']===$entry['attempt']+1,'wrong text starts new attempt');$failed=true;}else{$texts++;}
   // A simultaneous second submission is stale even if it would have the opposite result.
   foreach($entry['members'] as $m)rejects(fn()=>lq_race_answer($db,$input+['answer'=>$wrong?'rightleft':'wrong'],$tokens[$m['id']]),'stale teammate text cannot change resolved question');
   check(contentOf($db,$id)['_race']['entries'][$key]===$updated,'rejected stale requests leave progress unchanged');
  }else{
   foreach($entry['choices'] as $pid=>$own){$answer=array_keys(array_intersect($own,$current['correct']));if($answer)lq_race_answer($db,$input+['answer'=>$answer],$tokens[$pid]);}
  }
  $other=array_values(array_filter(contentOf($db,$id)['_race']['entries'],fn($e)=>$e['id']!==$key))[0];check($other['progress']===0&&$other['attempt']===0,'other team stays independent');
 }
 check($texts>0&&$failed,'exercised text success and failure');
 check(lq_state($db,$id,1,'',true)['winner']===$key,'text or mixed quiz finishes with team winner');
}
echo "$checks checks including Quizlet-like typed answers passed\n";
