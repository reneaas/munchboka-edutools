/* One host-only player, retained across questions and modal replacements. */
window.quizMusic = function () {
  const tracks = Array.from({length: 7}, (_, index) => `music/song_${index + 1}.mp3`);
  const audio = new Audio(tracks[0]);
  audio.loop = true;
  audio.preload = 'none';
  audio.volume = 0;
  let enabled = true, active = false, pending = false, blocked = false, volume = .25;
  let currentQuestion = null;
  const controls = document.createElement('div');
  controls.className = 'music-controls';
  const toggle = document.createElement('button');
  toggle.type = 'button';
  toggle.className = 'quiet';
  const label = document.createElement('label');
  label.textContent = 'Musikkvolum';
  const slider = document.createElement('input');
  slider.type = 'range'; slider.min = 0; slider.max = 100; slider.value = 25;
  label.append(slider); controls.append(toggle, label);
  function describe() {
    toggle.textContent = blocked && enabled ? 'Spill musikk' : enabled ? 'Musikk: på' : 'Musikk: av';
    toggle.setAttribute('aria-pressed', String(enabled));
  }
  function wanted() { return enabled && active; }
  function stop() { audio.pause(); audio.volume = 0; }
  function play(prime = false) {
    if (pending || blocked || !enabled || (!prime && !active)) return;
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
      if (shouldPlay && question !== currentQuestion) {
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
