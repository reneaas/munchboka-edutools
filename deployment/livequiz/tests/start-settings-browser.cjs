const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH});
 try{
 const p=await browser.newPage();p.setDefaultTimeout(12000);const errors=[];p.on('pageerror',e=>errors.push(e.message));const base=process.env.LIVEQUIZ_BASE||'http://127.0.0.1:8794';await p.goto(base+'/_test_login.php');
 const room=await p.evaluate(async()=>{const boot=await(await fetch('index.php?api=bootstrap')).json();const post=async(action,data)=>(await(await fetch('index.php?api='+action,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':boot.csrf},body:JSON.stringify(data)})).json());const q=await post('save',{content:{title:'Start settings',questions:[{type:'single',prompt:'2+2?',code:'',youtube:'',image:null,seconds:30,options:['3','4'],correct:[1],accepted:[]}]}});return await post('create',{id:q.id});});
 // Separate participant sessions avoid the existing two-second join rate limit.
 for(let i=0;i<2;i++){const player=await browser.newPage();await player.goto(base+'/?pin='+room.pin);await player.getByLabel('Kallenavn').fill('P'+i);await player.getByRole('button',{name:'Bli med',exact:true}).click();await player.locator('#app[data-state="LOBBY"]').waitFor();}
 await p.goto(base+'/?host='+room.room);await p.locator('.mode-settings').waitFor();
 for(const [game,mode] of [['race','individual'],['regular','teams'],['race','teams'],['regular','individual']]){
  await p.getByLabel('Spilltype',{exact:true}).selectOption(game);await p.getByLabel(mode==='teams'?'Tilfeldige lag':'Individuelt spill',{exact:true}).check();
  if(mode==='teams')await p.getByLabel('Maks antall spillere per lag').fill('2');
  if(game==='regular'){await p.getByLabel('Aktiver lynrunde',{exact:true}).check();await p.getByLabel('Varighet på lynrunde (sekunder)').fill('90');}
  const response=p.waitForResponse(r=>r.url().includes('api=control'));
  await p.getByRole('button',{name:/^(Start første spørsmål|Start Quiz Race|Fordel lag og start)$/}).click();
  const data=await(await response).json();assert.equal(data.state.game,game);assert.equal(data.state.mode,mode);assert.equal(data.state.state,mode==='teams'?'TEAM_OVERVIEW':game==='race'?'RACE_COUNTDOWN':'COUNTDOWN');if(game==='regular')assert.equal(data.state.lightning.seconds,90);
  assert.equal(await p.locator('#notice').isVisible(),false);
  await p.getByRole('button',{name:'Avslutt spillet',exact:true}).click();await p.getByRole('button',{name:'Spill igjen med samme spillere',exact:true}).click();await p.locator('.mode-settings').waitFor();
 }
 // Invalid visible fields must block Start without sending a mutation.
 await p.getByLabel('Tilfeldige lag',{exact:true}).check();await p.getByLabel('Maks antall spillere per lag').fill('1');
 await p.getByRole('button',{name:'Start første spørsmål',exact:true}).click();assert.equal(await p.locator('#app').getAttribute('data-state'),'LOBBY');assert.match(await p.locator('#notice').textContent(),/Kontroller spillinnstillingene/);
 // Explicit Save also updates the version before Start is available again.
 await p.getByLabel('Maks antall spillere per lag').fill('2');await p.getByLabel('Spilltype',{exact:true}).selectOption('race');
 await p.getByRole('button',{name:'Lagre spillmodus',exact:true}).click();await p.getByRole('button',{name:'Fordel lag og start',exact:true}).click();await p.locator('#app[data-state="TEAM_OVERVIEW"]').waitFor();
 assert.deepEqual(errors,[]);console.log('Direct Start passed for regular/race and individual/team modes, replay mode changes, Lightning settings, invalid fields and explicit save followed immediately by start.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
