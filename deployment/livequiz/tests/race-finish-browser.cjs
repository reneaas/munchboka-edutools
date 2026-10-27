const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH});
 try{
 const host=await browser.newPage(),a=await browser.newPage(),b=await browser.newPage(),pages=[host,a,b];const errors=[];
 for(const p of pages){p.setDefaultTimeout(12000);p.on('pageerror',e=>errors.push(e.message));}
 const base=process.env.LIVEQUIZ_BASE||'http://127.0.0.1:8793';await host.goto(base+'/_test_login.php');
 const wait=(p,phase)=>p.locator('#app[data-state="'+phase+'"]').waitFor();
 const state=p=>p.evaluate(async()=>{const params=new URLSearchParams(location.search),isHost=params.has('host'),room=params.get(isHost?'host':'room');return(await(await fetch('index.php?api=state&room='+room+(isHost?'&host=1':''),{headers:isHost?{}:{'X-Player-Token':sessionStorage.getItem('lq-room-'+room)}})).json());});
 for(const mode of ['individual','teams']){
  const room=await host.evaluate(async()=>{const boot=await(await fetch('index.php?api=bootstrap')).json();const post=async(action,data)=>(await(await fetch('index.php?api='+action,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':boot.csrf},body:JSON.stringify(data)})).json());const q=await post('save',{content:{title:'End active race',questions:Array.from({length:3},()=>({type:'single',prompt:'2+2?',code:'',youtube:'',image:null,seconds:30,options:['3','4'],correct:[1],accepted:[]}))}});return await post('create',{id:q.id});});
  await host.goto(base+'/?host='+room.room);await host.getByLabel('Spilltype',{exact:true}).selectOption('race');
  if(mode==='teams'){await host.getByLabel('Tilfeldige lag',{exact:true}).check();await host.getByLabel('Maks antall spillere per lag').fill('2');}
  for(const [i,p] of [a,b].entries()){await p.goto(base+'/?pin='+room.pin);await p.getByLabel('Kallenavn').fill('P'+i);await p.getByRole('button',{name:'Bli med',exact:true}).click();await wait(p,'LOBBY');}
  await host.getByRole('button',{name:'Start første spørsmål',exact:true}).click();
  if(mode==='teams'){await wait(host,'TEAM_OVERVIEW');await host.getByRole('button',{name:'Start Quiz Race',exact:true}).click();}
  await Promise.all(pages.map(p=>wait(p,'RACE_ACTIVE')));
  const frozen=await state(host),pattern='**/index.php?api=state*';
  await host.route(pattern,route=>route.fulfill({json:frozen}));
  const active=(await state(a)).can_answer?a:b;
  await active.locator('.answer-option:has(.rich:text-is("4")) input').check();const answer=active.waitForResponse(r=>r.url().includes('api=race-answer'));await active.getByRole('button',{name:'Send svar',exact:true}).click();await answer;
  assert.ok((await state(a)).version>frozen.version);
  const end=host.waitForResponse(r=>r.url().includes('api=control'));await host.getByRole('button',{name:'Avslutt spillet',exact:true}).click();const response=await end;
  assert.equal(response.status(),200);assert.equal(response.request().postDataJSON().version,frozen.version);
  await Promise.all(pages.map(p=>wait(p,'QUIZ_FINISHED')));assert.equal((await state(a)).winner,null);assert.equal(await a.locator('.question-answer-form').count(),0);
  await host.unroute(pattern);await host.getByRole('button',{name:'Spill igjen med samme spillere',exact:true}).click();await Promise.all(pages.map(p=>wait(p,'LOBBY')));
 }
 assert.deepEqual(errors,[]);console.log('Early race finish works with a deliberately stale host view in individual and team modes; participants stop and can return to the same lobby.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
