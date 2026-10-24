/* Livequiz proof of concept: same-origin PHP API, non-overlapping polling. */
(() => {
  'use strict';
  const app = document.querySelector('#app'), notice = document.querySelector('#notice');
  const params = new URLSearchParams(location.search);
  let csrf = '', uid = 0, pending = false, dirty = false, uploads = 0;
  const el = (tag, text, cls) => { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if (cls) n.className = cls; return n; };
  function error(e) { const target = document.querySelector('.question-modal .modal-notice') || notice; target.textContent = e.message || String(e); target.hidden = false; }
  function clearError() { notice.hidden = true; const target = document.querySelector('.question-modal .modal-notice'); if (target) target.hidden = true; }
  function button(label, fn, cls = '') {
    const b = el('button', label, cls); b.type = 'button';
    b.onclick = async () => { b.disabled = true; clearError(); try { await fn(); } catch (e) { error(e); } finally { b.disabled = false; } }; return b;
  }
  function link(text, href) { const a = el('a', text, 'button secondary'); a.href = href; return a; }
  function field(label, value, update, type = 'text') {
    const wrap = el('label', label), input = el(type === 'textarea' ? 'textarea' : 'input');
    if (type !== 'textarea') input.type = type;
    input.value = value; input.addEventListener('input', () => update(input.value)); wrap.append(input); return wrap;
  }
  function group(...children) { const n = el('div', undefined, 'actions'); n.append(...children); return n; }
  async function api(action, data, query = {}, token = '', binary = false) {
    const url = new URL('index.php', location.href); url.search = new URLSearchParams({api: action, ...query});
    const headers = {};
    if(params.has('host')){const key=sessionStorage.getItem('lq-host-'+params.get('host'));if(key)headers['X-Host-Token']=key;}
    if(action==='shared')headers['X-Quiz-Share']=new URLSearchParams(location.hash.slice(1)).get('key')||'';
    if (token) headers['X-Player-Token'] = token;
    if (data !== undefined) { headers['X-CSRF-Token'] = csrf; if (!(data instanceof FormData)) headers['Content-Type'] = 'application/json'; }
    const response = await fetch(url, {method: data === undefined ? 'GET' : 'POST', headers, body: data === undefined ? undefined : data instanceof FormData ? data : JSON.stringify(data), credentials: 'same-origin', cache: 'no-store', signal: AbortSignal.timeout(10000)});
    if (binary && response.ok) return response.blob();
    let result; try { result = await response.json(); } catch (_) { throw new Error('Serveren svarte ikke som forventet. Prøv igjen.'); }
    if (!response.ok) throw new Error(result.error || 'Forespørselen mislyktes.'); return result;
  }
  function rich(text) { const n = el('div', text, 'rich'); window.renderMathInElement(n); return n; }
  function optionOrder(n, seed) {
    let a = 1779033703 ^ seed.length;
    for (let i = 0; i < seed.length; i++) { a = Math.imul(a ^ seed.charCodeAt(i), 3432918353); a = a << 13 | a >>> 19; }
    a >>>= 0;
    const rand = () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
    const order = Array.from({length: n}, (_, i) => i);
    for (let i = n - 1; i > 0; i--) { const j = Math.floor(rand() * (i + 1)); [order[i], order[j]] = [order[j], order[i]]; }
    return order;
  }
  function optionCards(q, order, revealed) {
    const grid = el('div', undefined, 'option-grid');
    order.forEach((orig, pos) => {
      const card = el('div', undefined, 'option-card' + (revealed ? (q.correct.includes(orig) ? ' correct' : ' wrong') : ''));
      card.append(el('span', String(pos + 1), 'option-badge'), rich(q.options[orig]));
      if (revealed && q.correct.includes(orig)) card.append(el('span', 'Riktig svar', 'correct-label'));
      grid.append(card);
    });
    return grid;
  }
  function answerChart(s, order) {
    const q = s.question, d = s.distribution || {counts: [], correct: 0, answered: 0}, wrap = el('div'), text = q.type === 'text';
    const rows = text
      ? [{label: 'Riktig', count: d.correct, ok: true}, {label: 'Feil', count: d.answered - d.correct}, {label: 'Ikke svart', count: Math.max(0, s.players - d.answered)}]
      : order.map((orig, pos) => ({label: q.options[orig], badge: pos + 1, count: d.counts[orig] || 0, ok: q.correct.includes(orig)}));
    const base = Math.max(1, text ? s.players : d.answered), chart = el('div', undefined, 'chart');
    if (text) wrap.append(el('p', 'Riktig svar: ' + q.accepted.join(' · '), 'hint'));
    for (const r of rows) {
      const row = el('div', undefined, 'chart-row' + (r.ok ? ' correct' : '')), label = el('div', undefined, 'chart-label');
      if (r.badge) label.append(el('span', String(r.badge), 'option-badge'), rich(r.label)); else label.append(el('span', r.label));
      const track = el('div', undefined, 'chart-track'), bar = el('div', undefined, 'chart-bar'); bar.style.width = '0'; track.append(bar);
      row.append(label, track, el('span', String(r.count), 'chart-count')); chart.append(row);
      const pct = r.count > 0 ? Math.max(3, Math.round(100 * r.count / base)) : 0;
      requestAnimationFrame(() => requestAnimationFrame(() => { bar.style.width = pct + '%'; }));
    }
    wrap.append(chart, el('p', `${d.answered} av ${s.players} svarte · ${d.correct} riktige`, 'hint'));
    return wrap;
  }
  function leaderboardList(rows) {
    if (!rows.length) return el('p', 'Ingen deltakere ennå.', 'hint');
    const list = el('ol', undefined, 'board');
    rows.forEach((p, i) => {
      const li = el('li'), name = el('span', p.name || p.nickname, 'name');
      if (p.members) name.append(el('small', p.members.map(member => member.nickname).join(' · '), 'team-members'));
      li.append(el('span', String(i + 1), 'rank'), name, el('strong', p.score + ' poeng')); list.append(li);
    });
    return list;
  }
  async function content(q, target, context = {}, promptTarget = target) {
    promptTarget.append(rich(q.prompt));
    if (q.code) { const holder = el('div', undefined, 'code-display'); target.append(holder); renderCodeBlock(holder, q.code); }
    if (q.image && context.showImages !== false) {
      const img = el('img', undefined, 'question-image'); img.alt = q.image.alt || 'Bilde til spørsmålet'; target.append(img);
      try { const blob = await api('media', undefined, {...context.query, image: q.image.id}, context.token || '', true); const url = URL.createObjectURL(blob); img.onload = () => URL.revokeObjectURL(url); img.src = url; }
      catch (_) { img.replaceWith(el('p', 'Bildet kunne ikke lastes.')); }
    }
    if (q.youtube && context.showVideo !== false) void window.quizYouTube(target, q.youtube, context.autoplay !== false);
  }

  function home() {
    app.replaceChildren(el('p', 'LÆR SAMMEN', 'eyebrow'), el('h1', 'Klar for neste spørsmål?'), el('p', 'Bli med i lærerens quiz. Du trenger bare spillkoden og et kallenavn.', 'intro'));
    const form = el('form', undefined, 'card join'); let pin = params.get('pin') || '', name = '';
    const pinField = field('Spillkode', pin, v => pin = v); const inp = pinField.querySelector('input'); inp.inputMode = 'numeric'; inp.pattern = '[0-9]{6}'; inp.maxLength = 6; inp.required = true; inp.autocomplete = 'off';
    const nameField = field('Kallenavn', '', v => name = v); nameField.querySelector('input').maxLength = 40; nameField.querySelector('input').required = true;
    const join = el('button', 'Bli med'); join.type = 'submit'; form.append(pinField, nameField, join);
    form.onsubmit = async e => {
      e.preventDefault(); join.disabled = true; clearError();
      try {
        pin = pin.trim(); const key = 'lq-pin-' + pin;
        let token = sessionStorage.getItem(key);
        if (!token) { token = Array.from(crypto.getRandomValues(new Uint8Array(32)), b => b.toString(16).padStart(2,'0')).join(''); sessionStorage.setItem(key, token); }
        const r = await api('join', {pin, name}, {}, token); sessionStorage.setItem('lq-room-' + r.room, token); location.href = '?room=' + r.room;
      } catch (err) { error(err); join.disabled = false; }
    };
    app.append(form, el('p', 'Læreren styrer tempoet. Læreren velger faste poeng eller poeng for raske riktige svar.', 'hint'));
  }
  function login() {
    app.replaceChildren(el('p', 'DIN QUIZKONTO', 'eyebrow'), el('h1', uid ? 'Du er logget inn' : 'Logg inn med e-post'));
    if (uid) { app.append(link('Mine quizer', '?teacher=1'), button('Logg ut', async () => {await api('logout', {}); location.href='./';}, 'quiet')); return; }
    app.append(el('p', 'Bruk din @osloskolen.no-adresse. Vi sender en engangskode. Du logger inn separat her og på Jeopardy.', 'intro'));
    const form=el('form',undefined,'card join');let value='';
    const label=field(pending?'Engangskode':'E-post i Osloskolen','',v=>value=v,pending?'text':'email');
    const input=label.querySelector('input');input.required=true;
    if(pending){input.inputMode='numeric';input.pattern='[0-9]{8}';input.maxLength=8;input.autocomplete='one-time-code';}
    else {input.maxLength=254;input.autocomplete='email';}
    const submit=el('button',pending?'Logg inn':'Send kode');submit.type='submit';form.append(label,submit);
    form.onsubmit=async e=>{e.preventDefault();submit.disabled=true;clearError();try{await api(pending?'verify':'send',pending?{code:value}:{email:value});if(pending)location.href='?teacher=1';else{pending=true;login();}}catch(err){error(err);submit.disabled=false;}};
    app.append(form);
    if(pending)app.append(el('p','Koden gjelder i ti minutter. Sjekk også søppelpost.','hint'),button('Be om en ny kode',()=>{pending=false;login();},'quiet'));
  }
  async function library() {
    app.replaceChildren(el('p', 'DITT KLASSEROM', 'eyebrow'), el('h1', 'Mine quizer'));
    if (!uid) { app.append(el('p', 'Logg inn med Osloskolen-kontoen din for å lage og lagre quizer.'), link('Logg inn', '?login=1')); return; }
    app.append(link('＋ Lag en quiz', '?new=1'));
    const data = await api('library');
    if (!data.quizzes.length) app.append(el('p', 'Din første quiz starter med et godt spørsmål.'));
    const grid = el('div', undefined, 'library');
    for (const q of data.quizzes) {
      const card = el('article', undefined, 'card'); card.append(el('h2', q.title), el('p', 'Versjon ' + q.revision), group(link('Rediger', '?edit=' + q.id), button('Start spill', async () => { const r = await api('create', {id:q.id}); location.href = '?host=' + r.room; }), button('Del quiz',()=>shareQuiz(q,card),'secondary'), button('Slett', async () => { if (!confirm('Slette «' + q.title + '»? Dette kan ikke angres.')) return; await api('delete', {id:q.id}); card.remove(); }, 'quiet'))); grid.append(card);
    }
    app.append(grid);
    if (data.rooms.length) {
      app.append(el('h2', 'Siste spill · tilgjengelig i seks timer'));
      for (const r of data.rooms) app.append(link('Spill ' + r.pin + (r.phase === 'finished' ? ' · avsluttet' : ' · åpne'), '?host=' + r.id));
    }
  }
  async function shareQuiz(q,card) {
    const data=await api('share',{id:q.id,enabled:true});
    card.querySelector('.share-panel')?.remove();
    const panel=el('section',undefined,'share-panel');
    const url=new URL('./',location.href);url.searchParams.set('share',q.id);url.hash=new URLSearchParams({key:data.key});
    const label=field('Delingslenke',url.href,()=>{}),input=label.querySelector('input');input.readOnly=true;input.onclick=()=>input.select();
    const status=el('p','','hint');status.setAttribute('role','status');
    panel.append(el('p','Alle med lenken kan starte et eget spill uten konto. De kan ikke redigere quizen din. Lenken bruker siste lagrede versjon.','hint'),label,
      group(button('Kopier lenke',async()=>{try{await navigator.clipboard.writeText(url.href);status.textContent='Lenken er kopiert.';}catch(_){input.focus();input.select();status.textContent='Kopier den markerte lenken.';}}),
        button('Slå av deling',async()=>{await api('share',{id:q.id,enabled:false});panel.replaceChildren(el('p','Deling er slått av. Gamle lenker kan ikke starte nye spill. Spill som allerede er startet, fortsetter.','hint'));},'quiet')),status);
    card.append(panel);input.focus();input.select();
  }
  async function sharedQuiz() {
    const id=params.get('share'),key=new URLSearchParams(location.hash.slice(1)).get('key')||'';
    const quiz=await api('shared',undefined,{id});
    app.replaceChildren(el('p','DELT QUIZ','eyebrow'),el('h1',quiz.title),el('p',`${quiz.total} spørsmål · Du trenger ingen konto.`,'intro'),
      el('p','Start et eget spill for klassen din. Du styrer spørsmålene og får en egen spillkode til elevene. Hold denne fanen åpen; den gir deg tilgang til å styre spillet.'),
      button('Start spill for min klasse',async()=>{
        const hostToken=Array.from(crypto.getRandomValues(new Uint8Array(32)),b=>b.toString(16).padStart(2,'0')).join('');
        // Verify storage works before creating a room whose controls depend on it.
        sessionStorage.setItem('lq-storage-check','1');sessionStorage.removeItem('lq-storage-check');
        const room=await api('shared-start',{id,key,host_token:hostToken});
        sessionStorage.setItem('lq-host-'+room.room,hostToken);location.href='?host='+room.room;
      }));
  }
  const blankQuestion = () => ({type:'single', prompt:'', code:'', youtube:'', image:null, seconds:30, options:['','','',''], correct:[0], accepted:[]});
  async function editor() {
    if (!uid) return library();
    let saved = params.has('edit') ? await api('quiz', undefined, {id:params.get('edit')}) : {id:'',revision:0,content:{title:'',questions:[blankQuestion()]}};
    saved.content.scoring ??= 'fixed';
    let model = saved.content, baseline = JSON.stringify(model), saving = false;
    const status = el('p', '', 'hint');
    function changed() { dirty = JSON.stringify(model) !== baseline; status.textContent = uploads ? 'Laster opp bilde …' : saving ? 'Lagrer …' : dirty ? 'Ulagrede endringer' : saved.id ? 'Lagret · versjon ' + saved.revision : 'Ikke lagret ennå'; }
    const save = button('Lagre quiz', async () => {
      if (uploads) throw new Error('Vent til bildet er lastet opp.');
      saving = true; changed(); const snapshot = JSON.stringify(model);
      try { const r = await api('save', {id:saved.id, revision:saved.revision, content:JSON.parse(snapshot)}); saved = {...saved,...r}; baseline = snapshot; history.replaceState(null,'','?edit='+r.id); }
      finally { saving = false; changed(); }
    });
    const start = button('Start spill', async () => {
      if (dirty || !saved.id || uploads || saving) throw new Error('Lagre quizen før du starter et spill.');
      const r = await api('create', {id:saved.id}); location.href = '?host=' + r.room;
    }, 'secondary');
    const scoringLabel = el('label', 'Poengstil'), scoringSelect = el('select');
    for (const [value, label] of [['fixed','Faste poeng'], ['speed','Raske riktige svar']]) { const option = el('option', label); option.value = value; scoringSelect.append(option); }
    scoringSelect.value = model.scoring; scoringSelect.onchange = () => { model.scoring = scoringSelect.value; changed(); }; scoringLabel.append(scoringSelect);
    const list = el('div');
    app.replaceChildren(el('p', 'QUIZVERKSTED', 'eyebrow'), el('h1', 'Et spørsmål om gangen'), group(save, start, link('Mine quizer','?teacher=1')), status,
      field('Quizens tittel', model.title, v => {model.title=v; changed();}), scoringLabel, el('p', 'Faste poeng: 1000 for riktig svar. Raske riktige svar: 1000 ved start, 500 halvveis, ned mot 0 ved fristen. YouTube-spørsmål gir full poengsum de første fire sekundene. Feil svar gir alltid 0.', 'hint'), el('p', 'Bruk $...$ eller $$...$$ for matematikk. Kode vises som tekst og kjøres ikke.', 'hint'), list);
    function renderQuestions() {
      list.replaceChildren();
      model.questions.forEach((q,index) => {
        const card = el('section', undefined, 'card question-editor');
        card.append(el('h2', 'Spørsmål ' + (index+1)));
        const typeLabel = el('label','Svartype'), select = el('select');
        for (const [value,label] of [['single','Ett riktig alternativ'],['multi','Flere riktige alternativer'],['text','Skriv svaret']]) { const o = el('option',label); o.value=value; select.append(o); }
        select.value=q.type; select.onchange=()=>{q.type=select.value; if(q.type==='single') q.correct=[q.correct[0] ?? 0]; changed(); renderQuestions();}; typeLabel.append(select);
        const codeField = field('Kode (valgfritt)',q.code,v=>{q.code=v;changed();},'textarea');
        card.append(typeLabel, field('Spørsmål',q.prompt,v=>{q.prompt=v;changed();},'textarea'), codeField, field('YouTube-lenke eller video-ID (valgfritt)',q.youtube,v=>{q.youtube=v;changed();}), field('Svartid i sekunder (5–600)',q.seconds,v=>{q.seconds=Number(v);changed();},'number'));
        const imageLabel=el('label','Bilde (PNG, JPEG eller WebP, maks 2 MiB)'), upload=el('input'); upload.type='file'; upload.accept='image/png,image/jpeg,image/webp';
        upload.onchange=async()=>{const file=upload.files[0];if(!file)return;uploads++;changed();upload.disabled=true;try{if(file.size>2097152)throw new Error('Bildet er større enn 2 MiB.');const data=new FormData();data.set('image',file);const r=await api('upload',data);q.image={...r.image,alt:''};renderQuestions();}catch(e){error(e);}finally{uploads--;upload.disabled=false;changed();}};
        imageLabel.append(upload);card.append(imageLabel);
        if(q.image)card.append(button('Fjern bilde',()=>{q.image=null;changed();renderQuestions();},'quiet'));
        if(q.type==='text') card.append(field('Godkjente svar – ett per linje',q.accepted.join('\n'),v=>{q.accepted=v.split('\n').filter(x=>x.trim());changed();},'textarea'),el('p','Store/små bokstaver og ekstra mellomrom ignoreres. Ingen algebraisk eller numerisk tilnærming.','hint'));
        else {
          card.append(el('p','Marker riktig(e) alternativ(er). Flere riktige krever hele det riktige settet.','hint'));
          q.options.forEach((value,i)=>{
            const row=el('div',undefined,'option-editor'),label=el('label','Riktig '+(i+1)),check=el('input');check.type=q.type==='single'?'radio':'checkbox';check.name='correct-'+index;check.checked=q.correct.includes(i);
            check.onchange=()=>{q.correct=q.type==='single'?[i]:check.checked?[...q.correct,i]:q.correct.filter(x=>x!==i);changed();};label.prepend(check);
            row.append(label,field('Alternativ '+(i+1),value,v=>{q.options[i]=v;changed();}));card.append(row);
          });
          card.append(group(button('＋ Alternativ',()=>{if(q.options.length<6){q.options.push('');changed();renderQuestions();}},'quiet'),button('Fjern siste alternativ',()=>{if(q.options.length>2){q.options.pop();q.correct=q.correct.filter(i=>i<q.options.length);changed();renderQuestions();}},'quiet')));
        }
        const preview=el('div',undefined,'preview');
        card.append(group(button('Forhåndsvis',()=>{preview.replaceChildren();let normalized=q.youtube; if(normalized){try{const u=new URL(normalized);normalized=u.hostname==='youtu.be'?u.pathname.slice(1):u.searchParams.get('v')||u.pathname.split('/').pop();}catch(_){}if(!/^[\w-]{11}$/.test(normalized))throw new Error('Kontroller YouTube-lenken.');}void content({...q,youtube:normalized},preview);q.options.forEach((o,i)=>preview.append(rich((i+1)+'. '+o)));},'secondary'),button('Fjern spørsmål',()=>{if(model.questions.length===1)throw new Error('Quizen trenger minst ett spørsmål.');model.questions.splice(index,1);changed();renderQuestions();},'quiet')),preview);
        list.append(card);
        makeCodeEditor(codeField.querySelector('textarea'));
      });
    }
    app.append(button('＋ Legg til spørsmål',()=>{if(model.questions.length>=50)throw new Error('Maks 50 spørsmål.');model.questions.push(blankQuestion());changed();renderQuestions();}));renderQuestions();changed();
  }
  async function room(host) {
    const id=params.get(host?'host':'room'), token=host?'':sessionStorage.getItem('lq-room-'+id)||'';
    if(!host&&!token){app.replaceChildren(el('h1','Bli med på nytt'),el('p','Denne fanen har ingen deltakerøkt. Åpne den opprinnelige fanen eller bli med med spillkoden.'),link('Til spillkoden','./'));return;}
    const query={room:id,...(host?{host:'1'}:{})};
    const heading=el('h1','Henter spill …'),connection=el('p','Kobler til …','hint'),meta=el('p',undefined,'hint'),timer=el('p',undefined,'timer'),stage=el('section',undefined,'card stage'),controls=el('div',undefined,'actions'),results=el('section');
    app.replaceChildren(el('p',host?'LÆRERSKJERM':'DU ER MED','eyebrow'),heading,connection,meta,timer,stage,controls,results);timer.hidden=true;
    let state=null, rendered='', failures=0, online=false, offset=0, lastPoll=0, submit=null, ack=null, selection=null, submitting=false, hostClock=null, countdown=null;
    let polling=false, pollAgain=false, pollTimer=null, controlling=false, modeDirty=false;
    const music=host?window.quizMusic():null;
    const control=(command, extra={})=>async()=>{
      if(command==='next'&&modeDirty)throw new Error('Lagre spillmodus før du starter.');
      if(controlling)return;controlling=true;
      if(command==='next')music?.unlock();
      try{await api('control',{room:id,version:state.version,command,...extra});if(command==='configure')modeDirty=false;}
      finally{controlling=false;requestPoll();}
    };
    function modeSettings(s) {
      modeDirty=false;
      const form=el('form',undefined,'mode-settings'), modes=el('fieldset'), legend=el('legend','Spillmodus');modes.append(legend);
      let selected=s.mode||'individual';
      const maximum=field('Maks antall spillere per lag',s.max_team_size||3,()=>{modeDirty=true;},'number'), input=maximum.querySelector('input');
      input.min=2;input.max=60;input.step=1;input.required=true;
      maximum.hidden=selected!=='teams';input.disabled=selected!=='teams';
      for(const [value,title] of [['individual','Individuelt spill'],['teams','Tilfeldige lag']]){
        const label=el('label',title), radio=el('input');radio.type='radio';radio.name='game-mode';radio.value=value;radio.checked=selected===value;
        radio.onchange=()=>{selected=value;maximum.hidden=value!=='teams';input.disabled=value!=='teams';modeDirty=true;};label.prepend(radio);modes.append(label);
      }
      const saveMode=el('button','Lagre spillmodus');saveMode.type='submit';
      form.append(modes,maximum,el('p','Lagene fordeles tilfeldig når du starter. Alle svarer individuelt, og lagets poeng er summen av medlemmenes poeng. Nye deltakere kan ikke bli med etter lagfordelingen.','hint'),saveMode);
      form.onsubmit=async event=>{event.preventDefault();saveMode.disabled=true;clearError();try{await control('configure',{mode:selected,max_team_size:selected==='teams'?Number(input.value):s.max_team_size||3})();}catch(e){error(e);}finally{saveMode.disabled=false;}};
      return form;
    }
    function showTeams(s) {
      popup((header,body)=>{
        header.append(el('h2','Lagene er klare','modal-title'));
        body.append(el('p',host?'Finn laget ditt. Start første spørsmål når alle er klare.':`Du er på Lag ${s.my_team}. Vent på læreren.`,'intro'));
        const cards=el('div',undefined,'team-grid');
        for(const team of s.teams){
          if(!host&&team.id!==s.my_team)continue;
          const card=el('section',undefined,'team-card');card.append(el('h3',team.name),el('p',`${team.members.length} deltakere`,'hint'));
          const members=el('ul');for(const member of team.members)members.append(el('li',member.nickname));card.append(members);cards.append(card);
        }
        body.append(cards);
      },'teams-modal');
    }
    function updateClock(){
      if(!state)return;
      const now=Date.now()/1000+offset,left=Math.max(0,state.deadline-now),active=state.state==='QUESTION_ACTIVE';
      music?.update(active&&left>0&&online&&Date.now()-lastPoll<=5000&&!state.question?.youtube,state.index);
      const txt=active?(left>0?Math.ceil(left)+' sekunder':'Tiden er ute'):'';
      if(hostClock)hostClock.textContent=txt;
      if(countdown){const remaining=Math.max(0,Math.ceil(state.countdown_end-now));const text=remaining?String(Math.min(3,remaining)):'Venter …';if(countdown.textContent!==text)countdown.textContent=text;}
      if(submit)submit.disabled=submitting||!active||!online||Date.now()-lastPoll>5000||left<=0||state.submitted;
    }
    setInterval(updateClock,250);
    let overlay=null;
    const closePopup=()=>{if(overlay){timer.before(connection,meta);results.before(controls);overlay.close();overlay.remove();overlay=null;}};
    function popup(build,cls=''){
      closePopup();overlay=el('dialog',undefined,'question-modal '+cls);
      const header=el('div',undefined,'modal-header'),body=el('div',undefined,'modal-body');
      overlay.append(header,body);build(header,body);
      const title=overlay.querySelector('h2,.qcard-head,[role=status]'),footer=el('div',undefined,'question-modal-footer'),message=el('p',undefined,'modal-notice');
      title.id='quiz-modal-title';title.tabIndex=-1;overlay.setAttribute('aria-labelledby',title.id);message.hidden=true;message.setAttribute('role','alert');
      overlay.addEventListener('cancel',event=>event.preventDefault());
      footer.append(window.quizThemeButton(),meta,connection,message,controls);overlay.append(footer);document.body.append(overlay);overlay.showModal();title.focus();
    }
    function showAnswer(s,order){
      popup((header,body)=>{
        header.append(el('h2','Fasit','modal-title'));questionCard(s,order,header,body);
        const analysis=el('section',undefined,'results-analysis');
        if(host)analysis.append(answerChart(s,order));
        else {
          if(s.question.type==='text')analysis.append(el('p','Riktig svar: '+s.question.accepted.join(' · ')));
          analysis.append(el('p',s.submitted?`Du fikk ${s.points} poeng.`:'Du fikk 0 poeng. Du svarte ikke på dette spørsmålet.','result'));
        }
        body.append(analysis);
      },'results-modal');
    }
    function showBoard(s){popup((header,body)=>{const entries=el('div',undefined,'leaderboard-entries');entries.append(leaderboardList(s.leaderboard||[]));header.append(el('h2',s.mode==='teams'?'Lagresultater':'Leaderboard','modal-title'));body.append(entries);},'leaderboard-modal');}
    function showCountdown(){
      popup((header,body)=>{countdown=el('div','','countdown');countdown.setAttribute('role','status');countdown.setAttribute('aria-live','assertive');body.append(countdown);},'countdown-modal');
    }
    function questionCard(s,order,header,body){
      const q=s.question,head=el('div',undefined,'qcard-head'),media=el('div',undefined,'question-media');
      if(host&&(q.image||q.youtube))body.classList.add('media-question-body');
      hostClock=el('span',undefined,'qcard-timer');head.append(el('span',`Spørsmål ${s.index+1} av ${s.total}`),hostClock);
      header.append(head);body.append(media);void content(q,media,{query,token,showVideo:host,showImages:host,autoplay:s.state==='QUESTION_ACTIVE'},header);
      if(!host&&s.state==='QUESTION_ACTIVE')body.append(answerForm(s,order));
      else if(q.type==='text'){if(s.state==='QUESTION_ACTIVE')body.append(el('p','Elevene skriver svaret sitt.','qcard-note'));}
      else body.append(optionCards(q,order,s.state==='QUESTION_RESULTS'));
    }
    function answerForm(s,order){
      const form=el('form',undefined,'question-answer-form');selection=s.answer??(s.question.type==='text'?'':[]);
      if(s.question.type==='text')form.append(field('Ditt svar',selection,value=>selection=value));
      else{
        const grid=el('div',undefined,'option-grid');
        order.forEach((original,position)=>{
          const label=el('label',undefined,'answer-option option-card'),input=el('input');input.type=s.question.type==='single'?'radio':'checkbox';input.name='answer';input.checked=selection.includes(original);
          input.onchange=()=>{selection=s.question.type==='single'?[original]:input.checked?[...selection,original]:selection.filter(value=>value!==original);};
          label.append(input,el('span',String(position+1),'option-badge'),rich(s.question.options[original]));grid.append(label);
        });
        form.append(grid);
      }
      submit=el('button','Send svar');submit.type='submit';ack=el('p',s.submitted?'Svaret er mottatt. Vent på læreren.':'','hint');ack.setAttribute('role','status');form.append(submit,ack);
      const acknowledgement=ack,submitButton=submit;
      form.onsubmit=async event=>{
        event.preventDefault();if(submitButton.disabled)return;submitButton.disabled=true;submitting=true;clearError();form.querySelectorAll('input').forEach(input=>input.disabled=true);
        try{await api('answer',{room:id,index:s.index,answer:selection},{},token);if(state.index===s.index)state.submitted=true;acknowledgement.textContent='Svaret er mottatt. Vent på læreren.';}
        catch(err){error(err);if(state.index===s.index&&!state.submitted)form.querySelectorAll('input').forEach(input=>input.disabled=false);}
        finally{submitting=false;updateClock();requestPoll();}
      };
      if(s.submitted)form.querySelectorAll('input').forEach(input=>input.disabled=true);
      return form;
    }
    function render(s){
      if(state&&s.version<state.version)return;
      if(state&&s.version===state.version&&state.submitted)s.submitted=true;
      state=s;heading.textContent=s.title;meta.textContent=(s.my_team?`Lag ${s.my_team} · `:'')+`${s.players} deltakere · ${s.answers} svar`+(s.index>=0&&!host?` · Spørsmål ${Math.min(s.index+1,s.total)} av ${s.total}`:'');
      if(!host&&s.state==='QUESTION_RESULTS')meta.textContent=(s.my_team?`Lag ${s.my_team} · `:'')+`Spørsmål ${s.index+1} av ${s.total}`;
      if(ack&&s.submitted){ack.textContent='Svaret er mottatt. Vent på læreren.';overlay?.querySelectorAll('form input').forEach(input=>input.disabled=true);}
      if(rendered===String(s.version)){if(s.state==='LEADERBOARD')overlay.querySelector('.leaderboard-entries').replaceChildren(leaderboardList(s.leaderboard||[]));updateClock();return;}rendered=String(s.version);closePopup();stage.replaceChildren();stage.classList.remove('stage-flush');controls.replaceChildren();results.replaceChildren();submit=null;ack=null;hostClock=null;countdown=null;
      app.dataset.state=s.state;
      if(host&&s.state!=='QUIZ_FINISHED')controls.append(button('Avslutt spillet',control('finish'),'quiet'));
      if(s.state==='LOBBY'){
        stage.append(el('p', s.scoring === 'speed' ? 'Raske riktige svar: 0–1000 poeng. Jo raskere du svarer riktig, desto flere poeng. YouTube-spørsmål gir full poengsum de første fire sekundene. Feil svar gir 0.' : 'Faste poeng: 1000 for riktig svar, 0 for feil svar.', 'hint'));
        stage.append(el('h2',host?'Samle klassen':'Du er med!'),el('p',host?'Elevene skanner koden eller åpner lenken og skriver spillkoden.':'Vent på at læreren starter første spørsmål.'));
        if(host){stage.append(modeSettings(s));const url=new URL('./',location.href);url.searchParams.set('pin',s.pin);stage.append(el('div',s.pin,'pin'));const qr=qrcode(0,'M');qr.addData(url.href);qr.make();const img=el('img',undefined,'qr');img.src=qr.createDataURL(6,24);img.alt='QR-kode for å bli med i spillet';const a=link(url.href,url.href);a.target='_blank';a.rel='noopener';stage.append(img,a);controls.append(button(s.mode==='teams'?'Fordel lag og start':'Start første spørsmål',control('next')));}
      } else if(s.state==='QUIZ_FINISHED'){stage.append(el('h2','Takk for spillet!'),el('p','Se resultatene og snakk sammen om spørsmålene.'));}
      else if(s.state==='LEADERBOARD'){
        if(host)controls.prepend(button(s.index+1>=s.total?'Vis sluttresultat':'Neste spørsmål',control('next')));
        showBoard(s);
      }
      else if(s.state==='TEAM_OVERVIEW'){
        if(host)controls.prepend(button('Start første spørsmål',control('next')));
        showTeams(s);
      }
      else if(s.state==='COUNTDOWN')showCountdown();
      else {
        const order=s.question.options.length?optionOrder(s.question.options.length,id+':'+s.index):[];
        stage.classList.add('stage-flush');
        if(s.state==='QUESTION_ACTIVE'){
          if(host)controls.prepend(button('Vis fasit nå',control('reveal'),'secondary'));
          popup((header,body)=>questionCard(s,order,header,body),'active-question-modal');
        }else if(s.state==='QUESTION_RESULTS'){
          if(host)controls.prepend(button('Vis leaderboard',control('leaderboard')));
          showAnswer(s,order);
        }
      }
      if(music)controls.append(music.controls);
      updateClock();
    }
    function renderResults(s){
      results.replaceChildren();
      if(host&&s.roster){results.append(el('h2','I lobbyen'),el('p',s.roster.join(' · ')||'Venter på første deltaker …'));}
      if(s.state==='QUIZ_FINISHED')results.append(el('h2','Resultater'),leaderboardList(s.leaderboard||[]));
    }
    function requestPoll(){clearTimeout(pollTimer);if(polling)pollAgain=true;else void poll();}
    async function poll(){
      if(polling)return;polling=true;
      try{const started=Date.now(),s=await api('state',undefined,query,token);online=true;failures=0;lastPoll=Date.now();offset=s.now-(started+lastPoll)/2000;connection.textContent='Tilkoblet';render(s);renderResults(s);}
      catch(e){online=false;failures++;connection.textContent='Mistet kontakt: '+e.message+' Kobler til igjen …';updateClock();}
      finally{polling=false;const interval=state?.state==='COUNTDOWN'?200:state?.state==='QUIZ_FINISHED'?10000:1000;pollTimer=setTimeout(poll,pollAgain?0:Math.min(10000,interval*2**Math.min(failures,3)));pollAgain=false;}
    }
    await poll();
  }
  window.addEventListener('beforeunload',e=>{if(dirty||uploads){e.preventDefault();e.returnValue='';}});
  (async()=>{const init=await api('bootstrap');csrf=init.csrf;uid=init.uid;pending=init.pending;document.querySelector('#account-link').textContent=uid?'Min konto':'Logg inn';if(params.has('share'))await sharedQuiz();else if(params.has('login'))login();else if(params.has('host'))await room(true);else if(params.has('room'))await room(false);else if(params.has('edit')||params.has('new'))await editor();else if(params.has('teacher'))await library();else home();})().catch(error);
})();
