/* Against the disposable fixture from prepare-local.py, never the live site. */
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
(async () => {
 const browser = await chromium.launch({headless:true, executablePath:process.env.CHROMIUM_PATH});
 const teacher = await browser.newContext({viewport:{width:1280,height:1000}});
 const student = await browser.newContext({viewport:{width:390,height:844}});
 const student2 = await browser.newContext({viewport:{width:390,height:844}});
 const t = await teacher.newPage(), s = await student.newPage(), s2 = await student2.newPage();
 const errors=[]; for(const p of [t,s,s2])p.on('pageerror',e=>errors.push(e.message));
 const base=process.env.LIVEQUIZ_BASE||'http://127.0.0.1:8765';
 const currentState=page=>page.evaluate(async()=>{
	 const params=new URLSearchParams(location.search),host=params.has('host'),room=params.get(host?'host':'room');
	 const response=await fetch('index.php?api=state&room='+room+(host?'&host=1':''),{headers:host?{}:{'X-Player-Token':sessionStorage.getItem('lq-room-'+room)}});
	 if(!response.ok)throw new Error('State request failed: '+response.status);
	 return response.json();
 });
 const mutate=(page,action,data)=>page.evaluate(async({action,data})=>{
	 const bootstrap=await (await fetch('index.php?api=bootstrap')).json(),params=new URLSearchParams(location.search),room=params.get('room');
	 const headers={'Content-Type':'application/json','X-CSRF-Token':bootstrap.csrf};
	 if(room)headers['X-Player-Token']=sessionStorage.getItem('lq-room-'+room);
	 const response=await fetch('index.php?api='+action,{method:'POST',headers,body:JSON.stringify(data)});
	 return {status:response.status,body:await response.json()};
 },{action,data});
 const waitState=(page,state)=>page.locator('#app[data-state="'+state+'"]').waitFor({state:'attached'});
 async function sharedState(pages,expected){
	 await Promise.all(pages.map(page=>waitState(page,expected)));
	 const states=await Promise.all(pages.map(currentState));
	 for(const state of states){assert.equal(state.state,expected);assert.equal(state.version,states[0].version);assert.equal(state.index,states[0].index);assert.equal(state.deadline,states[0].deadline);}
	 return states;
 }
 await t.goto(base+'/_test_login.php');
 await t.getByRole('link',{name:'＋ Lag en quiz'}).click();
 await t.getByLabel('Quizens tittel').fill('Livequiz browser test');
 await t.getByLabel('Spørsmål',{exact:true}).fill('Hva er $2+2$?');
 // The code field is a CodeMirror editor and should auto-indent after a colon.
 await t.locator('.question-editor').first().locator('.CodeMirror').click();
 await t.keyboard.type('for i in range(2):\nprint(i)');
 assert.equal(await t.getByLabel('Kode (valgfritt)').inputValue(),'for i in range(2):\n    print(i)');
 await t.getByLabel('YouTube-lenke eller video-ID (valgfritt)').fill('https://youtu.be/dQw4w9WgXcQ');
 await t.getByLabel('Svartid i sekunder (5–600)').fill('120');
 for(const [i,v] of ['3','4','5','6'].entries()) await t.getByLabel('Alternativ '+(i+1),{exact:true}).fill(v);
 await t.getByLabel('Riktig 2',{exact:true}).check();
 // PNG upload travels through the real PHP upload endpoint and private DB storage.
 await t.locator('input[type=file]').setInputFiles({name:'test.png',mimeType:'image/png',buffer:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=','base64')});
 await t.getByLabel('Bildebeskrivelse').fill('Testbilde');
 await t.getByRole('button',{name:'＋ Legg til spørsmål',exact:true}).click();
 let card=t.locator('.question-editor').nth(1);
 await card.getByLabel('Svartype').selectOption('multi');
 await card.getByLabel('Spørsmål',{exact:true}).fill('Velg primtallene');
 await card.getByLabel('Svartid i sekunder (5–600)').fill('120');
 for(const [i,v] of ['2','3','4','6'].entries())await card.getByLabel('Alternativ '+(i+1),{exact:true}).fill(v);
 await card.getByLabel('Riktig 2',{exact:true}).check();
 await t.getByRole('button',{name:'＋ Legg til spørsmål',exact:true}).click();
 card=t.locator('.question-editor').nth(2);
 await card.getByLabel('Svartype').selectOption('text');
 await card.getByLabel('Spørsmål',{exact:true}).fill('Skriv fire');
 await card.getByLabel('Svartid i sekunder (5–600)').fill('120');
 await card.getByLabel('Godkjente svar – ett per linje').fill('fire\n4');
 await t.getByRole('button',{name:'Lagre quiz',exact:true}).click();
 await t.getByText('Lagret · versjon 1',{exact:true}).waitFor();
 await t.getByRole('button',{name:'Start spill',exact:true}).click();
 await t.locator('.pin').waitFor(); const pin=await t.locator('.pin').innerText();
 assert.match(pin,/^\d{6}$/);assert.ok(await t.locator('.qr').getAttribute('src'));
 await t.screenshot({path:'/tmp/livequiz-lobby.png',fullPage:true});
 await s.goto(base+'/?pin='+pin);await s.getByLabel('Kallenavn').fill('Ada');await s.getByRole('button',{name:'Bli med',exact:true}).click();
 await s.getByRole('heading',{name:'Du er med!',exact:true}).waitFor();
 await s2.goto(base+'/?pin='+pin);await s2.getByLabel('Kallenavn').fill('Bo');await s2.getByRole('button',{name:'Bli med',exact:true}).click();
 await s2.getByRole('heading',{name:'Du er med!',exact:true}).waitFor();
 await t.getByText('Ada · Bo',{exact:true}).waitFor();await t.getByRole('button',{name:'Start første spørsmål'}).click();
 await s.getByText('Ditt svar',{exact:true}).waitFor({timeout:500}).catch(()=>{});
 await s.locator('.answer-option:has(.rich:text-is("4"))').click();
 assert.ok(await s.locator('.katex').count());
 await s.waitForFunction(()=>document.querySelector('.question-image')?.naturalWidth===1);
 const before=await s.evaluate(async()=>{const room=new URLSearchParams(location.search).get('room');return (await fetch('index.php?api=state&room='+room,{headers:{'X-Player-Token':sessionStorage.getItem('lq-room-'+room)}})).json();});
 assert.equal(before.question.correct,undefined); assert.equal(before.question.accepted,undefined);
 await s.getByRole('button',{name:'Send svar',exact:true}).click();await s.getByText('Svaret er mottatt. Vent på læreren.',{exact:true}).waitFor();
 await s.reload();await s.getByText('Svaret er mottatt. Vent på læreren.',{exact:true}).waitFor();
 assert.equal(await s.getByRole('button',{name:'Send svar',exact:true}).isDisabled(),true);
 assert.equal(await s.locator('.answer-option:has(.rich:text-is("4"))').locator('input').isChecked(),true);
 await s.screenshot({path:'/tmp/livequiz-student.png',fullPage:true});
 // The host sees the options as a 2 x 2 card grid, in the same shuffled order as the students.
 await t.locator('.code-display .cm-keyword').first().waitFor();
 await s.locator('.code-display .cm-keyword').first().waitFor();
 for(const p of [t,s]){const box=await p.locator('.code-display .CodeMirror').boundingBox();assert.ok(box&&box.height>30,'code block visible, got '+JSON.stringify(box));}
 assert.equal(await t.locator('.option-card').count(),4);
 assert.equal(await t.locator('.option-grid').evaluate(g=>getComputedStyle(g).gridTemplateColumns.split(' ').length),2);
 assert.deepEqual(await t.locator('.option-card .rich').allInnerTexts(),await s.locator('.answer-option .rich').allInnerTexts());
 const questionModal=t.getByRole('dialog',{name:/Spørsmål 1 av 3/});
 assert.equal(await questionModal.evaluate(modal=>modal.matches(':modal')),true);
 assert.match(await questionModal.evaluate(modal=>getComputedStyle(modal,'::backdrop').backdropFilter),/blur\(8px\)/);
 assert.equal(await questionModal.locator('.qcard-body .rich').first().innerText(),await s.locator('.qcard-body > .rich').first().innerText());
 assert.equal(await questionModal.locator('.option-card').count(),4);
 assert.equal(await questionModal.getByRole('button',{name:'Vis fasit nå',exact:true}).isVisible(),true);
 assert.equal(await questionModal.getByRole('button',{name:'Avslutt spillet',exact:true}).isVisible(),true);
 assert.equal(await s.getByRole('dialog').evaluate(modal=>modal.matches(':modal')),true);
 assert.equal(await s.locator('.option-grid').evaluate(grid=>getComputedStyle(grid).gridTemplateColumns.split(' ').length),2);
 await t.keyboard.press('Escape');
 assert.equal(await questionModal.evaluate(modal=>modal.matches(':modal')),true);
 for(const viewport of [{width:390,height:844},{width:1280,height:720},{width:1280,height:1000}]){
	 await t.setViewportSize(viewport);
	 const bounds=await questionModal.boundingBox();
	 assert.ok(bounds.x>=0&&bounds.y>=0&&bounds.x+bounds.width<=viewport.width&&bounds.y+bounds.height<=viewport.height);
	 assert.equal(await questionModal.evaluate(modal=>modal.scrollWidth<=modal.clientWidth),true);
	 assert.equal(await questionModal.locator('.option-grid').evaluate(grid=>getComputedStyle(grid).gridTemplateColumns.split(' ').length),2);
	 await questionModal.getByRole('button',{name:'Vis fasit nå',exact:true}).scrollIntoViewIfNeeded();
	 await questionModal.evaluate(modal=>modal.scrollTop=0);
	 await t.screenshot({path:`/tmp/livequiz-host-modal-${viewport.width}x${viewport.height}.png`});
 }
 await t.screenshot({path:'/tmp/livequiz-host-question.png',fullPage:true});
 // Check video URL without making an external YouTube request.
 await t.route('https://www.youtube-nocookie.com/**',route=>route.fulfill({body:'<html>Test video</html>',contentType:'text/html'}));
 await t.getByRole('button',{name:'▶ Vis YouTube-video'}).click();
 assert.equal(await t.locator('iframe').getAttribute('src'),'https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ');
 // Bo answers wrongly; everyone has now answered, so the server reveals automatically.
 await s2.locator('.answer-option:has(.rich:text-is("3"))').click();await s2.getByRole('button',{name:'Send svar',exact:true}).click();
 const dialog=t.getByRole('dialog');
 await dialog.getByRole('heading',{name:'Fasit',exact:true}).waitFor();
 assert.equal(await t.locator('.active-question-modal').count(),0);
 assert.equal(await t.evaluate(()=>document.activeElement?.textContent),'Fasit');
 assert.equal(await dialog.locator('.chart-row').count(),4);
 assert.equal(await dialog.locator('.chart-row.correct .rich').innerText(),'4');
 assert.deepEqual((await dialog.locator('.chart-count').allInnerTexts()).sort(),['0','0','1','1']);
 await t.waitForTimeout(800);await t.screenshot({path:'/tmp/livequiz-popup-answer.png'});
 await s.getByText('Du fikk 1000 poeng.',{exact:true}).waitFor();
 await sharedState([t,s,s2],'QUESTION_RESULTS');
 for(const page of [s,s2]){
	 assert.deepEqual(await page.locator('.chart-count').allInnerTexts(),await t.locator('.chart-count').allInnerTexts());
	 assert.equal(await page.locator('.option-card.correct .rich').innerText(),'4');
	 assert.equal(await page.getByRole('button',{name:'Vis leaderboard',exact:true}).count(),0);
 }
 await s.reload();await t.reload();await sharedState([t,s,s2],'QUESTION_RESULTS');
 await s.screenshot({path:'/tmp/livequiz-student-results.png',fullPage:true});
 await dialog.getByRole('button',{name:'Vis leaderboard'}).click();
 await dialog.getByRole('heading',{name:'Leaderboard',exact:true}).waitFor();
 await s.reload();await sharedState([t,s,s2],'LEADERBOARD');
 assert.deepEqual(await s.locator('.board li').allInnerTexts(),await t.locator('.board li').allInnerTexts());
 assert.equal(await s.getByRole('button',{name:'Neste spørsmål',exact:true}).count(),0);
 await s.screenshot({path:'/tmp/livequiz-student-leaderboard.png',fullPage:true});
 assert.equal(await dialog.locator('.board li').count(),2);
 assert.match(await dialog.locator('.board li').first().innerText(),/Ada[\s\S]*1000 poeng/);
 await t.waitForTimeout(600);await t.screenshot({path:'/tmp/livequiz-popup-board.png'});
 const boardState=await currentState(t);
 await dialog.getByRole('button',{name:'Neste spørsmål',exact:true}).click();
 const replay=await mutate(t,'control',{room:boardState.room,version:boardState.version,command:'next'});
 assert.equal(replay.status,422);
 await t.locator('.countdown').waitFor();assert.match(await t.locator('.countdown').innerText(),/^[123]$/);
 const countdownStates=await sharedState([t,s,s2],'COUNTDOWN');
 assert.ok(countdownStates.every(state=>state.countdown_end===countdownStates[0].countdown_end));
 await s.reload();await waitState(s,'COUNTDOWN');
 await t.waitForTimeout(350);await t.screenshot({path:'/tmp/livequiz-countdown.png'});
 await s.getByText('Velg primtallene',{exact:true}).waitFor();
 const nextStates=await sharedState([t,s,s2],'QUESTION_ACTIVE');
 assert.equal(nextStates[0].index,1);
 assert.equal(nextStates[0].deadline,countdownStates[0].countdown_end+120);
 await s.locator('.answer-option:has(.rich:text-is("2"))').click();await s.locator('.answer-option:has(.rich:text-is("3"))').click();
 await s.getByRole('button',{name:'Send svar',exact:true}).click();await s.getByText('Svaret er mottatt. Vent på læreren.',{exact:true}).waitFor();
 // Bo has not answered, so the teacher closes this question manually.
 await t.getByRole('button',{name:'Vis fasit nå',exact:true}).click();await s.getByText('Du fikk 1000 poeng.',{exact:true}).waitFor();
 await dialog.getByRole('button',{name:'Vis leaderboard'}).click();await dialog.getByRole('button',{name:'Neste spørsmål',exact:true}).click();
 await s.getByLabel('Ditt svar').fill(' FIRE ');await s.getByRole('button',{name:'Send svar',exact:true}).click();await s.getByText('Svaret er mottatt. Vent på læreren.',{exact:true}).waitFor();
 await s2.getByLabel('Ditt svar').fill('fem');await s2.getByRole('button',{name:'Send svar',exact:true}).click();
 await dialog.getByRole('heading',{name:'Fasit',exact:true}).waitFor();
 assert.deepEqual(await dialog.locator('.chart-count').allInnerTexts(),['1','1','0']);
 await s.getByText('Du fikk 1000 poeng.',{exact:true}).waitFor();
 await dialog.getByRole('button',{name:'Vis leaderboard'}).click();
 await dialog.getByRole('button',{name:'Vis sluttresultat',exact:true}).click();await s.getByRole('heading',{name:'Takk for spillet!'}).waitFor();
 assert.ok(await s.getByText('3000 poeng',{exact:true}).count());
 await sharedState([t,s,s2],'QUIZ_FINISHED');
 const shortQuestion={type:'single',prompt:'Velg fire',code:'',youtube:'',image:null,seconds:5,options:['3','4','5','6'],correct:[1],accepted:[]};
 const saved=await mutate(t,'save',{content:{title:'Synchronized lifecycle',questions:[shortQuestion,{...shortQuestion,seconds:30}]}});
 assert.equal(saved.status,200);
 const created=await mutate(t,'create',{id:saved.body.id});assert.equal(created.status,200);
 const timedRoom=created.body.room,timedPin=created.body.pin;
 await t.goto(base+'/?host='+timedRoom);
 for(const [page,name] of [[s,'Ada'],[s2,'Bo']]){
	 await page.goto(base+'/?pin='+timedPin);await page.getByLabel('Kallenavn').fill(name);await page.getByRole('button',{name:'Bli med',exact:true}).click();await waitState(page,'LOBBY');
 }
 await t.getByText('Ada · Bo',{exact:true}).waitFor();
 await t.getByRole('button',{name:'Start første spørsmål'}).click();await sharedState([t,s,s2],'QUESTION_ACTIVE');
 await student2.setOffline(true);
 await s.locator('.answer-option:has(.rich:text-is("4"))').click();await s.getByRole('button',{name:'Send svar',exact:true}).click();
 const timedResults=await sharedState([t,s],'QUESTION_RESULTS');
 assert.equal(timedResults[0].answers,1);assert.deepEqual(timedResults[0].distribution.counts,[0,1,0,0]);
 await student2.setOffline(false);await s2.reload();await waitState(s2,'QUESTION_RESULTS');
 const lateAnswer=await mutate(s2,'answer',{room:timedRoom,index:0,answer:[1]});assert.equal(lateAnswer.status,422);
 const lateContext=await browser.newContext({viewport:{width:390,height:844}}),late=await lateContext.newPage();late.on('pageerror',error=>errors.push(error.message));
 await late.goto(base+'/?pin='+timedPin);await late.getByLabel('Kallenavn').fill('Cy');await late.getByRole('button',{name:'Bli med',exact:true}).click();await waitState(late,'QUESTION_RESULTS');
 const resultState=await currentState(t),boardInput={room:timedRoom,version:resultState.version,command:'leaderboard'};
 assert.equal((await mutate(late,'control',boardInput)).status,401);
 const duplicateBoard=await Promise.all([mutate(t,'control',boardInput),mutate(t,'control',boardInput)]);
 assert.deepEqual(duplicateBoard.map(result=>result.status).sort(),[200,422]);
 await sharedState([t,s,s2,late],'LEADERBOARD');
 assert.equal(await late.locator('.board li').count(),3);
 await t.getByRole('button',{name:'Neste spørsmål',exact:true}).click();await sharedState([t,s,s2,late],'COUNTDOWN');
 await sharedState([t,s,s2,late],'QUESTION_ACTIVE');
 const activeVersion=(await currentState(t)).version;
 const submitted=await Promise.all([
	 mutate(s,'answer',{room:timedRoom,index:1,answer:[1]}),mutate(s,'answer',{room:timedRoom,index:1,answer:[1]}),
	 mutate(s2,'answer',{room:timedRoom,index:1,answer:[0]}),mutate(late,'answer',{room:timedRoom,index:1,answer:[1]})
 ]);
 assert.ok(submitted.every(result=>result.status===200));
 const concurrentResults=await sharedState([t,s,s2,late],'QUESTION_RESULTS');
 assert.equal(concurrentResults[0].version,activeVersion+1);assert.equal(concurrentResults[0].answers,3);
 assert.deepEqual(concurrentResults[0].distribution.counts,[1,2,0,0]);
 await t.getByRole('button',{name:'Vis leaderboard',exact:true}).click();await sharedState([t,s,s2,late],'LEADERBOARD');
 assert.deepEqual((await currentState(t)).leaderboard.map(row=>[row.nickname,Number(row.score)]),[['Ada',2000],['Cy',1000],['Bo',0]]);
 await t.getByRole('button',{name:'Vis sluttresultat',exact:true}).click();await sharedState([t,s,s2,late],'QUIZ_FINISHED');
 await late.reload();await waitState(late,'QUIZ_FINISHED');await lateContext.close();
 const denied=await teacher.request.post(base+'/index.php?api=create',{data:{id:'a'.repeat(32)}});
 assert.equal(denied.status(),403);
 const boot=await (await student.request.get(base+'/index.php?api=bootstrap')).json();
 const noAuth=await student.request.post(base+'/index.php?api=save',{headers:{'X-CSRF-Token':boot.csrf},data:{}});assert.equal(noAuth.status(),401);
 assert.deepEqual(errors,[]);
 console.log('Browser flows passed: authoring/media/math/code; all answer types; host + three participants; shared question/results/leaderboard/countdown/finished states; refresh in results, leaderboard and countdown; timeout with disconnected player; late join; zero-count bars; simultaneous and duplicate answers; duplicate host progression; server countdown deadlines; final scores; CSRF and participant authorization.');
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1);});
