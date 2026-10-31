const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH});
 try{
 const host=await browser.newPage({viewport:{width:1280,height:900}}),a=await browser.newPage({viewport:{width:390,height:844}}),b=await browser.newPage({viewport:{width:390,height:844}}),pages=[host,a,b];
 const errors=[];for(const p of pages){p.setDefaultTimeout(15000);p.on('pageerror',e=>errors.push(e.message));}
 const base=process.env.LIVEQUIZ_BASE||'http://127.0.0.1:8796';await host.goto(base+'/_test_login.php');
 const state=p=>p.evaluate(async()=>{const params=new URLSearchParams(location.search),host=params.has('host'),room=params.get(host?'host':'room');return(await(await fetch('index.php?api=state&room='+room+(host?'&host=1':''),{headers:host?{}:{'X-Player-Token':sessionStorage.getItem('lq-room-'+room)}})).json());});
 const wait=(p,phase)=>p.locator('#app[data-state="'+phase+'"]').waitFor();
 const answer=(s,correct=true)=>s.question.type==='text'?(correct?'F I R E':'wrong'):s.question.type==='multi'?(correct?[0,1]:[0]):(correct?[1]:[0]);
 const request=(p,s,correct=true)=>p.evaluate(async({s,value})=>{const boot=await(await fetch('index.php?api=bootstrap')).json();const r=await fetch('index.php?api=race-answer',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':boot.csrf,'X-Player-Token':sessionStorage.getItem('lq-room-'+s.room)},body:JSON.stringify({room:s.room,index:s.index,attempt:s.race.attempt,race_revision:s.race.revision,answer:value})});return {status:r.status,body:await r.json()};},{s,value:answer(s,correct)});
 async function submit(p){
  await p.getByRole('button',{name:'Send svar',exact:true}).waitFor();const s=await state(p);
  if(s.question.image){await p.waitForFunction(()=>document.querySelector('.question-image')?.naturalWidth>0);const img=await p.locator('.question-image').boundingBox(),body=await p.locator('.modal-body').boundingBox();assert.ok(img.height>0&&img.y>=body.y&&img.y+img.height<=body.y+body.height+1);}
  if(s.question.type==='text')await p.getByLabel('Ditt svar').fill('fire');
  else for(const option of (s.question.type==='multi'?['2','3']:['4']))await p.locator('.answer-option').filter({has:p.locator('.rich').getByText(option,{exact:true})}).locator('input').check();
  const response=p.waitForResponse(r=>r.url().includes('api=race-answer'));await p.getByRole('button',{name:'Send svar',exact:true}).click();const reply=await(await response).json();assert.equal(reply.accepted,true);return reply.state;
 }
 for(const mode of ['individual','teams']){
  const created=await host.evaluate(async()=>{
   const boot=await(await fetch('index.php?api=bootstrap')).json();const post=async(action,data)=>(await(await fetch('index.php?api='+action,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':boot.csrf},body:JSON.stringify(data)})).json());
   const canvas=document.createElement('canvas');canvas.width=600;canvas.height=900;const ctx=canvas.getContext('2d');ctx.fillStyle='#e4f3e7';ctx.fillRect(0,0,600,900);ctx.strokeStyle='#146b54';ctx.lineWidth=12;ctx.strokeRect(100,200,400,500);ctx.fillStyle='#17332e';ctx.font='60px sans-serif';ctx.fillText('2 + 2',200,470);const form=new FormData();form.append('image',await new Promise(resolve=>canvas.toBlob(resolve)),'diagram.png');
   const image=(await(await fetch('index.php?api=upload',{method:'POST',headers:{'X-CSRF-Token':boot.csrf},body:form})).json()).image;
   const questions=[{type:'single',prompt:'Hva er $2+2$?',code:'print(2 + 2)\n\n',youtube:'',image,seconds:5,options:['3','4','5','6'],correct:[1],accepted:[]},{type:'multi',prompt:'Velg primtall',code:'',youtube:'',image:null,seconds:5,options:['2','3','4','6'],correct:[0,1],accepted:[]},{type:'text',prompt:'Skriv fire',code:'',youtube:'',image:null,seconds:5,options:[],correct:[],accepted:['fire']}];
   const quiz=await post('save',{content:{title:'Race browser '+Date.now(),questions}});return await post('create',{id:quiz.id});
  });
  await host.goto(base+'/?host='+created.room);await host.locator('.pin').waitFor();
  assert.equal(await host.getByLabel('Spilltype',{exact:true}).inputValue(),'regular');await host.getByLabel('Spilltype',{exact:true}).selectOption('race');assert.equal(await host.getByLabel('Aktiver lynrunde',{exact:true}).isVisible(),false);
  if(mode==='teams'){await host.getByLabel('Tilfeldige lag',{exact:true}).check();await host.getByLabel('Maks antall spillere per lag').fill('2');}
  await host.locator('.mode-settings[data-save-state="saved"]').waitFor();await host.getByRole('button',{name:mode==='teams'?'Fordel lag og start':'Start Quiz Race',exact:true}).waitFor();
  for(const [i,p] of [a,b].entries()){await p.goto(base+'/?pin='+created.pin);await p.getByLabel('Kallenavn').fill('Elev '+i);await p.getByRole('button',{name:'Bli med',exact:true}).click();await wait(p,'LOBBY');}
  await host.getByRole('button',{name:mode==='teams'?'Fordel lag og start':'Start Quiz Race',exact:true}).click();
  if(mode==='teams'){await wait(host,'TEAM_OVERVIEW');await host.getByRole('button',{name:'Start Quiz Race',exact:true}).click();}
  await Promise.all(pages.map(p=>wait(p,'RACE_COUNTDOWN')));assert.equal((await state(host)).countdown_end,(await state(a)).countdown_end);
  await Promise.all(pages.map(p=>wait(p,'RACE_ACTIVE')));assert.equal(await host.locator('.question-answer-form,.question-media').count(),0);
  await host.screenshot({path:'/tmp/livequiz-race-host.png'});
  if(mode==='individual'){
   const next=await submit(a);assert.equal(next.progress,1);assert.ok(next.question);assert.equal((await state(b)).progress,0);
   const before=await state(a);await a.reload();await wait(a,'RACE_ACTIVE');assert.equal((await state(a)).race.revision,before.race.revision);assert.equal((await state(a)).index,before.index);
   const wrong=await state(a);const duplicates=await Promise.all([request(a,wrong,false),request(a,wrong,false)]);assert.deepEqual(duplicates.map(r=>r.status).sort(),[200,422]);assert.equal((await state(a)).race.attempt,1);assert.equal((await state(a)).progress,0);
   await a.getByText('Feil svar! Start på nytt.',{exact:true}).waitFor();await a.screenshot({path:'/tmp/livequiz-race-reset.png'});
   for(const p of [a,b]){await submit(p);await submit(p);}
   const sa=await state(a),sb=await state(b);const finish=await Promise.all([request(a,sa),request(b,sb)]);assert.deepEqual(finish.map(r=>r.status).sort(),[200,422]);
  }else{
   let sa=await state(a);let active=sa.can_answer?a:b,waiting=sa.can_answer?b:a;const initial=await state(active);assert.equal(initial.race.start,0);assert.equal(await waiting.locator('.question-answer-form').count(),0);
   await submit(active);await waiting.getByRole('button',{name:'Send svar',exact:true}).waitFor();const turn=await state(waiting);assert.equal(turn.progress,1);assert.equal(turn.race.start,0);
   const bad=await Promise.all([request(waiting,turn,false),request(waiting,turn,false)]);assert.deepEqual(bad.map(r=>r.status).sort(),[200,422]);
   for(const p of [a,b]){await p.getByText(/Feil svar! Laget må starte på nytt/).waitFor();const s=await state(p);assert.equal(s.race.start,1);assert.equal(s.race.attempt,1);assert.equal(s.progress,0);}
   const before=await state(a);await a.reload();await wait(a,'RACE_ACTIVE');assert.deepEqual((await state(a)).race,before.race);await host.reload();await wait(host,'RACE_ACTIVE');
   for(let i=0;i<3;i++){sa=await state(a);active=sa.can_answer?a:b;await active.getByRole('button',{name:'Send svar',exact:true}).waitFor();if(i===0 && (await state(active)).question.image)await active.waitForFunction(()=>document.querySelector('.question-image')?.naturalWidth>0);if(i===0)await active.screenshot({path:'/tmp/livequiz-race-participant.png'});await submit(active);}
  }
  await Promise.all(pages.map(p=>wait(p,'RACE_FINISHED')));const final=await state(host);assert.ok(final.winner);for(const p of [a,b])assert.equal((await state(p)).winner,final.winner);
  assert.equal(final.race_board.filter(r=>r.completed).length,1);assert.equal(await a.locator('.question-answer-form').count(),0);
  await host.getByRole('button',{name:'Vis sluttresultat',exact:true}).click();await Promise.all(pages.map(p=>wait(p,'QUIZ_FINISHED')));assert.equal((await state(host)).winner,final.winner);
  for(const p of [a,b])assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
 }
 assert.deepEqual(errors,[]);console.log('Individual/team race browser flows passed: configuration, countdown, immediate answers, independent progress, team turns/resets, duplicate failures, refresh, media, concurrent winners and final results.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
