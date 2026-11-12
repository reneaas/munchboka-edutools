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
 await host.getByRole('button',{name:'Lagre quiz',exact:true}).click();await host.getByText('Lagret på nett',{exact:true}).waitFor();
 await host.reload();await host.locator('.sorting-editor-row input').first().waitFor();assert.deepEqual(await host.locator('.sorting-editor-row input').evaluateAll(es=>es.map(e=>e.value)),['En','To','Tre']);
 await host.getByRole('button',{name:'Forhåndsvis hele quizen',exact:true}).click();await host.getByLabel('Vis fasit',{exact:true}).check();assert.deepEqual(await host.locator('.sorting-options .rich').allTextContents(),['En','To','Tre']);await host.getByRole('button',{name:'Lukk forhåndsvisning',exact:true}).click();
 await host.getByRole('button',{name:'Start spill',exact:true}).click();await host.locator('.pin').waitFor();const pin=await host.locator('.pin').textContent();
 await player.goto(base+'/?pin='+pin);await player.getByLabel('Kallenavn').fill('Sorter');await player.getByRole('button',{name:'Bli med',exact:true}).click();await player.locator('#app[data-state="LOBBY"]').waitFor();
 await host.getByRole('button',{name:'Start første spørsmål',exact:true}).click();await player.locator('.sorting-list').waitFor();
 assert.equal(await player.locator('.sorting-handle').count(),0);
 const labels=()=>player.locator('.sorting-list .rich').allTextContents();
 // Mouse dragging moves a whole alternative and keeps its underlying answer index.
 await player.emulateMedia({reducedMotion:'no-preference'});
 await player.setViewportSize({width:1920,height:1080});
 await player.locator('.question-modal').evaluate(async e=>{await Promise.all(e.getAnimations().map(a=>a.finished));});
 const before=await labels(),first=await player.locator('.sorting-list li').first().boundingBox(),last=await player.locator('.sorting-list li').last().boundingBox();
 await player.mouse.move(first.x+first.width/2,first.y+first.height/2);await player.mouse.down();await player.mouse.move(last.x+last.width/2,last.y+last.height-8,{steps:12});
 await player.locator('.sorting-ghost').waitFor();await player.getByText('Slipp her · plass 3',{exact:true}).waitFor();assert.equal(await player.locator('.sorting-placeholder').count(),1);const ghost=await player.locator('.sorting-ghost').boundingBox();const source=await player.locator('.sorting-list li').first().boundingBox();assert.ok(Math.abs(ghost.width-source.width)<2,'drag preview preserves width on zoomed desktop: '+JSON.stringify({ghost,source}));await player.screenshot({path:'/tmp/livequiz-sorting-drag.png'});await player.mouse.up();
 assert.deepEqual(await labels(),[...before.slice(1),before[0]]);assert.equal(await player.locator('.sorting-ghost').count(),0);assert.equal(await player.locator('.sorting-placeholder').count(),0);assert.equal(await player.locator('.sorting-placed').count(),1);
 await player.emulateMedia({reducedMotion:'reduce'});
 await player.setViewportSize({width:390,height:844});
 await player.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
 await player.locator('.sorting-list').evaluate(async e=>{await Promise.all(e.getAnimations({subtree:true}).map(a=>a.finished));});
 // Native touch events exercise the same pointer path and touch-action on the whole card.
 const cdp=await player.context().newCDPSession(player),touchStart=await player.locator('.sorting-list li').last().boundingBox(),touchEnd=await player.locator('.sorting-list li').first().boundingBox();
 const x=touchStart.x+touchStart.width/2,y=touchStart.y+touchStart.height/2;
 await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y}]});
 for(let step=1;step<=10;step++)await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x,y:y+(touchEnd.y+8-y)*step/10}]});
 await player.locator('.sorting-ghost').waitFor();await player.getByText('Slipp her · plass 1',{exact:true}).waitFor();
 await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});assert.deepEqual(await labels(),before);
 // Cancelling a drag leaves the answer unchanged.
 const cancel=await player.locator('.sorting-list li').first().boundingBox();
 await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:cancel.x+10,y:cancel.y+10}]});
 await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:cancel.x+10,y:cancel.y+70}]});
 await cdp.send('Input.dispatchTouchEvent',{type:'touchCancel',touchPoints:[]});assert.deepEqual(await labels(),before);assert.equal(await player.locator('.sorting-ghost').count(),0);

 for(const [position,value] of ['En','To','Tre'].entries()){
  let index=(await labels()).indexOf(value);
  if(index>position){
   const from=await player.locator('.sorting-list li').nth(index).boundingBox(),to=await player.locator('.sorting-list li').nth(position).boundingBox();
   await player.mouse.move(from.x+from.width/2,from.y+from.height/2);await player.mouse.down();await player.mouse.move(to.x+to.width/2,to.y+5,{steps:10});await player.mouse.up();
  }
 }
 assert.deepEqual(await labels(),['En','To','Tre']);
 assert.equal(await player.getByRole('button',{name:/Flytt alternativ/}).count(),0);
 const ordered=await labels();await player.locator('.sorting-list li').first().focus();await player.keyboard.press('ArrowDown');assert.deepEqual(await labels(),ordered);
 assert.equal(await player.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
 await player.screenshot({path:'/tmp/livequiz-sorting-mobile.png'});
 await player.getByRole('button',{name:'Send svar',exact:true}).click();await player.getByRole('heading',{name:'Fasit',exact:true}).waitFor();
 assert.deepEqual(await player.locator('.sorting-options .rich').allTextContents(),['En','To','Tre']);await player.getByText('Du fikk 1000 poeng.',{exact:true}).waitFor();
 await host.getByRole('heading',{name:'Fasit',exact:true}).waitFor();assert.equal(await host.locator('.chart-row').count(),3);
 await player.reload();await player.getByText('Du fikk 1000 poeng.',{exact:true}).waitFor();assert.deepEqual(await player.locator('.sorting-options .rich').allTextContents(),['En','To','Tre']);
 assert.deepEqual(errors,[]);console.log('Sorting browser passed: editing, reordering, saving, mouse/touch dragging, drag cancellation, drag-only ordering, grading, results and reload.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
