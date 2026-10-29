const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH});
 try{
 const page=await browser.newPage({viewport:{width:390,height:844}}),base=process.env.LIVEQUIZ_BASE||'http://127.0.0.1:8797';
 page.setDefaultTimeout(10000);
 const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto(base+'/_test_login.php');
 const seeded=await page.evaluate(async()=>{
  const boot=await(await fetch('index.php?api=bootstrap')).json();
  const questions=['First','Second','Third'].map((prompt,i)=>({type:i===2?'text':'single',prompt,code:'print('+i+')\n\n',youtube:'',image:null,seconds:30+i,options:i===2?[]:['A','B','C','D'],correct:i===2?[]:[i],accepted:i===2?['three']:[]}));
  const saved=await(await fetch('index.php?api=save',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':boot.csrf},body:JSON.stringify({content:{title:'Reorder test',questions}})})).json();
  const original=await(await fetch('index.php?api=quiz&id='+saved.id)).json();return {id:saved.id,questions:original.content.questions};
 });
 await page.goto(base+'/?edit='+seeded.id);
 const cards=page.locator('.question-editor');await cards.nth(2).waitFor();
 // Preserve an unsaved edit while moving first to last, then last to first.
 await cards.nth(0).getByLabel('Spørsmål',{exact:true}).fill('Edited first');
 await cards.nth(0).getByRole('button',{name:'Skjul detaljer for spørsmål 1',exact:true}).click();
 assert.equal(await cards.nth(0).locator('.question-editor-summary').innerText(),'Edited first');
 assert.equal(await cards.nth(0).getByLabel('Alternativ 1',{exact:true}).isVisible(),false);
 assert.equal(await cards.nth(0).locator('.CodeMirror').isVisible(),false);
 assert.equal(await cards.nth(0).getByRole('button',{name:'Utvid spørsmål 1',exact:true}).getAttribute('aria-expanded'),'false');
 await page.screenshot({path:'/tmp/livequiz-collapsed-editor.png'});
 // The focused toggle is keyboard-operable, and CodeMirror refreshes on opening.
 await page.keyboard.press('Enter');
 assert.equal(await cards.nth(0).getByLabel('Spørsmål',{exact:true}).inputValue(),'Edited first');
 assert.ok((await cards.nth(0).locator('.CodeMirror').boundingBox()).height>20);
 await cards.nth(1).getByRole('button',{name:'Skjul detaljer for spørsmål 2',exact:true}).click();
 await cards.nth(0).getByLabel('Flytt til plass',{exact:true}).selectOption({value:'2'});await cards.nth(0).getByRole('button',{name:'Flytt spørsmål',exact:true}).click();
 assert.equal(await cards.nth(0).getByRole('button',{name:'Utvid spørsmål 1',exact:true}).getAttribute('aria-expanded'),'false');
 assert.equal(await cards.nth(0).locator('.question-editor-summary').innerText(),'Second');
 assert.deepEqual(await Promise.all([0,1,2].map(i=>cards.nth(i).getByLabel('Spørsmål',{exact:true}).inputValue())),['Second','Third','Edited first']);
 await cards.nth(1).getByLabel('Flytt til plass',{exact:true}).selectOption({value:'0'});await cards.nth(1).getByRole('button',{name:'Flytt spørsmål',exact:true}).click();
 await page.getByRole('button',{name:'Lagre quiz',exact:true}).click();await page.getByText('Lagret · versjon 2',{exact:true}).waitFor();
 await page.reload();await cards.nth(2).waitFor();
 const saved=await page.evaluate(async id=>(await(await fetch('index.php?api=quiz&id='+id)).json()).content.questions,seeded.id);
 seeded.questions[0].prompt='Edited first';assert.deepEqual(saved,[seeded.questions[2],seeded.questions[1],seeded.questions[0]]);
 assert.deepEqual(await cards.locator('h2').allTextContents(),['Spørsmål 1','Spørsmål 2','Spørsmål 3']);
 // The chosen order also becomes the game snapshot order.
 const first=await page.evaluate(async id=>{
  const boot=await(await fetch('index.php?api=bootstrap')).json();
  const post=async(action,body)=>(await(await fetch('index.php?api='+action,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':boot.csrf},body:JSON.stringify(body)})).json());
  const room=await post('create',{id});const state=await(await fetch('index.php?api=state&host=1&room='+room.room)).json();await post('control',{room:room.room,command:'next',version:state.version});return room.room;
 },seeded.id);
 await new Promise(resolve=>setTimeout(resolve,3200));
 const state=await page.evaluate(async room=>(await(await fetch('index.php?api=state&host=1&room='+room)).json()),first);
 assert.equal(state.question.prompt,'Third');
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
 await page.screenshot({path:'/tmp/livequiz-reorder-mobile.png'});
 assert.deepEqual(errors,[]);console.log('Question moves in both directions, unsaved edits, full question preservation, saved/reloaded order, game order and mobile layout passed.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
