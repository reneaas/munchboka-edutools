/* Disposable local fixture only; uses real PHP endpoints and separate browser sessions. */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH});
 try{
 const host=await browser.newPage({viewport:{width:1280,height:900},reducedMotion:'reduce'}),a=await browser.newPage({viewport:{width:390,height:844},reducedMotion:'reduce'}),b=await browser.newPage();
 const errors=[];for(const p of [host,a,b])p.on('pageerror',e=>errors.push(e.message));
 const base=process.env.LIVEQUIZ_BASE||'http://127.0.0.1:8799';await host.goto(base+'/_test_login.php');
 const state=p=>p.evaluate(async()=>{const params=new URLSearchParams(location.search),host=params.has('host'),room=params.get(host?'host':'room');return (await(await fetch('index.php?api=state&room='+room+(host?'&host=1':''),{headers:host?{}:{'X-Player-Token':sessionStorage.getItem('lq-room-'+room)}})).json());});
 const wait=(p,phase)=>p.locator('#app[data-state="'+phase+'"]').waitFor();
 const submit=async p=>{const s=await state(p);if(s.state==='LIGHTNING_ACTIVE'&&s.question.image){await p.waitForFunction(()=>document.querySelector('.question-image')?.naturalWidth>0);const body=await p.locator('.modal-body').boundingBox(),img=await p.locator('.question-image').boundingBox();assert.ok(img.height>0&&img.y>=body.y&&img.y+img.height<=body.y+body.height+1);}if(s.question.type==='text')await p.getByLabel('Ditt svar').fill('F I R E');else await p.locator('.answer-option:has(.rich:text-is("4"))').locator('input').check();await p.getByRole('button',{name:'Send svar',exact:true}).click();};
 for(const mode of ['individual','teams']){
  const created=await host.evaluate(async()=>{
   const boot=await(await fetch('index.php?api=bootstrap')).json();const post=async(action,data)=>(await(await fetch('index.php?api='+action,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':boot.csrf},body:JSON.stringify(data)})).json());
   const canvas=document.createElement('canvas');canvas.width=600;canvas.height=900;const form=new FormData();form.append('image',await new Promise(resolve=>canvas.toBlob(resolve)),'diagram.png');
   const image=(await(await fetch('index.php?api=upload',{method:'POST',headers:{'X-CSRF-Token':boot.csrf},body:form})).json()).image;
   const questions=[{type:'single',prompt:'Hva er $2+2$?',code:'print(2 + 2)\n\n',youtube:'',image,seconds:120,options:['3','4','5','6'],correct:[1],accepted:[]},{type:'text',prompt:'Skriv fire',code:'',youtube:'',image:null,seconds:120,options:[],correct:[],accepted:['fire','4']}];
   const quiz=await post('save',{content:{title:'Lightning browser '+Date.now(),questions}});return await post('create',{id:quiz.id});
  });
  await host.goto(base+'/?host='+created.room);await host.locator('.pin').waitFor();assert.equal(await host.getByLabel('Aktiver lynrunde',{exact:true}).isChecked(),false);
  await host.getByLabel('Aktiver lynrunde',{exact:true}).check();await host.getByLabel('Varighet på lynrunde (sekunder)').fill('60');
  if(mode==='teams'){await host.getByLabel('Tilfeldige lag',{exact:true}).check();await host.getByLabel('Maks antall spillere per lag').fill('2');}
  await host.getByRole('button',{name:'Lagre spillmodus'}).click();await host.waitForFunction(()=>!document.querySelector('.mode-settings button').disabled);
  for(const [i,p] of [a,b].entries()){await p.goto(base+'/?pin='+created.pin);await p.getByLabel('Kallenavn').fill('Elev '+i);await p.getByRole('button',{name:'Bli med',exact:true}).click();await wait(p,'LOBBY');}
  await host.getByRole('button',{name:mode==='teams'?'Fordel lag og start':'Start første spørsmål'}).click();
  if(mode==='teams'){await wait(host,'TEAM_OVERVIEW');await host.getByRole('button',{name:'Start første spørsmål'}).click();}
  for(let i=0;i<2;i++){
   await Promise.all([host,a,b].map(p=>wait(p,'QUESTION_ACTIVE')));await submit(a);await submit(b);await wait(host,'QUESTION_RESULTS');await host.getByRole('button',{name:'Vis leaderboard'}).click();await wait(host,'LEADERBOARD');
   if(i===0)await host.getByRole('button',{name:'Neste spørsmål'}).click();
  }
  assert.equal((await state(host)).index,1);
  await host.getByRole('button',{name:'Start lynrunde'}).click();await Promise.all([host,a,b].map(p=>wait(p,'LIGHTNING_INTRO')));
  assert.equal(await a.getByRole('button',{name:'Start lynrunde'}).count(),0);
  await host.getByRole('button',{name:'Start lynrunde'}).click();await Promise.all([host,a,b].map(p=>wait(p,'LIGHTNING_COUNTDOWN')));
  const count=await state(host);assert.equal((await state(a)).countdown_end,count.countdown_end);await a.reload();await wait(a,'LIGHTNING_COUNTDOWN');
  await Promise.all([host,a,b].map(p=>wait(p,'LIGHTNING_ACTIVE')));
  const initial=await state(a),initialB=await state(b);assert.equal(initial.deadline,count.countdown_end+60);assert.equal(initialB.deadline,initial.deadline);
  assert.equal(await host.locator('.option-card,.question-media,.question-answer-form').count(),0);assert.equal(await host.locator('.lightning-timer').count(),1);
  await host.screenshot({path:'/tmp/livequiz-lightning-host.png'});await a.screenshot({path:'/tmp/livequiz-lightning-participant.png'});
  const responsePromise=a.waitForResponse(r=>r.url().includes('api=lightning-answer'));
  await submit(a);const response=await(await responsePromise).json();assert.equal(response.state.progress,1);assert.equal(response.state.state,'LIGHTNING_ACTIVE');
  await a.getByText('LYNRUNDE · 2 av 2',{exact:true}).waitFor();assert.equal((await state(b)).progress,0);assert.equal(await a.locator('.chart,.leaderboard-entries,.countdown').count(),0);
  await a.reload();await wait(a,'LIGHTNING_ACTIVE');assert.equal((await state(a)).index,response.state.index);assert.equal((await state(a)).deadline,initial.deadline);
  // Overlapping identical requests must count only once and not skip questions.
  const reply=await a.evaluate(async()=>{const room=new URLSearchParams(location.search).get('room'),token=sessionStorage.getItem('lq-room-'+room),boot=await(await fetch('index.php?api=bootstrap')).json();const s=await(await fetch('index.php?api=state&room='+room,{headers:{'X-Player-Token':token}})).json();const data={room,index:s.index,answer:s.question.type==='text'?'fire':[1]};return Promise.all([1,2].map(async()=>{const r=await fetch('index.php?api=lightning-answer',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':boot.csrf,'X-Player-Token':token},body:JSON.stringify(data)});return r.json();}));});
  assert.ok(reply.every(r=>r.accepted&&r.state.progress===2));await a.getByText('Du har svart på alle spørsmålene!',{exact:true}).waitFor();
  const before=await state(b);await submit(b);await b.getByText('LYNRUNDE · 2 av 2',{exact:true}).waitFor();assert.notEqual((await state(b)).index,before.index);await submit(b);
  await Promise.all([host,a,b].map(p=>wait(p,'LIGHTNING_FINISHED')));const done=await state(host);
  assert.deepEqual(done.leaderboard.map(p=>Number(p.score)),mode==='teams'?[8000]:[4000,4000]);
  await host.getByRole('button',{name:'Vis sluttresultat'}).click();await Promise.all([host,a,b].map(p=>wait(p,'QUIZ_FINISHED')));
 }
 // A separate short round verifies automatic expiry in all connected views.
 const timed=await host.evaluate(async()=>{
  const boot=await(await fetch('index.php?api=bootstrap')).json();const post=async(action,data)=>(await(await fetch('index.php?api='+action,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':boot.csrf},body:JSON.stringify(data)})).json());
  const quiz=await post('save',{content:{title:'Lightning expiry',questions:[{type:'text',prompt:'Skriv fire',code:'',youtube:'',image:null,seconds:120,options:[],correct:[],accepted:['fire']}]}});const room=await post('create',{id:quiz.id});await post('control',{room:room.room,version:1,command:'configure',mode:'individual',max_team_size:3,lightning:{enabled:true,seconds:5}});return room;
 });
 await host.goto(base+'/?host='+timed.room);await host.locator('.pin').waitFor();await a.goto(base+'/?pin='+timed.pin);await a.getByLabel('Kallenavn').fill('Timer');await a.getByRole('button',{name:'Bli med',exact:true}).click();await wait(a,'LOBBY');
 await host.getByRole('button',{name:'Start første spørsmål'}).click();await wait(a,'QUESTION_ACTIVE');await submit(a);await wait(host,'QUESTION_RESULTS');await host.getByRole('button',{name:'Vis leaderboard'}).click();await wait(host,'LEADERBOARD');await host.getByRole('button',{name:'Start lynrunde'}).click();await wait(host,'LIGHTNING_INTRO');await host.getByRole('button',{name:'Start lynrunde'}).click();await wait(a,'LIGHTNING_ACTIVE');
 const timedState=await state(a);await a.reload();await wait(a,'LIGHTNING_ACTIVE');assert.equal((await state(a)).deadline,timedState.deadline);await host.reload();await wait(host,'LIGHTNING_ACTIVE');assert.equal((await state(host)).deadline,timedState.deadline);
 await Promise.all([host,a].map(p=>wait(p,'LIGHTNING_FINISHED')));assert.equal(Number((await state(host)).leaderboard[0].score),1000);
 assert.deepEqual(errors,[]);console.log('Lightning browser checks passed: individual/team full flow, intro, shared countdown/deadline, host timer-only view, independent immediate progression, refresh, overlapping duplicates, completed wait and combined final scores.');
 }finally{await browser.close();}
})();
