/* Uses only the disposable fixture from prepare-local.py. */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH});
 try{
  const base=process.env.LIVEQUIZ_BASE||'http://127.0.0.1:8765';
  const teacher=await browser.newContext({viewport:{width:1280,height:1000}}),t=await teacher.newPage();
  const students=[];for(let i=0;i<5;i++){const context=await browser.newContext({viewport:{width:390,height:844}});students.push(await context.newPage());}
  const errors=[];for(const page of [t,...students])page.on('pageerror',e=>errors.push(e.message));
  const state=page=>page.evaluate(async()=>{const p=new URLSearchParams(location.search),host=p.has('host'),id=p.get(host?'host':'room');return (await fetch('index.php?api=state&room='+id+(host?'&host=1':''),{headers:host?{}:{'X-Player-Token':sessionStorage.getItem('lq-room-'+id)}})).json();});
  const mutate=(page,action,data)=>page.evaluate(async({action,data})=>{const boot=await(await fetch('index.php?api=bootstrap')).json(),id=new URLSearchParams(location.search).get('room');const response=await fetch('index.php?api='+action,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':boot.csrf,...(id?{'X-Player-Token':sessionStorage.getItem('lq-room-'+id)}:{})},body:JSON.stringify(data)});return {status:response.status,body:await response.json()};},{action,data});
  const wait=(page,value)=>page.locator('#app[data-state="'+value+'"]').waitFor();
  const all=async value=>{await Promise.all([t,...students].map(page=>wait(page,value)));const ss=await Promise.all([t,...students].map(state));for(const s of ss){assert.equal(s.state,value);assert.deepEqual(s.teams,ss[0].teams);assert.equal(s.deadline,ss[0].deadline);assert.equal(s.version,ss[0].version);}return ss;};
  await t.goto(base+'/_test_login.php');
  const question={type:'single',prompt:'Velg fire',code:'',youtube:'',image:null,seconds:30,options:['3','4','5','6'],correct:[1],accepted:[]};
  const saved=await mutate(t,'save',{content:{title:'Tilfeldige lag test',questions:[question,{...question,seconds:5}]}});assert.equal(saved.status,200);
  const created=await mutate(t,'create',{id:saved.body.id});assert.equal(created.status,200);
  await t.goto(base+'/?host='+created.body.room);await wait(t,'LOBBY');
  assert.equal(await t.getByRole('radio',{name:'Individuelt spill',exact:true}).isChecked(),true);
  assert.equal(await t.getByLabel('Maks antall spillere per lag').isVisible(),false);
  await t.getByRole('radio',{name:'Tilfeldige lag',exact:true}).check();
  assert.equal(await t.getByLabel('Maks antall spillere per lag').inputValue(),'3');
  await t.getByLabel('Maks antall spillere per lag').fill('2.5');
  assert.equal(await t.getByLabel('Maks antall spillere per lag').evaluate(e=>e.checkValidity()),false);
  await t.getByLabel('Maks antall spillere per lag').fill('4');
  await t.getByRole('button',{name:'Lagre spillmodus',exact:true}).click();
  await t.getByRole('button',{name:'Fordel lag og start',exact:true}).waitFor();
  for(const [i,page] of students.entries()){await page.goto(base+'/?pin='+created.body.pin);await page.getByLabel('Kallenavn').fill('Elev '+i);await page.getByRole('button',{name:'Bli med',exact:true}).click();await wait(page,'LOBBY');}
  await t.getByRole('button',{name:'Fordel lag og start',exact:true}).click();
  await t.getByText(/5 deltakere kan ikke fordeles/).waitFor();
  assert.equal((await state(t)).state,'LOBBY');
  await t.getByLabel('Maks antall spillere per lag').fill('3');await t.getByRole('button',{name:'Lagre spillmodus',exact:true}).click();
  await t.waitForFunction(()=>document.querySelector('#notice').hidden&&document.querySelector('.mode-settings input[type=number]').value==='3');
  // Wait for the saved server version rather than relying on a render timing race.
  await t.waitForFunction(async()=>{const id=new URLSearchParams(location.search).get('host');return (await(await fetch('index.php?api=state&host=1&room='+id)).json()).max_team_size===3;});
  await t.getByRole('button',{name:'Fordel lag og start',exact:true}).click();
  let snapshots=await all('TEAM_OVERVIEW');const teams=snapshots[0].teams;
  assert.deepEqual(teams.map(team=>team.members.length),[3,2]);
  assert.equal(await t.locator('.team-card').count(),2);
  for(const [i,page] of students.entries()){
    assert.equal(await page.locator('.team-card').count(),1);
    assert.equal(await page.locator('.team-card h3').innerText(),snapshots[i+1].teams.find(team=>team.id===snapshots[i+1].my_team).name);
    assert.equal(await page.getByRole('button',{name:'Start første spørsmål',exact:true}).count(),0);
    assert.equal(await page.locator('dialog').evaluate(e=>e.scrollWidth<=e.clientWidth),true);
  }
  await t.screenshot({path:'/tmp/livequiz-teams-host.png'});await students[0].screenshot({path:'/tmp/livequiz-teams-mobile.png'});
  await t.reload();await students[0].reload();await all('TEAM_OVERVIEW');
  assert.deepEqual((await state(t)).teams,teams);
  assert.equal((await mutate(students[0],'control',{room:created.body.room,version:(await state(t)).version,command:'next'})).status,401);
  const lateContext=await browser.newContext(),late=await lateContext.newPage();await late.goto(base+'/?pin='+created.body.pin);await late.getByLabel('Kallenavn').fill('For sent');await late.getByRole('button',{name:'Bli med',exact:true}).click();await late.getByText(/Lagene er allerede fordelt/).waitFor();await lateContext.close();
  await t.getByRole('button',{name:'Start første spørsmål',exact:true}).click();await all('COUNTDOWN');
  await students[1].reload();await wait(students[1],'COUNTDOWN');
  snapshots=await all('QUESTION_ACTIVE');assert.equal(snapshots[0].index,0);
  await students[0].locator('.answer-option:has(.rich:text-is("4"))').click();await students[0].getByRole('button',{name:'Send svar',exact:true}).click();
  await students[0].getByText('Svaret er mottatt. Vent på læreren.',{exact:true}).waitFor();
  await students[0].reload();await students[0].getByText('Svaret er mottatt. Vent på læreren.',{exact:true}).waitFor();
  for(let i=1;i<5;i++)assert.equal((await mutate(students[i],'answer',{room:created.body.room,index:0,answer:[i<3?1:0]})).status,200);
  snapshots=await all('QUESTION_RESULTS');assert.deepEqual(snapshots[0].distribution.counts,[2,3,0,0]);
  for(const s of snapshots)assert.equal(s.distribution.correct,3);
  for(const page of [t,...students])assert.deepEqual((await page.locator('.chart-count').allInnerTexts()).sort(),['0','0','2','3']);
  const expected=new Map(teams.map(team=>[team.id,0]));for(let i=0;i<3;i++)expected.set(snapshots[i+1].my_team,expected.get(snapshots[i+1].my_team)+1000);
  for(const row of snapshots[0].leaderboard)assert.equal(row.score,expected.get(row.id));
  await t.getByRole('button',{name:'Vis leaderboard',exact:true}).click();await all('LEADERBOARD');
  await t.getByRole('heading',{name:'Lagresultater',exact:true}).waitFor();assert.equal(await t.locator('.board li').count(),2);
  const board=await t.locator('.board').innerText();await students[0].reload();await wait(students[0],'LEADERBOARD');assert.equal(await students[0].locator('.board').innerText(),board);
  const version=(await state(t)).version;
  const duplicate=await Promise.all([mutate(t,'control',{room:created.body.room,version,command:'next'}),mutate(t,'control',{room:created.body.room,version,command:'next'})]);
  assert.deepEqual(duplicate.map(r=>r.status).sort(),[200,422]);
  await all('COUNTDOWN');await all('QUESTION_ACTIVE');
  // One disconnected participant remains eligible; the server deadline closes it.
  await students[4].context().setOffline(true);
  for(let i=0;i<4;i++)await mutate(students[i],'answer',{room:created.body.room,index:1,answer:[1]});
  await wait(t,'QUESTION_RESULTS');assert.equal((await state(t)).answers,4);
  await students[4].context().setOffline(false);await students[4].reload();snapshots=await all('QUESTION_RESULTS');
  assert.deepEqual(snapshots[5].teams,teams);assert.equal(snapshots[5].submitted,false);
  await t.getByRole('button',{name:'Vis leaderboard',exact:true}).click();await all('LEADERBOARD');
  await t.getByRole('button',{name:'Vis sluttresultat',exact:true}).click();snapshots=await all('QUIZ_FINISHED');
  assert.equal(snapshots[0].leaderboard.reduce((sum,row)=>sum+row.score,0),7000);
  assert.deepEqual(snapshots[0].teams,teams);assert.equal(await t.locator('.board li').count(),2);
  assert.deepEqual(errors,[]);
  console.log('Team browser flow passed: mode defaults/validation, invalid start and correction, host/mobile overview, stable assignments across refresh/countdown/disconnection, host-only control, late join rejection, individual answer chart, team sums, duplicate progression, deadline and final leaderboard.');
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exit(1);});
