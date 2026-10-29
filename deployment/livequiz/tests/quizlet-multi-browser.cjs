const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH});
 try{
  const base=process.env.LIVEQUIZ_BASE||'http://127.0.0.1:8805',host=await browser.newPage(),players=[];
  for(let i=0;i<3;i++)players.push(await browser.newPage({viewport:{width:390,height:844}}));
  const errors=[];for(const p of [host,...players])p.on('pageerror',e=>errors.push(e.message));
  await host.goto(base+'/_test_login.php');
  const room=await host.evaluate(async()=>{
   const boot=await(await fetch('index.php?api=bootstrap')).json();const headers={'X-CSRF-Token':boot.csrf,'Content-Type':'application/json'};
   const post=async(api,data)=>(await(await fetch('index.php?api='+api,{method:'POST',headers,body:JSON.stringify(data)})).json());
   const q={type:'multi',prompt:'Which answer?',code:'',youtube:'',image:null,seconds:30,options:['Correct A','Correct B','Correct C','Correct D','Wrong A','Wrong B'],correct:[0,1,2,3],accepted:[]};
   const quiz=await post('save',{content:{title:'Quizlet browser',questions:[q]}});return post('create',{id:quiz.id});
  });
  const state=p=>p.evaluate(async()=>{
   const params=new URLSearchParams(location.search),id=params.get('room')||params.get('host'),host=params.has('host');
   return(await(await fetch('index.php?api=state&room='+id+(host?'&host=1':''),{headers:host?{}:{'X-Player-Token':sessionStorage.getItem('lq-room-'+id)}})).json());
  });
  const wait=(p,s)=>p.locator('#app[data-state="'+s+'"]').waitFor();
  await host.goto(base+'/?host='+room.room);await host.getByLabel('Spilltype',{exact:true}).selectOption('quizlet');
  assert.equal(await host.getByLabel('Tilfeldige lag',{exact:true}).isChecked(),true);
  assert.equal(await host.getByLabel('Individuelt spill',{exact:true}).isDisabled(),true);
  assert.equal(await host.getByLabel('Maks antall spillere per lag').getAttribute('max'),'6');
  for(const [i,p] of players.entries()){await p.goto(base+'/?pin='+room.pin);await p.getByLabel('Kallenavn').fill('Member '+i);await p.getByRole('button',{name:'Bli med',exact:true}).click();await wait(p,'LOBBY');}
  await host.getByRole('button',{name:'Start første spørsmål',exact:true}).click();await wait(host,'TEAM_OVERVIEW');
  await host.getByRole('button',{name:'Start Quizlet-like',exact:true}).click();await Promise.all(players.map(p=>wait(p,'RACE_ACTIVE')));
  await host.locator('.race-board progress').waitFor();assert.equal(await host.locator('.race-board progress').count(),1);
  const banner='Flere riktige svar – samarbeid! Alle riktige svar må sendes inn av dem som har dem.';
  for(const p of players)await p.getByText(banner,{exact:true}).waitFor();
  async function submit(p,texts){
   for(const text of texts)await p.locator('.answer-option').filter({has:p.getByText(text,{exact:true})}).locator('input').check();
   const response=p.waitForResponse(r=>r.url().includes('api=race-answer'));
   await p.getByRole('button',{name:'Send svar',exact:true}).click();return(await response).json();
  }
  let states=await Promise.all(players.map(state));
  assert.deepEqual(states.map(s=>s.question.options.length),[2,2,2]);
  const first=states[0].question.options.find(o=>o.startsWith('Correct'));
  let reply=await submit(players[0],[first]);assert.equal(reply.correct,true);assert.equal(reply.state.progress,0);
  await players[0].getByText('Riktig! Svaret er registrert. Laget må sende inn resten av de riktige svarene.',{exact:true}).waitFor();
  await players[0].reload();await wait(players[0],'RACE_ACTIVE');
  assert.equal(await players[0].locator('.answer-option').filter({has:players[0].getByText(first,{exact:true})}).locator('input').isDisabled(),true);
  states=await Promise.all(players.map(state));const wrong=states.findIndex(s=>s.question.options.some(o=>o.startsWith('Wrong')));
  reply=await submit(players[wrong],[states[wrong].question.options.find(o=>o.startsWith('Wrong'))]);assert.equal(reply.correct,false);
  for(const p of players)await p.waitForFunction(()=>document.querySelector('.qcard-head')?.textContent.includes('Forsøk 2'));
  states=await Promise.all(players.map(state));assert.ok(states.every(s=>s.confirmed.length===0));
  // All three members must contribute. A peer's answer must not clear an unsent selection.
  const pending=states[1].question.options.find(o=>o.startsWith('Correct'));
  await players[1].locator('.answer-option').filter({has:players[1].getByText(pending,{exact:true})}).locator('input').check();
  reply=await submit(players[0],states[0].question.options.filter(o=>o.startsWith('Correct')));assert.equal(reply.state.progress,0);
  await players[1].waitForResponse(r=>r.url().includes('api=state'));
  assert.equal(await players[1].locator('.answer-option').filter({has:players[1].getByText(pending,{exact:true})}).locator('input').isChecked(),true);
  reply=await submit(players[1],states[1].question.options.filter(o=>o.startsWith('Correct')));assert.equal(reply.state.progress,0);
  reply=await submit(players[2],states[2].question.options.filter(o=>o.startsWith('Correct')));assert.equal(reply.state.state,'RACE_FINISHED');
  await wait(host,'RACE_FINISHED');for(const p of players)await wait(p,'RACE_FINISHED');
  await host.getByRole('button',{name:'Spill igjen med samme spillere',exact:true}).click();await wait(host,'LOBBY');
  await host.getByLabel('Spilltype',{exact:true}).selectOption('regular');assert.equal(await host.getByLabel('Individuelt spill',{exact:true}).isDisabled(),false);
  assert.deepEqual(errors,[]);console.log('Quizlet multi-answer browser passed: banner, partial answers, refresh, disabled confirmed choices, reset, preserved teammate selection, collective completion and replay.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
