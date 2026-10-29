/* Livequiz proof of concept: same-origin PHP API, non-overlapping polling. */
(() => {
  'use strict';
  const app = document.querySelector('#app'), notice = document.querySelector('#notice');
  const params = new URLSearchParams(location.search);
  let canSetPassword=false, accountSetup=params.has('setup');
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
  function copyDestination(){
    try{const source=JSON.parse(sessionStorage.getItem('lq-copy-source'));if(!source||! /^[a-f0-9]{32}$/.test(source.id))return null;
      if(source.source==='public')return '?public='+source.id;
      if(source.source==='shared'&&/^[a-f0-9]{64}$/.test(source.key))return '?share='+source.id+'#key='+source.key;
    }catch(_){}return null;
  }
  function login(mode='code') {
    if(pending&&accountSetup)mode='verify-email';
    app.replaceChildren(el('p','DIN QUIZKONTO','eyebrow'),el('h1',uid&&mode!=='verify-email'?'Min konto':accountSetup?'Opprett konto eller sett nytt passord':'Logg inn'));
    const startSetup=()=>{accountSetup=true;pending=false;history.replaceState(null,'','?login=1&setup=1');login('verify-email');};
    if(uid&&mode!=='verify-email'){
      if(params.has('saved'))app.append(el('p','Passordet er lagret. Andre innlogginger er avsluttet.','result'));
      app.append(group(link('Mine quizer','?teacher=1'),button('Logg ut',async()=>{await api('logout',{});location.href='./';},'quiet')));
      if(!canSetPassword){app.append(el('p','Du kan bruke engangskode eller passord for den samme kontoen. Bekreft e-posten med en ny kode for å opprette eller endre passord.','intro'),button('Opprett eller endre passord',startSetup));return;}
      app.append(el('p','Velg et passord på minst 15 tegn. Du kan fortsatt logge inn med engangskode.','intro'));
      const form=el('form',undefined,'card join');let password='',confirmation='';
      for(const [label,update] of [['Nytt passord',v=>password=v],['Gjenta passord',v=>confirmation=v]]){const f=field(label,'',update,'password'),i=f.querySelector('input');i.required=true;i.minLength=15;i.autocomplete='new-password';form.append(f);}
      const save=el('button','Lagre passord');save.type='submit';form.append(save);
      form.onsubmit=async e=>{e.preventDefault();clearError();if(password!==confirmation){error(new Error('Passordene er ikke like.'));return;}save.disabled=true;try{await api('set-password',{password});location.href=copyDestination()||'?login=1&saved=1';}catch(err){error(err);save.disabled=false;}};
      app.append(form);return;
    }
    app.append(el('p','Bruk din @osloskolen.no-adresse. Engangskode og passord gir tilgang til de samme quizene.','intro'));
    if(!pending&&!accountSetup)app.append(group(button('Engangskode på e-post',()=>login('code'),'secondary'),button('Logg inn med passord',()=>login('password'),'secondary')));
    if(accountSetup)app.append(el('p','Bekreft e-posten med en engangskode. Deretter velger du passord. Dette gjelder også hvis du har glemt passordet.','hint'));
    const form=el('form',undefined,'card join');let value='',password='';
    const label=field(pending?'Engangskode':'E-post i Osloskolen','',v=>value=v,pending?'text':'email'),input=label.querySelector('input');input.required=true;
    if(pending){input.inputMode='numeric';input.pattern='[0-9]{8}';input.maxLength=8;input.autocomplete='one-time-code';}
    else{input.maxLength=254;input.autocomplete=mode==='password'?'username':'email';}
    form.append(label);
    if(mode==='password'&&!pending){const f=field('Passord','',v=>password=v,'password');f.querySelector('input').required=true;f.querySelector('input').autocomplete='current-password';form.append(f);}
    const submit=el('button',pending||mode==='password'?'Logg inn':'Send kode');submit.type='submit';form.append(submit);
    form.onsubmit=async e=>{e.preventDefault();submit.disabled=true;clearError();try{
      if(pending){await api('verify',{code:value});location.href=accountSetup?'?login=1':copyDestination()||'?teacher=1';}
      else if(mode==='password'){await api('password-login',{email:value,password});location.href=copyDestination()||'?teacher=1';}
      else{await api('send',{email:value});pending=true;login(uid?'verify-email':'code');}
    }catch(err){error(err);submit.disabled=false;}};
    app.append(form);
    if(pending)app.append(el('p','Koden gjelder i ti minutter. Sjekk også søppelpost.','hint'),button('Be om en ny kode',()=>{pending=false;login(uid?'verify-email':'code');},'quiet'));
    app.append(group(button('Opprett konto med passord',startSetup,'quiet'),button('Glemt passord?',startSetup,'quiet'),link('Tilbake til innlogging','?login=1')));
  }
  function organizationDialog(title,fields,save) {
    const dialog=el('dialog',undefined,'organization-dialog'),form=el('form'),message=el('p','','modal-notice');message.setAttribute('role','alert');
    const submit=el('button','Lagre');submit.type='submit';
    const close=()=>{dialog.close();dialog.remove();};
    form.append(el('h2',title),...fields,message,group(submit,button('Avbryt',close,'quiet')));dialog.append(form);document.body.append(dialog);
    dialog.addEventListener('cancel',event=>{event.preventDefault();close();});
    form.onsubmit=async event=>{event.preventDefault();submit.disabled=true;message.textContent='';try{await save();close();await library();}catch(e){message.textContent=e.message;}finally{submit.disabled=false;}};
    dialog.showModal();form.querySelector('input,select')?.focus();
  }
  async function library() {
    app.replaceChildren(el('p', 'DITT KLASSEROM', 'eyebrow'), el('h1', 'Mine quizer'));
    if (!uid) { app.append(el('p', 'Logg inn med Osloskolen-kontoen din for å lage og lagre quizer.'), link('Logg inn', '?login=1')); return; }
    const data=await api('library'),folders=new Map(data.folders.map(folder=>[folder.id,folder]));
    const current=folders.get(params.get('folder'))||null,currentId=current?.id||null;
    const libraryUrl=id=>'?teacher=1'+(id?'&folder='+id:'');
    const folderPath=id=>{const names=[];for(let f=folders.get(id);f;f=folders.get(f.parent))names.unshift(f.name);return names.join(' / ');};
    const sorted=[...folders.values()].sort((a,b)=>folderPath(a.id).localeCompare(folderPath(b.id),'nb'));
    function destination(value,excluded=null){
      const label=el('label','Mappe'),select=el('select');select.setAttribute('aria-label','Mappe');
      select.append(Object.assign(el('option','Mine quizer (øverste nivå)'),{value:''}));
      for(const folder of sorted){
        let forbidden=false;for(let f=folder;f;f=folders.get(f.parent))if(f.id===excluded)forbidden=true;
        if(!forbidden)select.append(Object.assign(el('option',folderPath(folder.id)),{value:folder.id}));
      }
      select.value=value||'';label.append(select);return {label,value:()=>select.value||null};
    }
    function nameDialog(title,command,folder=null){
      let name=folder?.name||'';const input=field('Mappenavn',name,value=>name=value);input.querySelector('input').required=true;input.querySelector('input').maxLength=120;
      organizationDialog(title,[input],()=>api('organize',{command,id:folder?.id,name,parent:currentId}));
    }
    const breadcrumbs=el('div',undefined,'folder-breadcrumbs');breadcrumbs.setAttribute('aria-label','Mappesti');breadcrumbs.append(link('Mine quizer',libraryUrl(null)));
    const ancestors=[];for(let f=current;f;f=folders.get(f.parent))ancestors.unshift(f);
    for(const folder of ancestors)breadcrumbs.append(el('span','/'),link(folder.name,libraryUrl(folder.id)));
    app.append(breadcrumbs,group(link('＋ Lag en quiz','?new=1'+(currentId?'&folder='+currentId:'')),button('Ny mappe',()=>nameDialog('Ny mappe','create-folder'),'secondary')));
    if(current){
      app.append(el('h2',current.name),group(button('Gi mappen nytt navn',()=>nameDialog('Gi mappen nytt navn','rename-folder',current),'quiet'),
        button('Flytt mappe',()=>{const target=destination(current.parent,current.id);organizationDialog('Flytt «'+current.name+'»',[target.label],()=>api('organize',{command:'move-folder',id:current.id,parent:target.value()}));},'quiet'),
        button('Slett mappe',async()=>{if(!confirm('Slette mappen «'+current.name+'»? Quizer og undermapper flyttes ett nivå opp. Ingen quizer slettes.'))return;await api('organize',{command:'delete-folder',id:current.id});location.href=libraryUrl(current.parent);},'quiet')));
    }
    const children=sorted.filter(folder=>folder.parent===currentId),quizzes=data.quizzes.filter(quiz=>quiz.folder===currentId);
    if(children.length){const list=el('div',undefined,'folder-list');for(const folder of children)list.append(link('📁 '+folder.name,libraryUrl(folder.id)));app.append(list);}
    if(!children.length&&!quizzes.length)app.append(el('p',current?'Denne mappen er tom. Lag en quiz eller flytt en quiz hit.':'Lag en quiz eller en mappe for å komme i gang.','hint'));
    const grid=el('div',undefined,'library');
    for(const q of quizzes){
      const card=el('article',undefined,'card');card.append(el('h2',q.title),el('p',(q.private?'Privat':'Offentlig')+' · Versjon '+q.revision),group(link('Rediger','?edit='+q.id+(currentId?'&folder='+currentId:'')),
        button('Start spill',async()=>{const r=await api('create',{id:q.id});location.href='?host='+r.room;}),button('Forhåndsvis',async()=>{const quiz=await api('quiz',undefined,{id:q.id});previewQuiz(quiz.content);},'secondary'),button('Del quiz',()=>shareQuiz(q,card),'secondary'),
        button('Flytt',()=>{const target=destination(q.folder);organizationDialog('Flytt «'+q.title+'»',[target.label],()=>api('organize',{command:'move-quiz',id:q.id,parent:target.value()}));},'quiet'),
        button('Slett',async()=>{if(!confirm('Slette «'+q.title+'»? Dette kan ikke angres.'))return;await api('delete',{id:q.id});await library();},'quiet')));grid.append(card);
    }
    app.append(grid);
    if(data.rooms.length){app.append(el('h2','Siste spill · tilgjengelig i seks timer'));for(const r of data.rooms)app.append(link('Spill '+r.pin+(r.phase==='finished'?' · avsluttet':' · åpne'),'?host='+r.id));}
  }
  async function shareQuiz(q,card) {
    const data=await api('share',{id:q.id,enabled:true});
    card.querySelector('.share-panel')?.remove();
    const panel=el('section',undefined,'share-panel');
    const url=new URL('./',location.href);url.searchParams.set('share',q.id);url.hash=new URLSearchParams({key:data.key});
    const label=field('Delingslenke',url.href,()=>{}),input=label.querySelector('input');input.readOnly=true;input.onclick=()=>input.select();
    const status=el('p','','hint');status.setAttribute('role','status');
    panel.append(el('p','Alle med lenken kan starte et eget spill uten konto. De kan lage en redigerbar kopi når de logger inn. Originalen din blir ikke endret. Lenken bruker siste lagrede versjon.','hint'),label,
      group(button('Kopier lenke',async()=>{try{await navigator.clipboard.writeText(url.href);status.textContent='Lenken er kopiert.';}catch(_){input.focus();input.select();status.textContent='Kopier den markerte lenken.';}}),
        button('Slå av deling',async()=>{await api('share',{id:q.id,enabled:false});panel.replaceChildren(el('p','Deling er slått av. Gamle lenker kan ikke starte nye spill. Spill som allerede er startet, fortsetter.','hint'));},'quiet')),status);
    card.append(panel);input.focus();input.select();
  }
  async function discover() {
    const search=params.get('q')||'',page=Math.max(0,Number(params.get('page'))||0);
    app.replaceChildren(el('p','OFFENTLIGE QUIZER','eyebrow'),el('h1','Finn en quiz'),el('p','Søk og start et spill for klassen din. Du trenger ingen konto.','intro'));
    const form=el('form'),label=field('Søk etter tittel',search,()=>{}),input=label.querySelector('input'),submit=el('button','Søk');input.maxLength=180;submit.type='submit';form.append(label,submit);
    form.onsubmit=e=>{e.preventDefault();location.href='?search=1&q='+encodeURIComponent(input.value);};app.append(form);
    const data=await api('discover',undefined,{q:search,page});
    const grid=el('div',undefined,'library');
    for(const quiz of data.quizzes){const card=el('article',undefined,'card');card.append(el('h2',quiz.title),el('p',quiz.total+' spørsmål'),link('Åpne quiz','?public='+quiz.id));grid.append(card);}
    app.append(grid);if(!data.quizzes.length)app.append(el('p','Ingen offentlige quizer funnet.','hint'));
    const pages=group();if(page)pages.append(link('Forrige','?search=1&q='+encodeURIComponent(search)+'&page='+(page-1)));if(data.more)pages.append(link('Neste','?search=1&q='+encodeURIComponent(search)+'&page='+(page+1)));app.append(pages);
  }
  async function sharedQuiz(publicQuiz=false) {
    const id=params.get(publicQuiz?'public':'share'),key=new URLSearchParams(location.hash.slice(1)).get('key')||'';
    if(uid)sessionStorage.removeItem('lq-copy-source');
    const quiz=await api(publicQuiz?'public-quiz':'shared',undefined,{id});
    app.replaceChildren(el('p',publicQuiz?'OFFENTLIG QUIZ':'DELT QUIZ','eyebrow'),el('h1',quiz.title),el('p',`${quiz.total} spørsmål · Du trenger ingen konto.`,'intro'),
      el('p','Start et eget spill for klassen din. Du styrer spørsmålene og får en egen spillkode til elevene. Hold denne fanen åpen; den gir deg tilgang til å styre spillet.'),
      button('Start spill for min klasse',async()=>{
        const hostToken=Array.from(crypto.getRandomValues(new Uint8Array(32)),b=>b.toString(16).padStart(2,'0')).join('');
        // Verify storage works before creating a room whose controls depend on it.
        sessionStorage.setItem('lq-storage-check','1');sessionStorage.removeItem('lq-storage-check');
        const room=await api(publicQuiz?'public-start':'shared-start',{id,key,host_token:hostToken});
        sessionStorage.setItem('lq-host-'+room.room,hostToken);location.href='?host='+room.room;
      }));
    if(publicQuiz)app.append(button('Forhåndsvis',async()=>previewQuiz(await api('public-preview',undefined,{id}),{public_quiz:id}),'secondary'));
    app.append(el('p','Lag din egen kopi for å endre spørsmål og svar. Originalen blir ikke endret. Du må være logget inn for å lagre kopien.','hint'),
      button(uid?'Lag en redigerbar kopi':'Logg inn for å lage en kopi',async()=>{
        const source={id,source:publicQuiz?'public':'shared',key};
        if(!uid){sessionStorage.setItem('lq-copy-source',JSON.stringify(source));location.href='?login=1';return;}
        const copy=await api('copy',source);location.href='?edit='+copy.id;
      },'secondary'));
  }
  function previewQuiz(contentModel,mediaQuery={}){
    const quiz=JSON.parse(JSON.stringify(contentModel));
    if(!quiz.questions.length)return;
    const opener=document.activeElement,dialog=el('dialog',undefined,'question-modal teacher-modal active-question-modal quiz-preview-modal');
    const header=el('div',undefined,'modal-header'),body=el('div',undefined,'modal-body'),footer=el('div',undefined,'question-modal-footer');
    const previous=el('button','Forrige','secondary'),next=el('button','Neste','secondary'),jumpLabel=el('label','Gå til spørsmål'),jump=el('select');
    const revealLabel=el('label'),reveal=el('input');reveal.type='checkbox';revealLabel.append(reveal,document.createTextNode(' Vis fasit'));
    let index=0;
    for(let i=0;i<quiz.questions.length;i++){const option=el('option','Spørsmål '+(i+1));option.value=String(i);jump.append(option);}jumpLabel.append(jump);
    const answers=el('div',undefined,'preview-answers');
    function renderAnswers(){const q=quiz.questions[index];answers.replaceChildren(q.type==='text'?el('p',reveal.checked?'Godkjente svar: '+q.accepted.join(' · '):'Deltakerne skriver inn svaret.','qcard-note'):optionCards(q,q.options.map((_,i)=>i),reveal.checked));}
    function render(){
      const q={...quiz.questions[index]},media=el('div',undefined,'question-media'),title=el('h2','Spørsmål '+(index+1)+' av '+quiz.questions.length,'modal-title');
      title.id='quiz-preview-title';header.replaceChildren(title);dialog.setAttribute('aria-labelledby',title.id);
      body.classList.toggle('media-question-body',!!(q.image||q.youtube));body.replaceChildren(media,answers);renderAnswers();
      previous.disabled=index===0;next.disabled=index===quiz.questions.length-1;jump.value=String(index);
      // Editing may contain a pasted URL that has not been normalized by saving yet.
      if(q.youtube){try{const u=new URL(q.youtube);q.youtube=u.hostname==='youtu.be'?u.pathname.slice(1):u.searchParams.get('v')||u.pathname.split('/').pop();}catch(_){} }
      void content(q,media,{showVideo:false,query:mediaQuery},header).then(()=>{
        if(!media.isConnected||!q.youtube)return;
        if(/^[\w-]{11}$/.test(q.youtube))void window.quizYouTube(media,q.youtube,false);
        else media.append(el('p','Kontroller YouTube-lenken i redigeringen.','hint'));
      });
      body.scrollTop=0;header.scrollTop=0;
    }
    previous.onclick=()=>{if(index>0){index--;render();}};next.onclick=()=>{if(index<quiz.questions.length-1){index++;render();}};
    jump.onchange=()=>{index=Number(jump.value);render();};reveal.onchange=renderAnswers;
    const fit=()=>dialog.style.setProperty('--teacher-scale',String(Math.max(1,Math.min((innerWidth-32)/900,(innerHeight-32)/700))));
    footer.append(el('p','Forhåndsvisning · '+(quiz.title||'Uten tittel'),'hint'),group(previous,jumpLabel,next,revealLabel,button('Lukk forhåndsvisning',()=>dialog.close(),'quiet')));
    dialog.append(header,body,footer);document.body.append(dialog);fit();dialog.showModal();render();
    window.addEventListener('resize',fit);
    dialog.addEventListener('close',()=>{window.removeEventListener('resize',fit);dialog.remove();opener?.focus();},{once:true});
  }
  const blankQuestion = () => ({type:'single', prompt:'', code:'', youtube:'', image:null, seconds:30, options:['','','',''], correct:[0], accepted:[]});
  async function editor() {
    if (!uid) return library();
    let saved = params.has('edit') ? await api('quiz', undefined, {id:params.get('edit')}) : {id:'',revision:0,content:{title:'',questions:[blankQuestion()]}};
    saved.content.scoring ??= 'fixed';saved.content.private ??= false;
    let model = saved.content, baseline = JSON.stringify(model), saving = false;
    const status = el('p', '', 'hint');
    function changed() { dirty = JSON.stringify(model) !== baseline; status.textContent = uploads ? 'Laster opp bilde …' : saving ? 'Lagrer …' : dirty ? 'Ulagrede endringer' : saved.id ? 'Lagret · versjon ' + saved.revision : 'Ikke lagret ennå'; }
    const save = button('Lagre quiz', async () => {
      if (uploads) throw new Error('Vent til bildet er lastet opp.');
      saving = true; changed(); const snapshot = JSON.stringify(model);
      try { const r = await api('save', {id:saved.id, revision:saved.revision, content:JSON.parse(snapshot),...(!saved.id&&params.get('folder')?{folder:params.get('folder')}:{})}); saved = {...saved,...r}; baseline = snapshot; history.replaceState(null,'','?edit='+r.id); }
      finally { saving = false; changed(); }
    });
    const start = button('Start spill', async () => {
      if (dirty || !saved.id || uploads || saving) throw new Error('Lagre quizen før du starter et spill.');
      const r = await api('create', {id:saved.id}); location.href = '?host=' + r.room;
    }, 'secondary');
    const privacyLabel=el('label'),privacy=el('input');privacy.type='checkbox';privacy.checked=model.private;privacy.onchange=()=>{model.private=privacy.checked;changed();};privacyLabel.append(privacy,document.createTextNode(' Privat – bare jeg kan starte nye spill'));
    const scoringLabel = el('label', 'Poengstil'), scoringSelect = el('select');
    for (const [value, label] of [['fixed','Faste poeng'], ['speed','Raske riktige svar']]) { const option = el('option', label); option.value = value; scoringSelect.append(option); }
    scoringSelect.value = model.scoring; scoringSelect.onchange = () => { model.scoring = scoringSelect.value; changed(); }; scoringLabel.append(scoringSelect);
    const list = el('div');
    app.replaceChildren(el('p', 'QUIZVERKSTED', 'eyebrow'), el('h1', 'Et spørsmål om gangen'), group(save, start, button('Forhåndsvis hele quizen',()=>{if(uploads)throw new Error('Vent til bildet er lastet opp.');previewQuiz(model);},'secondary'), link('Mine quizer','?teacher=1'+(params.get('folder')?'&folder='+params.get('folder'):''))), status,
      field('Quizens tittel', model.title, v => {model.title=v; changed();}), privacyLabel, el('p','Offentlige quizer kan finnes og spilles av alle uten konto. Privat skjuler quizen fra søk og slår av delingslenker når du lagrer. Allerede startet spill fortsetter.','hint'), scoringLabel, el('p', 'Faste poeng: 1000 for riktig svar. Raske riktige svar: 1000 ved start, 500 halvveis, ned mot 0 ved fristen. YouTube-spørsmål gir full poengsum de første fire sekundene. Feil svar gir alltid 0.', 'hint'), el('p', 'Bruk $...$ eller $$...$$ for matematikk. Kode vises som tekst og kjøres ikke.', 'hint'), list);
    const collapsedQuestions=new WeakSet();
    function renderQuestions() {
      list.replaceChildren();
      model.questions.forEach((q,index) => {
        const section=el('section',undefined,'card question-editor'),card=el('div',undefined,'question-editor-body');
        const summary=el('div',undefined,'question-editor-summary'),heading=el('div',undefined,'question-editor-heading');
        card.id='question-editor-body-'+index;
        const toggle=button('',()=>{
          if(collapsedQuestions.has(q))collapsedQuestions.delete(q);else collapsedQuestions.add(q);
          updateCollapsed();
          if(!card.hidden)card.querySelectorAll('.CodeMirror').forEach(node=>node.CodeMirror?.refresh());
        },'secondary');
        toggle.setAttribute('aria-controls',card.id);
        function updateCollapsed(){
          const collapsed=collapsedQuestions.has(q);card.hidden=collapsed;summary.hidden=!collapsed;
          toggle.textContent=collapsed?'Utvid':'Skjul detaljer';
          toggle.setAttribute('aria-label',(collapsed?'Utvid spørsmål ':'Skjul detaljer for spørsmål ')+(index+1));
          toggle.setAttribute('aria-expanded',String(!collapsed));
          if(collapsed)summary.replaceChildren(rich(q.prompt||'Uten spørsmålstekst'));
        }
        heading.append(el('h2','Spørsmål '+(index+1)),toggle);section.append(heading,summary,card);updateCollapsed();
        const positionLabel=el('label','Flytt til plass'),position=el('select');position.setAttribute('aria-label','Flytt til plass');
        for(let i=0;i<model.questions.length;i++){const option=el('option',String(i+1));option.value=String(i);position.append(option);}
        position.value=String(index);position.disabled=model.questions.length<2;positionLabel.append(position);
        const move=button('Flytt spørsmål',()=>{
          const destination=Number(position.value);
          if(destination===index)return;
          model.questions.splice(index,1);model.questions.splice(destination,0,q);
          changed();renderQuestions();
          const moved=list.children[destination];moved.querySelector('.question-order select').focus({preventScroll:true});moved.scrollIntoView({block:'start'});
        },'secondary');
        move.disabled=model.questions.length<2;
        const ordering=group(positionLabel,move);ordering.classList.add('question-order');card.append(ordering);

        const typeLabel = el('label','Svartype'), select = el('select');
        for (const [value,label] of [['single','Ett riktig alternativ'],['multi','Flere riktige alternativer'],['text','Skriv svaret']]) { const o = el('option',label); o.value=value; select.append(o); }
        select.value=q.type; select.onchange=()=>{q.type=select.value; if(q.type==='single') q.correct=[q.correct[0] ?? 0]; changed(); renderQuestions();}; typeLabel.append(select);
        const codeField = field('Kode (valgfritt)',q.code,v=>{q.code=v;changed();},'textarea');
        card.append(typeLabel, field('Spørsmål',q.prompt,v=>{q.prompt=v;changed();},'textarea'), codeField, field('YouTube-lenke eller video-ID (valgfritt)',q.youtube,v=>{q.youtube=v;changed();}), field('Svartid i sekunder (5–600)',q.seconds,v=>{q.seconds=Number(v);changed();},'number'));
        const imageLabel=el('label','Bilde (PNG, JPEG eller WebP, maks 2 MiB)'), upload=el('input'); upload.type='file'; upload.accept='image/png,image/jpeg,image/webp';
        upload.onchange=async()=>{const file=upload.files[0];if(!file)return;uploads++;changed();upload.disabled=true;try{if(file.size>2097152)throw new Error('Bildet er større enn 2 MiB.');const data=new FormData();data.set('image',file);const r=await api('upload',data);q.image={...r.image,alt:''};renderQuestions();}catch(e){error(e);}finally{uploads--;upload.disabled=false;changed();}};
        imageLabel.append(upload);card.append(imageLabel);
        if(q.image)card.append(button('Fjern bilde',()=>{q.image=null;changed();renderQuestions();},'quiet'));
        if(q.type==='text') card.append(field('Godkjente svar – ett per linje',q.accepted.join('\n'),v=>{q.accepted=v.split('\n').filter(x=>x.trim());changed();},'textarea'),el('p','Store/små bokstaver og alle mellomrom ignoreres. Desimaltall godtas med både komma og punktum (0,25 = 0.25). Ingen algebraisk eller numerisk tilnærming.','hint'));
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
        list.append(section);
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
    const joinCode=host?el('p','','host-join-code'):null;if(joinCode)timer.before(joinCode);
    let state=null, rendered='', failures=0, online=false, offset=0, lastPoll=0, submit=null, ack=null, selection=null, submitting=false, hostClock=null, countdown=null;
    let polling=false, pollAgain=false, pollTimer=null, controlling=false, modeDirty=false, readModeSettings=null;
    const music=host?window.quizMusic():null;
    const control=(command, extra={})=>async()=>{
      if(command==='next'&&state.state==='LOBBY'&&modeDirty)extra={...extra,settings:readModeSettings()};
      if(controlling)return;controlling=true;
      if(command==='next')music?.unlock();
      try{const reply=await api('control',{room:id,run:state.run,version:state.version,command,...extra});if(command==='configure'||command==='next')modeDirty=false;if(reply.state){render(reply.state);renderResults(reply.state);}}
      finally{controlling=false;requestPoll();}
    };
    function modeSettings(s) {
      modeDirty=false;
      const gameLabel=el('label','Spilltype'),gameSelect=el('select');gameSelect.setAttribute('aria-label','Spilltype');
      for(const [value,title] of [['regular','Vanlig quiz'],['race','Quiz Race']]){const option=el('option',title);option.value=value;gameSelect.append(option);}
      gameSelect.value=s.game||'regular';gameLabel.append(gameSelect);
      const form=el('form',undefined,'mode-settings'), modes=el('fieldset'), legend=el('legend','Spillmodus');modes.append(legend);
      let selected=s.mode||'individual';
      const maximum=field('Maks antall spillere per lag',s.max_team_size||3,()=>{modeDirty=true;},'number'), input=maximum.querySelector('input');
      input.min=2;input.max=60;input.step=1;input.required=true;
      maximum.hidden=selected!=='teams';input.disabled=selected!=='teams';
      for(const [value,title] of [['individual','Individuelt spill'],['teams','Tilfeldige lag']]){
        const label=el('label',title), radio=el('input');radio.type='radio';radio.name='game-mode';radio.value=value;radio.checked=selected===value;
        radio.onchange=()=>{selected=value;maximum.hidden=value!=='teams';input.disabled=value!=='teams';modeDirty=true;};label.prepend(radio);modes.append(label);
      }
      const lightningLabel=el('label','Aktiver lynrunde'),lightningToggle=el('input');lightningToggle.type='checkbox';lightningToggle.checked=s.lightning?.enabled||false;lightningLabel.prepend(lightningToggle);
      const lightningDuration=field('Varighet på lynrunde (sekunder)',s.lightning?.seconds||60,()=>{modeDirty=true;},'number'),durationInput=lightningDuration.querySelector('input');durationInput.min=5;durationInput.max=600;durationInput.step=1;durationInput.required=true;
      const showLightningDuration=()=>{const race=gameSelect.value==='race';lightningLabel.hidden=race;lightningToggle.disabled=race;lightningDuration.hidden=race||!lightningToggle.checked;durationInput.disabled=race||!lightningToggle.checked;};showLightningDuration();lightningToggle.onchange=()=>{modeDirty=true;showLightningDuration();};
      const saveMode=el('button','Lagre spillmodus');saveMode.type='submit';
      form.append(gameLabel,modes,maximum,lightningLabel,lightningDuration,el('p','Lynrunden gjentar spørsmålene i tilfeldig rekkefølge for hver deltaker. Riktig svar gir 1000 poeng, feil svar gir 0.','hint'),el('p','Lagene fordeles tilfeldig når du starter. Alle svarer individuelt, og lagets poeng er summen av medlemmenes poeng. Nye deltakere venter i lobbyen til neste spill etter lagfordelingen.','hint'),saveMode);
      const rules=el('p','','hint');form.insertBefore(rules,saveMode);
      const updateRules=()=>{showLightningDuration();for(const hint of form.querySelectorAll('p.hint'))hint.hidden=gameSelect.value==='race';rules.hidden=gameSelect.value!=='race';rules.textContent='Svar riktig på alle spørsmål uten feil. Feil svar starter et nytt forsøk. I lag spiller dere på tur; første spiller byttes etter hvert mislykkede forsøk. Første deltaker eller lag i mål vinner. Ingen poeng eller tidsfrist.';};
      gameSelect.onchange=()=>{modeDirty=true;updateRules();};updateRules();
      readModeSettings=()=>{
        if(!form.reportValidity())throw new Error('Kontroller spillinnstillingene før du starter.');
        return {game:gameSelect.value,mode:selected,max_team_size:selected==='teams'?Number(input.value):s.max_team_size||3,lightning:{enabled:lightningToggle.checked,seconds:durationInput.disabled?(s.lightning?.seconds||60):Number(durationInput.value)}};
      };
      form.onsubmit=async event=>{event.preventDefault();saveMode.disabled=true;clearError();try{await control('configure',readModeSettings())();}catch(e){error(e);}finally{saveMode.disabled=false;}};
      return form;
    }
    function showTeams(s) {
      popup((header,body)=>{
        header.append(el('h2','Lagene er klare','modal-title'));
        body.append(el('p',host?(s.game==='race'?'Finn laget ditt. Listen viser turrekkefølgen. Start løpet når alle er klare.':'Finn laget ditt. Start første spørsmål når alle er klare.'):`Du er på Lag ${s.my_team}. Vent på læreren.`,'intro'));
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
      const now=Date.now()/1000+offset,racing=state.state==='RACE_ACTIVE',left=racing?Infinity:Math.max(0,state.deadline-now),active=['QUESTION_ACTIVE','LIGHTNING_ACTIVE','RACE_ACTIVE'].includes(state.state);
      music?.update(active&&left>0&&online&&Date.now()-lastPoll<=5000&&!state.question?.youtube,`${state.run}:`+(racing?'race':state.state==='LIGHTNING_ACTIVE'?'lightning':state.index));
      const txt=racing?`${state.progress??0} / ${state.total} riktige`:active?(left>0?Math.ceil(left)+' sekunder':'Tiden er ute'):'';
      if(hostClock)hostClock.textContent=txt;
      if(countdown){const remaining=Math.max(0,Math.ceil(state.countdown_end-now));const text=remaining?String(Math.min(3,remaining)):'Venter …';if(countdown.textContent!==text)countdown.textContent=text;}
      if(submit)submit.disabled=submitting||!active||!online||Date.now()-lastPoll>5000||left<=0||state.submitted||(racing&&!state.can_answer);
    }
    setInterval(updateClock,250);
    let overlay=null;
    // Enlarge question canvases uniformly, constrained by both axes.
    // Keep the existing responsive layout on smaller screens.
    function fitQuestion(){
      if(!overlay)return;
      const scale=Math.max(1,Math.min((window.innerWidth-32)/900,(window.innerHeight-32)/700));
      overlay.style.setProperty('--teacher-scale',String(scale));
    }
    window.addEventListener('resize',fitQuestion);
    const closePopup=()=>{if(overlay){timer.before(connection,meta);if(joinCode)timer.before(joinCode);results.before(controls);overlay.close();overlay.remove();overlay=null;}};
    function popup(build,cls=''){
      closePopup();overlay=el('dialog',undefined,'question-modal '+cls+(host?' teacher-modal':' participant-modal'));
      const header=el('div',undefined,'modal-header'),body=el('div',undefined,'modal-body');
      overlay.append(header,body);build(header,body);
      const title=overlay.querySelector('h2,.qcard-head')||overlay.querySelector('[role=status]'),footer=el('div',undefined,'question-modal-footer'),message=el('p',undefined,'modal-notice');
      title.id='quiz-modal-title';title.tabIndex=-1;overlay.setAttribute('aria-labelledby',title.id);message.hidden=true;message.setAttribute('role','alert');
      overlay.addEventListener('cancel',event=>event.preventDefault());
      if(joinCode)footer.append(joinCode);
      footer.append(window.quizThemeButton(),meta,connection,message,controls);overlay.append(footer);document.body.append(overlay);fitQuestion();overlay.showModal();title.focus();
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
      if(q.image||(host&&q.youtube))body.classList.add('media-question-body');
      hostClock=el('span',undefined,'qcard-timer');head.append(el('span',s.state==='RACE_ACTIVE'?`Quiz Race · Forsøk ${s.race.attempt+1}`:s.state==='LIGHTNING_ACTIVE'?`LYNRUNDE · ${s.progress+1} av ${s.total}`:`Spørsmål ${s.index+1} av ${s.total}`),hostClock);
      header.append(head);body.append(media);void content(q,media,{query,token,showVideo:host,showImages:true,autoplay:s.state==='QUESTION_ACTIVE'},header);
      if(!host&&['QUESTION_ACTIVE','LIGHTNING_ACTIVE','RACE_ACTIVE'].includes(s.state))body.append(answerForm(s,order));
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
        try{
          const lightning=s.state==='LIGHTNING_ACTIVE',race=s.state==='RACE_ACTIVE';
          const reply=await api(race?'race-answer':lightning?'lightning-answer':'answer',{room:id,run:s.run,index:s.index,answer:selection,...(race?{attempt:s.race.attempt,race_revision:s.race.revision}:{})},{},token);
          if(lightning||race){lastPoll=Date.now();online=true;render(reply.state);renderResults(reply.state);}
          else {if(state.run===s.run&&state.index===s.index)state.submitted=true;acknowledgement.textContent='Svaret er mottatt. Vent på læreren.';}
        }
        catch(err){error(err);if(state.index===s.index&&!state.submitted)form.querySelectorAll('input').forEach(input=>input.disabled=false);}
        finally{submitting=false;updateClock();requestPoll();}
      };
      if(s.submitted)form.querySelectorAll('input').forEach(input=>input.disabled=true);
      return form;
    }
    function render(s){
      if(state&&s.version<state.version)return;
      if(state&&s.version===state.version&&s.state==='LIGHTNING_ACTIVE'&&(s.progress??0)<(state.progress??0))return;
      if(state&&s.version===state.version&&!['LIGHTNING_ACTIVE','RACE_ACTIVE'].includes(s.state)&&state.submitted)s.submitted=true;
      state=s;if(joinCode)joinCode.textContent=`Bli med: quiz.munchboka.no · Spillkode ${s.pin}`;heading.textContent=s.title;meta.textContent=(s.my_team?`Lag ${s.my_team} · `:'')+`${s.players} deltakere · ${s.answers} svar`+(s.index>=0&&!host?` · Spørsmål ${Math.min(s.index+1,s.total)} av ${s.total}`:'');
      if(!host&&s.state==='QUESTION_RESULTS')meta.textContent=(s.my_team?`Lag ${s.my_team} · `:'')+`Spørsmål ${s.index+1} av ${s.total}`;
      if(s.game==='race')meta.textContent=(s.my_team?`Lag ${s.my_team} · `:'')+'Quiz Race';
      if(s.state.startsWith('LIGHTNING_'))meta.textContent=(s.my_team?`Lag ${s.my_team} · `:'')+(host?`${s.players} deltakere`:'Lynrunde');
      if(host&&s.waiting_count)meta.textContent+=` · ${s.waiting_count} venter på neste spill`;
      if(ack&&s.submitted){ack.textContent='Svaret er mottatt. Vent på læreren.';overlay?.querySelectorAll('form input').forEach(input=>input.disabled=true);}
      const renderKey=s.state==='RACE_ACTIVE'?(host?`race:${s.run}:host`:`race:${s.run}:${s.race.revision}`):String(s.version)+(s.state==='LIGHTNING_ACTIVE'?':'+(s.progress??'host'):'');
      if(rendered===renderKey){if(host&&s.state==='RACE_ACTIVE')overlay.querySelector('.race-board').replaceWith(raceBoard(s));if(['LEADERBOARD','LIGHTNING_FINISHED'].includes(s.state))overlay.querySelector('.leaderboard-entries').replaceChildren(leaderboardList(s.leaderboard||[]));updateClock();return;}rendered=renderKey;closePopup();stage.replaceChildren();stage.classList.remove('stage-flush');controls.replaceChildren();results.replaceChildren();submit=null;ack=null;hostClock=null;countdown=null;
      app.dataset.state=s.state;
      if(host&&['QUIZ_FINISHED','RACE_FINISHED','LIGHTNING_FINISHED'].includes(s.state))controls.append(button('Spill igjen med samme spillere',control('restart'),'secondary'));
      if(host&&s.state!=='QUIZ_FINISHED')controls.append(button('Avslutt spillet',control('finish'),'quiet'));
      if(s.state==='WAITING_LOBBY'){stage.append(el('h2','Du er i lobbyen'),el('p','Spillet er i gang eller avsluttet. Du blir med automatisk når læreren starter neste spill.'));}
      else if(s.state==='LOBBY'){
        stage.append(el('p', s.game==='race'?'Quiz Race: Først til alle riktige uten feil vinner.':s.scoring === 'speed' ? 'Raske riktige svar: 0–1000 poeng. Jo raskere du svarer riktig, desto flere poeng. YouTube-spørsmål gir full poengsum de første fire sekundene. Feil svar gir 0.' : 'Faste poeng: 1000 for riktig svar, 0 for feil svar.', 'hint'));
        stage.append(el('h2',host?'Samle klassen':'Du er med!'),el('p',host?'Elevene skanner koden eller åpner lenken og skriver spillkoden.':'Vent på at læreren starter første spørsmål.'));
        if(host){stage.append(modeSettings(s));const url=new URL('./',location.href);url.searchParams.set('pin',s.pin);stage.append(el('div',s.pin,'pin'));const qr=qrcode(0,'M');qr.addData(url.href);qr.make();const img=el('img',undefined,'qr');img.src=qr.createDataURL(6,24);img.alt='QR-kode for å bli med i spillet';const a=link(url.href,url.href);a.target='_blank';a.rel='noopener';stage.append(img,a);controls.append(button(s.mode==='teams'?'Fordel lag og start':s.game==='race'?'Start Quiz Race':'Start første spørsmål',control('next')));}
      } else if(s.state==='QUIZ_FINISHED'){stage.append(el('h2','Det var det!'));}
      else if(s.state==='LEADERBOARD'){
        if(host)controls.prepend(button(s.index+1>=s.total?(s.lightning?.enabled?'Start lynrunde':'Vis sluttresultat'):'Neste spørsmål',control('next')));
        showBoard(s);
      }
      else if(s.state==='TEAM_OVERVIEW'){
        if(host)controls.prepend(button(s.game==='race'?'Start Quiz Race':'Start første spørsmål',control('next')));
        showTeams(s);
      }
      else if(['COUNTDOWN','LIGHTNING_COUNTDOWN','RACE_COUNTDOWN'].includes(s.state))showCountdown();
      else if(s.state==='RACE_ACTIVE'){
        if(host){popup((header,body)=>{header.append(el('h2','Quiz Race','modal-title'));body.append(el('p','Først til alle riktige uten feil vinner.','intro'),raceBoard(s));},'race-modal');}
        else{
          popup((header,body)=>{
            if(s.race.reset_at && s.now-s.race.reset_at<6){
              const reset=el('p',s.mode==='teams'?`Feil svar! Laget må starte på nytt. Neste forsøk starter med ${s.race.starting.nickname}.`:'Feil svar! Start på nytt.','race-reset');reset.setAttribute('role','status');header.append(reset);setTimeout(()=>reset.remove(),Math.max(0,(6-(s.now-s.race.reset_at))*1000));
            }
            if(s.can_answer){const order=s.question.options.length?optionOrder(s.question.options.length,id+':race:'+s.index):[];questionCard(s,order,header,body);}
            else{header.append(el('h2','Quiz Race','modal-title'));body.append(el('p',`Det er ${s.race.active.nickname} sin tur.`,'intro'),el('p',`${s.progress} av ${s.total} riktige · Forsøk ${s.race.attempt+1}`),el('p','Vent på lagkameraten din. Du får spørsmålet automatisk når det er din tur.','hint'));}
          },s.can_answer?'active-question-modal lightning-question-modal':'race-modal');
        }
      }
      else if(s.state==='RACE_FINISHED'){
        if(host)controls.prepend(button('Vis sluttresultat',control('next')));
        popup((header,body)=>{header.append(el('h2','Vi har en vinner!','modal-title'));body.append(raceBoard(s));},'race-modal');
      }
      else if(s.state==='LIGHTNING_INTRO'){
        if(host)controls.prepend(button('Start lynrunde',control('next')));
        popup((header,body)=>{header.append(el('h2','LYNRUNDE','modal-title'));body.append(el('p','Svar på så mange spørsmål du klarer innen tiden er ute!','intro'),el('p',`${s.lightning.seconds} sekunder`,'lightning-timer'),el('p',host?'Start når alle er klare.':'Vent på læreren.','hint'));},'lightning-modal');
      }
      else if(s.state==='LIGHTNING_ACTIVE'){
        if(host||s.completed){
          popup((header,body)=>{header.append(el('h2','LYNRUNDE','modal-title'));hostClock=el('p','','lightning-timer');body.append(hostClock,el('p',host?'Runden er i gang!': 'Du har svart på alle spørsmålene!','intro'));if(!host)body.append(el('p','Vent til lynrunden er ferdig.','hint'));},'lightning-modal');
        }else{
          const order=s.question.options.length?optionOrder(s.question.options.length,id+':lightning:'+s.index):[];
          popup((header,body)=>questionCard(s,order,header,body),'active-question-modal lightning-question-modal');
        }
      }
      else if(s.state==='LIGHTNING_FINISHED'){
        if(host)controls.prepend(button('Vis sluttresultat',control('next')));
        showBoard(s);
      }
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
    function raceBoard(s){
      const board=el('div',undefined,'race-board');
      for(const row of s.race_board||[]){
        const item=el('section',undefined,'race-row');item.append(el('h3',row.name+(row.id===s.winner?' · Vinner!':'')),el('p',`${row.progress} av ${s.total} riktige · Forsøk ${row.attempt+1}`));
        const bar=el('progress');bar.max=s.total;bar.value=row.progress;bar.setAttribute('aria-label',row.name+': fremdrift');item.append(bar);board.append(item);
      }return board;
    }
    function renderResults(s){
      if(state&&s.version<state.version)return;
      results.replaceChildren();
      if(host&&s.roster){results.append(el('h2','I lobbyen'),el('p',s.roster.join(' · ')||'Venter på første deltaker …'));}
      if(s.state==='QUIZ_FINISHED')results.append(el('h2','Resultater'),s.game==='race'?raceBoard(s):leaderboardList(s.leaderboard||[]));
    }
    function requestPoll(){clearTimeout(pollTimer);if(polling)pollAgain=true;else void poll();}
    async function poll(){
      if(polling)return;polling=true;
      try{const started=Date.now(),s=await api('state',undefined,query,token);online=true;failures=0;lastPoll=Date.now();offset=s.now-(started+lastPoll)/2000;connection.textContent='Tilkoblet';render(s);renderResults(s);}
      catch(e){online=false;failures++;connection.textContent='Mistet kontakt: '+e.message+' Kobler til igjen …';updateClock();}
      finally{polling=false;const interval=['COUNTDOWN','LIGHTNING_COUNTDOWN','RACE_COUNTDOWN'].includes(state?.state)?200:1000;pollTimer=setTimeout(poll,pollAgain?0:Math.min(10000,interval*2**Math.min(failures,3)));pollAgain=false;}
    }
    await poll();
  }
  window.addEventListener('beforeunload',e=>{if(dirty||uploads){e.preventDefault();e.returnValue='';}});
  (async()=>{const init=await api('bootstrap');csrf=init.csrf;uid=init.uid;pending=init.pending;canSetPassword=init.can_set_password;document.querySelector('#account-link').textContent=uid?'Min konto':'Logg inn';if(params.has('search'))await discover();else if(params.has('public'))await sharedQuiz(true);else if(params.has('share'))await sharedQuiz();else if(params.has('login'))login();else if(params.has('host'))await room(true);else if(params.has('room'))await room(false);else if(params.has('edit')||params.has('new'))await editor();else if(params.has('teacher'))await library();else home();})().catch(error);
})();
