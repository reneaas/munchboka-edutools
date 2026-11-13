const assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
(async()=>{
let audio, tick, rejectPlay=false, randomCalls=0;
const randomValues=[0,.999,.5];
const fakeMath=Object.create(Math);fakeMath.random=()=>randomValues[randomCalls++ % randomValues.length];
class Element { constructor(){this.children=[];} append(...nodes){this.children.push(...nodes);} setAttribute(k,v){this[k]=v;} }
const window={addEventListener(){}};
const tracks=['music/Calm%20song.mp3','music/new-track.ogg','music/Finale.MP3'];
const document={body:{dataset:{musicTracks:JSON.stringify(tracks)}},createElement:()=>new Element()};
vm.runInNewContext(fs.readFileSync(require('node:path').join(__dirname,'../public/music.js'),'utf8'),{performance:{now:()=>0},Math:fakeMath,window,document,Audio:class{addEventListener(){}constructor(src){audio=this;this.src=src;this.paused=true;this.calls=0;}play(){this.calls++;if(rejectPlay)return Promise.reject(Error('blocked'));this.paused=false;return Promise.resolve();}pause(){this.paused=true;}},setInterval(fn){tick=fn;return 1;},clearInterval(){}});
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
assert.equal(randomCalls,1);assert.equal(audio.src,tracks[0]);
audio.currentTime=12;m.update(true,0);await settle();assert.equal(audio.currentTime,12);assert.equal(randomCalls,1);
m.update(false,1);assert.equal(randomCalls,1);
m.update(true,1);await settle();assert.equal(audio.src,tracks[2]);assert.equal(audio.currentTime,0);assert.equal(randomCalls,2);
m.update(false,1);m.update(true,1);await settle();assert.equal(randomCalls,2);
m.update(true,2);await settle();assert.equal(audio.src,tracks[1]);assert.equal(randomCalls,3);
// A fresh player uses the new collection, including a single song or none.
document.body.dataset.musicTracks=JSON.stringify(['music/replacement.wav']);
const single=window.quizMusic();single.update(true,0);await settle();assert.equal(audio.src,'music/replacement.wav');
document.body.dataset.musicTracks='[]';
const empty=window.quizMusic();empty.unlock();empty.update(true,0);await settle();
assert.equal(audio.calls,0);assert.equal(audio.src,undefined);assert.equal(empty.controls.children[0].disabled,true);
assert.equal(empty.controls.children[0].textContent,'Ingen musikk tilgjengelig');
// Lobby music is independent, opt-in, and advances on ended instead of looping one track.
document.body.dataset.lobbyMusicTracks=JSON.stringify(['lobby_music/one.mp3','lobby_music/two.mp3','lobby_music/three.mp3']);
const lobby=window.quizMusic({lobby:true}),lobbyToggle=lobby.controls.children[0];
assert.equal(lobbyToggle.textContent,'Lobbymusikk: av');assert.equal(audio.loop,false);
lobby.update(true);await settle();assert.equal(audio.calls,0);
lobbyToggle.onclick();await settle();assert.equal(audio.paused,false);assert.equal(lobbyToggle.textContent,'Lobbymusikk: på');
for(let i=0;i<8;i++){const previous=audio.src;audio.onended();await settle();assert.notEqual(audio.src,previous);assert.ok(audio.src.startsWith('lobby_music/'));assert.equal(audio.paused,false);}
const lobbyTrack=audio.src,lobbyCalls=audio.calls;
lobby.update(true);await settle();assert.equal(audio.src,lobbyTrack);assert.equal(audio.calls,lobbyCalls);
lobby.update(false);assert.equal(audio.paused,true);audio.onended();await settle();assert.equal(audio.calls,lobbyCalls);
lobby.update(true);await settle();assert.equal(audio.paused,false);assert.equal(audio.src,lobbyTrack);
lobbyToggle.onclick();assert.equal(audio.paused,true);audio.onended();lobby.update(true);await settle();assert.equal(audio.paused,true);
lobbyToggle.onclick();lobby.update(false);await settle();assert.equal(audio.paused,true);
document.body.dataset.lobbyMusicTracks=JSON.stringify(['lobby_music/only.mp3']);
const singleLobby=window.quizMusic({lobby:true});singleLobby.update(true);singleLobby.controls.children[0].onclick();await settle();audio.onended();await settle();assert.equal(audio.src,'lobby_music/only.mp3');assert.equal(audio.calls,2);
document.body.dataset.lobbyMusicTracks='[]';const emptyLobby=window.quizMusic({lobby:true});emptyLobby.update(true);await settle();assert.equal(audio.calls,0);assert.equal(emptyLobby.controls.children[0].disabled,true);
// Shared selection never invokes random, seeks to the shared clock on reconnect,
// and recovers from autoplay rejection without changing the selected track.
document.body.dataset.musicTracks=JSON.stringify(tracks);
const sharedPlayer=window.quizMusic(),sharedAudio=audio;
const selection={key:'0:question:0',phase:'question',track:tracks[1],started_at:100};
sharedAudio.duration=60;sharedAudio.currentTime=0;
const beforeRandom=randomCalls;
sharedPlayer.update(true,0,selection,113);await settle();
assert.equal(sharedAudio.src,tracks[1]);assert.equal(sharedAudio.currentTime,13);
sharedAudio.currentTime=0;sharedPlayer.update(true,0,selection,175);await settle();
assert.equal(sharedAudio.currentTime,15);assert.equal(randomCalls,beforeRandom);
sharedPlayer.update(false,0,selection,175);rejectPlay=true;
sharedPlayer.update(true,0,selection,176);await settle();
assert.equal(sharedPlayer.controls.children[0].textContent,'Spill musikk');
rejectPlay=false;sharedPlayer.controls.children[0].onclick();await settle();
assert.equal(sharedAudio.paused,false);assert.equal(sharedAudio.src,tracks[1]);
const reconnected=window.quizMusic();audio.duration=60;audio.currentTime=0;
reconnected.update(true,0,selection,179);await settle();assert.equal(audio.currentTime,19);assert.equal(audio.src,sharedAudio.src);
const changed={...selection,key:'0:question:1',track:tracks[2],started_at:180};
reconnected.update(true,1,changed,185);await settle();assert.equal(audio.src,tracks[2]);assert.equal(audio.currentTime,5);
document.body.dataset.lobbyMusicTracks=JSON.stringify(['lobby_music/one.mp3']);
const sharedLobby=window.quizMusic({lobby:true});
sharedLobby.update(true,0,{key:'lobby',phase:'lobby',track:'lobby_music/one.mp3',started_at:100},120);
assert.equal(audio.loop,true);const selected=audio.src;audio.onended();assert.equal(audio.src,selected);
console.log('Shared music passed: server selection, seek/reconnect, looping, track changes and autoplay recovery.');
console.log('Question and lobby music passed: default-off lobby, random tracks, no immediate repeats, end-of-song advance, pause/resume, independent toggles, missing/single tracks and pending transitions.');
})();
