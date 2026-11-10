const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const publicDir=path.join(__dirname,'../public');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH});
 try{
  const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
  let saves=[],failNext=false,holdNext=false,release;
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
   if(req.method()==='POST'){
    const content=JSON.parse(req.postData().match(/name="content"\r\n\r\n([\s\S]*?)\r\n--/)[1]);
    if(holdNext){holdNext=false;await new Promise(resolve=>release=resolve);}
    if(failNext){failNext=false;await route.fulfill({status:500,json:{error:'Test save failure'}});return;}
    saves.push(content);await route.fulfill({json:{id:'a'.repeat(32),revision:saves.length+1}});return;
   }
   await route.fulfill({contentType:'text/html',body:'<main id="editor"></main>'});
  });
  await page.goto('http://jeopardy.test/');
  await page.evaluate(game=>{const root=document.querySelector('#editor');Object.assign(root.dataset,{game:JSON.stringify(game),id:'a'.repeat(32),revision:'1',csrf:'test'});window.renderMathInElement=()=>{};},initial);
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
  const board=await browser.newPage();await board.route('http://jeopardy.test/**',route=>route.fulfill({contentType:'text/html',body:'<div class="jeopardy-container"></div>'}));await board.goto('http://jeopardy.test/board');
  const config={teams:2,values:[100,200,300,400,500],categories:[{name:'A',tiles:[100,200,300,400,500].map(value=>({value,question:'Question',answer:'Answer',empty:value===200}))},{name:'B',tiles:[100,300,500].map(value=>({value,question:'Question',answer:'Answer',empty:false}))}]};
  await board.evaluate(cfg=>document.querySelector('.jeopardy-container').dataset.config=JSON.stringify(cfg),config);
  await board.addScriptTag({path:path.join(publicDir,'jeopardy.js')});await board.evaluate(()=>document.dispatchEvent(new Event('DOMContentLoaded')));
  assert.equal(await board.locator('.jeopardy-tile').count(),10);assert.equal(await board.locator('.jeopardy-tile:disabled').count(),3);
  await board.getByRole('button',{name:'Start spill',exact:true}).click();await board.getByRole('button',{name:'Reset spill',exact:true}).click();
  assert.equal(await board.locator('.jeopardy-tile:disabled').count(),3,'empty/missing cells remain disabled after reset');
  assert.deepEqual(errors,[]);console.log('Jeopardy browser passed: category-specific rows, autosave including edits during save and continuous typing, failure recovery, sparse board and reset.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
