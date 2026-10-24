/* Run only against the disposable prepare-local.py fixture. */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH});
 try {
 const owner=await browser.newContext(),guest=await browser.newContext(),other=await browser.newContext(),student=await browser.newContext();
 const t=await owner.newPage(),g=await guest.newPage(),o=await other.newPage(),s=await student.newPage();
 const participantMedia=[];student.on('request',r=>{if(new URL(r.url()).searchParams.get('api')==='media'||/youtube(?:-nocookie)?\.com/.test(r.url()))participantMedia.push(r.url());});
 const errors=[];for(const page of [t,g,o,s])page.on('pageerror',e=>errors.push(e.message));
 const base=process.env.LIVEQUIZ_BASE||'http://127.0.0.1:8798';
 const call=(page,action,data,headers={})=>page.evaluate(async({action,data,headers})=>{
   const boot=await(await fetch('index.php?api=bootstrap')).json();
   const response=await fetch('index.php?api='+action,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':boot.csrf,...headers},body:JSON.stringify(data)});
   return {status:response.status,body:await response.json()};
 },{action,data,headers});
 await t.goto(base+'/_test_login.php');
 const image=await t.evaluate(async()=>{
   const canvas=document.createElement('canvas');canvas.width=20;canvas.height=20;
   const blob=await new Promise(resolve=>canvas.toBlob(resolve));const data=new FormData();data.append('image',blob,'test.png');
   const boot=await(await fetch('index.php?api=bootstrap')).json();
   return (await(await fetch('index.php?api=upload',{method:'POST',headers:{'X-CSRF-Token':boot.csrf},body:data})).json()).image;
 });
 assert.ok(image.id);
 const quiz={title:'Shared classroom quiz '+Date.now(),questions:[{type:'single',prompt:'What is 2 + 2?',code:'',youtube:'',image:{id:image.id,alt:'Test image'},seconds:120,options:['3','4','5','6'],correct:[1],accepted:[]}]};
 const saved=await call(t,'save',{content:quiz});assert.equal(saved.status,200);
 await t.goto(base+'/?teacher=1');
 const card=t.locator('article').filter({has:t.getByRole('heading',{name:quiz.title,exact:true})});
 await card.getByRole('button',{name:'Del quiz',exact:true}).click();
 const share=await card.getByLabel('Delingslenke').inputValue();assert.ok(new URL(share).hash.includes('key='));
 await g.goto(share);await g.getByRole('heading',{name:quiz.title}).waitFor();
 assert.equal(await g.evaluate(async()=>(await(await fetch('index.php?api=bootstrap')).json()).uid),0);
 await g.getByRole('button',{name:'Start spill for min klasse'}).click();await g.locator('.pin').waitFor();
 const pin=await g.locator('.pin').innerText(),room=new URL(g.url()).searchParams.get('host');
 await o.goto(share);await o.getByRole('button',{name:'Start spill for min klasse'}).click();await o.locator('.pin').waitFor();
 assert.notEqual(await o.locator('.pin').innerText(),pin);
 const ownKey=await o.evaluate(()=>sessionStorage.getItem('lq-host-'+new URLSearchParams(location.search).get('host')));
 assert.equal((await call(o,'control',{room,version:1,command:'next'},{'X-Host-Token':ownKey})).status,422);
 assert.equal((await call(g,'save',{id:saved.body.id,revision:1,content:quiz})).status,401);
 assert.equal((await call(g,'share',{id:saved.body.id,enabled:false})).status,401);
 assert.equal((await call(g,'delete',{id:saved.body.id})).status,401);
 const missingCsrf=await g.evaluate(async room=>(await fetch('index.php?api=control',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({room,version:1,command:'next'})})).status,room);
 assert.equal(missingCsrf,403);
 await g.reload();await g.locator('.pin').waitFor();assert.equal(await g.locator('.pin').innerText(),pin);
 await s.goto(base+'/?pin='+pin);await s.getByLabel('Kallenavn').fill('Student');await s.getByRole('button',{name:'Bli med',exact:true}).click();await s.getByText('Du er med!',{exact:true}).waitFor();
 await g.getByRole('button',{name:'Start første spørsmål'}).click();await g.locator('.countdown').waitFor();
 await g.locator('.active-question-modal').waitFor();await s.locator('.active-question-modal').waitFor();
 await g.waitForFunction(()=>document.querySelector('.question-image')?.naturalWidth>0);
 assert.equal(await s.locator('.question-image').count(),0);
 await s.locator('.answer-option:has(.rich:text-is("4"))').locator('input').check();await s.getByRole('button',{name:'Send svar',exact:true}).click();
 await g.getByRole('heading',{name:'Fasit',exact:true}).waitFor();await s.getByText('Du fikk 1000 poeng.',{exact:true}).waitFor();
 await g.getByRole('button',{name:'Vis leaderboard'}).click();await g.getByRole('heading',{name:'Leaderboard',exact:true}).waitFor();
 await g.getByRole('button',{name:'Vis sluttresultat'}).click();await g.getByRole('heading',{name:'Takk for spillet!'}).waitFor();
 await card.getByRole('button',{name:'Slå av deling'}).click();
 const revoked=await other.newPage();await revoked.goto(share);await revoked.getByRole('alert').filter({hasText:'Delingslenken er ugyldig eller slått av.'}).waitFor();
 await o.reload();await o.locator('.pin').waitFor(); // Existing room survives revocation.
 assert.deepEqual(errors,[]);assert.deepEqual(participantMedia,[]);
 console.log('Sharing browser checks passed: owner link, two account-free hosts, isolated rooms, refresh, guest image display, participant scoring, host progression, edit/delete/share denial, CSRF, and revocation.');
 } finally {await browser.close();}
})();
