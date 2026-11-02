const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH});
 try{
 const base=process.env.LIVEQUIZ_BASE||'http://127.0.0.1:8827',host=await browser.newPage(),player=await browser.newPage({viewport:{width:390,height:844}});
 const errors=[];for(const p of [host,player])p.on('pageerror',e=>errors.push(e.message));
 await host.goto(base+'/_test_login.php');
 const fixture=await host.evaluate(async()=>{
  const boot=await(await fetch('index.php?api=bootstrap')).json();const post=async(api,data)=>(await(await fetch('index.php?api='+api,{method:'POST',headers:{'X-CSRF-Token':boot.csrf,'Content-Type':'application/json'},body:JSON.stringify(data)})).json());
  const question={type:'single',prompt:'First question',options:['Correct','Wrong'],correct:[0],accepted:[],seconds:120,code:'',youtube:'',image:null};
  const first=await post('save',{content:{title:'Original quiz',questions:[question]}}),second=await post('save',{content:{title:'Next quiz',questions:[{...question,prompt:'New question'}]}});
  return {first:first.id,second:second.id,...await post('create',{id:first.id})};
 });
 const wait=(p,s)=>p.locator('#app[data-state="'+s+'"]').waitFor();
 await host.goto(base+'/?host='+fixture.room);await wait(host,'LOBBY');
 await player.goto(base+'/?pin='+fixture.pin);await player.getByLabel('Kallenavn').fill('Keep me');await player.getByRole('button',{name:'Bli med',exact:true}).click();await wait(player,'LOBBY');const playerUrl=player.url();
 await host.getByRole('button',{name:'Bytt quiz, behold lobbyen',exact:true}).click();await host.getByRole('button',{name:'Avbryt',exact:true}).click();await host.getByRole('heading',{name:'Original quiz',exact:true}).waitFor();
 await host.getByRole('button',{name:'Start første spørsmål',exact:true}).click();await wait(player,'QUESTION_ACTIVE');
 await player.locator('.answer-option').filter({hasText:'Correct'}).locator('input').check();await player.getByRole('button',{name:'Send svar',exact:true}).click();await wait(host,'QUESTION_RESULTS');
 await host.getByRole('button',{name:'Avslutt spillet',exact:true}).click();await wait(host,'QUIZ_FINISHED');
 await host.getByRole('button',{name:'Bytt quiz, behold lobbyen',exact:true}).click();await host.getByLabel('Velg neste quiz',{exact:true}).selectOption(fixture.second);await host.getByRole('button',{name:'Bytt quiz',exact:true}).click();
 await wait(host,'LOBBY');await wait(player,'LOBBY');await player.getByRole('heading',{name:'Next quiz',exact:true}).waitFor();assert.equal(player.url(),playerUrl);assert.equal(await host.locator('.pin').textContent(),fixture.pin);await host.getByText('Keep me',{exact:true}).waitFor();
 await player.reload();await wait(player,'LOBBY');await host.getByRole('button',{name:'Start første spørsmål',exact:true}).click();await wait(player,'QUESTION_ACTIVE');await player.getByText('New question',{exact:true}).waitFor();
 await player.locator('.answer-option').filter({hasText:'Correct'}).locator('input').check();await player.getByRole('button',{name:'Send svar',exact:true}).click();await wait(player,'QUESTION_RESULTS');await player.getByText('Du fikk 1000 poeng.',{exact:true}).waitFor();
 await host.getByRole('button',{name:'Avslutt spillet',exact:true}).click();await wait(host,'QUIZ_FINISHED');
 await host.getByRole('button',{name:'Bytt quiz, behold lobbyen',exact:true}).click();await host.getByLabel('Velg neste quiz',{exact:true}).selectOption(fixture.first);await host.getByRole('button',{name:'Bytt quiz',exact:true}).click();await wait(host,'LOBBY');
 // A switch can also be made before starting, without requiring anyone to rejoin.
 await host.getByRole('button',{name:'Bytt quiz, behold lobbyen',exact:true}).click();await host.getByLabel('Velg neste quiz',{exact:true}).selectOption(fixture.second);await host.getByRole('button',{name:'Bytt quiz',exact:true}).click();await host.getByRole('heading',{name:'Next quiz',exact:true}).waitFor();await player.getByRole('heading',{name:'Next quiz',exact:true}).waitFor();assert.equal(player.url(),playerUrl);
 assert.deepEqual(errors,[]);console.log('Switch quiz browser passed: cancel, finished-game switch, same PIN/players, reload, new question/scoring and lobby-to-lobby switch.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
