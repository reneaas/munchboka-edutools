const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH});
 try{
 const host=await browser.newPage(),a=await browser.newPage({viewport:{width:390,height:844}}),b=await browser.newPage(),pages=[host,a,b];const errors=[];
 for(const p of pages){p.setDefaultTimeout(12000);p.on('pageerror',e=>errors.push(e.message));}
 const base=process.env.LIVEQUIZ_BASE||'http://127.0.0.1:8795';await host.goto(base+'/_test_login.php');
 const state=p=>p.evaluate(async()=>{const params=new URLSearchParams(location.search),host=params.has('host'),room=params.get(host?'host':'room');return(await(await fetch('index.php?api=state&room='+room+(host?'&host=1':''),{headers:host?{}:{'X-Player-Token':sessionStorage.getItem('lq-room-'+room)}})).json());});
 const wait=(p,phase)=>p.locator('#app[data-state="'+phase+'"]').waitFor();
 const all=phase=>Promise.all(pages.map(p=>wait(p,phase)));
 const created=await host.evaluate(async()=>{const boot=await(await fetch('index.php?api=bootstrap')).json();const post=async(action,data)=>(await(await fetch('index.php?api='+action,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':boot.csrf},body:JSON.stringify(data)})).json());const quiz=await post('save',{content:{title:'Replay browser',questions:[{type:'single',prompt:'2 + 2?',code:'',youtube:'',image:null,seconds:60,options:['3','4','5','6'],correct:[1],accepted:[]}]}});return await post('create',{id:quiz.id});});
 await host.goto(base+'/?host='+created.room);await wait(host,'LOBBY');
 for(const [i,p] of [a,b].entries()){await p.goto(base+'/?pin='+created.pin);await p.getByLabel('Kallenavn').fill('Elev '+i);await p.getByRole('button',{name:'Bli med',exact:true}).click();await wait(p,'LOBBY');}
 const tokens=await Promise.all([a,b].map(p=>p.evaluate(room=>sessionStorage.getItem('lq-room-'+room),created.room)));
 async function submit(p){await p.locator('.answer-option:has(.rich:text-is("4")) input').check();await p.getByRole('button',{name:'Send svar',exact:true}).click();}
 for(let run=0;run<4;run++){
  if(run===2){await host.getByLabel('Spilltype',{exact:true}).selectOption('race');await host.getByLabel('Tilfeldige lag',{exact:true}).check();await host.getByLabel('Maks antall spillere per lag').fill('2');await host.getByRole('button',{name:'Lagre spillmodus'}).click();await host.waitForFunction(()=>!document.querySelector('.mode-settings button').disabled);}
  if(run===3){await host.getByLabel('Spilltype',{exact:true}).selectOption('regular');await host.getByLabel('Individuelt spill',{exact:true}).check();await host.getByLabel('Aktiver lynrunde',{exact:true}).check();await host.getByRole('button',{name:'Lagre spillmodus'}).click();await host.getByRole('button',{name:'Start første spørsmål',exact:true}).waitFor();}
  await host.getByRole('button',{name:run===2?'Fordel lag og start':'Start første spørsmål',exact:true}).click();
  if(run===2){await all('TEAM_OVERVIEW');await host.getByRole('button',{name:'Start Quiz Race',exact:true}).click();await all('RACE_ACTIVE');const active=(await state(a)).can_answer?a:b;await submit(active);await all('RACE_FINISHED');}
  else{
   await all('QUESTION_ACTIVE');assert.equal((await state(a)).run,run);assert.equal((await state(a)).submitted,false);
   if(run===1){const status=await a.evaluate(async room=>{const boot=await(await fetch('index.php?api=bootstrap')).json();return(await fetch('index.php?api=answer',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':boot.csrf,'X-Player-Token':sessionStorage.getItem('lq-room-'+room)},body:JSON.stringify({room,run:0,index:0,answer:[1]})})).status;},created.room);assert.equal(status,422);}
   await submit(a);await submit(b);await all('QUESTION_RESULTS');await host.getByRole('button',{name:'Vis leaderboard',exact:true}).click();await all('LEADERBOARD');
   for(const row of (await state(host)).leaderboard)assert.equal(Number(row.score),1000);
   if(run===3){await host.getByRole('button',{name:'Start lynrunde',exact:true}).click();await all('LIGHTNING_INTRO');await host.getByRole('button',{name:'Start lynrunde',exact:true}).click();await all('LIGHTNING_ACTIVE');await submit(a);await submit(b);await all('LIGHTNING_FINISHED');for(const row of (await state(host)).leaderboard)assert.equal(Number(row.score),2000);}
   else{await host.getByRole('button',{name:'Vis sluttresultat',exact:true}).click();await all('QUIZ_FINISHED');}
  }
  assert.equal(await a.getByRole('button',{name:'Spill igjen med samme spillere',exact:true}).count(),0);
  if(run===0)await host.screenshot({path:'/tmp/livequiz-replay-end.png'});
  await host.getByRole('button',{name:'Spill igjen med samme spillere',exact:true}).click();await all('LOBBY');
  const lobby=await state(host);assert.equal(lobby.pin,created.pin);assert.equal(lobby.players,2);assert.equal(lobby.run,run+1);assert.equal(lobby.teams.length,0);
  assert.equal(lobby.mode,run===2?'teams':'individual');assert.equal(lobby.game,run===2?'race':'regular');
  assert.deepEqual(await Promise.all([a,b].map(p=>p.evaluate(room=>sessionStorage.getItem('lq-room-'+room),created.room))),tokens);
 }
 // A successful answer response delayed across a replay must not mark the new question answered.
 await host.getByRole('button',{name:'Start første spørsmål',exact:true}).click();await all('QUESTION_ACTIVE');
 let release,received;const gate=new Promise(resolve=>release=resolve),serverReceived=new Promise(resolve=>received=resolve);
 await a.route('**/index.php?api=answer',async route=>{const response=await route.fetch();received();await gate;await route.fulfill({response});});
 await submit(a);await serverReceived;
 await host.getByRole('button',{name:'Avslutt spillet',exact:true}).click();await all('QUIZ_FINISHED');
 await host.getByRole('button',{name:'Spill igjen med samme spillere',exact:true}).click();await all('LOBBY');
 await host.getByRole('button',{name:'Start første spørsmål',exact:true}).click();await all('QUESTION_ACTIVE');
 const response=a.waitForResponse(r=>r.url().includes('api=answer'));release();await response;
 await a.waitForFunction(()=>!document.querySelector('.question-answer-form button').disabled);
 assert.equal((await state(a)).submitted,false);assert.equal(await a.getByText('Svaret er mottatt. Vent på læreren.',{exact:true}).count(),0);
 await a.unroute('**/index.php?api=answer');await submit(a);await submit(b);await all('QUESTION_RESULTS');
 await host.getByRole('button',{name:'Avslutt spillet',exact:true}).click();await all('QUIZ_FINISHED');await host.getByRole('button',{name:'Spill igjen med samme spillere',exact:true}).click();await all('LOBBY');
 await a.reload();await wait(a,'LOBBY');assert.equal((await state(a)).players,2);assert.deepEqual(errors,[]);
 console.log('Replay browser checks passed: same players/PIN/tokens, normal replay, cooperative race and Lightning Round switching, fresh scores, old-answer rejection, host-only controls and reconnect.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
