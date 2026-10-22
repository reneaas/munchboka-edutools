/* Presentation playback: reveal after four uninterrupted seconds of PLAYING.
 * This is a timing workaround, not a guarantee about YouTube's title UI. */
(() => {
  'use strict';
  let apiReady;
  function loadAPI() {
    if (window.YT?.Player) return Promise.resolve(window.YT);
    if (apiReady) return apiReady;
    apiReady = new Promise((resolve, reject) => {
      const script = document.createElement('script');
      const timeout = setTimeout(() => reject(new Error('YouTube svarte ikke. Last siden på nytt for å prøve igjen.')), 15000);
      window.onYouTubeIframeAPIReady = () => { clearTimeout(timeout); resolve(window.YT); };
      script.onerror = () => { clearTimeout(timeout); reject(new Error('YouTube kunne ikke lastes. Kontroller nettforbindelsen.')); };
      script.src = 'https://www.youtube.com/iframe_api'; document.head.append(script);
    });
    return apiReady;
  }
  window.quizYouTube = async (target, videoId, autoplay = true) => {
    const wrap = document.createElement('div'), screen = document.createElement('div'), frame = document.createElement('iframe');
    wrap.className = 'quiz-video'; screen.className = 'quiz-video-screen';
    frame.title = 'YouTube-video'; frame.tabIndex = -1; frame.setAttribute('aria-hidden', 'true');
    frame.allow = 'autoplay; encrypted-media'; frame.referrerPolicy = 'strict-origin-when-cross-origin';
    // API initiates playback only after its listeners are ready.
    frame.src = 'https://www.youtube-nocookie.com/embed/' + videoId + '?' + new URLSearchParams({enablejsapi:'1', origin:location.origin, autoplay:'0', mute:'0', controls:'0', disablekb:'1', playsinline:'1', cc_load_policy:'0', rel:'0'});
    const control = document.createElement('button'), message = document.createElement('p');
    control.type = 'button'; control.className = 'secondary'; control.textContent = 'Spill av'; control.disabled = true;
    message.className = 'hint'; message.setAttribute('role', 'status'); message.textContent = 'Laster YouTube …';
    screen.append(frame); wrap.append(screen, control, message); target.append(wrap);
    let player, timer, state = -1, disposed = false, observer;
    const hide = () => { clearTimeout(timer); timer = undefined; screen.classList.remove('video-visible'); };
    const dispose = () => { disposed = true; hide(); observer?.disconnect(); player?.destroy(); };
    const fail = text => { hide(); control.disabled = true; message.textContent = text; };
    function changed(value) {
      if (disposed) return;
      const previous = state; state = value;
      control.textContent = value === 1 ? 'Pause' : value === 0 ? 'Spill igjen' : 'Spill av';
      if (value === 1) {
        if (previous === 1) return;
        message.textContent = 'Lyden spilles. Videoen vises etter fire sekunder.';
        timer = setTimeout(() => {
          if (!wrap.isConnected || disposed || state !== 1) return;
          screen.classList.add('video-visible'); message.textContent = 'Spiller av.';
        }, 4000);
      } else {
        hide();
        message.textContent = value === 0 ? 'Avspillingen er ferdig.' : value === 3 ? 'Laster video …' : 'Trykk Spill av for lyd. Videoen vises etter fire sekunder.';
      }
    }
    try {
      const YT = await loadAPI();
      if (!wrap.isConnected) return;
      observer = new MutationObserver(() => { if (!wrap.isConnected) dispose(); });
      observer.observe(document.body, {childList:true, subtree:true});
      player = new YT.Player(frame, {events: {
        onReady: event => {
          if (disposed) return;
          control.disabled = false; message.textContent = 'Trykk Spill av for lyd. Videoen vises etter fire sekunder.';
          event.target.unMute();
          if (autoplay) event.target.playVideo();
        },
        onStateChange: event => changed(event.data),
        onAutoplayBlocked: () => { if (!disposed) { hide(); message.textContent = 'Nettleseren blokkerte automatisk avspilling. Trykk Spill av.'; } },
        onError: () => { if (!disposed) fail('Videoen kunne ikke spilles av. Den kan være utilgjengelig eller blokkert for innbygging.'); }
      }});
      control.onclick = () => {
        if (state === 1) { hide(); player.pauseVideo(); }
        else { player.unMute(); player.playVideo(); }
      };
    } catch (err) { if (!disposed && wrap.isConnected) fail(err.message); }
  };
})();
