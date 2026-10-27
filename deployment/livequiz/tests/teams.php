<?php
declare(strict_types=1);
require __DIR__ . '/core.php';
$beforeTeams = $checks;
$examples = [
    3 => [2=>[2],3=>[3],4=>[2,2],5=>[3,2],6=>[3,3],7=>[3,2,2],8=>[3,3,2],9=>[3,3,3],10=>[3,3,2,2],13=>[3,3,3,2,2]],
    4 => [5=>null,6=>[3,3],7=>[4,3],8=>[4,4],9=>[3,3,3],10=>[4,3,3],11=>[4,4,3],12=>[4,4,4],13=>[4,3,3,3]],
    5 => [6=>null,7=>null,8=>[4,4],9=>[5,4],10=>[5,5],11=>null,12=>[4,4,4],13=>[5,4,4],14=>[5,5,4],17=>[5,4,4,4],19=>[5,5,5,4]],
];
foreach ($examples as $maximum => $cases) foreach ($cases as $n => $expected) {
    if ($expected === null) rejects(fn()=>lq_assign_teams(range(1,$n),$maximum), "invalid example $n/$maximum");
    else check(array_map(fn($t)=>count($t['members']),lq_assign_teams(range(1,$n),$maximum))===$expected,"example $n/$maximum");
}
rejects(fn()=>lq_assign_teams([],3),'empty lobby');
foreach ([null,'3',2.5,1,61] as $invalid) rejects(fn()=>lq_validate_play('teams',$invalid),'maximum must be a valid integer');
rejects(fn()=>lq_validate_play('unknown',3),'unknown mode');
for ($maximum=2;$maximum<=60;$maximum++) for ($n=1;$n<=60;$n++) {
    $k=(int)ceil($n/$maximum);$valid=intdiv($n,$k)>=$maximum-1;
    if (!$valid) { rejects(fn()=>lq_assign_teams(range(1,$n),$maximum),'invalid distribution rejected'); continue; }
    $source=range(1,$n);$teams=lq_assign_teams($source,$maximum);
    $sizes=array_map(fn($team)=>count($team['members']),$teams);
    $members=array_merge(...array_column($teams,'members'));sort($members);
    check($members===$source && count($teams)===$k,'every participant exactly once and minimal team count');
    check(max($sizes)<=$maximum && min($sizes)>=$maximum-1 && max($sizes)-min($sizes)<=1,'balanced permitted sizes');
}
$compositions=[];
for($i=0;$i<10;$i++)$compositions[]=json_encode(lq_assign_teams(range(1,12),3));
check(count(array_unique($compositions))>1,'different shuffles produce different compositions');
check(lq_team_total([1000,0,500])===1500,'modular team aggregation sums members');
$ties=lq_team_leaderboard([['id'=>2,'name'=>'Lag 2','members'=>[]],['id'=>1,'name'=>'Lag 1','members'=>[]]],[]);
check(array_column($ties,'id')===[1,2],'ties use stable team number');

