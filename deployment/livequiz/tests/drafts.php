<?php
require __DIR__.'/core.php';
$complete = ['type'=>'single','prompt'=>'Ready','code'=>'','youtube'=>'','image'=>null,'seconds'=>30,'options'=>['Yes','No'],'correct'=>[0],'accepted'=>[]];
$drafts = [
    array_replace($complete,['prompt'=>'']),
    array_replace($complete,['options'=>['Partly written','']]),
    array_replace($complete,['correct'=>[]]),
    array_replace($complete,['type'=>'single','correct'=>[0,1]]),
    array_replace($complete,['type'=>'multi','correct'=>[]]),
    array_replace($complete,['type'=>'text','accepted'=>[]]),
    array_replace($complete,['type'=>'text','accepted'=>['Answer','']]),
    array_replace($complete,['type'=>'sort','correct'=>[1]]),
    array_replace($complete,['type'=>'sort','correct'=>[0,0]]),
    array_replace($complete,['youtube'=>'https://youtu.be/partial']),
    array_replace($complete,['seconds'=>0]),
    array_replace($complete,['seconds'=>null]),
    array_replace($complete,['seconds'=>5.5]),
];
foreach ($drafts as $i=>$question) {
    $normalized=lq_validate($db,1,['title'=>'Draft','questions'=>[$question]],true);
    check(!lq_question_ready($normalized['questions'][0]),'incomplete question skipped '.$i);
}
$questions=[$drafts[0],$complete,...array_slice($drafts,1),array_replace($complete,['type'=>'text','prompt'=>'Last ready','accepted'=>['Answer']])];
$savedDraft=lq_save($db,1,['content'=>['title'=>'Draft coverage','questions'=>$questions]]);
$draftId=$savedDraft['id'];
$stored=json_decode(lq_quiz($db,1,$draftId)['content'],true);
check(count($stored['questions'])===count($questions),'save retains all drafts');
check($stored['questions'][10]['youtube']==='https://youtu.be/partial','partial URL retained');
check($stored['questions'][12]['seconds']===null,'unfinished timer retained');
check(lq_save($db,1,['id'=>$draftId,'revision'=>0,'content'=>['title'=>'Draft coverage','questions'=>$questions]])===$savedDraft,'draft save replay is safe');
$room=lq_create_room($db,1,$draftId);
$snapshot=json_decode(lq_room($db,$room['room'])['content'],true);
check(array_column($snapshot['questions'],'prompt')===['Ready','Last ready'],'room filters and reindexes questions in original order');
check(lq_state($db,$room['room'],1,'',true)['total']===2,'game count excludes drafts');
check(count(json_decode(lq_quiz($db,1,$draftId)['content'],true)['questions'])===count($questions),'playing never deletes drafts');
$key=lq_share($db,1,$draftId,true)['key'];
foreach ([lq_shared_start($db,$draftId,$key,bin2hex(random_bytes(32))),lq_public_start($db,$draftId,bin2hex(random_bytes(32)))] as $started) {
    check(count(json_decode(lq_room($db,$started['room'])['content'],true)['questions'])===2,'guest game filters drafts');
}
check(count(lq_public_preview($db,$draftId)['questions'])===2,'public preview filters drafts');
check(lq_discover($db,'Draft coverage')['quizzes'][0]['total']===2,'discovery counts playable questions');
lq_query($db,'INSERT INTO jp_users (id,email) VALUES (?,?)',[999,'draft-copy@osloskolen.no']);
$copy=lq_copy_quiz($db,999,$draftId,'public','');
check(count(json_decode(lq_quiz($db,999,$copy['id'])['content'],true)['questions'])===count($questions),'editable copy preserves drafts');
$empty=lq_save($db,1,['content'=>['title'=>'Only drafts','questions'=>$drafts]]);
$count=(int)lq_query($db,'SELECT COUNT(*) FROM lq_rooms')->fetchColumn();
rejects(fn()=>lq_create_room($db,1,$empty['id']),'no playable questions cannot start');
rejects(fn()=>lq_public_start($db,$empty['id'],bin2hex(random_bytes(32))),'empty public quiz cannot start');
$emptyKey=lq_share($db,1,$empty['id'],true)['key'];
rejects(fn()=>lq_shared_start($db,$empty['id'],$emptyKey,bin2hex(random_bytes(32))),'empty shared quiz cannot start');
check((int)lq_query($db,'SELECT COUNT(*) FROM lq_rooms')->fetchColumn()===$count,'empty quizzes create no rooms');
$state=lq_state($db,$room['room'],1,'',true);
$control=['room'=>$room['room'],'run'=>$state['run'],'version'=>$state['version'],'command'=>'switch-quiz'];
rejects(fn()=>lq_control($db,1,$control+['quiz'=>$empty['id']]),'cannot switch to all-draft quiz');
check(lq_state($db,$room['room'],1,'',true)['version']===$state['version'],'failed switch preserves lobby');
lq_control($db,1,$control+['quiz'=>$draftId]);
check(lq_state($db,$room['room'],1,'',true)['total']===2,'switch filters drafts');
foreach (['code','image','youtube'] as $kind) {
    $question=array_replace($complete,['prompt'=>'']);
    $question[$kind]=match($kind){'code'=>'print(1)','image'=>['id'=>$img,'alt'=>'Image'],'youtube'=>'dQw4w9WgXcQ'};
    check(lq_question_ready($question),$kind.'-only question is playable');
}
foreach ([['prompt'=>str_repeat('x',8001)],['correct'=>['0']],['image'=>['id'=>str_repeat('0',32)]],['seconds'=>'bad'],['type'=>'unknown']] as $invalid) {
    rejects(fn()=>lq_save($db,1,['content'=>['title'=>'Invalid','questions'=>[array_replace($complete,$invalid)]]]),'drafts still enforce safe field types, bounds and image access');
}
echo "$checks checks including incomplete drafts passed\n";
