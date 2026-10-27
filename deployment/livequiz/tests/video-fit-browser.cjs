const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH});
 try{
 const page=await browser.newPage({viewport:{width:1280,height:720},reducedMotion:'reduce'});
 await require('./youtube-stub.cjs')(page.context());
 await page.goto((process.env.LIVEQUIZ_BASE||'http://127.0.0.1:8798')+'/_test_login.php');
 const room=await page.evaluate(async()=>{
  const boot=await(await fetch('index.php?api=bootstrap')).json();
  const post=async(a,d)=>(await(await fetch('index.php?api='+a,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':boot.csrf},body:JSON.stringify(d)})).json());
  const q=await post('save',{content:{title:'Video fitting',questions:[{type:'single',prompt:'Hvilket alternativ er riktig?',code:'',youtube:'dQw4w9WgXcQ',image:null,seconds:600,options:['Alternativ én','Alternativ to','Alternativ tre','Alternativ fire'],correct:[1],accepted:[]}]}});
  return await post('create',{id:q.id});
 });
 await page.goto(new URL('?host='+room.room,page.url()).href);await page.locator('.pin').waitFor();await page.getByRole('button',{name:'Start første spørsmål'}).click();await page.locator('.active-question-modal').waitFor();await page.locator('.quiz-video-screen iframe').waitFor({state:'attached'});
 async function fits(){
  await page.waitForFunction(()=>{
   const body=document.querySelector('.modal-body'),img=body.querySelector('.quiz-video-screen iframe'),b=body.getBoundingClientRect(),i=img.getBoundingClientRect();
   return i.height>10&&Math.abs(i.width/i.height-16/9)<.02&&body.scrollHeight<=body.clientHeight+1&&i.top>=b.top&&i.bottom<=b.bottom+1&&[...body.querySelectorAll('.option-card')].every(e=>{const r=e.getBoundingClientRect();return r.top>=b.top&&r.bottom<=b.bottom+1;});
  },null,{timeout:3000});
  const b=await page.locator('.quiz-video>button').boundingBox(),area=await page.locator('.modal-body').boundingBox();assert.ok(b.y>=area.y&&b.y+b.height<=area.y+area.height+1);
 }
 for(const size of [{width:1280,height:720},{width:1920,height:1080},{width:2560,height:1440},{width:1024,height:768},{width:390,height:844},{width:844,height:390}]){
  await page.setViewportSize(size);await fits();
  await page.screenshot({path:`/tmp/livequiz-video-fit-${size.width}x${size.height}.png`});
 }
 await page.getByRole('button',{name:'Vis fasit nå'}).click();await page.getByRole('heading',{name:'Fasit',exact:true}).waitFor();
 for(const size of [{width:1280,height:720},{width:1920,height:1080},{width:2560,height:1440},{width:390,height:844},{width:844,height:390}]){
  await page.setViewportSize(size);await fits();
  await page.screenshot({path:`/tmp/livequiz-video-results-${size.width}x${size.height}.png`});
 }
 console.log('Video fit checks passed: active and results screens, full 16:9 frame, visible alternatives and playback controls across desktop and mobile sizes.');
 }finally{await browser.close();}
})();
