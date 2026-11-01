const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH});
 try{
 const host=await browser.newPage({reducedMotion:'reduce'}),player=await browser.newPage({viewport:{width:390,height:844},reducedMotion:'reduce'}),base=process.env.LIVEQUIZ_BASE||'http://127.0.0.1:8822';
 const errors=[];for(const p of [host,player])p.on('pageerror',e=>errors.push(e.message));
 await host.goto(base+'/_test_login.php');
 const quiz=await host.evaluate(async()=>{
  const boot=await(await fetch('index.php?api=bootstrap')).json();
  return(await(await fetch('index.php?api=save',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':boot.csrf},body:JSON.stringify({content:{title:'Sorting browser',questions:[{type:'sort',prompt:'Sorter tallene fra minst til størst',code:'',youtube:'',image:null,seconds:120,options:['Tre','En','To'],correct:[1,2,0],accepted:[]}]}})})).json());
 });
 assert.ok(quiz.id,JSON.stringify(quiz));await host.goto(base+'/?edit='+quiz.id);
 assert.equal(await host.getByLabel('Svartype').inputValue(),'sort');
 assert.deepEqual(await host.locator('.sorting-editor-row input').evaluateAll(es=>es.map(e=>e.value)),['En','To','Tre']);
 await host.getByRole('button',{name:'Flytt alternativ 1 ned',exact:true}).click();
 assert.deepEqual(await host.locator('.sorting-editor-row input').evaluateAll(es=>es.map(e=>e.value)),['To','En','Tre']);
 await host.getByRole('button',{name:'Flytt alternativ 2 opp',exact:true}).click();
 await host.getByRole('button',{name:'Lagre quiz',exact:true}).click();await host.getByText('Lagret · versjon 2',{exact:true}).waitFor();
 await host.reload();await host.locator('.sorting-editor-row input').first().waitFor();assert.deepEqual(await host.locator('.sorting-editor-row input').evaluateAll(es=>es.map(e=>e.value)),['En','To','Tre']);
 await host.getByRole('button',{name:'Forhåndsvis hele quizen',exact:true}).click();await host.getByLabel('Vis fasit',{exact:true}).check();assert.deepEqual(await host.locator('.sorting-options .rich').allTextContents(),['En','To','Tre']);await host.getByRole('button',{name:'Lukk forhåndsvisning',exact:true}).click();
 await host.getByRole('button',{name:'Start spill',exact:true}).click();await host.locator('.pin').waitFor();const pin=await host.locator('.pin').textContent();
 await player.goto(base+'/?pin='+pin);await player.getByLabel('Kallenavn').fill('Sorter');await player.getByRole('button',{name:'Bli med',exact:true}).click();await player.locator('#app[data-state="LOBBY"]').waitFor();
 await host.getByRole('button',{name:'Start første spørsmål',exact:true}).click();await player.locator('.sorting-list').waitFor();
 const labels=()=>player.locator('.sorting-list .rich').allTextContents();
 for(const [position,value] of ['En','To','Tre'].entries()){
  let index=(await labels()).indexOf(value);
  while(index>position){await player.getByRole('button',{name:'Flytt alternativ '+(index+1)+' opp',exact:true}).press('Enter');index--;}
 }
 assert.deepEqual(await labels(),['En','To','Tre']);
 assert.equal(await player.getByRole('button',{name:'Flytt alternativ 1 opp',exact:true}).isDisabled(),true);
 assert.equal(await player.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
 await player.screenshot({path:'/tmp/livequiz-sorting-mobile.png'});
 await player.getByRole('button',{name:'Send svar',exact:true}).click();await player.getByRole('heading',{name:'Fasit',exact:true}).waitFor();
 assert.deepEqual(await player.locator('.sorting-options .rich').allTextContents(),['En','To','Tre']);await player.getByText('Du fikk 1000 poeng.',{exact:true}).waitFor();
 await host.getByRole('heading',{name:'Fasit',exact:true}).waitFor();assert.equal(await host.locator('.chart-row').count(),3);
 await player.reload();await player.getByText('Du fikk 1000 poeng.',{exact:true}).waitFor();assert.deepEqual(await player.locator('.sorting-options .rich').allTextContents(),['En','To','Tre']);
 assert.deepEqual(errors,[]);console.log('Sorting browser passed: editing, reordering, saving, mobile keyboard movement, grading, results and reload.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
