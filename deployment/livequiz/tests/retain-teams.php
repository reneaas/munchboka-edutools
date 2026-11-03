<?php
require __DIR__.'/core.php';
function retainControl(PDO $db,string $id,string $command,array $extra=[]): array {
 $s=lq_state($db,$id,1,'',true);return lq_control($db,1,['room'=>$id,'run'=>$s['run'],'version'=>$s['version'],'command'=>$command]+$extra)['state'];
}
$save=lq_save($db,1,['content'=>['title'=>'Keep teams','questions'=>[$q]]]);$next=lq_save($db,1,['content'=>['title'=>'Another quiz','questions'=>[$q]]]);
$small=lq_save($db,1,['content'=>['title'=>'Two choices','questions'=>[array_replace($q,['options'=>['A','B'],'correct'=>[0]])]]]);
$room=lq_create_room($db,1,$save['id']);$id=$room['room'];$tokens=[];
for($i=0;$i<7;$i++){$tokens[]=bin2hex(random_bytes(32));lq_join($db,$room['pin'],'P'.$i,$tokens[$i]);}
retainControl($db,$id,'configure',['mode'=>'teams','max_team_size'=>4]);$s=retainControl($db,$id,'next');$teams=$s['teams'];check(array_sum(array_map(fn($t)=>count($t['members']),$teams))===7,'initial assignments');
retainControl($db,$id,'finish');$s=retainControl($db,$id,'restart',['keep_teams'=>true]);check($s['teams']===$teams&&$s['keep_teams'],'restart retains exact names IDs and members');
foreach(['race','quizlet','regular'] as $game){
 $s=retainControl($db,$id,'configure',['game'=>$game,'mode'=>'teams','max_team_size'=>4]);check($s['teams']===$teams,'mode change preserves assignments');
}
// Switching to individual and back does not discard the preserved roster.
retainControl($db,$id,'configure',['game'=>'regular','mode'=>'individual','max_team_size'=>4]);
$s=retainControl($db,$id,'configure',['mode'=>'teams','max_team_size'=>4]);check($s['teams']===$teams,'individual toggle retains team snapshot');
retainControl($db,$id,'configure',['mode'=>'teams','max_team_size'=>4,'keep_teams'=>false]);
$s=retainControl($db,$id,'configure',['mode'=>'teams','max_team_size'=>4,'keep_teams'=>true]);check($s['teams']===$teams,'retention can be toggled before starting');
$s=retainControl($db,$id,'next');check($s['teams']===$teams,'start does not reshuffle retained teams');retainControl($db,$id,'finish');
$s=retainControl($db,$id,'switch-quiz',['quiz'=>$next['id'],'keep_teams'=>true]);check($s['teams']===$teams&&$s['title']==='Another quiz'&&$s['mode']==='teams','switch quiz preserves teams');
foreach($tokens as $token){$p=lq_state($db,$id,0,$token,false);check($p['my_team']!==null&&$p['teams']===$teams,'participant sees original team after switch');}
$newToken=bin2hex(random_bytes(32));lq_join($db,$room['pin'],'New player',$newToken);$newId=lq_player($db,$id,$newToken)['id'];
$removed=$teams[0]['members'][0]['id'];retainControl($db,$id,'kick',['player'=>$removed]);
$s=retainControl($db,$id,'next');$updated=$s['teams'];
foreach($teams as $old){$team=array_values(array_filter($updated,fn($t)=>$t['id']===$old['id']))[0];check($team['name']===$old['name'],'team name stable');foreach($old['members'] as $m)if($m['id']!==$removed)check(in_array($m['id'],array_column($team['members'],'id'),true),'existing members never moved');}
$ids=array_merge(...array_map(fn($t)=>array_column($t['members'],'id'),$updated));check(!in_array($removed,$ids,true)&&in_array($newId,$ids,true)&&count($ids)===count(array_unique($ids)),'new player included once and kicked player excluded');
retainControl($db,$id,'finish');retainControl($db,$id,'switch-quiz',['quiz'=>$small['id'],'keep_teams'=>true]);
$before=lq_room($db,$id)['content'];rejects(fn()=>retainControl($db,$id,'configure',['game'=>'quizlet','mode'=>'teams','max_team_size'=>2]),'incompatible retained teams rejected');check(lq_room($db,$id)['content']===$before,'failed mode change leaves teams untouched');
$s=retainControl($db,$id,'configure',['game'=>'quizlet','mode'=>'teams','max_team_size'=>2,'keep_teams'=>false]);$s=retainControl($db,$id,'next');foreach($s['teams'] as $team)check(count($team['members'])<=2,'explicit opt-out allows new teams under new limit');
retainControl($db,$id,'finish');$s=retainControl($db,$id,'restart');check($s['teams']===[]&&!$s['keep_teams'],'ordinary replay still resets teams');
rejects(fn()=>retainControl($db,$id,'configure',['mode'=>'teams','max_team_size'=>3,'keep_teams'=>'yes']),'retention flag requires boolean');
echo "$checks checks including retained teams passed\n";
