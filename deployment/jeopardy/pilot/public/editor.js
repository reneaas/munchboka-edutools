(function () {
  'use strict';
  const root = document.getElementById('editor');
  if (!root) return;
  const game = JSON.parse(root.dataset.game);
  let id = root.dataset.id, revision = Number(root.dataset.revision), active = 0;
  let baseline = JSON.stringify(game), uploading = 0, saving = false;
  const csrf = root.dataset.csrf;
  let share = JSON.parse(root.dataset.share || 'null'), sharing = false;
  const el = (tag, text, cls) => {
    const n = document.createElement(tag);
    if (text !== undefined) n.textContent = text;
    if (cls) n.className = cls;
    return n;
  };
  const button = (text, fn, cls = 'quiet') => {
    const b = el('button', text, cls); b.type = 'button'; b.addEventListener('click', fn); return b;
  };
  const status = el('p', '', 'save-status'); status.setAttribute('role', 'status');
  const error = el('div', '', 'error'); error.hidden = true; error.setAttribute('role', 'alert');
  const toolbar = el('div', undefined, 'editor-toolbar');
  const save = button('Lagre på nett', saveGame, '');
  const play = el('a', 'Spill lagret versjon');
  const form = el('div', undefined, 'card');
  toolbar.append(save, play, status);
  const sharingPanel = el('section', undefined, 'card');
  const shareStatus = el('p', '', 'hint'); shareStatus.setAttribute('role', 'status');
  const shareButton = button('Del spill', () => changeSharing('share'));
  const stopButton = button('Stopp deling', () => changeSharing('unshare'));
  const linkLabel = el('label', 'Delingslenke');
  const shareLink = el('input'); shareLink.readOnly = true; linkLabel.append(shareLink);
  const copyButton = button('Kopier lenke', async () => {
    try { await navigator.clipboard.writeText(shareLink.value); shareStatus.textContent = 'Lenken er kopiert.'; }
    catch (_) { shareLink.focus(); shareLink.select(); shareStatus.textContent = 'Marker lenken og kopier den med Ctrl+C eller Cmd+C.'; }
  });
  const openLink = el('a', 'Åpne delt spill'); openLink.target = '_blank'; openLink.rel = 'noopener noreferrer';
  const shareActions = el('div', undefined, 'actions'); shareActions.append(shareButton, copyButton, openLink, stopButton);
  sharingPanel.append(el('h2', 'Del spillet'), el('p', 'Alle med lenken kan spille uten innlogging, men kan ikke redigere originalen. Bare den delte versjonen og bildene i den blir tilgjengelige. Senere endringer deles først når du velger «Oppdater delt versjon».'), linkLabel, shareActions, shareStatus);
  root.append(toolbar, error, sharingPanel, form);
  function changed() {
    const dirty = JSON.stringify(game) !== baseline;
    status.textContent = uploading ? 'Laster opp bilde …' : saving ? 'Lagrer …' : dirty ? 'Ulagrede endringer' : id ? `Lagret på nett · versjon ${revision}` : 'Ikke lagret ennå';
    save.disabled = uploading > 0 || saving || sharing;
    play.hidden = !id || !game.categories.length;
    play.href = id ? '/?play=' + id : '#';
    shareButton.textContent = share ? 'Oppdater delt versjon' : 'Del spill';
    shareButton.disabled = !id || dirty || !game.categories.length || uploading > 0 || saving || sharing;
    stopButton.disabled = sharing;
    stopButton.hidden = copyButton.hidden = openLink.hidden = linkLabel.hidden = !share;
    shareLink.value = share ? location.origin + '/?share=' + share.token : '';
    openLink.href = shareLink.value || '#';
    shareStatus.textContent = sharing ? 'Oppdaterer deling …' : share ? `Versjon ${share.revision} er delt.${dirty || revision !== share.revision ? ' Lagre endringene og oppdater delingen når de er klare.' : ''}` : id && !dirty ? 'Spillet er privat. Velg «Del spill» for å lage en lenke.' : 'Lagre spillet før du deler det.';
  }
  function fail(message) { error.textContent = message; error.hidden = false; }
  function field(label, value, oninput, multiline = false) {
    const wrap = el('label', label);
    const input = el(multiline ? 'textarea' : 'input');
    input.value = value;
    input.maxLength = multiline ? 8000 : 180;
    if (multiline) input.rows = 3;
    input.addEventListener('input', () => { oninput(input.value); changed(); });
    wrap.append(input);
    return wrap;
  }
  async function request(data) {
    const response = await fetch('/', {method: 'POST', headers: {'X-Jeopardy-Request': 'editor'}, body: data, credentials: 'same-origin'});
    let result;
    try { result = await response.json(); } catch (_) { throw new Error('Serveren svarte ikke som forventet. Endringene er fortsatt i denne fanen.'); }
    if (!response.ok) {
      if (response.status === 401) throw new Error('Innloggingen er utløpt. Logg inn i en ny fane og behold denne fanen åpen. Last deretter inn den nye spillfanen før du kopierer endringene dine.');
      throw new Error(result.error || 'Forespørselen mislyktes. Prøv igjen.');
    }
    return result;
  }
  function dataFor(action) { const data = new FormData(); data.set('action', action); data.set('csrf', csrf); return data; }
  async function saveGame() {
    if (saving || uploading || sharing) return;
    saving = true; error.hidden = true; changed();
    const snapshot = JSON.stringify(game);
    const data = dataFor('save'); data.set('content', snapshot); data.set('id', id); data.set('revision', String(revision));
    try {
      const result = await request(data);
      id = result.id; revision = result.revision; baseline = snapshot;
      history.replaceState(null, '', '/?edit=' + id);
    } catch (e) { fail(e.message); }
    finally { saving = false; changed(); }
  }
  async function changeSharing(action) {
    if (sharing || !id) return;
    if (action === 'share' && (saving || uploading || JSON.stringify(game) !== baseline)) return;
    sharing = true; error.hidden = true; changed();
    const data = dataFor(action); data.set('id', id); data.set('revision', String(revision));
    try { const result = await request(data); share = result.share; }
    catch (e) { fail(e.message); }
    finally { sharing = false; changed(); }
  }
  function preview(tile, side, target) {
    target.replaceChildren();
    const text = el('div', tile[side], 'jp-text'); target.append(text);
    window.renderMathInElement(text);
    const image = tile[side + 'Image'];
    if (image) {
      const img = el('img'); img.src = '/?media=' + image.id; img.alt = image.alt; img.className = 'jp-content-image'; target.append(img);
    }
  }
  function sideEditor(tile, side, label) {
    const box = el('section', undefined, 'side-editor');
    const view = el('div', undefined, 'content-preview');
    let timer;
    box.append(field(label, tile[side], v => {
      tile[side] = v; clearTimeout(timer); timer = setTimeout(() => preview(tile, side, view), 180);
    }, true));
    const imageControls = el('div', undefined, 'image-controls');
    function renderImageControls() {
      imageControls.replaceChildren();
      const image = tile[side + 'Image'];
      if (image) {
        const altField = field('Bildebeskrivelse', image.alt, v => { image.alt = v; preview(tile, side, view); });
        altField.querySelector('input').maxLength = 500;
        imageControls.append(altField, button('Fjern bildet fra ruten', () => { tile[side + 'Image'] = null; renderImageControls(); preview(tile, side, view); changed(); }));
      }
      const label = el('label', image ? 'Bytt bilde' : 'Legg til bilde');
      const input = el('input'); input.type = 'file'; input.accept = 'image/png,image/jpeg,image/webp';
      input.addEventListener('change', async () => {
        const file = input.files[0]; if (!file) return;
        if (file.size > 2 * 1024 * 1024) { fail('Bildet må være mindre enn 2 MB.'); input.value = ''; return; }
        uploading++; changed(); input.disabled = true; error.hidden = true;
        const data = dataFor('upload'); data.set('image', file);
        try {
          const result = await request(data);
          tile[side + 'Image'] = {...result.image, alt: file.name.replace(/\.[^.]+$/, '').replace(/[_-]/g, ' ')};
          renderImageControls(); preview(tile, side, view);
        } catch (e) { fail(e.message); input.value = ''; }
        finally { uploading--; input.disabled = false; changed(); }
      });
      label.append(input); imageControls.append(label);
    }
    renderImageControls();
    box.append(imageControls, el('p', 'Forhåndsvisning', 'hint'), view);
    preview(tile, side, view);
    return box;
  }
  function emptyTile(value) { return {value, question: '', answer: '', questionImage: null, answerImage: null}; }
  function render() {
    form.replaceChildren();
    form.append(field('Spillets tittel', game.title, v => { game.title = v; }));
    const layout = el('div', undefined, 'actions');
    const catLabel = el('label', 'Velg kategori');
    const select = el('select');
    game.categories.forEach((c, i) => { const option = el('option', c.name || `Kategori ${i + 1}`); option.value = i; option.selected = i === active; select.append(option); });
    select.addEventListener('change', () => { active = Number(select.value); render(); });
    catLabel.append(select);
    catLabel.hidden = !game.categories.length;
    const newCategoryLabel = el('label', 'Ny kategori');
    const newCategory = el('input'); newCategory.placeholder = 'Skriv kategorinavn'; newCategory.maxLength = 180;
    newCategoryLabel.append(newCategory);
    function createCategory() {
      if (game.categories.length >= 8) return;
      const name = newCategory.value.trim();
      if (!name) { newCategory.setCustomValidity('Skriv et navn på kategorien.'); newCategory.reportValidity(); return; }
      const values = game.categories.length ? game.categories[0].tiles.map(t => t.value) : [100, 200, 300];
      game.categories.push({name, tiles: values.map(emptyTile)});
      active = game.categories.length - 1; render(); changed();
    }
    newCategory.addEventListener('input', () => newCategory.setCustomValidity(''));
    newCategory.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); createCategory(); } });
    const addCategory = button('Legg til kategori', createCategory);
    addCategory.disabled = game.categories.length >= 8;
    newCategory.disabled = game.categories.length >= 8;
    const removeCategory = button('Fjern kategori', () => {
      const category = game.categories[active];
      const hasContent = category && category.tiles.some(t => t.question || t.answer || t.questionImage || t.answerImage);
      if (category && (!hasContent || confirm('Fjerne denne kategorien og alle spørsmålene i den?'))) {
        game.categories.splice(active, 1); active = Math.max(0, active - 1); render(); changed();
      }
    });
    removeCategory.hidden = !game.categories.length;
    layout.append(catLabel, removeCategory, newCategoryLabel, addCategory); form.append(layout);
    if (!game.categories.length) {
      form.append(el('h2', 'Dine kategorier'), el('p', 'Ingen kategorier ennå. Skriv et kategorinavn og velg «Legg til kategori» for å begynne. Du bestemmer selv temaene og innholdet.'));
      return;
    }
    const category = game.categories[active];
    form.append(field('Kategorinavn', category.name, v => { category.name = v; select.options[active].textContent = v || `Kategori ${active + 1}`; form.querySelectorAll('.tile-editor > summary').forEach((summary, i) => { summary.textContent = `${v || 'Kategori'} · ${category.tiles[i].value} poeng`; }); }));
    const rows = el('div', undefined, 'row-controls');
    rows.append(el('h2', 'Poengrader'), el('p', 'Poengverdiene gjelder for alle kategorier. Maks åtte kategorier og åtte rader.', 'hint'));
    category.tiles.forEach((tile, i) => {
      const label = el('label', `Rad ${i + 1}`);
      const input = el('input'); input.type = 'number'; input.min = 1; input.max = 10000; input.step = 1; input.value = tile.value;
      input.addEventListener('input', () => { game.categories.forEach(c => { c.tiles[i].value = Number(input.value); }); changed(); });
      input.addEventListener('change', () => render());
      label.append(input); rows.append(label);
    });
    const addRow = button('Legg til rad', () => {
      if (category.tiles.length >= 8) return;
      const value = Math.min(10000, Math.max(...category.tiles.map(t => t.value)) + 100);
      game.categories.forEach(c => c.tiles.push(emptyTile(value))); render(); changed();
    });
    addRow.disabled = category.tiles.length >= 8;
    const removeRow = button('Fjern siste rad', () => {
      if (category.tiles.length > 1 && confirm('Fjerne siste rad i alle kategorier?')) {
        game.categories.forEach(c => c.tiles.pop()); render(); changed();
      }
    });
    removeRow.disabled = category.tiles.length <= 1;
    const actions = el('div', undefined, 'actions'); actions.append(addRow, removeRow); rows.append(actions); form.append(rows);
    form.append(el('p', 'Bilder: PNG, JPEG eller WebP, maks 2 MB per bilde. Skriv en kort bildebeskrivelse. Bilder lastes opp med én gang; lagre spillet for å beholde koblingen til ruten.', 'hint'));
    category.tiles.forEach((tile, i) => {
      const details = el('details', undefined, 'tile-editor'); details.open = i === 0;
      details.append(el('summary', `${category.name || 'Kategori'} · ${tile.value} poeng`));
      const sides = el('div', undefined, 'tile-sides'); sides.append(sideEditor(tile, 'question', 'Spørsmål'), sideEditor(tile, 'answer', 'Svar'));
      details.append(sides); form.append(details);
    });
  }
  window.addEventListener('beforeunload', e => {
    if (JSON.stringify(game) !== baseline || uploading || saving) { e.preventDefault(); e.returnValue = ''; }
  });
  play.addEventListener('click', e => {
    if (JSON.stringify(game) !== baseline && !confirm('Spille den sist lagrede versjonen? Du har ulagrede endringer.')) e.preventDefault();
  });
  render(); changed();
})();
