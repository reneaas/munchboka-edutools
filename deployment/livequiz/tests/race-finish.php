<?php
require __DIR__.'/race.php';
foreach(['individual','teams'] as $mode){
 [$rid,$tokens]=raceFixture($db,$mode,2,2);
 $host=lq_state($db,$rid,1,'',true);$entry=reset(raceContent($db,$rid)['_race']['entries']);$active=lq_race_active($entry);$token=$tokens[$active['id']];
 $input=raceInput($db,$rid,$entry,true);lq_race_answer($db,$input,$token);
 $finish=['room'=>$rid,'run'=>$host['run'],'version'=>$host['version'],'command'=>'finish'];
 rejects(fn()=>lq_control($db,0,$finish),'participant cannot stop race');
 $done=lq_control($db,1,$finish)['state'];check($done['state']==='QUIZ_FINISHED','host can finish with stale progress version');
 check($done['winner']===null,'early finish invents no winner');check($done['race_board'][0]['progress']===1,'early finish preserves current progress');
 rejects(fn()=>lq_race_answer($db,$input,$token),'no answers after early finish');
 raceControl($db,$rid,'restart');$new=lq_state($db,$rid,1,'',true);
 rejects(fn()=>lq_control($db,1,array_replace($finish,['version'=>$new['version']])),'old finish cannot stop replay even with current version');
 check(lq_state($db,$rid,1,'',true)['state']==='LOBBY','replayed lobby survives stale finish');
}
echo "$checks checks including early race finish passed\n";
