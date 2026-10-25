const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH});
 try{
 const page=await browser.newPage({viewport:{width:1280,height:1000},colorScheme:'dark'}),base=process.env.LIVEQUIZ_BASE||'http://127.0.0.1:8798';
 const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto(base+'/_test_login.php');
 const prefix='Folders '+Date.now(),rootName=prefix+' Matematikk',subName='Algebra';
 const saved=await page.evaluate(async title=>{
  const boot=await(await fetch('index.php?api=bootstrap')).json();
  return (await(await fetch('index.php?api=save',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':boot.csrf},body:JSON.stringify({content:{title,questions:[{type:'single',prompt:'2+2?',code:'',youtube:'',image:null,seconds:30,options:['3','4'],correct:[1],accepted:[]}]}})})).json());
 },prefix+' quiz');
 await page.reload();
 async function createFolder(name){await page.getByRole('button',{name:'Ny mappe',exact:true}).click();await page.getByLabel('Mappenavn').fill(name);await page.getByRole('dialog').getByRole('button',{name:'Lagre',exact:true}).click();await page.getByRole('link',{name:'📁 '+name,exact:true}).waitFor();}
 await createFolder(rootName);await page.getByRole('link',{name:'📁 '+rootName,exact:true}).click();await page.getByRole('heading',{name:rootName,exact:true}).waitFor();const rootId=new URL(page.url()).searchParams.get('folder');
 await createFolder(subName);await page.getByRole('link',{name:'📁 '+subName,exact:true}).click();await page.getByRole('heading',{name:subName,exact:true}).waitFor();const subId=new URL(page.url()).searchParams.get('folder');
 await page.locator('.folder-breadcrumbs').getByRole('link',{name:'Mine quizer',exact:true}).click();
 const card=page.locator('article').filter({has:page.getByRole('heading',{name:prefix+' quiz',exact:true})});
 await card.getByRole('button',{name:'Flytt',exact:true}).click();await page.getByLabel('Mappe',{exact:true}).selectOption(subId);await page.getByRole('dialog').getByRole('button',{name:'Lagre',exact:true}).click();await card.waitFor({state:'detached'});
 await page.goto(base+'/?teacher=1&folder='+subId);await page.getByRole('heading',{name:prefix+' quiz',exact:true}).waitFor();await page.reload();await page.getByRole('heading',{name:prefix+' quiz',exact:true}).waitFor();
 await page.getByRole('link',{name:'＋ Lag en quiz'}).click();await page.getByLabel('Quizens tittel').fill(prefix+' new');await page.getByLabel('Spørsmål',{exact:true}).fill('Velg A');
 for(const [i,value] of ['A','B','C','D'].entries())await page.getByLabel('Alternativ '+(i+1),{exact:true}).fill(value);
 await page.getByLabel('Riktig 1',{exact:true}).check();await page.getByRole('button',{name:'Lagre quiz',exact:true}).click();await page.getByText('Lagret · versjon 1',{exact:true}).waitFor();await page.getByRole('link',{name:'Mine quizer',exact:true}).click();
 assert.equal(new URL(page.url()).searchParams.get('folder'),subId);await page.getByRole('heading',{name:prefix+' new',exact:true}).waitFor();
 await page.getByRole('button',{name:'Gi mappen nytt navn'}).click();await page.getByLabel('Mappenavn').fill('Likninger');await page.getByRole('dialog').getByRole('button',{name:'Lagre',exact:true}).click();await page.getByRole('heading',{name:'Likninger',exact:true}).waitFor();
 await page.screenshot({path:'/tmp/livequiz-folders-desktop.png'});
 await page.setViewportSize({width:390,height:844});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);await page.screenshot({path:'/tmp/livequiz-folders-mobile.png'});
 await page.getByRole('button',{name:'Flytt mappe',exact:true}).click();assert.equal(await page.getByLabel('Mappe',{exact:true}).locator(`option[value="${subId}"]`).count(),0);await page.getByLabel('Mappe',{exact:true}).selectOption('');await page.getByRole('dialog').getByRole('button',{name:'Lagre',exact:true}).click();await page.getByRole('dialog').waitFor({state:'detached'});
 page.once('dialog',d=>d.accept());await page.getByRole('button',{name:'Slett mappe',exact:true}).click();await page.waitForURL(url=>!url.searchParams.has('folder'));await page.getByRole('heading',{name:prefix+' quiz',exact:true}).waitFor();await page.getByRole('heading',{name:prefix+' new',exact:true}).waitFor();assert.equal(new URL(page.url()).searchParams.get('folder'),null);
 const denied=await page.request.post(base+'/index.php?api=organize',{data:{command:'delete-folder',id:rootId}});assert.equal(denied.status(),403);
 const guest=await browser.newPage();await guest.goto(base);const guestStatus=await guest.evaluate(async()=>{const b=await(await fetch('index.php?api=bootstrap')).json();return (await fetch('index.php?api=organize',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':b.csrf},body:JSON.stringify({command:'create-folder',name:'No'})})).status;});assert.equal(guestStatus,401);
 assert.deepEqual(errors,[]);assert.ok(saved.id);
 console.log('Folder browser checks passed: nested folders, quiz moves, direct save in folder, rename, folder move, safe deletion, refresh, dark/mobile layout, CSRF and guest authorization.');
 }finally{await browser.close();}
})();
