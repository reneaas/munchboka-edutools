const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH});
 try{
 const page=await browser.newPage({viewport:{width:1280,height:900}}),base=process.env.LIVEQUIZ_BASE||'http://127.0.0.1:8800';
 await require('./youtube-stub.cjs')(page.context());const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(base+'/_test_login.php');
 const quiz=await page.evaluate(async()=>{
  const b=await(await fetch('index.php?api=bootstrap')).json(),headers={'X-CSRF-Token':b.csrf};
  const canvas=document.createElement('canvas');canvas.width=500;canvas.height=200;canvas.getContext('2d').fillRect(0,0,500,200);const form=new FormData();form.append('image',await new Promise(r=>canvas.toBlob(r)),'preview.png');
  const image=(await(await fetch('index.php?api=upload',{method:'POST',headers,body:form})).json()).image;
  const repeated=(await(await fetch('index.php?api=upload',{method:'POST',headers,body:form})).json()).image;
  if(repeated.id!==image.id)throw new Error('Repeated upload should reuse its image ID');
  const q={type:'single',prompt:'First $2+2$',code:'print(4)\n\n',youtube:'',image,seconds:30,options:['1','2','3','4'],correct:[3],accepted:[]};
  return(await(await fetch('index.php?api=save',{method:'POST',headers:{...headers,'Content-Type':'application/json'},body:JSON.stringify({content:{title:'Whole quiz preview fixture',questions:[q,{...q,type:'multi',prompt:'Second',code:'',image:null,youtube:'dQw4w9WgXcQ',correct:[1,3]},{...q,type:'text',prompt:'Third',image:null,code:'',options:[],correct:[],accepted:['four','4']}]}})})).json());
 });
 const gameplay=[];page.on('request',r=>{if(/[?&]api=(create|join|control|state|answer|race-answer|lightning-answer)(?:&|$)/.test(r.url()))gameplay.push(r.url());});
 await page.goto(base+'/?edit='+quiz.id);await page.getByLabel('Spørsmål',{exact:true}).first().fill('Unsaved $2+2$');
 await page.getByRole('button',{name:'Forhåndsvis hele quizen',exact:true}).click();const modal=page.locator('.quiz-preview-modal');
 await modal.getByRole('heading',{name:'Spørsmål 1 av 3',exact:true}).waitFor();await page.waitForFunction(()=>document.querySelector('.quiz-preview-modal img')?.naturalWidth===500);
 assert.ok(await modal.locator('.katex').count());assert.ok(await modal.locator('.CodeMirror').count());assert.equal(await modal.locator('.option-card').count(),4);assert.equal(await modal.getByRole('button',{name:'Forrige',exact:true}).isDisabled(),true);
 await modal.getByLabel('Vis fasit').check();assert.equal(await modal.locator('.option-card.correct').count(),1);
 for(const viewport of [{width:1920,height:1080},{width:390,height:844}]){await page.setViewportSize(viewport);await page.waitForTimeout(100);const box=await modal.boundingBox();assert.ok(box.x>=15&&box.y>=15&&box.x+box.width<=viewport.width-15&&box.y+box.height<=viewport.height-15);await page.screenshot({path:`/tmp/livequiz-preview-${viewport.width}.png`});}
 await modal.getByRole('button',{name:'Neste',exact:true}).click();await modal.locator('iframe').waitFor({state:'attached'});assert.equal(await modal.locator('.option-card.correct').count(),2);
 await modal.getByRole('button',{name:'Neste',exact:true}).click();await modal.getByText('Godkjente svar: four · 4').waitFor();assert.equal(await modal.locator('iframe').count(),0);assert.equal(await modal.getByRole('button',{name:'Neste',exact:true}).isDisabled(),true);
 await modal.getByLabel('Gå til spørsmål').selectOption('0');await modal.getByRole('heading',{name:'Spørsmål 1 av 3',exact:true}).waitFor();await modal.getByRole('button',{name:'Lukk forhåndsvisning',exact:true}).click();
 assert.equal(await page.getByLabel('Spørsmål',{exact:true}).first().inputValue(),'Unsaved $2+2$');await page.getByText('Ulagrede endringer',{exact:true}).waitFor();
 await page.getByRole('button',{name:'Forhåndsvis hele quizen',exact:true}).click();await page.keyboard.press('Escape');await modal.waitFor({state:'detached'});assert.equal(await modal.count(),0);
 // Restore the draft before leaving, then preview the saved quiz from the library.
 await page.getByLabel('Spørsmål',{exact:true}).first().fill('First $2+2$');await page.goto(base+'/?teacher=1');const card=page.locator('article').filter({has:page.locator('a[href="?edit='+quiz.id+'"]')});await card.getByRole('button',{name:'Forhåndsvis',exact:true}).click();await modal.getByRole('heading',{name:'Spørsmål 1 av 3',exact:true}).waitFor();assert.match(await modal.locator('.modal-header').innerText(),/First/);
 const saved=await page.evaluate(async id=>(await(await fetch('index.php?api=quiz&id='+id)).json()),quiz.id);assert.equal(saved.revision,1);assert.equal(saved.content.questions[0].prompt,'First $2+2$');assert.deepEqual(gameplay,[]);assert.deepEqual(errors,[]);
 // Public previews work in a fresh anonymous session, including protected image storage.
 const guestContext=await browser.newContext();await require('./youtube-stub.cjs')(guestContext);
 const guest=await guestContext.newPage();guest.on('pageerror',e=>errors.push(e.message));
 guest.on('request',r=>{if(/[?&]api=(create|public-start|join|control|state|answer)(?:&|$)/.test(r.url()))gameplay.push(r.url());});
 await guest.goto(base+'/?public='+quiz.id);await guest.getByRole('button',{name:'Forhåndsvis',exact:true}).click();
 const publicModal=guest.locator('.quiz-preview-modal');
 await guest.waitForFunction(()=>document.querySelector('.quiz-preview-modal img')?.naturalWidth===500);
 assert.ok(await publicModal.locator('.katex').count());assert.ok(await publicModal.locator('.CodeMirror').count());
 await publicModal.getByRole('button',{name:'Neste',exact:true}).click();await publicModal.locator('iframe').waitFor({state:'attached'});
 await publicModal.getByLabel('Gå til spørsmål').selectOption('2');await publicModal.getByLabel('Vis fasit').check();await publicModal.getByText('Godkjente svar: four · 4').waitFor();
 await publicModal.getByRole('button',{name:'Lukk forhåndsvisning',exact:true}).click();await publicModal.waitFor({state:'detached'});
 assert.deepEqual(gameplay,[]);assert.deepEqual(errors,[]);await guestContext.close();
 console.log('Whole-quiz preview passed: unsaved and saved versions, all answer types, math/code/images/video, manual navigation, answer reveal, mobile/desktop sizing, close/reopen and zero gameplay requests.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
