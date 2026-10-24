/* Apply before styles load to avoid a light flash; preference is local to this browser. */
(() => {
  const key = 'lq-theme', system = matchMedia('(prefers-color-scheme: dark)');
  let preference = null;
  try { preference = localStorage.getItem(key); } catch (_) {}
  const valid = value => value === 'light' || value === 'dark';
  if (!valid(preference)) preference = null;
  function apply() {
    const theme = preference || (system.matches ? 'dark' : 'light');
    document.documentElement.dataset.theme = theme;
    document.querySelectorAll('.theme-toggle').forEach(button => {
      button.textContent = theme === 'dark' ? 'Lys modus' : 'Mørk modus';
      button.setAttribute('aria-label', theme === 'dark' ? 'Bytt til lys modus' : 'Bytt til mørk modus');
    });
  }
  window.quizThemeButton = () => {
    const button = document.createElement('button');
    button.type = 'button'; button.className = 'theme-toggle quiet';
    const dark = document.documentElement.dataset.theme === 'dark';
    button.textContent = dark ? 'Lys modus' : 'Mørk modus';
    button.setAttribute('aria-label', dark ? 'Bytt til lys modus' : 'Bytt til mørk modus');
    button.onclick = () => {
      preference = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
      try { localStorage.setItem(key, preference); } catch (_) {}
      apply();
    };
    return button;
  };
  system.addEventListener('change', () => { if (!preference) apply(); });
  window.addEventListener('storage', event => {
    if (event.key === key || event.key === null) { preference = valid(event.newValue) ? event.newValue : null; apply(); }
  });
  apply();
  document.addEventListener('DOMContentLoaded', () => {
    document.querySelector('body > header nav').append(window.quizThemeButton());
  });
})();
