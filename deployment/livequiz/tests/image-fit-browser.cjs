const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH});
 try{
 const page=await browser.newPage({viewport:{width:1280,height:720},reducedMotion:'reduce'});
 await page.goto((process.env.LIVEQUIZ_BASE||'http://127.0.0.1:8798')+'/_test_login.php');
 const room=await page.evaluate(async()=>{
  const boot=await(await fetch('index.php?api=bootstrap')).json();
  const post=async(a,d)=>(await(await fetch('index.php?api='+a,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':boot.csrf},body:JSON.stringify(d)})).json());
  const canvas=document.createElement('canvas');canvas.width=1200;canvas.height=1800;
  const ctx=canvas.getContext('2d');ctx.fillStyle='#e7c59c';ctx.fillRect(0,0,1200,1800);ctx.strokeStyle='#672a17';ctx.lineWidth=40;ctx.strokeRect(20,20,1160,1760);ctx.fillStyle='#672a17';ctx.font='100px sans-serif';ctx.fillText('Hele bildet',300,900);
  const form=new FormData();form.append('image',await new Promise(r=>canvas.toBlob(r)),'portrait.png');
  const image=(await(await fetch('index.php?api=upload',{method:'POST',headers:{'X-CSRF-Token':boot.csrf},body:form})).json()).image;
  const q=await post('save',{content:{title:'Image fitting',questions:[{type:'single',prompt:'Hvilket alternativ er riktig?',code:'',youtube:'',image,seconds:600,options:['Alternativ én','Alternativ to','Alternativ tre','Alternativ fire'],correct:[1],accepted:[]}]}});
  return await post('create',{id:q.id});
 });
 await page.goto(new URL('?host='+room.room,page.url()).href);await page.locator('.pin').waitFor();await page.getByRole('button',{name:'Start første spørsmål'}).click();await page.locator('.active-question-modal').waitFor();await page.waitForFunction(()=>document.querySelector('.question-image')?.naturalWidth>0);
 async function fits(){
  await page.waitForFunction(()=>{
   const body=document.querySelector('.modal-body'),img=body.querySelector('.question-image'),b=body.getBoundingClientRect(),i=img.getBoundingClientRect();
   return i.height>10&&body.scrollHeight<=body.clientHeight+1&&i.top>=b.top&&i.bottom<=b.bottom+1&&[...body.querySelectorAll('.option-card')].every(e=>{const r=e.getBoundingClientRect();return r.top>=b.top&&r.bottom<=b.bottom+1;});
  },null,{timeout:3000});
  assert.equal(await page.locator('.question-image').evaluate(e=>getComputedStyle(e).objectFit),'contain');
 }
 for(const size of [{width:1280,height:720},{width:1920,height:1080},{width:1024,height:768},{width:390,height:844},{width:844,height:390}]){
  await page.setViewportSize(size);await fits();
  await page.screenshot({path:`/tmp/livequiz-image-fit-${size.width}x${size.height}.png`});
 }
 // Loaded landscape/square images also fit; resize recomputes without rebuilding the question.
 for(const [width,height] of [[2400,800],[1000,1000]]){
  await page.evaluate(async({width,height})=>{const c=document.createElement('canvas');c.width=width;c.height=height;const img=document.querySelector('.question-image');img.src=c.toDataURL();await img.decode();},{width,height});
  await page.setViewportSize({width:1280,height:720});await fits();
 }
 await page.evaluate(()=>{const grid=document.querySelector('.option-grid');for(let i=0;i<2;i++)grid.append(grid.firstElementChild.cloneNode(true));});
 for(const size of [{width:1280,height:720},{width:390,height:844}]){await page.setViewportSize(size);await fits();}
 await page.getByRole('button',{name:'Vis fasit nå'}).click();await page.getByRole('heading',{name:'Fasit',exact:true}).waitFor();
 await page.waitForFunction(()=>document.querySelector('.question-image')?.naturalWidth>0);
 for(const size of [{width:1280,height:720},{width:390,height:844},{width:844,height:390}]){
  await page.setViewportSize(size);await fits();
  assert.equal(await page.locator('.results-analysis').evaluate(e=>e.clientHeight>0),true);
  await page.screenshot({path:`/tmp/livequiz-image-results-${size.width}x${size.height}.png`});
 }
 console.log('Image fit checks passed: portrait, landscape, square; desktop, projector, tablet, mobile and landscape phone; image and all alternatives visible without scrolling.');
 }finally{await browser.close();}
})();
