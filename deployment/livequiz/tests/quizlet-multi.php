<?php
require __DIR__.'/quizlet.php';
foreach([2,3,4] as $size){
 $mq=array_replace($q,['type'=>'multi','options'=>['A','B','C','D','E','F'],'correct'=>[0,1,2,3]]);
 $saved=lq_save($db,1,['content'=>['title'=>'Multi team','questions'=>[$mq,$mq]]]);$room=lq_create_room($db,1,$saved['id']);$id=$room['room'];
 qc($db,$id,'configure',['game'=>'quizlet','mode'=>'teams','max_team_size'=>$size]);$tokens=[];
 for($i=0;$i<$size;$i++){$t=bin2hex(random_bytes(32));lq_join($db,$room['pin'],'P'.$i,$t);$tokens[lq_player($db,$id,$t)['id']]=$t;}
 qc($db,$id,'next');qc($db,$id,'next');lq_query($db,'UPDATE lq_rooms SET deadline=1 WHERE id=?',[$id]);lq_state($db,$id,1,'',true);
 $entry=reset(contentOf($db,$id)['_race']['entries']);$key=$entry['id'];
 $entryOf=fn()=>contentOf($db,$id)['_race']['entries'][$key];
 $inputOf=fn($e,$a)=>['room'=>$id,'run'=>0,'index'=>$e['order'][$e['progress']],'attempt'=>$e['attempt'],'race_revision'=>$e['revision'],'answer'=>$a];
 // Correct alternatives are spread across teammates, while local ordering stays random.
 $holders=0;foreach($entry['choices'] as $own)if(array_intersect($own,$mq['correct']))$holders++;
 check($holders===min(4,$size),'correct choices spread across multiple members');
 $pid=array_key_first($entry['choices']);$local=array_key_first(array_intersect($entry['choices'][$pid],$mq['correct']));$input=$inputOf($entry,[$local]);
 $reply=lq_race_answer($db,$input,$tokens[$pid]);$partial=$entryOf();
 check($reply['correct']&&$partial['progress']===0&&count($partial['confirmed'])===1,'partial correct answer does not advance');
 check($partial['revision']===$entry['revision']&&$partial['choices']===$entry['choices'],'partial answer keeps question revision and distribution');
 check($reply['state']['confirmed']===[$local],'only own confirmed local choice returned');
 rejects(fn()=>lq_race_answer($db,$input,$tokens[$pid]),'repeated partial choice rejected');
 check($entryOf()===$partial,'duplicate partial submission changes nothing');
 // Wrong response after partial progress resets everything.
 foreach($entry['choices'] as $wrongPid=>$own){$wrong=array_diff($own,$mq['correct']);if($wrong)break;}
 $reply=lq_race_answer($db,$inputOf($entry,[array_key_first($wrong)]),$tokens[$wrongPid]);
 $reset=$entryOf();check(!$reply['correct']&&$reset['confirmed']===[]&&$reset['attempt']===1&&$reset['progress']===0,'wrong answer clears collected choices and resets');
 rejects(fn()=>lq_race_answer($db,$input,$tokens[$pid]),'old attempt cannot contribute after reset');
 // All teammates use the same initial revision, just as simultaneous requests do.
 for($question=0;$question<2;$question++){
  $entry=$entryOf();$completed=0;
  foreach($entry['choices'] as $pid=>$own){
   $correct=array_keys(array_intersect($own,$mq['correct']));if(!$correct)continue;
   $reply=lq_race_answer($db,$inputOf($entry,$correct),$tokens[$pid]);$completed+=count($correct);
   check($reply['correct'],'member can submit several assigned correct choices at once');
   $current=$entryOf();check($current['progress']===($completed===4?$question+1:$question),'advance exactly once only after all correct choices');
   if($completed<4){
    $s=lq_state($db,$id,0,$tokens[$pid],false);check($s['confirmed']===$correct,'refresh preserves own confirmations');
    check($current['choices']===$entry['choices'],'teammate submissions do not reshuffle remaining alternatives');
   }
  }
  rejects(fn()=>lq_race_answer($db,$inputOf($entry,$correct),$tokens[$pid]),'stale final submission cannot advance next question');
 }
 check($reply['state']['state']==='RACE_FINISHED','all multiple-answer questions completed');
}
echo "$checks checks including Quizlet-like multi-answer collaboration passed\n";
