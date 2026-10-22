/* Deterministic API double. Does not validate real YouTube playback or title timing. */
module.exports = async context => {
 await context.route('https://www.youtube-nocookie.com/**', route => route.fulfill({body:'<html>Test video</html>',contentType:'text/html'}));
 await context.route('https://www.youtube.com/iframe_api', route => route.fulfill({contentType:'application/javascript',body:`
 window.__ytPlayers=[];
 window.YT={Player:class {
   constructor(frame, options) {
     this.frame=frame;this.events=options.events;this.state=-1;this.ready=false;this.destroyed=false;
     window.__ytPlayers.push(this);
     queueMicrotask(()=>{this.ready=true;this.events.onReady({target:this});});
   }
   emit(state){this.state=state;this.events.onStateChange({target:this,data:state});}
   unMute(){this.muted=false;}
   playVideo(){if(window.__ytBlocked)this.events.onAutoplayBlocked();else this.emit(1);}
   pauseVideo(){this.emit(2);}
   destroy(){this.destroyed=true;this.frame.remove();}
 }};
 window.onYouTubeIframeAPIReady();
 `}));
};
