// The editor and kernel belong to JupyterLite. This shell supplies the student workflow.
const $ = id => document.getElementById(id);
const frame = $('editor');
let application;
let loading;
let exercise;
const recentKey = 'munchboka:notebook:last:' + new URL('.', location.href).pathname;

function remember(path) {
  try { localStorage.setItem(recentKey, path); } catch { /* Recovery still works through JupyterLite. */ }
}

function status(message, error = false) {
  $('status').textContent = message;
  $('status').classList.toggle('error', error);
}

function report(error) {
  console.error(error);
  status(`Noe gikk galt: ${error.message || error}. Prøv igjen, eller last siden på nytt.`, true);
}

function notebookPanel() {
  const panel = application?.shell.currentWidget;
  if (!panel?.content?.model?.cells) throw new Error('Velg en notebook først');
  return panel;
}

async function editor() {
  $('welcome').hidden = true;
  $('workspace').hidden = false;
  if (loading) return loading;
  loading = (async () => {
    status('Laster notebook-verktøyene …');
    frame.src = 'lite/lab/index.html?mode=single-document';
    const deadline = Date.now() + 90000;
    while (!frame.contentWindow?.jupyterapp) {
      if (Date.now() > deadline) throw new Error('Notebook-verktøyene kunne ikke lastes');
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    const app = frame.contentWindow.jupyterapp;
    await app.started;
    await app.restored;
    await app.serviceManager.ready;
    application = app;
    app.shell.currentChanged.connect(() => {
      const panel = app.shell.currentWidget;
      if (panel?.content?.model?.cells) remember(panel.context.path);
    });
    app.shell.collapseLeft();
    status('Verktøyene er klare. Arbeidet lagres i nettleseren. Last ned en fil når du vil ta vare på det.');
    return app;
  })();
  try { return await loading; }
  catch (error) { loading = null; throw error; }
}

async function openPath(path) {
  status('Åpner notebook …');
  const app = await editor();
  const panel = await app.commands.execute('docmanager:open', { path, factory: 'Notebook' });
  if (!panel) throw new Error('Filen kunne ikke åpnes');
  await panel.context.ready;
  remember(panel.context.path);
  status('Klar. Shift + Enter kjører en celle. Last ned notebooken før du leverer.');
  return panel;
}

function validate(data) {
  if (!data || data.nbformat !== 4 || !Array.isArray(data.cells) || !data.metadata ||
      typeof data.metadata !== 'object' || !Number.isInteger(data.nbformat_minor) ||
      !data.cells.every(cell => cell && ['code', 'markdown', 'raw'].includes(cell.cell_type) &&
        (typeof cell.source === 'string' || (Array.isArray(cell.source) && cell.source.every(s => typeof s === 'string'))))) {
    throw new Error('Filen er ikke en gyldig .ipynb-notebook (format 4)');
  }
  const language = data.metadata.kernelspec?.language || data.metadata.language_info?.name || 'python';
  if (language.toLowerCase() !== 'python') throw new Error('Denne notebooken bruker et annet språk enn Python');
  // Uploaded output must not acquire trust from another computer.
  for (const cell of data.cells) {
    if (cell.metadata) delete cell.metadata.trusted;
  }
  return data;
}

async function saveCopy(data, filename) {
  const app = await editor();
  const safeName = filename.replace(/[\\/]/g, '_').replace(/\.ipynb$/i, '');
  const path = `${safeName}-${crypto.randomUUID().slice(0, 8)}.ipynb`;
  await app.serviceManager.contents.save(path, { type: 'notebook', format: 'json', content: validate(data) });
  return openPath(path);
}

async function newNotebook() {
  await saveCopy({ nbformat: 4, nbformat_minor: 5,
    metadata: { kernelspec: { name: 'python', display_name: 'Python (Pyodide)', language: 'python' } },
    cells: [{ id: crypto.randomUUID(), cell_type: 'code', source: '', metadata: {}, outputs: [], execution_count: null }]
  }, 'Min notebook.ipynb');
}

async function download() {
  const panel = notebookPanel();
  // Download directly from the live model, even if browser storage is full.
  const blob = new Blob([JSON.stringify(panel.content.model.toJSON(), null, 2) + '\n'],
    { type: 'application/x-ipynb+json' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = panel.context.path.split('/').pop();
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 30000);
  status('Notebooken er sendt til nettleserens nedlastinger.');
}

async function original() {
  if (!exercise) return;
  const response = await fetch('lite/files/' + exercise.path.split('/').map(encodeURIComponent).join('/'));
  if (!response.ok) throw new Error('Originaloppgaven kunne ikke hentes');
  // Keep the fresh copy beside the supplied notebook, so relative data paths still work.
  const data = validate(await response.json());
  const path = exercise.path.replace(/\.ipynb$/i, `-ny-${crypto.randomUUID().slice(0, 8)}.ipynb`);
  await application.serviceManager.contents.save(path, { type: 'notebook', format: 'json', content: data });
  await openPath(path);
}

function action(id, callback) {
  $(id).addEventListener('click', async () => {
    $(id).disabled = true;
    try { await callback(); } catch (error) { report(error); }
    finally { $(id).disabled = false; }
  });
}

for (const id of ['upload', 'welcome-upload']) action(id, () => $('file').click());
for (const id of ['new', 'welcome-new']) action(id, newNotebook);
action('welcome-resume', async () => {
  let path;
  try { path = localStorage.getItem(recentKey); } catch { /* Storage may be disabled. */ }
  if (path) await openPath(path);
  else await editor();
});
action('download', download);
action('original', original);
action('open-new-tab', () => {
  // Same URL an embedding page would otherwise have linked to; pops out this
  // exact notebook (or blank notebook) into a full standalone tab.
  if (!window.open(location.href, '_blank', 'noopener')) {
    throw new Error('Nettleseren blokkerte den nye fanen. Tillat popup-vinduer for denne siden.');
  }
});
action('run', () => { notebookPanel(); return application.commands.execute('notebook:run-cell-and-select-next'); });
action('run-all', () => { notebookPanel(); return application.commands.execute('notebook:run-all-cells'); });
action('restart', async () => {
  const panel = notebookPanel();
  const kernel = panel.sessionContext.session?.kernel;
  if (!kernel) throw new Error('Python er ikke startet ennå');
  if (!confirm('Starte Python på nytt? Variablene slettes, men cellene og teksten beholdes.')) return;
  status('Starter Python på nytt …');
  await kernel.restart();
  status('Python er startet på nytt. Kjør cellene du trenger på nytt.');
});
$('file').addEventListener('change', async () => {
  const file = $('file').files[0];
  if (!file) return;
  try {
    if (file.size > 25 * 1024 * 1024) throw new Error('Filen er for stor (maks. 25 MB)');
    const data = validate(JSON.parse(await file.text()));
    await saveCopy(data, file.name);
  } catch (error) { report(error); }
  finally { $('file').value = ''; }
});
$('help-toggle').addEventListener('click', () => {
  $('help').hidden = !$('help').hidden;
  $('help-toggle').setAttribute('aria-expanded', String(!$('help').hidden));
});

window.addEventListener('beforeunload', event => {
  if (!application) return;
  // JupyterLite also prompts inside its frame; guard navigation of the outer page.
  const dirty = [...application.shell.widgets('main')].some(widget => widget.context?.model?.dirty);
  if (dirty) { event.preventDefault(); event.returnValue = ''; }
});

try {
  if (location.protocol === 'file:') throw new Error('Åpne nettsiden via en webserver, ikke direkte som fil');
  const response = await fetch('catalog.json');
  if (!response.ok) throw new Error('Oppgavelisten kunne ikke lastes');
  const catalog = await response.json();
  document.title = catalog.title;
  for (const item of catalog.notebooks) {
    const link = document.createElement('a');
    link.className = 'card';
    link.href = '?notebook=' + encodeURIComponent(item.id);
    const title = document.createElement('strong');
    title.textContent = item.title;
    const label = document.createElement('span');
    label.textContent = 'Åpne oppgaven →';
    link.append(title, label);
    $('exercises').append(link);
  }
  status('Velg en oppgave, eller åpne en .ipynb-fil fra datamaskinen.');
  const params = new URLSearchParams(location.search);
  const requested = params.get('notebook');
  if (requested) {
    exercise = catalog.notebooks.find(item => item.id === requested);
    if (!exercise) throw new Error('Oppgaven finnes ikke på denne nettsiden');
    $('original').hidden = false;
    await openPath(exercise.path);
  } else if (params.has('new')) {
    // Embedded via {notebook} with no .ipynb argument: skip the welcome screen entirely.
    await newNotebook();
  }
} catch (error) { report(error); }
