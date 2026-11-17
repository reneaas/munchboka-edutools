<?php
require __DIR__.'/core.php';
foreach (['90'=>90,'1:30'=>90,'1m30s'=>90,'1h2m3s'=>3723,''=>0,'0:00'=>0] as $input=>$expected) check(lq_youtube_start($input)===$expected,'start time parsing');
foreach ([-1,'-1','1:90','1.5',[],true,'2147483648'] as $input) rejects(fn()=>lq_youtube_start($input),'invalid start time');
foreach (['https://youtu.be/dQw4w9WgXcQ?t=1m30s','https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=90','https://www.youtube.com/embed/dQw4w9WgXcQ?start=90'] as $url) {
 $question=$q;$question['youtube']=$url;
 $saved=lq_validate($db,1,['title'=>'Offset','questions'=>[$question]]);
 check($saved['questions'][0]['youtube_start']===90,'timestamp imported before video ID normalization');
 $question['youtube_start']='0:15';
 check(lq_validate($db,1,['title'=>'Override','questions'=>[$question]])['questions'][0]['youtube_start']===15,'explicit start overrides URL');
}
check(lq_validate($db,1,['title'=>'Legacy','questions'=>[$q]])['questions'][0]['youtube_start']===0,'legacy default');
$question=$q;$question['youtube_start']='bad';
$draft=lq_validate($db,1,['title'=>'Draft','questions'=>[$question]],true);
check(!lq_question_ready($draft['questions'][0]),'invalid draft remains editable but cannot play');
rejects(fn()=>lq_validate($db,1,['title'=>'Invalid','questions'=>[$question]]),'invalid published offset');
echo "$checks checks including YouTube start times passed\n";
