// Three classrooms, separate teacher and student sessions; disposable fixture only.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH});
 const errors=[];
 async function page(){const context=await browser.newContext({viewport:{width:1280,height:900}});await require('./youtube-stub.cjs')(context);await context.addInitScript(()=>{const Native=window.Audio;window.__audios=[];window.Audio=function(...args){const audio=new Native(...args);window.__audios.push(audio);return audio;};});const p=await context.newPage();p.on('pageerror',e=>errors.push(e.message));return p;}
 const base=process.env.LIVEQUIZ_BASE||'http://127.0.0.1:8765';
 const state=p=>p.evaluate(async()=>{const params=new URLSearchParams(location.search),room=params.get('host')||params.get('cohost')||params.get('room'),headers={};if(params.has('cohost'))headers['X-Cohost-Token']=sessionStorage.getItem('lq-cohost-'+room);if(params.has('room'))headers['X-Player-Token']=sessionStorage.getItem('lq-room-'+room);return(await fetch('index.php?api=state&room='+room+(!params.has('room')?'&host=1':''),{headers})).json();});
 const wait=(p,s)=>p.locator('#app[data-state="'+s+'"]').waitFor({state:'attached'});
 try{
  const main=await page();await main.goto(base+'/_test_login.php');
  const room=await main.evaluate(async()=>{
   const b=await(await fetch('index.php?api=bootstrap')).json();const headers={'Content-Type':'application/json','X-CSRF-Token':b.csrf};
   const q={type:'single',prompt:'Class Battle question one',code:'',youtube:'',image:null,seconds:60,options:['Yes','No'],correct:[0],accepted:[]};
   const quiz=await(await fetch('index.php?api=save',{method:'POST',headers,body:JSON.stringify({content:{title:'Three classrooms',questions:[q,{...q,prompt:'Class Battle question two'}]}})})).json();
   return(await(await fetch('index.php?api=create',{method:'POST',headers,body:JSON.stringify({id:quiz.id})})).json());
  });
  await main.goto(base+'/?host='+room.room);await main.getByLabel('Spilltype').selectOption('classbattle');
  await main.getByRole('button',{name:'Inviter medvert',exact:true}).waitFor();
  const codeA=await main.locator('.lobby-code-summary .pin').innerText();
  const urls=[];
  for(let i=0;i<3;i++){
   await main.getByRole('button',{name:'Inviter medvert',exact:true}).click();
   await main.locator('.battle-invitation').nth(i).waitFor();
   urls.push(await main.locator('.battle-invitation input').nth(i).inputValue());
  }
  assert.equal(new Set(urls).size,3);
  assert.equal(await main.getByRole('button',{name:'Kopier invitasjonslenke',exact:true}).count(),3);
  await main.context().grantPermissions(['clipboard-read','clipboard-write']);
  for(let i=0;i<3;i++){
   await main.getByRole('button',{name:'Kopier invitasjonslenke',exact:true}).nth(i).click();
   assert.equal(await main.evaluate(()=>navigator.clipboard.readText()),urls[i]);
  }
  await main.screenshot({path:'/private/tmp/class-battle-invitations.png',fullPage:true});
  await main.reload();await wait(main,'LOBBY');
  assert.deepEqual(await main.locator('.battle-invitation input').evaluateAll(inputs=>inputs.map(i=>i.value)),urls);
  let invitationIndex=0;
  async function invite(name){
   const url=urls[invitationIndex++];
   const p=await page();await p.goto(url);await p.getByLabel('Klassenavn').fill(name);await p.getByRole('button',{name:'Bli med som medvert',exact:true}).click();await wait(p,'LOBBY');
   assert.equal(await p.getByRole('button',{name:'Start første spørsmål',exact:true}).count(),0);
   assert.equal(await p.getByRole('button',{name:'Avslutt spillet',exact:true}).count(),0);
   return {page:p,url,code:await p.locator('.lobby-code-summary .pin').innerText()};
  }
  const b=await invite('Class B'),c=await invite('Class C'),d=await invite('Empty class');
  await main.getByText('Godtatt · Class B',{exact:true}).waitFor();
  await b.page.getByRole('button',{name:'Klar',exact:true}).click();
  await main.getByText('1 av 3 medverter klare',{exact:true}).waitFor();
  await b.page.reload();await wait(b.page,'LOBBY');
  await b.page.getByRole('button',{name:'Klar ✓ — angre',exact:true}).click();
  await main.getByText('0 av 3 medverter klare',{exact:true}).waitFor();
  const lobbyStates=await Promise.all([main,b.page,c.page,d.page].map(state));
  for(const s of lobbyStates)assert.deepEqual(s.battle.music,lobbyStates[0].battle.music);
  assert.equal(new Set([codeA,b.code,c.code]).size,3);
  // Opening an already claimed invitation resumes its class, even in a fresh tab.
  await b.page.goto(b.url);await wait(b.page,'LOBBY');
  const students=[];
  for(const [className,code,n] of [['Class A',codeA,3],['Class B',b.code,2],['Class C',c.code,1]]){
   for(let i=0;i<n;i++){const p=await page();await p.goto(base+'/?pin='+code);await p.getByLabel('Kallenavn').fill(className+' '+i);await p.getByRole('button',{name:'Bli med',exact:true}).click();await wait(p,'LOBBY');assert.equal((await state(p)).battle.class_name,className);students.push({page:p,className,index:i});}
  }
  await main.waitForFunction(()=>document.querySelector('.battle-live').textContent.includes('3 elever'));
  const before=await state(b.page);assert.equal(before.lobby_players.length,2);assert.equal(before.battle.results.length,1);
  // A co-host cannot bypass the read-only interface with an API request.
  const denied=await b.page.evaluate(async()=>{
   const room=new URLSearchParams(location.search).get('cohost'),b=await(await fetch('index.php?api=bootstrap')).json();
   return(await fetch('index.php?api=control',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':b.csrf,'X-Cohost-Token':sessionStorage.getItem('lq-cohost-'+room)},body:JSON.stringify({room,command:'finish'})})).status;
  });assert.equal(denied,403);
  await b.page.screenshot({path:'/private/tmp/class-battle-lobby.png',fullPage:true});
  await c.page.setViewportSize({width:390,height:844});
  assert.equal(await c.page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'eight-digit code fits mobile lobby');
  await c.page.screenshot({path:'/private/tmp/class-battle-mobile.png',fullPage:true});
  await c.page.setViewportSize({width:1280,height:900});
  await main.getByRole('button',{name:'Start første spørsmål',exact:true}).click();
  await Promise.all([main,b.page,c.page,...students.map(s=>s.page)].map(p=>wait(p,'QUESTION_ACTIVE')));
  const initial=await Promise.all([main,b.page,c.page].map(state));
  for(const s of initial)assert.deepEqual(s.battle.music,initial[0].battle.music);
  const sources=await Promise.all([main,b.page,c.page].map(p=>p.evaluate(()=>window.__audios[0].src)));
  assert.equal(new Set(sources).size,1);assert(sources[0].includes(initial[0].battle.music.track));assert.equal(new Set(initial.map(s=>s.deadline)).size,1);assert.equal(new Set(initial.map(s=>s.index)).size,1);
  await b.page.screenshot({path:'/private/tmp/class-battle-question.png',fullPage:true});
  // Student and co-host reconnect to the same phase and roster.
  await students[0].page.reload();await wait(students[0].page,'QUESTION_ACTIVE');await c.page.reload();await wait(c.page,'QUESTION_ACTIVE');
  assert.deepEqual((await state(c.page)).battle.music,initial[0].battle.music);
  assert.equal(await c.page.getByRole('button',{name:'Klar',exact:true}).count(),0);
  const late=await page();await late.goto(base+'/?pin='+b.code);await late.getByLabel('Kallenavn').fill('Too late');await late.getByRole('button',{name:'Bli med',exact:true}).click();await late.getByText('Klasselistene er låst.',{exact:false}).waitFor();
  for(let question=0;question<2;question++){
   await Promise.all(students.map(async student=>{
    const correct=student.className==='Class B'||(student.className==='Class A'&&student.index<2)||question===1;
    const p=student.page;await p.locator('.answer-option').filter({hasText:correct?'Yes':'No'}).click();await p.getByRole('button',{name:'Send svar',exact:true}).click();
   }));
   await Promise.all([main,b.page,c.page].map(p=>wait(p,'QUESTION_RESULTS')));
   const standings=await Promise.all([main,b.page,c.page].map(state));assert.deepEqual(standings[0].battle.classes,standings[1].battle.classes);assert.deepEqual(standings[0].battle.classes,standings[2].battle.classes);
   assert.equal(standings[0].battle.classes[0].name,'Class B');
   await main.getByRole('button',{name:'Vis leaderboard',exact:true}).click();await wait(b.page,'LEADERBOARD');
   await main.getByRole('button',{name:question===0?'Neste spørsmål':'Vis sluttresultat',exact:true}).click();
   await Promise.all([main,b.page,c.page,...students.map(s=>s.page)].map(p=>wait(p,question===0?'QUESTION_ACTIVE':'QUIZ_FINISHED')));
  }
  await b.page.getByRole('heading',{name:'Vinner: Class B',exact:true}).waitFor();
  const final=await state(b.page);assert.equal(final.battle.classes[0].score,2000);assert.equal(final.battle.classes.find(c=>c.name==='Class A').count,3);
  await b.page.getByText('Class B · individuelle resultater',{exact:true}).click();
  await b.page.waitForResponse(r=>r.url().includes('api=state'));
  assert.equal(await b.page.locator('details[data-class-name="Class B"]').getAttribute('open'),'');
  assert.equal((await state(main)).battle.results.length,4);
  const mvps=(await state(main)).battle.mvps;
  assert.equal(mvps.length,3);assert.equal(mvps[0].score,2000);
  for(const p of [main,b.page,c.page,d.page]){
   await wait(p,'QUIZ_FINISHED');await p.getByRole('heading',{name:'MVPs',exact:true}).waitFor();
   assert.deepEqual((await state(p)).battle.mvps,mvps);
   assert.equal(await p.locator('.mvp-card').count(),3);
  }
  await b.page.screenshot({path:'/private/tmp/class-battle-final.png',fullPage:true});
  await b.page.setViewportSize({width:390,height:844});
  assert.equal(await b.page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await b.page.screenshot({path:'/private/tmp/class-battle-mvps-mobile.png',fullPage:true});
  assert.deepEqual(errors,[]);console.log('Class Battle browser passed: four teachers, three persistent invitations, readiness toggles, synchronized music after reload, identical global MVPs, classes of 3/2/1 students, distinct entry codes, shared deadlines, individual answers, averages, permission rejection, roster locks, reconnects and final winner.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
