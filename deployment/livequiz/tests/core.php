<?php
declare(strict_types=1);
session_save_path('/tmp'); session_start();
require __DIR__ . '/../../jeopardy/pilot/private/app.php';
require __DIR__ . '/../private/livequiz/app.php';
class QuizTestDatabase extends PDO {
    public function prepare(string $query, array $options = []): PDOStatement|false {
        return parent::prepare(str_replace([' FOR UPDATE', 'INSERT IGNORE'], ['', 'INSERT OR IGNORE'], $query), $options);
    }
}
$db = new QuizTestDatabase('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE=>PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE=>PDO::FETCH_ASSOC]);
$sql = file_get_contents(__DIR__.'/../private/livequiz/schema.sql');
$sql = preg_replace('/ CHARACTER SET ascii| COLLATE ascii_bin| ENGINE=InnoDB DEFAULT CHARSET=utf8mb4/', '', $sql);
$sql = preg_replace('/,\s*INDEX [^\n]+/', '', $sql);
$db->exec($sql);
$db->exec('CREATE TABLE jp_media (id TEXT PRIMARY KEY, owner_id INTEGER, mime TEXT, size INTEGER, bytes BLOB)');
$checks = 0;
function check(bool $ok, string $label): void { global $checks; if (!$ok) throw new RuntimeException('FAIL: '.$label); $checks++; }
function rejects(callable $fn, string $label): void { try { $fn(); } catch (DomainException $e) { check(true,$label); return; } throw new RuntimeException('FAIL: '.$label); }
$q = ['type'=>'single','prompt'=>'Hva er $2+2$?','code'=>'print(2+2)','youtube'=>'https://youtu.be/dQw4w9WgXcQ','image'=>null,'seconds'=>30,'options'=>['3','4','5','6'],'correct'=>[1],'accepted'=>[]];
$multi = array_replace($q, ['type'=>'multi','options'=>['2','3','4'],'correct'=>[0,1],'youtube'=>'']);
$typed = array_replace($q, ['type'=>'text','accepted'=>['Fire','4'],'youtube'=>'']);
$quiz = ['title'=>'Matematikk','questions'=>[$q,$multi,$typed]];
$saved = lq_save($db,1,['content'=>$quiz]); $id=$saved['id'];
$spacedCode="\n  print(2 * 3 + 5)  \n\n";
$spacedQuiz=lq_save($db,1,['content'=>['title'=>'Code whitespace','questions'=>[array_replace($q,['code'=>$spacedCode])]]]);
$spacedContent=json_decode(lq_quiz($db,1,$spacedQuiz['id'])['content'],true);
check($spacedContent['questions'][0]['code']===$spacedCode,'saved code preserves leading/trailing spaces and blank lines');
$spacedRoom=lq_create_room($db,1,$spacedQuiz['id']);
check(json_decode(lq_room($db,$spacedRoom['room'])['content'],true)['questions'][0]['code']===$spacedCode,'game snapshot preserves code whitespace');
rejects(fn()=>lq_code([]),'code must be a string');
rejects(fn()=>lq_code(str_repeat(' ',8001)),'code length limit includes whitespace');
rejects(fn()=>lq_code("\xff"),'invalid UTF-8 code rejected');
rejects(fn()=>lq_validate($db,1,['title'=>'Blank','questions'=>[array_replace($q,['prompt'=>'','code'=>" \n\t",'youtube'=>''])]]),'whitespace-only code is not question content');

check($saved['revision']===1,'save first revision');
check(json_decode(lq_quiz($db,1,$id)['content'],true)['questions'][0]['youtube']==='dQw4w9WgXcQ','normalize video');
rejects(fn()=>lq_quiz($db,2,$id),'cross-account read');
rejects(fn()=>lq_save($db,2,['id'=>$id,'revision'=>1,'content'=>$quiz]),'cross-account write');
$saved=lq_save($db,1,['id'=>$id,'revision'=>1,'content'=>$quiz]);check($saved['revision']===2,'revision increments');
rejects(fn()=>lq_save($db,1,['id'=>$id,'revision'=>1,'content'=>$quiz]),'stale write');
rejects(fn()=>lq_validate($db,1,['title'=>'x','questions'=>[]]),'empty quiz');
rejects(fn()=>lq_validate($db,1,['title'=>'x','questions'=>[array_replace($q,['correct'=>[0,1]])]]),'single requires one key');
rejects(fn()=>lq_validate($db,1,['title'=>'x','questions'=>[array_replace($q,['seconds'=>0])]]),'timer range');
rejects(fn()=>lq_youtube('https://youtube.com.evil.test/watch?v=dQw4w9WgXcQ'),'video lookalike domain');
rejects(fn()=>lq_youtube('javascript:alert(1)'),'video protocol');
check(lq_youtube('https://www.youtube.com/watch?v=dQw4w9WgXcQ')==='dQw4w9WgXcQ','watch URL');
check(lq_grade($multi,[1,0])[1]===1000,'multi order independent');
check(lq_grade($multi,[0])[1]===0,'multi requires complete answer');
check(lq_grade($multi,[0,1,2])[1]===0,'multi extra choice incorrect');
check(lq_grade($typed,'  FIRE  ')[1]===1000,'typed normalization');
$words=array_replace($typed,['accepted'=>['Right left']]);
foreach (["right left","RIGHTLEFT"," R i G h T   l E F t ","right\tleft","right\nleft","right\u{00A0}left","right\u{2003}left"] as $variant) {
    check(lq_grade($words,$variant)[1]===1000,'case and all whitespace normalized');
}
check(lq_grade(array_replace($typed,['accepted'=>['Æ Ø Å']]),'æøå')[1]===1000,'Norwegian case normalization');
foreach ([['0.25','0,25'],['0,25','0.25'],['-0.25',' - 0 , 2 5 '],['+0,25','+0.25'],['.25',',25']] as [$expected,$submitted]) {
    check(lq_grade(array_replace($typed,['accepted'=>[$expected]]),$submitted)[1]===1000,'decimal separator normalized on both sides');
}
foreach ([['0.25','0,26'],['0.25','0,2,5'],['0.25','0.250'],['a,b','a.b'],['1,2,3','1.2.3']] as [$expected,$submitted]) {
    check(lq_grade(array_replace($typed,['accepted'=>[$expected]]),$submitted)[1]===0,'normalization preserves other differences');
}
rejects(fn()=>lq_grade($typed," \t\u{00A0}\u{2003}"),'whitespace-only answer rejected');

rejects(fn()=>lq_grade($q,[0,1]),'single cannot submit multi');
rejects(fn()=>lq_grade($q,[12]),'invalid option');
rejects(fn()=>lq_grade($q,['1']),'option strict integer');
$room=lq_create_room($db,1,$id);$rid=$room['room'];$token=str_repeat('a',64);$other=str_repeat('b',64);
check(strlen($room['pin'])===6,'six-digit PIN');
check(lq_join($db,$room['pin'],'Elev',$token)['room']===$rid,'join');
check(lq_join($db,$room['pin'],'Elev',$token)['room']===$rid,'join retry');
lq_join($db,$room['pin'],'Elev 2',$other);
check(lq_state($db,$rid,1,'',true)['players']===2,'join retry no duplicate');
rejects(fn()=>lq_state($db,$rid,2,'',true),'host ownership');
rejects(fn()=>lq_state($db,$rid,0,'invalid',false),'participant authentication');
rejects(fn()=>lq_control($db,2,['room'=>$rid,'version'=>1,'command'=>'next']),'control ownership');
$quiz['title']='Changed after start';lq_save($db,1,['id'=>$id,'revision'=>2,'content'=>$quiz]);
check(lq_state($db,$rid,1,'',true)['title']==='Matematikk','room snapshot independent');
lq_control($db,1,['room'=>$rid,'version'=>1,'command'=>'next']);
$firstCountdown=lq_state($db,$rid,0,$token,false);
check($firstCountdown['state']==='COUNTDOWN' && $firstCountdown['index']===-1,'first question begins with countdown');
check($firstCountdown['countdown_end']-$firstCountdown['now']>2.5 && $firstCountdown['countdown_end']-$firstCountdown['now']<=3.001,'initial countdown lasts three seconds');
check(!isset($firstCountdown['question']),'first question hidden during countdown');
check(lq_state($db,$rid,1,'',true)['countdown_end']===$firstCountdown['countdown_end'],'first countdown shared by host and participants');
rejects(fn()=>lq_answer($db,['room'=>$rid,'index'=>0,'answer'=>[1]],$token),'first countdown rejects early answers');
function expireInitialCountdown(PDO $db, string $room): void {
    $end=(int)round((microtime(true)-0.01)*1000);
    lq_query($db,'UPDATE lq_rooms SET deadline = ? WHERE id = ?',[$end,$room]);
    $state=lq_state($db,$room,1,'',true);
    check($state['state']==='QUESTION_ACTIVE' && $state['index']===0,'first countdown opens question zero');
    check(abs($state['deadline']-($end/1000+$state['question']['seconds']))<0.001,'first question gets full answer/scoring time after countdown');
}
expireInitialCountdown($db,$rid);
rejects(fn()=>lq_control($db,1,['room'=>$rid,'version'=>1,'command'=>'next']),'duplicate advance rejected');
check(lq_join($db,$room['pin'],'Late',str_repeat('c',64))['room']===$rid,'late participant joins current session');
check(lq_join($db,$room['pin'],'Elev',$token)['room']===$rid,'existing player reconnects');
$state=lq_state($db,$rid,0,$token,false);
check(!isset($state['question']['correct'])&&!isset($state['question']['accepted'])&&!isset($state['leaderboard']),'answer key and score hidden');
check($state['question']['prompt']==='Hva er $2+2$?','math preserved');
check(!isset($state['question']['youtube']),'participants never receive question video ID');
check(lq_state($db,$rid,1,'',true)['question']['youtube']==='dQw4w9WgXcQ','host retains question video');
check(lq_answer($db,['room'=>$rid,'index'=>0,'answer'=>[1]],$token)===['accepted'=>true],'answer acknowledged without grade');
lq_answer($db,['room'=>$rid,'index'=>0,'answer'=>[0]],$token);
check((int)$db->query('SELECT COUNT(*) FROM lq_answers')->fetchColumn()===1,'answer retry does not duplicate');
check((int)$db->query('SELECT points FROM lq_answers')->fetchColumn()===1000,'answer cannot be replaced');
check(!isset(lq_state($db,$rid,0,$token,false)['points']),'points hidden until reveal');
rejects(fn()=>lq_answer($db,['room'=>$rid,'index'=>1,'answer'=>[0]],$other),'future question');
$db->exec('UPDATE lq_rooms SET deadline = 1');
rejects(fn()=>lq_answer($db,['room'=>$rid,'index'=>0,'answer'=>[1]],$other),'late answer rejected by server');
lq_control($db,1,['room'=>$rid,'version'=>3,'command'=>'reveal']);
$state=lq_state($db,$rid,0,$token,false);
check($state['points']===1000&&$state['question']['correct']===[1],'reveal gives grade and key');
check(!isset($state['question']['youtube']),'participant results omit video ID');
check((int)$state['leaderboard'][0]['score']===1000,'leaderboard server scored');
function progressQuestion(PDO $db, string $room): void {
    $state = lq_state($db,$room,1,'',true);
    rejects(fn()=>lq_control($db,1,['room'=>$room,'version'=>$state['version'],'command'=>'next']),'results cannot skip leaderboard');
    lq_control($db,1,['room'=>$room,'version'=>$state['version'],'command'=>'leaderboard']);
    $board = lq_state($db,$room,0,str_repeat('a',64),false);
    check($board['state']==='LEADERBOARD','participant receives persistent leaderboard');
    $input = ['room'=>$room,'version'=>$board['version'],'command'=>'next'];
    lq_control($db,1,$input);
    rejects(fn()=>lq_control($db,1,$input),'duplicate next cannot skip a question');
    $countdown = lq_state($db,$room,1,'',true);
    if ($countdown['phase'] === 'finished') return;
    check($countdown['state']==='COUNTDOWN'&&$countdown['countdown_end']===$countdown['deadline'],'server countdown deadline');
    check($countdown['countdown_end']-$countdown['now']>2.5&&$countdown['countdown_end']-$countdown['now']<=3.001,'countdown lasts three full seconds');
    check($countdown['index']===$state['index'],'countdown has not advanced question');
    rejects(fn()=>lq_answer($db,['room'=>$room,'index'=>$state['index']+1,'answer'=>[0]],str_repeat('a',64)),'countdown rejects early answers');
    lq_query($db,'UPDATE lq_rooms SET deadline = ? WHERE id = ?',[time()-1,$room]);
    $next = lq_state($db,$room,0,str_repeat('a',64),false);
    check($next['state']==='QUESTION_ACTIVE'&&$next['index']===$state['index']+1,'participant poll advances expired countdown');
    check($next['version']===$countdown['version']+1,'countdown advances exactly once');
    check(lq_state($db,$room,1,'',true)['deadline']===$next['deadline'],'host and player share question deadline');
    check((int)lq_room($db,$room)['deadline']>1000000000000,'new question stores precise deadline without schema change');
}
progressQuestion($db,$rid);
check(lq_answer($db,['room'=>$rid,'index'=>0,'answer'=>[1]],$token)['accepted'],'old retry safe after advance');
check(lq_answer($db,['room'=>$rid,'index'=>1,'answer'=>[1,0]],$token)['accepted'],'multi submission');
lq_control($db,1,['room'=>$rid,'version'=>lq_room($db,$rid)['version'],'command'=>'reveal']);progressQuestion($db,$rid);
lq_answer($db,['room'=>$rid,'index'=>2,'answer'=>'fire'],$token);
lq_control($db,1,['room'=>$rid,'version'=>lq_room($db,$rid)['version'],'command'=>'reveal']);progressQuestion($db,$rid);
$state=lq_state($db,$rid,0,$token,false);check($state['phase']==='finished'&&(int)$state['leaderboard'][0]['score']===3000,'complete game scores');
rejects(fn()=>lq_answer($db,['room'=>$rid,'index'=>2,'answer'=>'fire'],$other),'finished rejects new answers');
$ar=lq_create_room($db,1,$id);$ra=$ar['room'];$a1=str_repeat('1',64);$a2=str_repeat('2',64);
lq_join($db,$ar['pin'],'A',$a1);lq_join($db,$ar['pin'],'B',$a2);
lq_control($db,1,['room'=>$ra,'version'=>1,'command'=>'next']);expireInitialCountdown($db,$ra);
lq_answer($db,['room'=>$ra,'index'=>0,'answer'=>[1]],$a1);
check(lq_state($db,$ra,1,'',true)['phase']==='question','no reveal until everyone has answered');
lq_answer($db,['room'=>$ra,'index'=>0,'answer'=>[0]],$a2);
$s=lq_state($db,$ra,1,'',true);
check($s['phase']==='reveal'&&$s['version']===4,'auto reveal when all have answered');
check($s['distribution']['counts']===[1,1,0,0]&&$s['distribution']['correct']===1&&$s['distribution']['answered']===2,'four bars include zero counts');
check(!isset(lq_state($db,$ra,0,$a1,false)['distribution']),'participant results omit statistics');
rejects(fn()=>lq_control($db,1,['room'=>$ra,'version'=>3,'command'=>'reveal']),'manual reveal after auto reveal rejected');
check(lq_state($db,$ra,1,'',true)['version']===4,'auto reveal is applied once');
$tr=lq_create_room($db,1,$id);$rt=$tr['room'];lq_join($db,$tr['pin'],'C',str_repeat('3',64));lq_join($db,$tr['pin'],'D',str_repeat('4',64));
lq_control($db,1,['room'=>$rt,'version'=>1,'command'=>'next']);expireInitialCountdown($db,$rt);
check(lq_state($db,$rt,1,'',true)['phase']==='question','question stays open before deadline');
$db->exec("UPDATE lq_rooms SET deadline = 1 WHERE id = '$rt'");
$s=lq_state($db,$rt,1,'',true);
check($s['state']==='QUESTION_RESULTS'&&$s['distribution']['answered']===0&&$s['distribution']['counts']===[0,0,0,0],'deadline closes question with disconnected or unanswered players');
$er=lq_create_room($db,1,$id);lq_control($db,1,['room'=>$er['room'],'version'=>1,'command'=>'next']);expireInitialCountdown($db,$er['room']);
check(lq_state($db,$er['room'],1,'',true)['phase']==='question','empty room never auto reveals before deadline');
$img=str_repeat('d',32);$db->prepare('INSERT INTO jp_media VALUES (?,1,?,?,?)')->execute([$img,'image/png',3,'PNG']);
$withImage=array_replace($q,['image'=>['id'=>$img,'alt'=>'Diagram']]);
foreach ([['id'=>$img], ['id'=>$img,'alt'=>'']] as $imageWithoutDescription) {
    $imageQuiz=lq_save($db,1,['content'=>['title'=>'No image description','questions'=>[array_replace($q,['image'=>$imageWithoutDescription])]]]);
    $imageContent=json_decode(lq_quiz($db,1,$imageQuiz['id'])['content'],true);
    check($imageContent['questions'][0]['image']['id']===$img,'image saved without description');
    check($imageContent['questions'][0]['image']['alt']==='','missing and empty image descriptions accepted');
}
check(lq_validate($db,1,['title'=>'Existing description','questions'=>[$withImage]])['questions'][0]['image']['alt']==='Diagram','existing description preserved');
rejects(fn()=>lq_validate($db,2,['title'=>'Stolen','questions'=>[$withImage]]),'image ownership validation');
$i=lq_save($db,1,['content'=>['title'=>'Images','questions'=>[$withImage,$q]]]);$ir=lq_create_room($db,1,$i['id']);$it=str_repeat('e',64);lq_join($db,$ir['pin'],'Img',$it);
rejects(fn()=>lq_room_media($db,$ir['room'],0,$it,false,$img),'lobby hides future image');
lq_control($db,1,['room'=>$ir['room'],'version'=>1,'command'=>'next']);expireInitialCountdown($db,$ir['room']);
check(lq_room_media($db,$ir['room'],1,'',true,$img)['bytes']==='PNG','host current image available');
rejects(fn()=>lq_room_media($db,$ir['room'],0,$it,false,$img),'participant cannot download current image');
rejects(fn()=>lq_room_media($db,$ir['room'],0,$it,true,$img),'participant cannot impersonate host for image');
foreach (['question','reveal','leaderboard'] as $mediaPhase) {
    lq_query($db,'UPDATE lq_rooms SET phase = ? WHERE id = ?',[$mediaPhase,$ir['room']]);
    $participantState=lq_state($db,$ir['room'],0,$it,false);
    check(!isset($participantState['question']['image'])&&!isset($participantState['question']['youtube']),'participant media omitted in '.$mediaPhase);
    check(isset(lq_state($db,$ir['room'],1,'',true)['question']['image']),'host image retained in '.$mediaPhase);
    rejects(fn()=>lq_room_media($db,$ir['room'],0,$it,false,$img),'participant image denied in '.$mediaPhase);
}
rejects(fn()=>lq_room_media($db,$ir['room'],0,$token,false,$img),'other room cannot view media');
rejects(fn()=>lq_room_media($db,$ir['room'],1,'',true,str_repeat('f',32)),'host cannot fetch unrelated image');
$db->exec('UPDATE lq_rooms SET expires_at = 1');
rejects(fn()=>lq_state($db,$rid,1,'',true),'expired room');
$db->exec('CREATE TABLE jp_users (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE); CREATE TABLE jp_login (email TEXT PRIMARY KEY, code_hash TEXT)');
$db->exec("INSERT INTO jp_users VALUES (1, 'teacher@osloskolen.no'); INSERT INTO jp_login VALUES ('teacher@osloskolen.no', 'untouched')");
function seedQuizCode(PDO $db, int $expires, string $email = 'teacher@osloskolen.no'): void {
    $db->exec('DELETE FROM lq_login');
    $challenge = str_repeat('a',64);
    lq_query($db,'INSERT INTO lq_login (email,challenge,code_hash,expires_at,attempts) VALUES (?,?,?,?,0)',[$email,$challenge,password_hash('12345678',PASSWORD_DEFAULT),$expires]);
    $_SESSION=['email_pending'=>$email,'challenge'=>$challenge];
}
rejects(fn()=>lq_send_code($db,'outside@example.com'),'quiz rejects outside domain before email');
seedQuizCode($db,time()+600);
rejects(fn()=>lq_verify($db,'00000000'),'quiz wrong code');
check((int)$db->query('SELECT attempts FROM lq_login')->fetchColumn()===1,'quiz failed attempt persisted');
$_SESSION['challenge']='wrong';rejects(fn()=>lq_verify($db,'12345678'),'quiz code session bound');
seedQuizCode($db,time()-1);rejects(fn()=>lq_verify($db,'12345678'),'quiz expired code');
seedQuizCode($db,time()+600);$db->exec('UPDATE lq_login SET attempts=5');rejects(fn()=>lq_verify($db,'12345678'),'quiz attempt limit');
seedQuizCode($db,time()+600);lq_verify($db,'12345678');
check($_SESSION['uid']===1,'quiz reuses existing account');
check(strlen($_SESSION['csrf'])===64,'quiz rotates csrf on login');
check($db->query('SELECT code_hash FROM lq_login')->fetchColumn()===null,'quiz code consumed');
check($db->query('SELECT code_hash FROM jp_login')->fetchColumn()==='untouched','Jeopardy challenge untouched');
rejects(fn()=>lq_verify($db,'12345678'),'quiz code cannot be reused');
seedQuizCode($db,time()+600,'new@osloskolen.no');lq_verify($db,'12345678');
check($_SESSION['uid']>1 && lq_query($db,'SELECT email FROM jp_users WHERE id = ?',[$_SESSION['uid']])->fetchColumn()==='new@osloskolen.no','quiz new verified account');
// Scoring is a quiz snapshot setting, with legacy fixed-point compatibility.
check(lq_validate($db,1,$quiz)['scoring']==='fixed','missing scoring defaults to fixed');
rejects(fn()=>lq_validate($db,1,array_replace($quiz,['scoring'=>'unknown'])),'invalid scoring rejected');
foreach ([5,30,600] as $duration) {
    check(lq_points(1000,'speed',$duration,$duration)===1000,'full speed points');
    check(lq_points(1000,'speed',$duration,$duration/2)===500,'halfway speed points');
    check(lq_points(1000,'speed',$duration,0)===0,'minimum speed points');
    check(lq_points(0,'speed',$duration,$duration)===0,'wrong answer no speed points');
    check(lq_points(1000,'fixed',$duration,0)===1000,'fixed score independent of time');
    check(lq_points(1000,'speed',$duration,$duration,true)===1000,'video full points at start');
    check(lq_points(1000,'speed',$duration,$duration-2,true)===1000,'video full points during grace');
    check(lq_points(1000,'speed',$duration,$duration-4,true)===1000,'video full points at grace boundary');
    check(lq_points(1000,'speed',$duration,($duration-4)/2,true)===500,'video halfway through scoring interval');
    check(lq_points(1000,'speed',$duration,0,true)===0,'video score reaches zero at original deadline');
    check(lq_points(0,'speed',$duration,$duration-2,true)===0,'wrong video answer during grace earns zero');
    check(lq_points(1000,'fixed',$duration,0,true)===1000,'fixed video scoring unaffected');
}
check(lq_points(1000,'speed',600,0.1)===0,'last moment correct answer rounds to zero');
check(lq_points(1000,'speed',30,60)===1000 && lq_points(1000,'speed',30,-5)===0,'speed points clamped');
foreach ([$q,$multi,$typed] as $question) {
    $question['seconds']=600;
    $speedQuiz=lq_save($db,1,['content'=>['title'=>'Speed','scoring'=>'speed','questions'=>[$question]]]);
    $speedRoom=lq_create_room($db,1,$speedQuiz['id']);$sr=$speedRoom['room'];
    $fast=bin2hex(random_bytes(32));$slow=bin2hex(random_bytes(32));$wrong=bin2hex(random_bytes(32));
    foreach ([$fast,$slow,$wrong] as $n=>$tok) lq_join($db,$speedRoom['pin'],'Speed '.$n,$tok);
    lq_save($db,1,['id'=>$speedQuiz['id'],'revision'=>1,'content'=>['title'=>'Changed','scoring'=>'fixed','questions'=>[$question]]]);
    check(lq_state($db,$sr,0,$fast,false)['scoring']==='speed','room preserves scoring snapshot');
    lq_control($db,1,['room'=>$sr,'version'=>1,'command'=>'next']);expireInitialCountdown($db,$sr);
    check((int)lq_room($db,$sr)['deadline']>1000000000000,'first question precise deadline');
    $correctAnswer=$question['type']==='text'?'fire':$question['correct'];
    $wrongAnswer=$question['type']==='text'?'wrong':[2];
    lq_query($db,'UPDATE lq_rooms SET deadline = ? WHERE id = ?',[(int)round((microtime(true)+598)*1000),$sr]);
    lq_answer($db,['room'=>$sr,'index'=>0,'answer'=>$correctAnswer],$fast);
    lq_query($db,'UPDATE lq_rooms SET deadline = ? WHERE id = ?',[(int)round((microtime(true)+(empty($question['youtube'])?300:298))*1000),$sr]);
    lq_answer($db,['room'=>$sr,'index'=>0,'answer'=>$correctAnswer,'points'=>1000,'elapsed'=>0],$slow);
    check(!isset(lq_state($db,$sr,0,$slow,false)['points']),'speed score hidden until reveal');
    lq_answer($db,['room'=>$sr,'index'=>0,'answer'=>$wrongAnswer],$slow);
    lq_answer($db,['room'=>$sr,'index'=>0,'answer'=>$wrongAnswer],$wrong);
    $fastState=lq_state($db,$sr,0,$fast,false);$slowState=lq_state($db,$sr,0,$slow,false);
    if (!empty($question['youtube'])) check($fastState['points']===1000,'server applies video grace from room snapshot');
    check($fastState['points']>=990 && $slowState['points']>=490 && $slowState['points']<=500,'all answer types reward earlier correct answers');
    check(lq_state($db,$sr,0,$wrong,false)['points']===0,'wrong speed answer zero');
    check(lq_state($db,$sr,1,'',true)['distribution']['correct']===2,'host speed results count correctness');
    check((int)$slowState['leaderboard'][0]['score']===$fastState['points'],'leaderboard uses speed score');
    // A valid answer just before the deadline can round to zero: correctness
    // must use the stored answer, including for typed-answer result charts.
    lq_query($db,'UPDATE lq_answers SET points = 0 WHERE room_id = ?',[$sr]);
    check(lq_state($db,$sr,1,'',true)['distribution']['correct']===2,'zero-point correct answers remain correct');
}
echo "$checks backend checks passed\n";
