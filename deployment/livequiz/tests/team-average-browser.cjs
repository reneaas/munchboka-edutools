const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH});
 try{
 const base=process.env.LIVEQUIZ_BASE||'http://127.0.0.1:8829',host=await browser.newPage(),players=[];
 await host.goto(base+'/_test_login.php');
 const room=await host.evaluate(async()=>{
  const boot=await(await fetch('index.php?api=bootstrap')).json(),headers={'X-CSRF-Token':boot.csrf,'Content-Type':'application/json'};
  const post=async(api,data)=>(await(await fetch('index.php?api='+api,{method:'POST',headers,body:JSON.stringify(data)})).json());
  const q=await post('save',{content:{title:'Average team score',questions:[{type:'single',prompt:'Choose',code:'',youtube:'',image:null,seconds:120,options:['Correct','Wrong'],correct:[0],accepted:[]}]}});return post('create',{id:q.id});
 });
 await host.goto(base+'/?host='+room.room);await host.getByLabel('Tilfeldige lag',{exact:true}).check();await host.getByLabel('Maks antall spillere per lag').fill('4');
 for(let i=0;i<7;i++){const p=await browser.newPage();players.push(p);await p.goto(base+'/?pin='+room.pin);await p.getByLabel('Kallenavn').fill('P'+i);await p.getByRole('button',{name:'Bli med',exact:true}).click();await p.locator('#app[data-state="LOBBY"]').waitFor();}
 await host.getByRole('button',{name:'Fordel lag og start',exact:true}).click();await host.locator('#app[data-state="TEAM_OVERVIEW"]').waitFor();
 const state=()=>host.evaluate(async()=>{const room=new URLSearchParams(location.search).get('host');return(await(await fetch('index.php?api=state&host=1&room='+room)).json());});
 const teams=(await state()).teams;assert.deepEqual(teams.map(t=>t.members.length).sort(),[3,4]);
 const correctNames=new Set(teams.flatMap(t=>t.members.slice(0,t.members.length-1).map(m=>m.nickname)));
 await host.getByRole('button',{name:'Start første spørsmål',exact:true}).click();
 for(const [i,p] of players.entries()){await p.locator('#app[data-state="QUESTION_ACTIVE"]').waitFor();await p.locator('.answer-option').filter({hasText:correctNames.has('P'+i)?'Correct':'Wrong'}).locator('input').check();await p.getByRole('button',{name:'Send svar',exact:true}).click();}
 await host.locator('#app[data-state="QUESTION_RESULTS"]').waitFor();const results=await state();assert.equal(results.leaderboard[0].members.length,4);assert.equal(results.leaderboard[0].score,750);assert.equal(results.leaderboard[1].score,667);
 await host.getByRole('button',{name:'Vis leaderboard',exact:true}).click();await host.getByText('667 poeng',{exact:true}).waitFor();await host.getByText('750 poeng',{exact:true}).waitFor();await players[0].getByText('667 poeng',{exact:true}).waitFor();
 await host.reload();await host.getByText('667 poeng',{exact:true}).waitFor();console.log('Team averages passed: 3/4 member teams, rounded server averages, ranking, whole-point display, participant view and reload.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
