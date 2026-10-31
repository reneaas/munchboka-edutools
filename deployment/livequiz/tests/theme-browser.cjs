const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH});
 try {
 const context=await browser.newContext({colorScheme:'dark',reducedMotion:'reduce',viewport:{width:1280,height:1000}}),page=await context.newPage();
 const base=process.env.LIVEQUIZ_BASE||'http://127.0.0.1:8798';
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const theme=()=>page.locator('html').getAttribute('data-theme');
 await page.goto(base);await page.getByRole('heading',{name:'Klar for neste spørsmål?'}).waitFor();
 assert.equal(await theme(),'dark');
 await page.getByRole('button',{name:'Bytt til lys modus'}).click();assert.equal(await theme(),'light');
 await page.reload();assert.equal(await theme(),'light');
 await page.getByRole('button',{name:'Bytt til mørk modus'}).click();assert.equal(await theme(),'dark');
 await page.goto(base+'/_test_login.php');await page.getByRole('link',{name:'＋ Lag en quiz'}).waitFor();
 const room=await page.evaluate(async()=>{
  const boot=await(await fetch('index.php?api=bootstrap')).json();
  const post=async(action,data)=>(await(await fetch('index.php?api='+action,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':boot.csrf},body:JSON.stringify(data)})).json());
  const quiz=await post('save',{content:{title:'Theme check',questions:[{type:'single',prompt:'Hva er $2+2$?',code:'print(2 + 2) # et spørsmål',youtube:'',image:null,seconds:120,options:['3','4','5','6'],correct:[1],accepted:[]}]}});
  return {...await post('create',{id:quiz.id}),quiz:quiz.id};
 });
 await page.goto(base+'/?host='+room.room);await page.locator('.pin').waitFor();assert.equal(await theme(),'dark');
 await page.getByRole('button',{name:'Start første spørsmål'}).click();await page.locator('.active-question-modal').waitFor();
 const dialog=page.getByRole('dialog');
 assert.equal(await dialog.evaluate(e=>getComputedStyle(e).backgroundColor),'rgb(15, 23, 42)');
 await dialog.getByRole('button',{name:'Bytt til lys modus'}).click();assert.equal(await theme(),'light');
 assert.equal(await dialog.evaluate(e=>getComputedStyle(e).backgroundColor),'rgb(248, 250, 252)');
 await dialog.getByRole('button',{name:'Bytt til mørk modus'}).click();
 await page.screenshot({path:'/tmp/livequiz-dark-question.png'});
 await page.getByRole('button',{name:'Vis fasit nå'}).click();await page.getByRole('heading',{name:'Fasit',exact:true}).waitFor();
 await page.screenshot({path:'/tmp/livequiz-dark-results.png'});
 await page.goto(base+'/?edit='+room.quiz);await page.locator('.CodeMirror').waitFor();
 assert.equal(await page.locator('.CodeMirror').first().evaluate(e=>getComputedStyle(e).backgroundColor),'rgb(20, 33, 30)');
 await page.screenshot({path:'/tmp/livequiz-dark-editor.png'});
 await page.setViewportSize({width:390,height:844});await page.goto(base);
 await page.getByRole('heading',{name:'Klar for neste spørsmål?'}).waitFor();
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
 await page.screenshot({path:'/tmp/livequiz-dark-mobile.png'});
 const tab=await context.newPage();await tab.goto(base);await tab.getByRole('button',{name:'Bytt til lys modus'}).click();
 await page.waitForFunction(()=>document.documentElement.dataset.theme==='light');
 const noStorage=await browser.newContext({colorScheme:'dark'});
 await noStorage.addInitScript(()=>{Storage.prototype.getItem=()=>{throw Error('blocked');};Storage.prototype.setItem=()=>{throw Error('blocked');};});
 const restricted=await noStorage.newPage();await restricted.goto(base);await restricted.getByRole('button',{name:'Bytt til lys modus'}).click();
 assert.equal(await restricted.locator('html').getAttribute('data-theme'),'light');
 assert.deepEqual(errors,[]);
 console.log('Theme checks passed: system default, toggle, persistence, navigation, modal controls, editor, mobile width, cross-tab sync and blocked storage.');
 } finally {await browser.close();}
})();
