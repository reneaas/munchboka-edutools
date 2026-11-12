const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const publicDir=path.join(__dirname,'../public');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH});
 try{
  const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
  let saves=[],failNext=false,holdNext=false,release,expired=false,wrongAccount=false,loseNext=false;
  const receipts = new Map();
  async function waitSaved(revision){
   const deadline=Date.now()+10000;
   while(saves.length<revision-1&&Date.now()<deadline)await new Promise(resolve=>setTimeout(resolve,20));
   assert.ok(saves.length>=revision-1,'expected save completed');
   await page.getByText('Lagret på nett',{exact:true}).waitFor();
  }
  const tile=value=>({value,question:'Question '+value,answer:'Answer '+value,questionImage:null,answerImage:null});
  const initial={title:'Draft',categories:[{name:'A',tiles:[100,200,300,400,500].map(tile)},{name:'B',tiles:[100,300,500].map(tile)}]};
  await page.route('http://jeopardy.test/**',async route=>{
   const req=route.request();
   if(req.url().includes('session=1')) { await route.fulfill(expired ? {status:401,json:{error:'expired'}} : {json:{uid:wrongAccount?'11':'10',csrf:'fresh-token'}});return; }
   if(req.method()==='POST'){
    assert.ok(req.postData().includes('fresh-token'), 'save uses refreshed CSRF');
    const content=JSON.parse(req.postData().match(/name="content"\r\n\r\n([\s\S]*?)\r\n--/)[1]);
    if(holdNext){holdNext=false;await new Promise(resolve=>release=resolve);}
    if(failNext){failNext=false;await route.fulfill({status:500,json:{error:'Test save failure'}});return;}
    const key = req.postData().match(/name="revision"\r\n\r\n([\s\S]*?)\r\n--/)[1] + JSON.stringify(content);
    if (!receipts.has(key)) { saves.push(content); receipts.set(key, {id:'a'.repeat(32),revision:saves.length+1}); }
    if (loseNext) { loseNext=false; await route.abort('failed'); return; }
    await route.fulfill({json:receipts.get(key)});return;
   }
   await route.fulfill({contentType:'text/html',body:'<main id="editor"></main>'});
  });
  await page.goto('http://jeopardy.test/');
  await page.evaluate(game=>{const root=document.querySelector('#editor');Object.assign(root.dataset,{game:JSON.stringify(game),id:'a'.repeat(32),revision:'1',csrf:'test',uid:'10'});window.renderMathInElement=()=>{};},initial);
  await page.addScriptTag({path:path.join(publicDir,'editor.js')});
  await page.getByLabel('Velg kategori').selectOption('1');
  await page.getByLabel('Rad 2',{exact:true}).fill('400');
  await page.getByLabel('Rad 2',{exact:true}).press('Tab');
  await waitSaved(2);
  assert.deepEqual(saves[0].categories[0].tiles.map(t=>t.value),[100,200,300,400,500]);
  assert.deepEqual(saves[0].categories[1].tiles.map(t=>t.value),[100,400,500]);
  page.once('dialog',dialog=>dialog.accept());
  await page.getByRole('button',{name:'Fjern rad 2',exact:true}).click();
  await page.getByRole('button',{name:'Legg til rad',exact:true}).click();
  await waitSaved(3);
  assert.deepEqual(saves[1].categories[1].tiles.map(t=>t.value),[100,500,600]);
  holdNext=true;await page.getByLabel('Spillets tittel').fill('First snapshot');
  await page.getByText('Lagrer …',{exact:true}).waitFor();
  while(!release)await new Promise(r=>setTimeout(r,20));
  await page.getByLabel('Spillets tittel').fill('Edit during save');release();
  await waitSaved(5);
  assert.equal(saves[2].title,'First snapshot');assert.equal(saves[3].title,'Edit during save');
  failNext=true;await page.getByLabel('Spillets tittel').fill('Retain failed edit');
  await page.getByText('Test save failure',{exact:true}).waitFor();assert.equal(await page.getByLabel('Spillets tittel').inputValue(),'Retain failed edit');
  await page.getByRole('button',{name:'Lagre på nett',exact:true}).click();
  await waitSaved(6);
  await page.clock.install();
  for(let i=0;i<16;i++){await page.getByLabel('Spillets tittel').fill('Continuous edit '+i);await page.clock.runFor(1000);}
  await waitSaved(7);
  assert.ok(saves.length>=6,'periodic autosave runs while typing continuously');
  await page.clock.resume();
  await page.getByRole('button',{name:'Lagre på nett',exact:true}).click();
  await page.waitForFunction(()=>!document.querySelector('.save-status').textContent.includes('Lagrer'));
  await page.getByLabel('Velg kategori').selectOption('0');
  const beforeSwap = saves.length;
  await page.getByLabel('Rad 5',{exact:true}).fill('300');
  await page.getByLabel('Rad 5',{exact:true}).press('Tab');
  await waitSaved(beforeSwap+2);
  assert.deepEqual(saves.at(-1).categories[0].tiles.map(t=>t.value),[100,200,300,400,500]);
  assert.equal(saves.at(-1).categories[0].tiles[2].question,'Question 500');
  assert.equal(saves.at(-1).categories[0].tiles[4].question,'Question 300');
  assert.equal(saves.at(-1).categories[0].tiles[2].answer,'Answer 500');
  const beforePrivacy = saves.length;
  await page.getByRole('switch').uncheck(); await waitSaved(beforePrivacy+2);
  assert.equal(saves.at(-1).private,false);
  const beforeTimeout = saves.length;
  release = null; holdNext = true;
  await page.getByLabel('Spillets tittel').fill('Recover stalled request');
  await page.getByRole('button',{name:'Lagre på nett',exact:true}).click();
  while (!release) await new Promise(r=>setTimeout(r,20));
  await page.clock.runFor(20001);
  await page.getByText('Forbindelsen ble brutt.',{exact:false}).waitFor();
  assert.equal(await page.getByRole('button',{name:'Lagre på nett',exact:true}).isEnabled(),true,'timed-out request releases save button');
  release();
  await page.getByText('Lagret på nett',{exact:true}).waitFor();
  assert.equal(saves.length,beforeTimeout+1,'timeout retries exact snapshot');
  const beforeLost = saves.length;
  loseNext=true;
  await page.getByLabel('Spillets tittel').fill('Response lost after commit');
  await page.getByText('Forbindelsen ble brutt.',{exact:false}).waitFor();
  await page.getByText('Lagret på nett',{exact:true}).waitFor();
  assert.equal(saves.length,beforeLost+1,'retry of committed save does not duplicate');
  expired=true;
  await page.getByLabel('Spillets tittel').fill('Survives expired session');
  await page.getByRole('link',{name:'Logg inn i en ny fane'}).waitFor();
  const beforeLogin = saves.length;
  assert.ok(await page.evaluate(()=>Object.values(localStorage).some(v=>v.includes('Survives expired session'))));
  expired=false; wrongAccount=true;
  await page.getByRole('button',{name:'Lagre på nett',exact:true}).click();
  await page.getByText('Logg inn med samme konto som åpnet dette spillet. Utkastet beholdes.',{exact:true}).waitFor();
  assert.equal(saves.length,beforeLogin,'different account cannot save draft');
  wrongAccount=false;
  await page.getByRole('button',{name:'Lagre på nett',exact:true}).click();
  await waitSaved(beforeLogin+2);
  // Reload while a session is expired, then recover and save the local draft.
  expired=true;
  await page.getByLabel('Spillets tittel').fill('Recover after reload');
  await page.getByRole('link',{name:'Logg inn i en ny fane'}).waitFor();
  page.once('dialog',dialog=>dialog.accept());
  await page.reload();
  await page.evaluate(({game,revision})=>{Object.assign(document.querySelector('#editor').dataset,{game:JSON.stringify(game),id:'a'.repeat(32),revision:String(revision),csrf:'old-token',uid:'10'});window.renderMathInElement=()=>{};},{game:saves.at(-1),revision:saves.length+1});
  await page.addScriptTag({path:path.join(publicDir,'editor.js')});
  await page.getByRole('button',{name:'Gjenopprett utkast'}).click();
  assert.equal(await page.getByLabel('Spillets tittel').inputValue(),'Recover after reload');
  expired=false;
  const beforeRecovery=saves.length;
  await page.getByRole('button',{name:'Lagre på nett',exact:true}).click();
  await waitSaved(beforeRecovery+2);
  assert.equal(await page.evaluate(()=>Object.keys(localStorage).filter(k=>k.startsWith('jeopardy-draft:')).length),0,'confirmed save clears recovery draft');
  const board=await browser.newPage();await board.route('http://jeopardy.test/**',route=>route.fulfill({contentType:'text/html',body:'<div class="jeopardy-container"></div>'}));await board.goto('http://jeopardy.test/board');
  const config={teams:2,values:[100,200,300,400,500],categories:[{name:'A',tiles:[100,200,300,400,500].map(value=>({value,question:'Question',answer:'Answer',empty:value===200}))},{name:'B',tiles:[100,300,500].map(value=>({value,question:'Question',answer:'Answer',empty:false}))}]};
  await board.evaluate(cfg=>document.querySelector('.jeopardy-container').dataset.config=JSON.stringify(cfg),config);
  await board.addScriptTag({path:path.join(publicDir,'jeopardy.js')});await board.evaluate(()=>document.dispatchEvent(new Event('DOMContentLoaded')));
  assert.equal(await board.locator('.jeopardy-tile').count(),10);assert.equal(await board.locator('.jeopardy-tile:disabled').count(),3);
  await board.getByRole('button',{name:'Start spill',exact:true}).click();await board.getByRole('button',{name:'Reset spill',exact:true}).click();
  assert.equal(await board.locator('.jeopardy-tile:disabled').count(),3,'empty/missing cells remain disabled after reset');
  assert.deepEqual(errors,[]);console.log('Jeopardy browser passed: category-specific rows, autosave including edits during save and continuous typing, timeout/lost-response retries, session recovery, account isolation, local draft recovery, sparse board and reset.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
