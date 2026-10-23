/* Delete saved games only after explicit confirmation. */
(() => {
  'use strict';
  document.querySelectorAll('form.delete-game').forEach(form => {
    const submit = form.querySelector('button[type=submit]');
    submit.disabled = false;
    form.addEventListener('submit', event => {
      if (!window.confirm(`Slette «${form.dataset.title}»? Quizen og lagrede versjoner slettes, og delingslenker slutter å virke. Dette kan ikke angres.`)) {
        event.preventDefault();
        return;
      }
      submit.disabled = true;
    });
  });
})();
