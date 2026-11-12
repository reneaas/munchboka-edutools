<?php
require __DIR__.'/core.php';
$quizData=['title'=>'Overwrite autosave','questions'=>[$q]];
$saved=lq_save($db,1,['content'=>$quizData]);
$room=lq_create_room($db,1,$saved['id']);
$snapshot=lq_room($db,$room['room'])['content'];
$count=(int)lq_query($db,'SELECT COUNT(*) FROM lq_quizzes')->fetchColumn();
for($i=1;$i<=25;$i++) {
    $quizData['title']='Latest autosave '.$i;
    $saved=lq_save($db,1,$saved+['content'=>$quizData]);
}
check((int)lq_query($db,'SELECT COUNT(*) FROM lq_quizzes')->fetchColumn()===$count,'repeated autosaves overwrite one quiz record');
check(lq_quiz($db,1,$saved['id'])['title']==='Latest autosave 25','only latest quiz content retained');
check($saved['revision']===26,'concurrency counter still advances');
check(lq_room($db,$room['room'])['content']===$snapshot,'editing does not alter an ongoing game');
rejects(fn()=>lq_save($db,1,['id'=>$saved['id'],'revision'=>1,'content'=>$quizData]),'older tab cannot overwrite current quiz');
echo "$checks checks including overwrite saves passed\n";
