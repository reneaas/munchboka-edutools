const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH});
 try{
 const host=await browser.newPage(),a=await browser.newPage(),late=await browser.newPage({viewport:{width:390,height:844}}),pages=[host,a,late];for(const p of pages)p.setDefaultTimeout(12000);
 const errors=[];for(const p of pages)p.on('pageerror',e=>errors.push(e.message));const base=process.env.LIVEQUIZ_BASE||'http://127.0.0.1:8792';await host.goto(base+'/_test_login.php');
 const wait=(p,s)=>p.locator('#app[data-state="'+s+'"]').waitFor();
 async function join(p,pin,name){await p.goto(base+'/?pin='+pin);await p.getByLabel('Kallenavn').fill(name);await p.getByRole('button',{name:'Bli med',exact:true}).click();}
 async function answer(p){await p.locator('.answer-option:has(.rich:text-is("4")) input').check();await p.getByRole('button',{name:'Send svar',exact:true}).click();}
 for(const game of ['regular','race','lightning'])for(const mode of ['individual','teams']){
  const room=await host.evaluate(async()=>{const boot=await(await fetch('index.php?api=bootstrap')).json();const post=async(action,data)=>(await(await fetch('index.php?api='+action,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':boot.csrf},body:JSON.stringify(data)})).json());const q=await post('save',{content:{title:'Late join',questions:[{type:'single',prompt:'2+2?',code:'',youtube:'',image:null,seconds:60,options:['3','4','5','6'],correct:[1],accepted:[]}]}});return await post('create',{id:q.id});});
  await host.goto(base+'/?host='+room.room);await host.getByLabel('Spilltype',{exact:true}).selectOption(game==='race'?'race':'regular');
  if(mode==='teams'){await host.getByLabel('Tilfeldige lag',{exact:true}).check();await host.getByLabel('Maks antall spillere per lag').fill('2');}
  if(game==='lightning')await host.getByLabel('Aktiver lynrunde',{exact:true}).check();
  await join(a,room.pin,'First');await wait(a,'LOBBY');await host.getByRole('button',{name:'Start første spørsmål',exact:true}).click();
  if(mode==='teams'){await wait(host,'TEAM_OVERVIEW');await host.getByRole('button',{name:game==='race'?'Start Quiz Race':'Start første spørsmål',exact:true}).click();}
  await wait(host,game==='race'?'RACE_COUNTDOWN':'COUNTDOWN');assert.equal(await host.locator('dialog .host-join-code').isVisible(),true);assert.ok((await host.locator('.host-join-code').textContent()).includes(room.pin));
  await wait(a,game==='race'?'RACE_ACTIVE':'QUESTION_ACTIVE');
  if(game==='lightning'){await answer(a);await wait(host,'QUESTION_RESULTS');await host.getByRole('button',{name:'Vis leaderboard',exact:true}).click();await host.getByRole('button',{name:'Start lynrunde',exact:true}).click();await host.getByRole('button',{name:'Start lynrunde',exact:true}).click();await wait(a,'LIGHTNING_ACTIVE');}
  await join(late,room.pin,'Late');await wait(late,mode==='teams'?'WAITING_LOBBY':game==='race'?'RACE_ACTIVE':game==='lightning'?'LIGHTNING_ACTIVE':'QUESTION_ACTIVE');
  assert.equal(await host.locator('dialog .host-join-code').isVisible(),true);assert.equal(await late.locator('.host-join-code').count(),0);
  if(mode==='teams'){assert.equal(await late.getByRole('heading',{name:'Du er i lobbyen',exact:true}).isVisible(),true);await host.getByText(/1 venter på neste spill/).waitFor();await late.reload();await wait(late,'WAITING_LOBBY');}
  if(game==='regular'){await answer(a);if(mode==='individual')await answer(late);await wait(host,'QUESTION_RESULTS');await host.getByRole('button',{name:'Vis leaderboard',exact:true}).click();await host.getByRole('button',{name:'Vis sluttresultat',exact:true}).click();}
  else if(game==='lightning'){await answer(a);if(mode==='individual')await answer(late);await wait(host,'LIGHTNING_FINISHED');}
  else {await answer(mode==='individual'?late:a);await wait(host,'RACE_FINISHED');}
  assert.equal(await host.locator('.host-join-code').isVisible(),true);
  if(mode==='teams')await wait(late,'WAITING_LOBBY');
  if(game==='race'&&mode==='teams')await host.screenshot({path:'/tmp/livequiz-late-code.png'});
  await host.getByRole('button',{name:'Spill igjen med samme spillere',exact:true}).click();await Promise.all(pages.map(p=>wait(p,'LOBBY')));
  if(mode==='teams'){await host.getByRole('button',{name:'Fordel lag og start',exact:true}).click();await wait(late,'TEAM_OVERVIEW');assert.ok((await late.locator('.team-card').textContent()).includes('Late'));}
 }
 assert.deepEqual(errors,[]);console.log('Late join browser checks passed across regular/race/lightning and individual/team modes: visible teacher PIN, immediate individual play, team waiting, reconnect, completion and next-game membership.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