$question=array_replace($q,['youtube'=>'','seconds'=>30]);
$savedTeam=lq_save($db,1,['content'=>['title'=>'Team integration','questions'=>[$question,$question]]]);
$newRoom=lq_create_room($db,1,$savedTeam['id']);$ridTeam=$newRoom['room'];$tokens=[];
for($i=0;$i<5;$i++) { $tokens[]=bin2hex(random_bytes(32));lq_join($db,$newRoom['pin'],'Team player '.$i,$tokens[$i]); }
$controlTeam = function(string $command,array $extra=[])use($db,$ridTeam){$r=lq_room($db,$ridTeam);return lq_control($db,1,['room'=>$ridTeam,'version'=>(int)$r['version'],'command'=>$command]+$extra);};
check(lq_state($db,$ridTeam,1,'',true)['mode']==='individual','new rooms default individual');
$storedContent=json_decode(lq_room($db,$ridTeam)['content'],true);
check($storedContent['play']['mode']==='individual' && $storedContent['play']['max_team_size']===3,'default mode and maximum persisted');
unset($storedContent['play']);
lq_query($db,'UPDATE lq_rooms SET content = ? WHERE id = ?',[json_encode($storedContent),$ridTeam]);
check(lq_state($db,$ridTeam,1,'',true)['mode']==='individual','legacy rooms without settings default individual');
rejects(fn()=>lq_control($db,2,['room'=>$ridTeam,'version'=>1,'command'=>'configure','mode'=>'teams','max_team_size'=>3]),'only owner configures');
$controlTeam('configure',['mode'=>'teams','max_team_size'=>4]);
$invalidRoom=lq_room($db,$ridTeam);
rejects(fn()=>$controlTeam('next'),'invalid team count prevents start');
check(lq_room($db,$ridTeam)===$invalidRoom,'invalid start changes no persisted state');
$controlTeam('configure',['mode'=>'teams','max_team_size'=>3]);
$startVersion=(int)lq_room($db,$ridTeam)['version'];
$db->exec("CREATE TRIGGER block_team_start BEFORE UPDATE OF phase ON lq_rooms WHEN NEW.phase = 'teams' BEGIN SELECT RAISE(ABORT, 'test failure'); END");
try {$controlTeam('next');throw new RuntimeException('Expected failure');}catch(PDOException $e){check(true,'failed start propagated');}
check(lq_play_settings(json_decode(lq_room($db,$ridTeam)['content'],true))['teams']===[],'failed start rolls back assignment');
check((int)lq_room($db,$ridTeam)['version']===$startVersion,'failed start leaves version unchanged');
$db->exec('DROP TRIGGER block_team_start');
$controlTeam('next');
$overview=lq_state($db,$ridTeam,1,'',true);$teams=$overview['teams'];
// Put all three teammates first so the test guarantees different answers within
// one team, regardless of the randomized assignment.
$tokensById=[];foreach($tokens as $token)$tokensById[lq_player($db,$ridTeam,$token)['id']]=$token;
$tokens=[];foreach($teams as $team)foreach($team['members'] as $member)$tokens[]=$tokensById[$member['id']];
check($overview['state']==='TEAM_OVERVIEW' && $overview['index']===-1,'overview before first question');
check(array_map(fn($team)=>count($team['members']),$teams)===[3,2],'persisted balanced teams');
rejects(fn()=>lq_control($db,1,['room'=>$ridTeam,'version'=>$startVersion,'command'=>'next']),'duplicate start cannot reshuffle');
rejects(fn()=>$controlTeam('configure',['mode'=>'individual','max_team_size'=>3]),'settings frozen after start');
$lateToken=bin2hex(random_bytes(32));lq_join($db,$newRoom['pin'],'Late',$lateToken);check(lq_state($db,$newRoom['room'],0,$lateToken,false)['state']==='WAITING_LOBBY','team late arrival waits for next game');
foreach($tokens as $token){
    $s=lq_state($db,$ridTeam,0,$token,false);
    check($s['teams']===$teams && $s['my_team']!==null,'all clients agree on team assignments');
    check(lq_join($db,$newRoom['pin'],'Reconnect',$token)['room']===$ridTeam,'existing participant reconnects');
}
rejects(fn()=>lq_answer($db,['room'=>$ridTeam,'index'=>0,'answer'=>[1]],$tokens[0]),'no answers during overview');
$controlTeam('next');$countdown=lq_state($db,$ridTeam,1,'',true);
check($countdown['state']==='COUNTDOWN' && $countdown['index']===-1,'first question uses countdown');
check($countdown['countdown_end']-$countdown['now']>2.5,'three-second countdown');
lq_query($db,'UPDATE lq_rooms SET deadline = ? WHERE id = ?',[(int)round((microtime(true)-0.1)*1000),$ridTeam]);
check(lq_state($db,$ridTeam,1,'',true)['index']===0,'countdown begins question zero');
// Lag 1: two correct answers and one wrong answer. Lag 2: one correct,
// one disconnected. Every answer remains independent.
foreach(array_slice($tokens,0,4) as $i=>$token)lq_answer($db,['room'=>$ridTeam,'index'=>0,'answer'=>[$i===2?0:1]],$token);
lq_answer($db,['room'=>$ridTeam,'index'=>0,'answer'=>[0],'points'=>100000,'team_id'=>2],$tokens[0]);
$firstPlayer=lq_player($db,$ridTeam,$tokens[0]);
$stored=lq_query($db,'SELECT answer, points FROM lq_answers WHERE room_id = ? AND player_id = ? AND question_index = 0',[$ridTeam,$firstPlayer['id']])->fetch();
check(json_decode($stored['answer'],true)===[1] && (int)$stored['points']===1000,'repeated answer cannot replace original or inject points');
check((int)lq_query($db,'SELECT COUNT(*) FROM lq_answers WHERE room_id = ?',[$ridTeam])->fetchColumn()===4,'retry creates no additional answer record');
try {
    lq_query($db,'INSERT INTO lq_answers (room_id,player_id,question_index,answer,points) VALUES (?,?,?,?,?)',[$ridTeam,$firstPlayer['id'],0,'[1]',1000]);
    throw new RuntimeException('Expected unique constraint rejection');
} catch(PDOException $e) { check(true,'database prevents duplicate participant/question records'); }

