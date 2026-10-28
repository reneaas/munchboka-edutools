/* Disposable local fixture only. */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH});
 try{
 const base=process.env.LIVEQUIZ_BASE||'http://127.0.0.1:8797';
 const owner=await browser.newPage(),guest=await browser.newPage({viewport:{width:390,height:844}});
 const errors=[];for(const p of [owner,guest])p.on('pageerror',e=>errors.push(e.message));
 await owner.goto(base+'/_test_login.php');await owner.goto(base+'/?new=1');
 await owner.getByLabel('Quizens tittel').fill('Discovery browser fixture');
 assert.equal(await owner.getByLabel('Privat – bare jeg kan starte nye spill').isChecked(),false);
 await owner.getByLabel('Spørsmål',{exact:true}).fill('Hva er 2+2?');
 for(const [i,v] of ['1','2','3','4'].entries())await owner.getByLabel('Alternativ '+(i+1),{exact:true}).fill(v);
 await owner.getByLabel('Riktig 4',{exact:true}).check();await owner.getByRole('button',{name:'Lagre quiz',exact:true}).click();await owner.getByText('Lagret · versjon 1',{exact:true}).waitFor();
 const id=new URL(owner.url()).searchParams.get('edit');
 await guest.goto(base+'/?search=1');await guest.getByLabel('Søk etter tittel').fill('Discovery browser fixture');await guest.getByRole('button',{name:'Søk',exact:true}).click();
 await guest.getByRole('heading',{name:'Discovery browser fixture',exact:true}).waitFor();await guest.screenshot({path:'/tmp/livequiz-public-search.png'});
 await guest.getByRole('link',{name:'Åpne quiz',exact:true}).click();await guest.getByRole('button',{name:'Start spill for min klasse',exact:true}).click();await guest.locator('.pin').waitFor();
 assert.equal(await guest.evaluate(async()=>(await(await fetch('index.php?api=bootstrap')).json()).uid),0);
 const game=guest.url();await guest.reload();await guest.locator('.pin').waitFor();
 await owner.getByLabel('Privat – bare jeg kan starte nye spill').check();await owner.getByRole('button',{name:'Lagre quiz',exact:true}).click();await owner.getByText('Lagret · versjon 2',{exact:true}).waitFor();await owner.reload();assert.equal(await owner.getByLabel('Privat – bare jeg kan starte nye spill').isChecked(),true);
 // Existing guest room survives visibility changes.
 await guest.getByRole('button',{name:'Start første spørsmål',exact:true}).click();await guest.locator('.active-question-modal').waitFor();
 await guest.goto(base+'/?search=1&q=Discovery%20browser%20fixture');await guest.getByText('Ingen offentlige quizer funnet.').waitFor();
 const denied=await guest.evaluate(async id=>{
  const boot=await(await fetch('index.php?api=bootstrap')).json();
  const detail=await fetch('index.php?api=public-quiz&id='+id);
  const create=await fetch('index.php?api=public-start',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':boot.csrf},body:JSON.stringify({id,host_token:'a'.repeat(64)})});
  const missingCsrf=await fetch('index.php?api=public-start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,host_token:'a'.repeat(64)})});
  return [detail.status,create.status,missingCsrf.status];
 },id);assert.deepEqual(denied,[422,422,403]);
 await owner.getByLabel('Privat – bare jeg kan starte nye spill').uncheck();await owner.getByRole('button',{name:'Lagre quiz',exact:true}).click();await owner.getByText('Lagret · versjon 3',{exact:true}).waitFor();
 await owner.goto(base+'/?search=1&q=Discovery%20browser%20fixture');await owner.getByRole('heading',{name:'Discovery browser fixture',exact:true}).waitFor();
 await guest.reload();await guest.getByRole('heading',{name:'Discovery browser fixture',exact:true}).waitFor();
 assert.deepEqual(errors,[]);console.log('Public discovery browser checks passed: public default, owner toggle, anonymous and signed-in search, guest hosting and refresh, private access denial, CSRF and existing-game preservation.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
