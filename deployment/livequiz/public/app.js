/* Livequiz proof of concept: same-origin PHP API, non-overlapping polling. */
(() => {
  'use strict';
  const app = document.querySelector('#app'), notice = document.querySelector('#notice');
  const params = new URLSearchParams(location.search);
  let csrf = '', uid = 0, pending = false, dirty = false, uploads = 0;
  const el = (tag, text, cls) => { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if (cls) n.className = cls; return n; };
  function error(e) { notice.textContent = e.message || String(e); notice.hidden = false; }
  function clearError() { notice.hidden = true; }
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
    const headers = {}; if (token) headers['X-Player-Token'] = token;
    if (data !== undefined) { headers['X-CSRF-Token'] = csrf; if (!(data instanceof FormData)) headers['Content-Type'] = 'application/json'; }
    const response = await fetch(url, {method: data === undefined ? 'GET' : 'POST', headers, body: data === undefined ? undefined : data instanceof FormData ? data : JSON.stringify(data), credentials: 'same-origin', cache: 'no-store', signal: AbortSignal.timeout(10000)});
    if (binary && response.ok) return response.blob();
    let result; try { result = await response.json(); } catch (_) { throw new Error('Serveren svarte ikke som forventet. Prøv igjen.'); }
    if (!response.ok) throw new Error(result.error || 'Forespørselen mislyktes.'); return result;
  }
  function rich(text) { const n = el('div', text, 'rich'); window.renderMathInElement(n); return n; }
  async function content(q, target, context = {}) {
    target.append(rich(q.prompt));
    if (q.code) { const pre = el('pre'); pre.append(el('code', q.code)); target.append(pre); }
    if (q.image) {
      const img = el('img', undefined, 'question-image'); img.alt = q.image.alt; target.append(img);
      try { const blob = await api('media', undefined, {...context.query, image: q.image.id}, context.token || '', true); const url = URL.createObjectURL(blob); img.onload = () => URL.revokeObjectURL(url); img.src = url; }
      catch (_) { img.replaceWith(el('p', 'Bildet kunne ikke lastes.')); }
    }
    if (q.youtube) {
      const slot = el('div');
      slot.append(button('▶ Vis YouTube-video', () => {
        const frame = el('iframe'); frame.title = 'YouTube-video'; frame.src = 'https://www.youtube-nocookie.com/embed/' + q.youtube;
        frame.allow = 'encrypted-media; picture-in-picture; fullscreen'; frame.allowFullscreen = true; slot.replaceChildren(frame);
      }, 'secondary')); target.append(slot);
    }
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
    app.append(form, el('p', 'Læreren styrer tempoet. Riktig svar gir 1000 poeng; hastighet gir ingen ekstra poeng.', 'hint'));
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
      const card = el('article', undefined, 'card'); card.append(el('h2', q.title), el('p', 'Versjon ' + q.revision), group(link('Rediger', '?edit=' + q.id), button('Start spill', async () => { const r = await api('create', {id:q.id}); location.href = '?host=' + r.room; }))); grid.append(card);
    }
    app.append(grid);
    if (data.rooms.length) {
      app.append(el('h2', 'Siste spill · tilgjengelig i seks timer'));
      for (const r of data.rooms) app.append(link('Spill ' + r.pin + (r.phase === 'finished' ? ' · avsluttet' : ' · åpne'), '?host=' + r.id));
    }
  }
  const blankQuestion = () => ({type:'single', prompt:'', code:'', youtube:'', image:null, seconds:30, options:['','','',''], correct:[0], accepted:[]});
  async function editor() {
    if (!uid) return library();
    let saved = params.has('edit') ? await api('quiz', undefined, {id:params.get('edit')}) : {id:'',revision:0,content:{title:'',questions:[blankQuestion()]}};
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
    const list = el('div');
    app.replaceChildren(el('p', 'QUIZVERKSTED', 'eyebrow'), el('h1', 'Et spørsmål om gangen'), group(save, start, link('Mine quizer','?teacher=1')), status,
      field('Quizens tittel', model.title, v => {model.title=v; changed();}), el('p', 'Bruk $...$ eller $$...$$ for matematikk. Kode vises som tekst og kjøres ikke.', 'hint'), list);
    function renderQuestions() {
      list.replaceChildren();
      model.questions.forEach((q,index) => {
        const card = el('section', undefined, 'card question-editor');
        card.append(el('h2', 'Spørsmål ' + (index+1)));
        const typeLabel = el('label','Svartype'), select = el('select');
        for (const [value,label] of [['single','Ett riktig alternativ'],['multi','Flere riktige alternativer'],['text','Skriv svaret']]) { const o = el('option',label); o.value=value; select.append(o); }
        select.value=q.type; select.onchange=()=>{q.type=select.value; if(q.type==='single') q.correct=[q.correct[0] ?? 0]; changed(); renderQuestions();}; typeLabel.append(select);
        card.append(typeLabel, field('Spørsmål',q.prompt,v=>{q.prompt=v;changed();},'textarea'), field('Kode (valgfritt)',q.code,v=>{q.code=v;changed();},'textarea'), field('YouTube-lenke eller video-ID (valgfritt)',q.youtube,v=>{q.youtube=v;changed();}), field('Svartid i sekunder (5–600)',q.seconds,v=>{q.seconds=Number(v);changed();},'number'));
        const imageLabel=el('label','Bilde (PNG, JPEG eller WebP, maks 2 MiB)'), upload=el('input'); upload.type='file'; upload.accept='image/png,image/jpeg,image/webp';
        upload.onchange=async()=>{const file=upload.files[0];if(!file)return;uploads++;changed();upload.disabled=true;try{if(file.size>2097152)throw new Error('Bildet er større enn 2 MiB.');const data=new FormData();data.set('image',file);const r=await api('upload',data);q.image={...r.image,alt:''};renderQuestions();}catch(e){error(e);}finally{uploads--;upload.disabled=false;changed();}};
        imageLabel.append(upload);card.append(imageLabel);
        if(q.image)card.append(field('Bildebeskrivelse',q.image.alt,v=>{q.image.alt=v;changed();}),button('Fjern bilde',()=>{q.image=null;changed();renderQuestions();},'quiet'));
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
      });
    }
    app.append(button('＋ Legg til spørsmål',()=>{if(model.questions.length>=50)throw new Error('Maks 50 spørsmål.');model.questions.push(blankQuestion());changed();renderQuestions();}));renderQuestions();changed();
  }
  async function room(host) {
    const id=params.get(host?'host':'room'), token=host?'':sessionStorage.getItem('lq-room-'+id)||'';
    if(!host&&!token){app.replaceChildren(el('h1','Bli med på nytt'),el('p','Denne fanen har ingen deltakerøkt. Åpne den opprinnelige fanen eller bli med med spillkoden.'),link('Til spillkoden','./'));return;}
    const query={room:id,...(host?{host:'1'}:{})};
    const heading=el('h1','Henter spill …'),connection=el('p','Kobler til …','hint'),meta=el('p',undefined,'hint'),timer=el('p',undefined,'timer'),stage=el('section',undefined,'card stage'),controls=el('div',undefined,'actions'),results=el('section');
    app.replaceChildren(el('p',host?'LÆRERSKJERM':'DU ER MED','eyebrow'),heading,connection,meta,timer,stage,controls,results);
    let state=null, rendered='', failures=0, online=false, offset=0, lastPoll=0, submit=null, ack=null, selection=null, submitting=false;
    const control=command=>async()=>{await api('control',{room:id,version:state.version,command});rendered='';};
    function updateClock(){if(!state)return;const left=Math.max(0,state.deadline-(Date.now()/1000+offset));timer.textContent=state.phase==='question'?(left>0?Math.ceil(left)+' sekunder':'Tiden er ute · venter på læreren'):'';if(submit)submit.disabled=submitting||!online||Date.now()-lastPoll>5000||left<=0||state.submitted;}
    setInterval(updateClock,250);
    function render(s){
      state=s;heading.textContent=s.title;meta.textContent=`${s.players} deltakere · ${s.answers} svar`+(s.index>=0?` · Spørsmål ${Math.min(s.index+1,s.total)} av ${s.total}`:'');
      if(ack&&s.submitted){ack.textContent='Svaret er mottatt. Vent på læreren.';stage.querySelectorAll('form input').forEach(n=>{n.disabled=true;});}
      if(rendered===String(s.version)){updateClock();return;}rendered=String(s.version);stage.replaceChildren();controls.replaceChildren();results.replaceChildren();submit=null;ack=null;
      if(s.phase==='lobby'){
        stage.append(el('h2',host?'Samle klassen':'Du er med!'),el('p',host?'Elevene skanner koden eller åpner lenken og skriver spillkoden.':'Vent på at læreren starter første spørsmål.'));
        if(host){const url=new URL('./',location.href);url.searchParams.set('pin',s.pin);stage.append(el('div',s.pin,'pin'));const qr=qrcode(0,'M');qr.addData(url.href);qr.make();const img=el('img',undefined,'qr');img.src=qr.createDataURL(6,24);img.alt='QR-kode for å bli med i spillet';const a=link(url.href,url.href);a.target='_blank';a.rel='noopener';stage.append(img,a);controls.append(button('Start første spørsmål',control('next')));}
      } else if(s.phase==='finished'){stage.append(el('h2','Takk for spillet!'),el('p','Se resultatene og snakk sammen om spørsmålene.'));}
      else {
        void content(s.question,stage,{query,token});
        if(host){s.question.options.forEach((v,i)=>stage.append(rich((i+1)+'. '+v)));controls.append(button(s.phase==='question'?'Vis fasit / steng svar':s.index+1<s.total?'Neste spørsmål':'Vis sluttresultat',control(s.phase==='question'?'reveal':'next')));}
        else if(s.phase==='question'){
          const form=el('form');selection=s.answer??(s.question.type==='text'?'':[]);
          if(s.question.type==='text'){form.append(field('Ditt svar',selection,v=>selection=v));}
          else s.question.options.forEach((v,i)=>{const label=el('label',undefined,'answer-option'),input=el('input');input.type=s.question.type==='single'?'radio':'checkbox';input.name='answer';input.checked=selection.includes(i);input.onchange=()=>{selection=s.question.type==='single'?[i]:input.checked?[...selection,i]:selection.filter(x=>x!==i);};label.append(input,rich(v));form.append(label);});
          submit=el('button','Send svar');submit.type='submit';ack=el('p',s.submitted?'Svaret er mottatt. Vent på læreren.':'','hint');ack.setAttribute('role','status');form.append(submit,ack);
          form.onsubmit=async e=>{e.preventDefault();if(submit.disabled)return;submit.disabled=true;submitting=true;clearError();try{await api('answer',{room:id,index:s.index,answer:selection},{},token);state.submitted=true;form.querySelectorAll('input').forEach(n=>n.disabled=true);ack.textContent='Svaret er mottatt. Vent på læreren.';}catch(err){error(err);}finally{submitting=false;updateClock();}};if(s.submitted)form.querySelectorAll('input').forEach(n=>n.disabled=true);stage.append(form);
        }
        if(s.phase==='reveal'){
          const correct=s.question.type==='text'?s.question.accepted:s.question.correct.map(i=>s.question.options[i]);
          stage.append(el('h2','Fasit'));correct.forEach(v=>stage.append(rich(v)));
          if(!host)stage.append(el('p',s.submitted?`Du fikk ${s.points} poeng.`:'Du svarte ikke på dette spørsmålet.','result'));
        }
      }
      if(host&&s.phase!=='finished')controls.append(button('Avslutt spillet',control('finish'),'quiet'));
      updateClock();
    }
    function renderResults(s){
      results.replaceChildren();
      if(host&&s.roster){results.append(el('h2','I lobbyen'),el('p',s.roster.join(' · ')||'Venter på første deltaker …'));}
      if(s.leaderboard){results.append(el('h2','Resultater'));const list=el('ol',undefined,'leaderboard');s.leaderboard.forEach(p=>{const li=el('li');li.append(el('span',p.nickname),el('strong',p.score+' poeng'));list.append(li);});results.append(list);}
    }
    async function poll(){
      try{const s=await api('state',undefined,query,token);online=true;failures=0;lastPoll=Date.now();offset=s.now-Date.now()/1000;connection.textContent='Tilkoblet · oppdateres hvert sekund';render(s);renderResults(s);}
      catch(e){online=false;failures++;connection.textContent='Mistet kontakt: '+e.message+' Kobler til igjen …';updateClock();}
      setTimeout(poll,state?.phase==='finished'?10000:Math.min(10000,1000*2**Math.min(failures,3)));
    }
    await poll();
  }
  window.addEventListener('beforeunload',e=>{if(dirty||uploads){e.preventDefault();e.returnValue='';}});
  (async()=>{const init=await api('bootstrap');csrf=init.csrf;uid=init.uid;pending=init.pending;document.querySelector('#account-link').textContent=uid?'Min konto':'Logg inn';if(params.has('login'))login();else if(params.has('host'))await room(true);else if(params.has('room'))await room(false);else if(params.has('edit')||params.has('new'))await editor();else if(params.has('teacher'))await library();else home();})().catch(error);
})();
