const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH});
 try{
 const base=process.env.LIVEQUIZ_BASE||'http://127.0.0.1:8830',host=await browser.newPage();
 await host.addInitScript(()=>{const NativeAudio=window.Audio;window.testAudio=[];window.Audio=function(...args){const audio=new NativeAudio(...args);window.testAudio.push(audio);return audio;};});
 await host.goto(base+'/_test_login.php');
 const room=await host.evaluate(async()=>{const boot=await(await fetch('index.php?api=bootstrap')).json();const post=async(api,data)=>(await(await fetch('index.php?api='+api,{method:'POST',headers:{'X-CSRF-Token':boot.csrf,'Content-Type':'application/json'},body:JSON.stringify(data)})).json());const q=await post('save',{content:{title:'Lobby music',questions:[{type:'single',prompt:'Question',code:'',youtube:'',image:null,seconds:120,options:['A','B'],correct:[0],accepted:[]}]}});return post('create',{id:q.id});});
 await host.goto(base+'/?host='+room.room);await host.locator('.lobby-music-controls').waitFor();
 const tracks=await host.evaluate(()=>JSON.parse(document.body.dataset.lobbyMusicTracks));assert.ok(tracks.length>=2);assert.ok(tracks.every(t=>t.startsWith('lobby_music/')));
 assert.equal(await host.getByRole('button',{name:'Lobbymusikk: av',exact:true}).getAttribute('aria-pressed'),'false');assert.equal(await host.evaluate(()=>testAudio[1].paused),true);
 await host.getByRole('button',{name:'Lobbymusikk: av',exact:true}).click();await host.waitForFunction(()=>!testAudio[1].paused&&testAudio[1].currentTime>0);
 const first=await host.evaluate(()=>testAudio[1].src);await host.evaluate(()=>testAudio[1].dispatchEvent(new Event('ended')));await host.waitForFunction(previous=>testAudio[1].src!==previous&&!testAudio[1].paused,first);
 await host.getByRole('button',{name:'Lobbymusikk: på',exact:true}).click();assert.equal(await host.evaluate(()=>testAudio[1].paused),true);
 await host.getByRole('button',{name:'Lobbymusikk: av',exact:true}).click();await host.waitForFunction(()=>!testAudio[1].paused);
 await host.getByRole('button',{name:'Start første spørsmål',exact:true}).click();await host.locator('#app[data-state="QUESTION_ACTIVE"]').waitFor();assert.equal(await host.evaluate(()=>testAudio[1].paused),true);assert.equal(await host.locator('.lobby-music-controls').count(),0);
 await host.getByRole('button',{name:'Avslutt spillet',exact:true}).click();await host.locator('#app[data-state="QUIZ_FINISHED"]').waitFor();assert.equal(await host.evaluate(()=>testAudio[1].paused),true);
 await host.getByRole('button',{name:'Spill igjen med samme spillere',exact:true}).click();await host.locator('.lobby-music-controls').waitFor();await host.waitForFunction(()=>!testAudio[1].paused);
 await host.reload();await host.getByRole('button',{name:'Lobbymusikk: av',exact:true}).waitFor();assert.equal(await host.evaluate(()=>testAudio[1].paused),true);
 console.log('Lobby music browser passed: folder discovery, default off, real audio playback, next track, toggle, game transition, replay lobby and reload default.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
