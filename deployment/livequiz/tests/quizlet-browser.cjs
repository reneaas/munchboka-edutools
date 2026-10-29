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
   const q={type:'single',prompt:'Which answer?',code:'',youtube:'',image:null,seconds:30,options:['Correct','Wrong A','Wrong B','Wrong C'],correct:[0],accepted:[]};
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
  assert.equal(await host.getByLabel('Maks antall spillere per lag').getAttribute('max'),'4');
  for(const [i,p] of players.entries()){await p.goto(base+'/?pin='+room.pin);await p.getByLabel('Kallenavn').fill('Member '+i);await p.getByRole('button',{name:'Bli med',exact:true}).click();await wait(p,'LOBBY');}
  await host.getByRole('button',{name:'Start første spørsmål',exact:true}).click();await wait(host,'TEAM_OVERVIEW');
  await host.getByRole('button',{name:'Start Quizlet-like',exact:true}).click();await Promise.all(players.map(p=>wait(p,'RACE_ACTIVE')));
  await host.locator('.race-board progress').waitFor();assert.equal(await host.locator('.race-board progress').count(),1);
  async function answer(correct){
   const states=await Promise.all(players.map(state));assert.equal(new Set(states.map(s=>s.index)).size,1);
   assert.deepEqual(states.flatMap(s=>s.question.options).sort(),['Correct','Wrong A','Wrong B','Wrong C'].sort());
   assert.deepEqual(states.map(s=>s.question.options.length).sort(),[1,1,2]);
   const i=states.findIndex(s=>s.question.options.some(o=>(o==='Correct')===correct));const p=players[i],s=states[i],text=s.question.options.find(o=>(o==='Correct')===correct);
   await p.locator('.answer-option').filter({has:p.getByText(text,{exact:true})}).locator('input').check();
   const response=p.waitForResponse(r=>r.url().includes('api=race-answer'));await p.locator('.answer-option input:checked').press('Enter');
   const reply=await(await response).json();assert.equal(reply.correct,correct);
   if(reply.state.state==='RACE_ACTIVE'){
    for(const page of players){
     const expected=await state(page);
     await page.waitForFunction(expected=>{
      const labels=Array.from(document.querySelectorAll('.answer-option .rich'),e=>e.textContent).sort();
      return document.querySelector('.qcard-head')?.textContent.includes('Forsøk '+(expected.race.attempt+1))
       && document.querySelector('.modal-header>.rich')?.textContent===expected.question.prompt
       && JSON.stringify(labels)===JSON.stringify([...expected.question.options].sort());
     },expected);
    }
   }
   return reply;
  }
  await answer(false);for(const p of players)await p.getByText('Feil svar! Laget starter på nytt med nye svaralternativer.').waitFor();
  await answer(true);await answer(true);await wait(host,'RACE_FINISHED');
  for(const p of players)await wait(p,'RACE_FINISHED');
  await host.getByRole('button',{name:'Spill igjen med samme spillere',exact:true}).click();await wait(host,'LOBBY');
  await host.getByLabel('Spilltype',{exact:true}).selectOption('regular');assert.equal(await host.getByLabel('Individuelt spill',{exact:true}).isDisabled(),false);
  assert.deepEqual(errors,[]);console.log('Quizlet-like browser passed: team-only configuration, distributed choices, mobile selection + Enter, shared reset/progression, host progress, winner and replay.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
