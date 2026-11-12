// Run against prepare-local.py's isolated fixture, never production.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH});
 try {
  const page=await browser.newPage(),base=process.env.LIVEQUIZ_BASE||'http://127.0.0.1:8765';
  const errors=[],requests=[];page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{if(r.url().includes('?api=save'))requests.push(r.postDataJSON());});
  const saved=()=>page.getByText('Lagret på nett',{exact:true}).waitFor();
  const read=()=>page.evaluate(async()=>{const id=new URLSearchParams(location.search).get('edit');return(await fetch('index.php?api=quiz&id='+id)).json();});
  await page.clock.install();
  await page.goto(base+'/_test_login.php');await page.goto(base+'/?new=1');
  await page.getByLabel('Spørsmål',{exact:true}).fill('Draft without title');
  await page.clock.runFor(16000);
  assert.equal(requests.length,0,'untitled draft remains local');
  await page.clock.resume();await page.getByLabel('Quizens tittel').fill('Autosave draft');await saved();
  const initial=await read();assert.equal(initial.content.questions[0].prompt,'Draft without title');
  assert.equal(initial.revision,1,'incomplete question autosaves without manual click');
  await page.getByRole('button',{name:'Lagre quiz',exact:true}).click();
  assert.equal(requests.length,1,'manual save of unchanged content does not write again');
  const beforeTyping=requests.length;
  for(let i=0;i<17;i++){
   await page.getByLabel('Spørsmål',{exact:true}).fill('Continuous typing '+i);
   await page.clock.runFor(1000);
   await new Promise(resolve=>setTimeout(resolve,20));
  }
  assert.ok(requests.length>beforeTyping,'periodic autosave runs during continuous typing');
  await page.clock.resume();await saved();
  assert.equal((await read()).content.questions[0].prompt,'Continuous typing 16');
  // Serialize snapshots while allowing edits during the request.
  let release,held=false;
  await page.route('**/index.php?api=save',async route=>{
   const response=await route.fetch();
   if(!held){held=true;await new Promise(resolve=>release=resolve);}
   await route.fulfill({response});
  });
  await page.getByLabel('Spørsmål',{exact:true}).fill('First pending snapshot');
  while(!release)await new Promise(resolve=>setTimeout(resolve,20));
  await page.getByLabel('Spørsmål',{exact:true}).fill('Edited during autosave');release();await saved();
  await page.unroute('**/index.php?api=save');
  assert.equal((await read()).content.questions[0].prompt,'Edited during autosave');
  // A committed save with a lost response retries the identical snapshot.
  let lost=false;const retryRequests=[];
  await page.route('**/index.php?api=save',async route=>{
   retryRequests.push(route.request().postDataJSON());const response=await route.fetch();
   if(!lost){lost=true;await route.abort('failed');}else await route.fulfill({response});
  });
  const beforeLost=(await read()).revision;
  await page.getByLabel('Spørsmål',{exact:true}).fill('Retry autosave');await saved();
  assert.equal((await read()).revision,beforeLost+1);assert.equal(retryRequests.length,2);
  assert.deepEqual(retryRequests[0],retryRequests[1]);await page.unroute('**/index.php?api=save');
  // Server validation failure must not cause a periodic retry loop.
  await page.getByLabel('Quizens tittel').fill('x'.repeat(181));
  await page.locator('#notice:not([hidden])').waitFor();
  const rejected=requests.length;await page.clock.runFor(31000);
  assert.equal(requests.length,rejected,'validation failure pauses autosave');
  await page.clock.resume();await page.getByLabel('Quizens tittel').fill('Corrected draft');await saved();
  assert.equal((await read()).id,initial.id,'all autosaves update the same quiz');
  assert.equal(await page.evaluate(()=>Object.keys(localStorage).filter(k=>k.startsWith('livequiz-draft:')).length),0);
  assert.deepEqual(errors,[]);
  console.log('Quiz autosave passed: debounce, continuous typing, incomplete drafts, serialized edits, retry safety, validation pause, unchanged saves and local draft cleanup.');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
