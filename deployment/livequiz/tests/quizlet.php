<?php
require __DIR__.'/core.php';
function qc(PDO $db,string $id,string $command,array $extra=[]): void {
    $s=lq_state($db,$id,1,'',true);lq_control($db,1,['room'=>$id,'run'=>$s['run'],'version'=>$s['version'],'command'=>$command]+$extra);
}
function contentOf(PDO $db,string $id): array {return json_decode(lq_room($db,$id)['content'],true);}
$questions=[array_replace($q,['image'=>['id'=>$img,'alt'=>'']]),$q,$q];
$base=['title'=>'Quizlet-like','questions'=>$questions];
$settings=['game'=>'quizlet','mode'=>'teams','max_team_size'=>3];
rejects(fn()=>lq_configure_content($base,array_replace($settings,['mode'=>'individual'])),'teams required');
rejects(fn()=>lq_configure_content($base,array_replace($settings,['max_team_size'=>5])),'no member without choices');
foreach([$multi,$typed] as $bad)rejects(fn()=>lq_configure_content(['questions'=>[$bad]],$settings),'only single answer questions');
foreach([2,3,4] as $size){
 $saved=lq_save($db,1,['content'=>$base]);$room=lq_create_room($db,1,$saved['id']);$id=$room['room'];
 qc($db,$id,'configure',array_replace($settings,['max_team_size'=>$size]));$tokens=[];
 for($i=0;$i<$size*2;$i++){$t=bin2hex(random_bytes(32));lq_join($db,$room['pin'],'P'.$i,$t);$tokens[lq_player($db,$id,$t)['id']]=$t;}
 qc($db,$id,'next');qc($db,$id,'next');
 lq_query($db,'UPDATE lq_rooms SET deadline=1 WHERE id=?',[$id]);lq_state($db,$id,1,'',true);
 $content=contentOf($db,$id);$teams=$content['play']['teams'];$entry=reset($content['_race']['entries']);$key=$entry['id'];
 $late=bin2hex(random_bytes(32));lq_join($db,$room['pin'],'Late',$late);check(lq_state($db,$id,0,$late,false)['state']==='WAITING_LOBBY','late players wait');
 for($turn=0;$turn<5;$turn++){
  $content=contentOf($db,$id);$entry=$content['_race']['entries'][$key];$index=$entry['order'][$entry['progress']];
  $seen=[];$correctPlayer=null;$wrongPlayer=null;
  foreach($entry['members'] as $m){
   $t=$tokens[$m['id']];$s=lq_state($db,$id,0,$t,false);$own=$entry['choices'][$m['id']];$seen=array_merge($seen,$own);
   check($s['can_answer']&&$s['index']===$index,'all team members see same question and can answer');
   check(count($own)>=1&&count($own)<=ceil(4/$size),'balanced nonempty choices');
   check($s['question']['options']===array_map(fn($i)=>$questions[$index]['options'][$i],$own),'only own alternatives in payload');
   check(!isset($s['question']['correct'])&&!isset($s['question']['youtube'])&&!isset($s['race']['choices']),'no solution or other assignments leak');
   check($s['question']===lq_state($db,$id,0,$t,false)['question'],'polling does not reshuffle');
   if($index===0)check(lq_room_media($db,$id,0,$t,false,$img)['bytes']==='PNG','all members can view question image');
   $input=['room'=>$id,'run'=>$s['run'],'attempt'=>$entry['attempt'],'race_revision'=>$entry['revision'],'index'=>$index];
   rejects(fn()=>lq_race_answer($db,$input+['answer'=>[count($own)]],$t),'unassigned index rejected');
   foreach($own as $local=>$global){if($global===1){$correctPlayer=[$t,$local];}else{$wrongPlayer=[$t,$local];}}
  }
  sort($seen);check($seen===[0,1,2,3],'every choice assigned exactly once');
  $wrong=$turn%2===1;[$t,$local]=$wrong?$wrongPlayer:$correctPlayer;
  $input['answer']=[$local];$reply=lq_race_answer($db,$input,$t);
  check($reply['correct']===!$wrong,'local selection mapped correctly');
  check($reply['state']['progress']===($wrong?0:$entry['progress']+1),'shared advance or reset');
  rejects(fn()=>lq_race_answer($db,$input,$t),'duplicate answer rejected');
  foreach($entry['members'] as $m)rejects(fn()=>lq_race_answer($db,$input,$tokens[$m['id']]),'concurrent teammate stale answer rejected');
  $other=array_values(array_filter(contentOf($db,$id)['_race']['entries'],fn($e)=>$e['id']!==$key))[0];check($other['progress']===0&&$other['attempt']===0,'other team progresses independently');
 }
 while(true){
  $content=contentOf($db,$id);$entry=$content['_race']['entries'][$key];if($entry['completed'])break;
  foreach($entry['choices'] as $pid=>$choices)if(in_array(1,$choices,true)){
   $reply=lq_race_answer($db,['room'=>$id,'index'=>$entry['order'][$entry['progress']],'attempt'=>$entry['attempt'],'race_revision'=>$entry['revision'],'answer'=>[array_search(1,$choices,true)]],$tokens[$pid]);break;
  }
 }
 check($reply['state']['state']==='RACE_FINISHED'&&$reply['state']['winner']===$key,'first completed team wins');
 check(contentOf($db,$id)['play']['teams']===$teams,'teams unchanged throughout game');
 qc($db,$id,'restart');$s=lq_state($db,$id,1,'',true);check($s['state']==='LOBBY'&&$s['game']==='quizlet','same lobby can replay');
 qc($db,$id,'configure',['game'=>'regular','mode'=>'individual','max_team_size'=>3]);qc($db,$id,'next');check(lq_state($db,$id,1,'',true)['state']==='COUNTDOWN','switch back to regular works');
}
echo "$checks checks including Quizlet-like passed\n";
