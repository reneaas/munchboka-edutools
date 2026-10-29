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
   const q={type:'text',prompt:'Which answer?',code:'',youtube:'',image:null,seconds:30,options:[],correct:[],accepted:['Right left','0.25']};
   const quiz=await post('save',{content:{title:'Quizlet browser',questions:[q,{...q,prompt:'Second question'}]}});return post('create',{id:quiz.id});
  });
  const state=p=>p.evaluate(async()=>{
   const params=new URLSearchParams(location.search),id=params.get('room')||params.get('host'),host=params.has('host');
   return(await(await fetch('index.php?api=state&room='+id+(host?'&host=1':''),{headers:host?{}:{'X-Player-Token':sessionStorage.getItem('lq-room-'+id)}})).json());
  });
  const wait=(p,s)=>p.locator('#app[data-state="'+s+'"]').waitFor();
  await host.goto(base+'/?host='+room.room);await host.getByLabel('Spilltype',{exact:true}).selectOption('quizlet');
  assert.equal(await host.getByLabel('Tilfeldige lag',{exact:true}).isChecked(),true);
  assert.equal(await host.getByLabel('Individuelt spill',{exact:true}).isDisabled(),true);
  assert.equal(await host.getByLabel('Maks antall spillere per lag').getAttribute('max'),'60');
  for(const [i,p] of players.entries()){await p.goto(base+'/?pin='+room.pin);await p.getByLabel('Kallenavn').fill('Member '+i);await p.getByRole('button',{name:'Bli med',exact:true}).click();await wait(p,'LOBBY');}
  await host.getByRole('button',{name:'Start første spørsmål',exact:true}).click();await wait(host,'TEAM_OVERVIEW');
  await host.getByRole('button',{name:'Start Quizlet-like',exact:true}).click();await Promise.all(players.map(p=>wait(p,'RACE_ACTIVE')));
  await host.locator('.race-board progress').waitFor();assert.equal(await host.locator('.race-board progress').count(),1);
  const notice='Alle på laget kan skrive. Første riktige svar tar laget videre. Feil svar nullstiller laget.';
  for(const p of players){
   await p.getByText(notice,{exact:true}).waitFor();await p.getByLabel('Ditt svar').waitFor();
   await p.waitForFunction(()=>!document.querySelector('.question-answer-form button').disabled);
  }
  async function typeAnswer(p,value){
   await p.getByLabel('Ditt svar').fill(value);
   const response=p.waitForResponse(r=>r.url().includes('api=race-answer'));
   await p.getByLabel('Ditt svar').press('Enter');return(await response).json();
  }
  let reply=await typeAnswer(players[1],'wrong');assert.equal(reply.correct,false);
  for(const p of players)await p.waitForFunction(()=>document.querySelector('.qcard-head')?.textContent.includes('Forsøk 2'));
  reply=await typeAnswer(players[2],'R I G H T  left');assert.equal(reply.correct,true);assert.equal(reply.state.progress,1);
  for(const p of players)await p.waitForFunction(()=>document.querySelector('.qcard-timer')?.textContent==='1 / 2 riktige');
  await players[0].reload();await wait(players[0],'RACE_ACTIVE');await players[0].getByLabel('Ditt svar').waitFor();
  reply=await typeAnswer(players[0],'0,25');assert.equal(reply.correct,true);assert.equal(reply.state.state,'RACE_FINISHED');
  await wait(host,'RACE_FINISHED');for(const p of players)await wait(p,'RACE_FINISHED');
  await host.getByRole('button',{name:'Spill igjen med samme spillere',exact:true}).click();await wait(host,'LOBBY');
  await host.getByLabel('Spilltype',{exact:true}).selectOption('regular');assert.equal(await host.getByLabel('Individuelt spill',{exact:true}).isDisabled(),false);
  assert.deepEqual(errors,[]);console.log('Quizlet typed browser passed: text-only configuration, input for all members, Enter submission, reset, normalized answers, shared progress, refresh, winner and replay.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
