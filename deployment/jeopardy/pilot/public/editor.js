(function () {
  'use strict';
  const root = document.getElementById('editor');
  if (!root) return;
  let game = JSON.parse(root.dataset.game);
  game.private = game.private ?? true;
  let id = root.dataset.id, revision = Number(root.dataset.revision), active = 0;
  const expandedTiles = new WeakMap();
  let renderedTiles = [];
  let baseline = JSON.stringify(game), uploading = 0, saving = false, autosaveTimer, autosaveBlocked = false;
  let csrf = root.dataset.csrf;
  const owner = root.dataset.uid;
  let pendingSave = null, retryDelay = 2000, draftFailed = false;
  const draftPrefix = 'jeopardy-draft:' + owner + ':';
  const draftSuffix = Array.from(crypto.getRandomValues(new Uint8Array(16)), b => b.toString(16).padStart(2, '0')).join('');
  let draftKey = draftPrefix + (id || 'new') + ':' + draftSuffix;
  function persistDraft() {
    try {
      if (JSON.stringify(game) === baseline && !pendingSave) localStorage.removeItem(draftKey);
      else localStorage.setItem(draftKey, JSON.stringify({game, id, revision, baseline, pendingSave}));
      draftFailed = false;
    } catch (_) { draftFailed = true; }
  }
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
  const privacyLabel = el('label', 'Privat – skjul fra søk og deaktiver deling');
  const privacy = el('input'); privacy.type = 'checkbox'; privacy.setAttribute('role', 'switch'); privacy.checked = game.private;
  privacy.addEventListener('change', () => { game.private = privacy.checked; changed(); });
  privacyLabel.prepend(privacy);
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
  sharingPanel.append(el('h2', 'Synlighet og deling'), privacyLabel, el('p', 'Offentlige spill er søkbare og kan kopieres av andre. Privat deaktiverer også eksisterende delingslenker når endringen lagres.'), el('p', 'Alle med lenken kan spille uten innlogging, men kan ikke redigere originalen. Delingslenken viser en valgt versjon. Oppdater den med «Oppdater delt versjon». Offentlig søk viser alltid den sist lagrede versjonen.'), linkLabel, shareActions, shareStatus);
  const login = el('a', 'Logg inn i en ny fane');
  login.href = '/'; login.target = '_blank'; login.rel = 'noopener'; login.hidden = true;
  root.append(toolbar, error, login, sharingPanel, form);
  // Offer recovery explicitly: never silently overwrite a newer server version.
  try {
    for (const storedKey of Object.keys(localStorage).filter(key => key.startsWith(draftPrefix + (id || 'new') + ':'))) {
      const draft = JSON.parse(localStorage.getItem(storedKey) || 'null');
      if (draft && draft.game && typeof draft.baseline === 'string') {
        const recovery = el('div', undefined, 'card');
        recovery.append(el('p', 'Det finnes et lokalt utkast med ulagrede endringer på denne enheten.'),
          button('Gjenopprett utkast', () => {
            draftKey = storedKey;
            game = draft.game; id = draft.id; revision = draft.revision;
            baseline = draft.baseline; pendingSave = draft.pendingSave;
            privacy.checked = game.private; active = 0; recovery.remove(); render(); changed();
          }), button('Forkast lokalt utkast', () => { localStorage.removeItem(storedKey); recovery.remove(); }));
        root.prepend(recovery);
      }
    }
  } catch (_) { draftFailed = true; }
  function changed(schedule = true) {
    const dirty = !!pendingSave || JSON.stringify(game) !== baseline;
    if(schedule){persistDraft();autosaveBlocked=false;clearTimeout(autosaveTimer);if(dirty)autosaveTimer=setTimeout(autosave,1500);}
    status.textContent = uploading ? 'Laster opp bilde …' : saving ? 'Lagrer …' : dirty ? (autosaveBlocked ? 'Ikke lagret · prøv «Lagre på nett» igjen' : game.title.trim() ? 'Ulagrede endringer · lagres automatisk' : 'Skriv en tittel for å lagre automatisk') : id ? 'Lagret på nett' : 'Ikke lagret ennå';
    if (dirty && draftFailed) status.textContent += ' · lokal sikkerhetskopi er utilgjengelig; behold fanen åpen';
    save.disabled = uploading > 0 || saving || sharing;
    play.hidden = !revision || !game.categories.length;
    play.href = id ? '/?play=' + id : '#';
    shareButton.textContent = share ? 'Oppdater delt versjon' : 'Del spill';
    shareButton.disabled = game.private || !id || dirty || !game.categories.length || uploading > 0 || saving || sharing;
    stopButton.disabled = sharing;
    stopButton.hidden = copyButton.hidden = openLink.hidden = linkLabel.hidden = !share;
    shareLink.value = share ? location.origin + '/?share=' + share.token : '';
    openLink.href = shareLink.value || '#';
    shareStatus.textContent = sharing ? 'Oppdaterer deling …' : share ? `Spillet er delt med lenke.${dirty || revision !== share.revision ? ' Lagre endringene og oppdater delingen når de er klare.' : ''}` : id && !dirty ? (game.private ? 'Spillet er privat.' : 'Spillet er offentlig og kan finnes og kopieres via «Finn Jeopardy».') : 'Lagre spillet før du deler det.';
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
  async function fetchJSON(url, options = {}) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 20000);
    try {
      const response = await fetch(url, {...options, headers: {'X-Jeopardy-Request': 'editor'}, credentials: 'same-origin', signal: controller.signal});
      let result;
      try { result = await response.json(); }
      catch (_) { throw Object.assign(new Error('Serveren svarte ikke som forventet. Prøver igjen automatisk.'), {retryable: true}); }
      if (!response.ok) {
        const auth = response.status === 401 || response.status === 403;
        login.hidden = !auth;
        throw Object.assign(new Error(auth ? 'Logg inn i en ny fane, og kom tilbake hit. Endringene dine beholdes.' : result.error || 'Lagring mislyktes.'), {retryable: auth || response.status >= 500 || response.status === 429});
      }
      return result;
    } catch (e) {
      if (e.name === 'AbortError' || e instanceof TypeError) {
        throw Object.assign(new Error('Forbindelsen ble brutt. Endringene beholdes, og lagring prøves igjen automatisk.'), {retryable: true});
      }
      throw e;
    } finally { clearTimeout(timeout); }
  }
  async function refreshSession() {
    const session = await fetchJSON('/?session=1');
    if (session.uid !== owner) {
      login.hidden = false;
      throw new Error('Logg inn med samme konto som åpnet dette spillet. Utkastet beholdes.');
    }
    csrf = session.csrf; login.hidden = true;
  }
  async function request(data) {
    await refreshSession();
    data.set('csrf', csrf);
    return fetchJSON('/', {method: 'POST', body: data});
  }
  function dataFor(action) { const data = new FormData(); data.set('action', action); data.set('csrf', csrf); data.set('owner', owner); return data; }
  function autosave() {
    if(!autosaveBlocked && (pendingSave || (game.title.trim() && JSON.stringify(game)!==baseline)))void saveGame();
  }
  setInterval(autosave,15000);
  // Keep PHP's session storage alive while the editor is open. The absolute
  // authentication expiry and credential revocation still apply.
  setInterval(() => { if (document.visibilityState === 'visible') void refreshSession().catch(() => {}); }, 300000);
  window.addEventListener('focus', () => { autosaveBlocked = false; autosave(); });
  window.addEventListener('online',()=>{autosaveBlocked=false;autosave();});
  async function saveGame() {
    if (saving || uploading || sharing) return;
    clearTimeout(autosaveTimer);saving = true; error.hidden = true; changed(false);
    if (!id) id = Array.from(crypto.getRandomValues(new Uint8Array(16)), b => b.toString(16).padStart(2, '0')).join('');
    pendingSave ??= {snapshot: JSON.stringify(game), id, revision};
    const {snapshot} = pendingSave;
    persistDraft();
    const data = dataFor('save'); data.set('content', snapshot); data.set('id', pendingSave.id); data.set('revision', String(pendingSave.revision));
    try {
      const result = await request(data);
      if (result.id !== pendingSave.id || !Number.isInteger(result.revision) || result.revision < 1) {
        throw Object.assign(new Error('Lagring er ikke bekreftet. Prøver igjen automatisk.'), {retryable: true});
      }
      id = result.id; revision = result.revision; baseline = snapshot; if (JSON.parse(snapshot).private) share = null; autosaveBlocked=false;
      pendingSave = null; retryDelay = 2000;
      const oldKey = draftKey;
      draftKey = draftPrefix + id + ':' + draftSuffix;
      persistDraft();
      if (!draftFailed && oldKey !== draftKey) { try { localStorage.removeItem(oldKey); } catch (_) {} }
      history.replaceState(null, '', '/?edit=' + id);
    } catch (e) {
      autosaveBlocked = true; fail(e.message);
      if (e.retryable) {
        autosaveTimer = setTimeout(() => { autosaveBlocked = false; autosave(); }, retryDelay);
        retryDelay = Math.min(retryDelay * 2, 60000);
      } else { pendingSave = null; }
      persistDraft();
    }
    finally { saving = false; changed(false);if(!autosaveBlocked&&JSON.stringify(game)!==baseline)autosaveTimer=setTimeout(autosave,1500); }
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
    for (const [tile, details] of renderedTiles) expandedTiles.set(tile, details.open);
    renderedTiles = [];
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
      const values = [100, 200, 300];
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
    rows.append(el('h2', 'Poengrader'), el('p', 'Hver kategori har sine egne poengrader, maks åtte. Spillebrettet viser alle poengverdiene i stigende rekkefølge. Skriv en eksisterende poengverdi for å bytte plass med den raden. Spørsmål, svar og bilder følger med. Manglende rader og ruter uten spørsmål kan ikke velges.', 'hint'));
    category.tiles.forEach((tile, i) => {
      const label = el('label', `Rad ${i + 1}`);
      const input = el('input'); input.type = 'number'; input.min = 1; input.max = 10000; input.step = 1; input.value = tile.value;
      input.addEventListener('change', () => {
        const value = Number(input.value);
        if (!Number.isInteger(value) || value < 1 || value > 10000) { input.value = tile.value; fail('Poeng må være hele tall fra 1 til 10000.'); return; }
        const other = category.tiles.find(t => t !== tile && t.value === value);
        if (other) other.value = tile.value;
        tile.value = value;
        category.tiles.sort((a,b) => a.value-b.value);
        render(); changed();
      });
      const remove=button('Fjern rad',()=>{if(category.tiles.length<=1)return;if((tile.question||tile.answer||tile.questionImage||tile.answerImage)&&!confirm('Fjerne denne raden fra kategorien?'))return;category.tiles.splice(i,1);render();changed();});remove.disabled=category.tiles.length<=1;remove.setAttribute('aria-label','Fjern rad '+(i+1));
      const row=el('div',undefined,'actions');label.append(input);row.append(label,remove);rows.append(row);
    });
    const addRow = button('Legg til rad', () => {
      if (category.tiles.length >= 8) return;
      let value = Math.min(10000, Math.max(...category.tiles.map(t => t.value)) + 100);
      if(category.tiles.some(t=>t.value===value)){value=1;while(category.tiles.some(t=>t.value===value))value++;}
      const tile = emptyTile(value);
      expandedTiles.set(tile, true);
      category.tiles.push(tile); render(); changed();
    });
    addRow.disabled = category.tiles.length >= 8;
    const actions = el('div', undefined, 'actions'); actions.append(addRow); rows.append(actions); form.append(rows);
    form.append(el('p', 'Bilder: PNG, JPEG eller WebP, maks 2 MB per bilde. Skriv en kort bildebeskrivelse. Bilder lastes opp med én gang; koblingen til ruten lagres automatisk.', 'hint'));
    category.tiles.forEach((tile, i) => {
      const details = el('details', undefined, 'tile-editor'); details.open = expandedTiles.get(tile) ?? (i === 0);
      renderedTiles.push([tile, details]);
      details.append(el('summary', `${category.name || 'Kategori'} · ${tile.value} poeng`));
      const sides = el('div', undefined, 'tile-sides'); sides.append(sideEditor(tile, 'question', 'Spørsmål'), sideEditor(tile, 'answer', 'Svar'));
      details.append(sides); form.append(details);
    });
  }
  window.addEventListener('beforeunload', e => {
    if (pendingSave || JSON.stringify(game) !== baseline || uploading || saving) { e.preventDefault(); e.returnValue = ''; }
  });
  play.addEventListener('click', e => {
    if (JSON.stringify(game) !== baseline && !confirm('Spille den sist lagrede versjonen? Du har ulagrede endringer.')) e.preventDefault();
  });
  render(); changed(false);
})();
