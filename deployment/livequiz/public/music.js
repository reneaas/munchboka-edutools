/* One host-only player, retained across questions and modal replacements. */
window.quizMusic = function ({lobby = false} = {}) {
  const tracks = JSON.parse((lobby ? document.body.dataset.lobbyMusicTracks : document.body.dataset.musicTracks) || '[]');
  const audio = new Audio(tracks[0] || undefined);
  audio.loop = !lobby;
  audio.preload = 'none';
  audio.volume = 0;
  let enabled = !lobby, active = false, pending = false, blocked = false, volume = .25;
  let currentQuestion = null, currentTrack = null;
  const controls = document.createElement('div');
  controls.className = 'music-controls'+(lobby?' lobby-music-controls':'');
  const toggle = document.createElement('button');
  toggle.type = 'button';
  toggle.className = 'quiet';
  const label = document.createElement('label');
  label.textContent = lobby ? 'Lobbymusikkvolum' : 'Musikkvolum';
  const slider = document.createElement('input');
  slider.type = 'range'; slider.min = 0; slider.max = 100; slider.value = 25;
  label.append(slider); controls.append(toggle, label);
  function describe() {
    toggle.disabled = tracks.length === 0;
    slider.disabled = tracks.length === 0;
    const name = lobby ? 'Lobbymusikk' : 'Musikk';
    toggle.textContent = !tracks.length ? (lobby ? 'Ingen lobbymusikk tilgjengelig' : 'Ingen musikk tilgjengelig') : blocked && enabled ? (lobby ? 'Spill lobbymusikk' : 'Spill musikk') : name + (enabled ? ': på' : ': av');
    toggle.setAttribute('aria-pressed', String(enabled));
  }
  function wanted() { return tracks.length > 0 && enabled && active; }
  function stop() { audio.pause(); audio.volume = 0; }
  function nextLobbyTrack() {
    const choices = tracks.length > 1 ? tracks.filter(track => track !== currentTrack) : tracks;
    currentTrack = choices[Math.floor(Math.random() * choices.length)];
    audio.src = currentTrack;
    audio.currentTime = 0;
  }
  audio.onended = () => {
    if (!lobby || !wanted()) return;
    nextLobbyTrack();
    play();
  };
  function play(prime = false) {
    if (!tracks.length || pending || blocked || !enabled || (!prime && !active)) return;
    if (lobby && currentTrack === null) nextLobbyTrack();
    pending = true;
    // Called directly from Start/Next to unlock this element during a user gesture.
    audio.play().then(() => {
      pending = false;
      if (!wanted()) stop();
    }).catch(error => {
      pending = false;
      // Pausing during a phase change can cancel an in-flight play request.
      if (error.name !== 'AbortError') blocked = true;
      stop(); describe();
    });
  }
  toggle.onclick = () => {
    if (blocked && enabled) blocked = false;
    else enabled = !enabled;
    describe();
    if (enabled) play(true); else stop();
  };
  slider.oninput = () => { volume = Number(slider.value) / 100; };
  const fade = setInterval(() => {
    if (wanted() && !audio.paused) audio.volume += Math.max(-.05, Math.min(.05, volume - audio.volume));
  }, 100);
  window.addEventListener('pagehide', () => { active = false; stop(); clearInterval(fade); }, {once:true});
  describe();
  return {
    controls,
    unlock() { blocked = false; describe(); play(true); },
    update(shouldPlay, question = 0) {
      if (!lobby && tracks.length && shouldPlay && question !== currentQuestion) {
        stop();
        currentQuestion = question;
        audio.src = tracks[Math.floor(Math.random() * tracks.length)];
        audio.currentTime = 0;
      }
      active = shouldPlay;
      if (!wanted()) stop();
      else if (audio.paused) play();
    }
  };
};
