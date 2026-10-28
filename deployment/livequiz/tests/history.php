<?php
require __DIR__.'/core.php';
function historyRoom(PDO $db,int $n,int $owner,string $phase,int $expires,?float $finished): string {
    $id=str_pad(dechex(10000+$n),32,'0',STR_PAD_LEFT);
    $content=['title'=>'History fixture','questions'=>[]];if($finished!==null)$content['_finished_at']=$finished;
    lq_query($db,'INSERT INTO lq_rooms (id,pin,owner_id,content,phase,expires_at) VALUES (?,?,?,?,?,?)',[$id,(string)(700000+$n),$owner,json_encode($content),$phase,$expires]);
    lq_query($db,'INSERT INTO lq_players (id,room_id,nickname,token_hash) VALUES (?,?,?,?)',[$id,$id,'Player',hash('sha256',$id)]);
    lq_query($db,'INSERT INTO lq_answers (room_id,player_id,question_index,answer,points) VALUES (?,?,0,?,1000)',[$id,$id,'[1]']);return $id;
}
$now=time();$ids=[];
for($i=1;$i<=8;$i++)$ids[$i]=historyRoom($db,$i,999,['finished','race_done','light_done'][$i%3],$now+600,$now+$i);
$active=historyRoom($db,20,999,'question',$now+600,null);
$lobby=historyRoom($db,21,999,'lobby',$now+600,null);
$expired=historyRoom($db,22,999,'question',$now-1,null);
$other=historyRoom($db,23,1000,'finished',$now+600,1);
$quizzes=$db->query('SELECT COUNT(*) FROM lq_quizzes')->fetchColumn();$media=$db->query('SELECT COUNT(*) FROM jp_media')->fetchColumn();
check(lq_prune_history($db,999)===4,'three older completions and one expired abandoned room removed');
foreach([$ids[1],$ids[2],$ids[3],$expired] as $id)foreach(['lq_rooms'=>'id','lq_players'=>'room_id','lq_answers'=>'room_id'] as $table=>$column)check((int)lq_query($db,"SELECT COUNT(*) FROM $table WHERE $column = ?",[$id])->fetchColumn()===0,"all history removed from $table");
foreach([$ids[4],$ids[5],$ids[6],$ids[7],$ids[8],$active,$lobby,$other] as $id)check((int)lq_query($db,'SELECT COUNT(*) FROM lq_rooms WHERE id = ?',[$id])->fetchColumn()===1,'recent/active/other owner preserved');
check($quizzes===$db->query('SELECT COUNT(*) FROM lq_quizzes')->fetchColumn(),'saved quizzes preserved');
check($media===$db->query('SELECT COUNT(*) FROM jp_media')->fetchColumn(),'uploaded images preserved');
check(lq_prune_history($db,999)===0,'cleanup idempotent');
// An expired finished room still counts as history; expiry does not erase all results.
for($i=30;$i<36;$i++)historyRoom($db,$i,1001,'finished',$now-1000+$i,null);
check(lq_prune_history($db,1001)===1,'legacy expired completions retain newest five');
$r=lq_room($db,$active);$r=lq_transaction($db,fn()=>lq_transition($db,$r,'race_done',0,0));
$stamp=json_decode($r['content'],true)['_finished_at'];check($stamp>=$now,'completion timestamp recorded');
$r=lq_transaction($db,fn()=>lq_transition($db,$r,'finished',0,0));check(json_decode($r['content'],true)['_finished_at']===$stamp,'final-screen transition preserves completion time');
check(lq_prune_history($db,999)===1,'new finish replaces oldest retained result');
$atomic=historyRoom($db,50,1002,'lobby',$now-1,null);
$db->exec("CREATE TRIGGER history_rollback BEFORE DELETE ON lq_rooms WHEN OLD.owner_id = 1002 BEGIN SELECT RAISE(ABORT, 'test failure'); END");
try {lq_prune_history($db,1002);check(false,'failure must propagate');}catch(PDOException $e){}
foreach(['lq_rooms'=>'id','lq_players'=>'room_id','lq_answers'=>'room_id'] as $table=>$column)check((int)lq_query($db,"SELECT COUNT(*) FROM $table WHERE $column = ?",[$atomic])->fetchColumn()===1,'failed cleanup rolls back '.$table);
$db->exec('DROP TRIGGER history_rollback');
echo "$checks checks including history retention passed\n";
