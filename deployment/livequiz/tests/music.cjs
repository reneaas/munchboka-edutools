const assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
(async()=>{
let audio, tick, rejectPlay=false, randomCalls=0;
const randomValues=[0,.999,.5];
const fakeMath=Object.create(Math);fakeMath.random=()=>randomValues[randomCalls++ % randomValues.length];
class Element { constructor(){this.children=[];} append(...nodes){this.children.push(...nodes);} setAttribute(k,v){this[k]=v;} }
const window={addEventListener(){}};
vm.runInNewContext(fs.readFileSync(require('node:path').join(__dirname,'../public/music.js'),'utf8'),{Math:fakeMath,window,document:{createElement:()=>new Element()},Audio:class{constructor(src){audio=this;this.src=src;this.paused=true;this.calls=0;}play(){this.calls++;if(rejectPlay)return Promise.reject(Error('blocked'));this.paused=false;return Promise.resolve();}pause(){this.paused=true;}},setInterval(fn){tick=fn;return 1;},clearInterval(){}});
const m=window.quizMusic(),toggle=m.controls.children[0],slider=m.controls.children[1].children[0];
const settle=async()=>{await Promise.resolve();await Promise.resolve();};
assert.equal(audio.calls,0);assert.equal(audio.loop,true);assert.equal(audio.preload,'none');
m.unlock();await settle();assert.equal(audio.paused,true);
m.update(true);await settle();assert.equal(audio.paused,false);for(let i=0;i<10;i++)tick();assert.equal(audio.volume,.25);
m.update(true);assert.equal(audio.calls,2);
m.update(false);assert.equal(audio.paused,true);assert.equal(audio.volume,0);
m.update(true);await settle();toggle.onclick();assert.equal(audio.paused,true);m.update(true);assert.equal(audio.paused,true);
toggle.onclick();await settle();assert.equal(audio.paused,false);slider.value=60;slider.oninput();for(let i=0;i<20;i++)tick();assert.equal(audio.volume,.6);
m.update(false);rejectPlay=true;m.update(true);await settle();assert.equal(toggle.textContent,'Spill musikk');const calls=audio.calls;m.update(true);assert.equal(audio.calls,calls);rejectPlay=false;toggle.onclick();await settle();assert.equal(audio.paused,false);
// A pending play completion must not restart music after leaving a question.
m.update(false);m.update(true);m.update(false);await settle();assert.equal(audio.paused,true);
// Selection happens once per question, never on polling, toggles or reconnection.
assert.equal(randomCalls,1);assert.equal(audio.src,'music/song_1.mp3');
audio.currentTime=12;m.update(true,0);await settle();assert.equal(audio.currentTime,12);assert.equal(randomCalls,1);
m.update(false,1);assert.equal(randomCalls,1);
m.update(true,1);await settle();assert.equal(audio.src,'music/song_7.mp3');assert.equal(audio.currentTime,0);assert.equal(randomCalls,2);
m.update(false,1);m.update(true,1);await settle();assert.equal(randomCalls,2);
m.update(true,2);await settle();assert.equal(audio.src,'music/song_4.mp3');assert.equal(randomCalls,3);
for(let i=1;i<=7;i++)assert.ok(fs.statSync(require('node:path').join(__dirname,`../public/music/song_${i}.mp3`)).size>0);
console.log('Random selection and music lifecycle, volume, toggle, autoplay retry and pending transition checks passed.');
})();
