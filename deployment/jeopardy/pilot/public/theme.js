(function () {
  'use strict';
  const key = 'munchboka-jeopardy-theme';
  const media = window.matchMedia('(prefers-color-scheme: dark)');
  let preference = 'system';
  try { preference = localStorage.getItem(key) || 'system'; } catch (_) {}
  function apply(value) {
    preference = ['light', 'dark', 'system'].includes(value) ? value : 'system';
    document.documentElement.dataset.theme = preference === 'system' ? (media.matches ? 'dark' : 'light') : preference;
    const select = document.getElementById('theme');
    if (select) select.value = preference;
  }
  apply(preference);
  media.addEventListener('change', () => { if (preference === 'system') apply('system'); });
  window.addEventListener('storage', event => { if (event.key === key) apply(event.newValue || 'system'); });
  document.addEventListener('DOMContentLoaded', () => {
    const select = document.getElementById('theme');
    if (!select) return;
    select.value = preference;
    select.addEventListener('change', () => {
      apply(select.value);
      try { localStorage.setItem(key, preference); } catch (_) {}
    });
  });
})();