check(lq_state($db,$ridTeam,1,'',true)['state']==='QUESTION_ACTIVE','disconnected player stays eligible until deadline');
lq_query($db,'UPDATE lq_rooms SET deadline = 1 WHERE id = ?',[$ridTeam]);
$results=lq_state($db,$ridTeam,1,'',true);
check($results['state']==='QUESTION_RESULTS' && $results['distribution']['counts']===[1,3,0,0],'results count individual answers after timeout');
check($results['distribution']['correct']===3 && $results['answers']===4,'individual correct and submission counts');
rejects(fn()=>lq_answer($db,['room'=>$ridTeam,'index'=>0,'answer'=>[1]],$tokens[4]),'disconnected player cannot submit late');
$correctIds=[];foreach([0,1,3] as $i)$correctIds[]=lq_player($db,$ridTeam,$tokens[$i])['id'];
foreach($results['leaderboard'] as $team)check($team['score']===1000*count(array_intersect(array_column($team['members'],'id'),$correctIds)),'team sum matches individual scores');
check(array_sum(array_column($results['leaderboard'],'score'))===3000,'no duplicate points');
$teamScores=array_column($results['leaderboard'],'score','id');
check($teamScores[1]===2000 && $teamScores[2]===1000,'teammates can disagree and each earns their own points');
foreach([1000,1000,0,1000,0] as $i=>$expected)check((lq_state($db,$ridTeam,0,$tokens[$i],false)['points']??0)===$expected,'personal result independent of teammates');
$controlTeam('leaderboard');check(lq_state($db,$ridTeam,0,$tokens[0],false)['leaderboard']===$results['leaderboard'],'participant and host see same leaderboard');
$controlTeam('next');
lq_query($db,'UPDATE lq_rooms SET deadline = ? WHERE id = ?',[(int)round((microtime(true)-0.1)*1000),$ridTeam]);
check(lq_state($db,$ridTeam,1,'',true)['index']===1,'next countdown advances one question');
foreach($tokens as $token)lq_answer($db,['room'=>$ridTeam,'index'=>1,'answer'=>[1]],$token);
$results=lq_state($db,$ridTeam,1,'',true);
check($results['state']==='QUESTION_RESULTS','all answered ends question');
check(array_sum(array_column($results['leaderboard'],'score'))===8000,'team scores accumulate across questions');
foreach([2000,2000,1000,2000,1000] as $i=>$expected){
    $player=lq_player($db,$ridTeam,$tokens[$i]);
    $total=(int)lq_query($db,'SELECT SUM(points) FROM lq_answers WHERE room_id = ? AND player_id = ?',[$ridTeam,$player['id']])->fetchColumn();
    check($total===$expected,'individual total accumulates independently across questions');
}
$teamScores=array_column($results['leaderboard'],'score','id');
check($teamScores[1]===5000 && $teamScores[2]===3000,'team cumulative score sums cumulative individual totals');
$controlTeam('leaderboard');$controlTeam('next');
$final=lq_state($db,$ridTeam,0,$tokens[0],false);
check($final['state']==='QUIZ_FINISHED' && $final['teams']===$teams,'teams stable through entire lifecycle');
check($final['leaderboard']===$results['leaderboard'],'final team leaderboard preserved');
echo ($checks-$beforeTeams)." team checks passed\n";
