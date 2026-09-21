// Run before the stylesheet paints: same-origin book theme wins over the OS.
(() => {
  const media = window.matchMedia('(prefers-color-scheme: dark)');
  let host;
  try {
    const source = window.parent !== window ? window.parent : window.opener;
    host = source?.document;
  } catch { /* Cross-origin embeds follow the operating system. */ }
  let editorApp;
  let desired;
  let pending;

  function resolve() {
    for (const node of [host?.documentElement, host?.body]) {
      if (!node) continue;
      for (const key of ['data-theme', 'data-mode']) {
        const value = node.getAttribute(key);
        if (value === 'light' || value === 'dark') return value;
        if (value === 'auto' || value === 'system') return media.matches ? 'dark' : 'light';
      }
      if (node.classList.contains('dark')) return 'dark';
      if (node.classList.contains('light')) return 'light';
    }
    return media.matches ? 'dark' : 'light';
  }

  async function applyEditor() {
    if (!editorApp) return;
    if (pending) return pending;
    pending = (async () => {
      // Disable Jupyter's independent OS preference; the book is authoritative.
      const commands = editorApp.commands;
      if (commands.isToggled('apputils:adaptive-theme')) {
        await commands.execute('apputils:adaptive-theme');
      }
      let applied;
      do {
        applied = desired;
        const name = applied === 'dark' ? 'JupyterLab Dark' : 'JupyterLab Light';
        const body = document.getElementById('editor').contentDocument.body;
        if (body.dataset.jpThemeName !== name) {
          // The command saves settings before the asynchronous CSS load finishes.
          let observer;
          let timer;
          const changed = new Promise((resolve, reject) => {
            observer = new MutationObserver(() => {
              if (body.dataset.jpThemeName === name) resolve();
            });
            observer.observe(body, { attributes: true, attributeFilter: ['data-jp-theme-name'] });
            timer = setTimeout(() => reject(new Error('Temaet kunne ikke lastes')), 15000);
          });
          try { await Promise.all([commands.execute('apputils:change-theme', { theme: name }), changed]); }
          finally { clearTimeout(timer); observer.disconnect(); }
          // Let Jupyter finish redrawing before starting another theme change.
          const editorWindow = document.getElementById('editor').contentWindow;
          await new Promise(resolve => editorWindow.requestAnimationFrame(() =>
            editorWindow.requestAnimationFrame(resolve)));
        }
      } while (applied !== desired);
    })();
    try { await pending; }
    finally { pending = null; }
  }

  function update() {
    desired = resolve();
    document.documentElement.dataset.theme = desired;
    document.documentElement.style.colorScheme = desired;
    applyEditor().catch(error => console.error('Notebook-tema:', error));
  }

  if (host) {
    const observer = new MutationObserver(update);
    for (const node of [host.documentElement, host.body]) {
      if (node) observer.observe(node, {
        attributes: true, attributeFilter: ['data-theme', 'data-mode', 'class'],
      });
    }
  }
  media.addEventListener('change', update);
  update();
  window.munchbokaTheme = {
    async attach(app) {
      editorApp = app;
      await applyEditor();
      document.getElementById('editor').classList.add('theme-ready');
    },
  };
})();
