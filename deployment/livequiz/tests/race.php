<?php
require __DIR__.'/core.php';
function raceControl(PDO $db,string $id,string $command,array $extra=[]): void {
    $s=lq_state($db,$id,1,'',true);lq_control($db,1,['room'=>$id,'version'=>$s['version'],'command'=>$command]+$extra);
}
function raceFixture(PDO $db,string $mode,int $size=3,int $n=0): array {
    global $q,$multi,$typed,$img;
    $questions=[$q,$multi,$typed,$q,$multi,$typed];$questions[0]['image']=['id'=>$img,'alt'=>''];
    $quiz=lq_save($db,1,['content'=>['title'=>'Race','scoring'=>'speed','questions'=>$questions]]);
    $room=lq_create_room($db,1,$quiz['id']);$id=$room['room'];
    raceControl($db,$id,'configure',['game'=>'race','mode'=>$mode,'max_team_size'=>$size,'lightning'=>['enabled'=>true,'seconds'=>60]]);
    rejects(fn()=>raceControl($db,$id,'configure',['game'=>'invalid','mode'=>$mode,'max_team_size'=>$size]),'invalid game rejected');
    $tokens=[];
    for($i=0;$i<($n?:$size*2);$i++){$token=bin2hex(random_bytes(32));lq_join($db,$room['pin'],'Player '.$i,$token);$p=lq_player($db,$id,$token);$tokens[$p['id']]=$token;}
    raceControl($db,$id,'next');
    if($mode==='teams'){check(lq_state($db,$id,1,'',true)['state']==='TEAM_OVERVIEW','existing team overview');raceControl($db,$id,'next');}
    $state=lq_state($db,$id,1,'',true);check($state['state']==='RACE_COUNTDOWN','initial synchronized countdown');
    rejects(fn()=>lq_race_answer($db,['room'=>$id],reset($tokens)),'no answers before countdown');
    rejects(fn()=>lq_join($db,$room['pin'],'Late',bin2hex(random_bytes(32))),'late join blocked');
    lq_query($db,'UPDATE lq_rooms SET deadline=? WHERE id=?',[(int)(microtime(true)*1000)-1,$id]);
    check(lq_state($db,$id,1,'',true)['state']==='RACE_ACTIVE','race activates');
    return [$id,$tokens,$room['pin']];
}
function raceContent(PDO $db,string $id): array {return json_decode(lq_room($db,$id)['content'],true);}
function raceInput(PDO $db,string $id,array $entry,bool $correct): array {
    $index=$entry['order'][$entry['progress']];$q=raceContent($db,$id)['questions'][$index];
    return ['room'=>$id,'index'=>$index,'attempt'=>$entry['attempt'],'race_revision'=>$entry['revision'],'answer'=>$q['type']==='text'?($correct?'F I R E':'wrong'):($correct?$q['correct']:[0])];
}
foreach([2,3,4,5] as $size){
 [$id,$tokens,$pin]=raceFixture($db,'teams',$size);
 $content=raceContent($db,$id);$entries=$content['_race']['entries'];$entry=reset($entries);$key=$entry['id'];$other=end($entries);
 $members=$entry['members'];$orders=[];
 check(lq_race_active($entry)['id']===$members[0]['id'],'first attempt starts with first member');
 for($attempt=0;$attempt<=$size;$attempt++){
    $entry=raceContent($db,$id)['_race']['entries'][$key];$orders[]=json_encode($entry['order']);
    check($entry['attempt']===$attempt && $entry['start']===$attempt%$size,'starting position cycles with failures');
    $sorted=$entry['order'];sort($sorted);check($sorted===range(0,5),'question order is a permutation');
    // Fail at different positions, so failing/next player cannot determine next start.
    $steps=$attempt%4;
    for($j=0;$j<$steps;$j++){
        $active=lq_race_active($entry);$token=$tokens[$active['id']];
        check($active['id']===$members[($attempt+$j)%$size]['id'],'correct turns are cyclic');
        $input=raceInput($db,$id,$entry,true);$reply=lq_race_answer($db,$input,$token);
        $entry=raceContent($db,$id)['_race']['entries'][$key];
        check($entry['start']===$attempt%$size && $entry['progress']===$j+1,'correct answers preserve starting index and advance once');
        rejects(fn()=>lq_race_answer($db,$input,$token),'duplicate correct rejected');
        check($reply['state']['race']['revision']===$entry['revision'],'answer returns new state immediately');
    }
    $active=lq_race_active($entry);$token=$tokens[$active['id']];$waiting=$members[($entry['start']+$entry['progress']+1)%$size];
    $input=raceInput($db,$id,$entry,false);
    rejects(fn()=>lq_race_answer($db,$input,$tokens[$waiting['id']]),'inactive teammate cannot submit');
    rejects(fn()=>lq_race_answer($db,array_replace($input,['index'=>99]),$token),'wrong question rejected');
    $state=lq_state($db,$id,0,$token,false);
    check(!isset($state['question']['correct'])&&!isset($state['question']['accepted'])&&!isset($state['question']['youtube']),'answers and video hidden');
    $wait=lq_state($db,$id,0,$tokens[$waiting['id']],false);check(!$wait['can_answer']&&!isset($wait['question']),'inactive teammate waits');
    $reply=lq_race_answer($db,$input,$token);$reset=raceContent($db,$id)['_race']['entries'][$key];
    check(!$reply['correct']&&$reset['progress']===0 && $reset['attempt']===$attempt+1,'incorrect resets all team progress');
    check($reset['start']===($attempt+1)%$size,'reset advances start exactly one');
    rejects(fn()=>lq_race_answer($db,$input,$token),'duplicate incorrect cannot rotate twice');
    check(raceContent($db,$id)['_race']['entries'][$key]===$reset,'duplicate leaves persisted state intact');
    foreach($members as $member){
        lq_join($db,$pin,'Reconnected',$tokens[$member['id']]);
        $s=lq_state($db,$id,0,$tokens[$member['id']],false);$again=lq_state($db,$id,0,$tokens[$member['id']],false);
        check($s['race']===$again['race']&&$s['race']['start']===$reset['start'],'refresh/reconnect preserve start and progress');
        check($s['race']['active']['id']===$members[$reset['start']]['id'],'all teammates see same new starter');
    }
    check(raceContent($db,$id)['_race']['entries'][$other['id']]===$other,'other teams unaffected');
 }
 check(count(array_unique($orders))>1,'failed attempts reshuffle question order');
 $entry=raceContent($db,$id)['_race']['entries'][$key];$start=$entry['start'];$seen=[];
 while(!$entry['completed']){
    $active=lq_race_active($entry);$input=raceInput($db,$id,$entry,true);$seen[]=$input['index'];
    $reply=lq_race_answer($db,$input,$tokens[$active['id']]);$entry=raceContent($db,$id)['_race']['entries'][$key];
 }
 check(count(array_unique($seen))===6,'each question answered exactly once in successful attempt');
 check($entry['start']===$start && is_float($entry['completed_at']),'completion records time without rotation');
 check($reply['state']['state']==='RACE_FINISHED'&&$reply['state']['winner']===$key,'first completed team wins');
 rejects(fn()=>lq_race_answer($db,raceInput($db,$id,$other,true),$tokens[lq_race_active($other)['id']]),'later finisher cannot change winner');
 check(raceContent($db,$id)['_race']['winner']===$key,'winner is stable');
 rejects(fn()=>raceControl($db,$id,'reveal'),'no normal reveal transition');
 raceControl($db,$id,'next');$final=lq_state($db,$id,1,'',true);check($final['state']==='QUIZ_FINISHED' && $final['winner']===$key,'host finishes with race outcome');
 rejects(fn()=>raceControl($db,$id,'next'),'finished cannot restart');
}
[$id,$tokens]=raceFixture($db,'individual',2,2);$content=raceContent($db,$id);$entries=$content['_race']['entries'];$entry=reset($entries);$other=end($entries);$token=$tokens[$entry['members'][0]['id']];
$input=raceInput($db,$id,$entry,true);rejects(fn()=>lq_race_answer($db,$input,str_repeat('f',64)),'invalid token rejected');
rejects(fn()=>lq_answer($db,$input,$token),'normal answer endpoint cannot mutate race');
rejects(fn()=>lq_lightning_answer($db,$input,$token),'lightning endpoint cannot mutate race');
for($i=0;$i<2;$i++){$reply=lq_race_answer($db,raceInput($db,$id,$entry,true),$token);$entry=raceContent($db,$id)['_race']['entries'][$entry['id']];check(isset($reply['state']['question']),'individual response immediately contains next question');}
$old=raceInput($db,$id,$entry,false);lq_race_answer($db,$old,$token);$entry=raceContent($db,$id)['_race']['entries'][$entry['id']];
check($entry['progress']===0&&$entry['attempt']===1&&$entry['start']===0,'individual reset');
rejects(fn()=>lq_race_answer($db,$old,$token),'old attempt rejected even if question repeats');
check(raceContent($db,$id)['_race']['entries'][$other['id']]===$other,'individual progress independent');
while(!$entry['completed']){
 $state=lq_state($db,$id,0,$token,false);
 if($state['index']===0){check(lq_room_media($db,$id,0,$token,false,$img)['bytes']==='PNG','active image allowed');rejects(fn()=>lq_room_media($db,$id,0,$token,false,str_repeat('f',32)),'unrelated media denied');}
 lq_race_answer($db,raceInput($db,$id,$entry,true),$token);$entry=raceContent($db,$id)['_race']['entries'][$entry['id']];
}
check((int)lq_query($db,'SELECT COUNT(*) FROM lq_answers WHERE room_id=?',[$id])->fetchColumn()===0,'race does not alter normal or lightning points');
check(!isset(lq_state($db,$id,1,'',true)['question']),'teacher has progress board only');
echo "$checks checks including Quiz Race passed\n";
// Single-question, single-member team, empty-room and guest-host boundaries.
$single=lq_save($db,1,['content'=>['title'=>'One question','questions'=>[$q]]]);
$r=lq_create_room($db,1,$single['id']);raceControl($db,$r['room'],'configure',['game'=>'race','mode'=>'individual','max_team_size'=>2]);
rejects(fn()=>raceControl($db,$r['room'],'next'),'race cannot start empty');check(lq_state($db,$r['room'],1,'',true)['state']==='LOBBY','empty start leaves lobby intact');
raceControl($db,$r['room'],'configure',['game'=>'race','mode'=>'teams','max_team_size'=>2]);
$t=bin2hex(random_bytes(32));lq_join($db,$r['pin'],'Solo',$t);raceControl($db,$r['room'],'next');raceControl($db,$r['room'],'next');lq_query($db,'UPDATE lq_rooms SET deadline=1 WHERE id=?',[$r['room']]);
$s=lq_state($db,$r['room'],0,$t,false);check($s['can_answer'],'singleton team may answer');
$e=lq_race_entry(raceContent($db,$r['room']),lq_player($db,$r['room'],$t)['id']);
$malformed=raceInput($db,$r['room'],$e,true);$malformed['answer']=[];rejects(fn()=>lq_race_answer($db,$malformed,$t),'empty answer rejected without reset');
check(lq_race_entry(raceContent($db,$r['room']),lq_player($db,$r['room'],$t)['id'])===$e,'malformed answer leaves turn unchanged');
$reply=lq_race_answer($db,raceInput($db,$r['room'],$e,true),$t);check($reply['state']['state']==='RACE_FINISHED','single question can win immediately');
$share=lq_share($db,1,$single['id'],true);$hostToken=bin2hex(random_bytes(32));$guest=lq_shared_start($db,$single['id'],$share['key'],$hostToken);
$gs=lq_state($db,$guest['room'],0,'',true,$hostToken);lq_control($db,0,['room'=>$guest['room'],'version'=>$gs['version'],'command'=>'configure','game'=>'race','mode'=>'individual','max_team_size'=>2],$hostToken);
check(lq_state($db,$guest['room'],0,'',true,$hostToken)['game']==='race','account-free host can configure race');
rejects(fn()=>lq_control($db,0,['room'=>$guest['room'],'version'=>2,'command'=>'next']),'guest host token required');
[$many,$manyTokens]=raceFixture($db,'individual',2,30);$orders=array_column(raceContent($db,$many)['_race']['entries'],'order');check(count(array_unique(array_map('json_encode',$orders)))>1,'independent participants receive independent shuffles');
echo "$checks checks including race boundaries passed\n";
