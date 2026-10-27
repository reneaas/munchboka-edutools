<?php
require __DIR__.'/core.php';
foreach(['regular','race'] as $game)foreach(['individual','teams'] as $mode){
 $r=lq_create_room($db,1,$id);$rid=$r['room'];foreach([0,1] as $i)lq_join($db,$r['pin'],'P'.$i,bin2hex(random_bytes(32)));
 $settings=['game'=>$game,'mode'=>$mode,'max_team_size'=>2,'lightning'=>['enabled'=>true,'seconds'=>90]];
 $reply=lq_control($db,1,['room'=>$rid,'version'=>1,'command'=>'next','settings'=>$settings]);
 check($reply['state']['mode']===$mode&&$reply['state']['game']===$game,'start applies selected mode');
 check($reply['state']['lightning']['seconds']===90,'start applies lightning settings');
 check($reply['state']['state']===($mode==='teams'?'TEAM_OVERVIEW':($game==='race'?'RACE_COUNTDOWN':'COUNTDOWN')),'start enters selected lifecycle');
 check($reply['state']['version']===2,'settings and start commit one transition');
 rejects(fn()=>lq_control($db,1,['room'=>$rid,'version'=>1,'command'=>'next','settings'=>$settings]),'duplicate combined start rejected');
}
$r=lq_create_room($db,1,$id);$rid=$r['room'];lq_join($db,$r['pin'],'One',bin2hex(random_bytes(32)));
$before=lq_room($db,$rid);
rejects(fn()=>lq_control($db,1,['room'=>$rid,'version'=>1,'command'=>'next','settings'=>['game'=>'race','mode'=>'teams','max_team_size'=>5]]),'invalid team allocation rolls back start');
check(lq_room($db,$rid)===$before,'failed start preserves saved settings/version');
$save=lq_control($db,1,['room'=>$rid,'version'=>1,'command'=>'configure','game'=>'race','mode'=>'individual','max_team_size'=>2]);
check($save['state']['state']==='LOBBY'&&$save['state']['version']===2,'save response provides latest lobby version');
$start=lq_control($db,1,['room'=>$rid,'version'=>$save['state']['version'],'command'=>'next']);
check($start['state']['state']==='RACE_COUNTDOWN','start immediately after save needs no poll');
echo "$checks checks including start settings passed\n";
