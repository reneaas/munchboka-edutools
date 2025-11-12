// Ported turtleCode.js minimal wrapper that uses CodeEditor + Skulpt

function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = (Math.random() * 16) | 0;
        const v = c === 'x' ? r : (r & 0x3) | 0x8;
        return v.toString(16);
    });
}

class TurtleCode {
    constructor(containerId, initialCode = "", cmOptions = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        if (!this.container) throw new Error(`Container ${containerId} not found`);
        this.initialCode = initialCode;
        this.cmOptions = cmOptions;
        this.uniqueSuffix = generateUUID();
        this.createUI();
        this.editor = new CodeEditor(this.textAreaEl.id);
        setTimeout(() => { this.editor.setValue(this.initialCode); }, 200);
        this.runButtonEl.addEventListener("click", () => this.runCode());
    }

    createUI() {
        this.container.innerHTML = "";
        const wrap = document.createElement('div');
        wrap.style.display = 'flex'; wrap.style.flexWrap = 'wrap'; wrap.style.width = '100%';
        const left = document.createElement('div'); left.style.flex = '1'; left.style.minWidth = '220px'; left.style.display='flex'; left.style.flexDirection='column';
        const right = document.createElement('div'); right.style.flex = '1'; right.style.minWidth = '320px'; right.style.display='flex'; right.style.flexDirection='column'; right.style.alignItems='center'; right.style.justifyContent='center';
        this.textAreaEl = document.createElement('textarea'); this.textAreaEl.id = `skulpt-editor-${this.uniqueSuffix}`; this.textAreaEl.style.display='none'; left.appendChild(this.textAreaEl);
        this.runButtonEl = document.createElement('button'); this.runButtonEl.className='button button-run'; this.runButtonEl.textContent='Kjør kode'; this.runButtonEl.style.margin='1em 0'; left.appendChild(this.runButtonEl);
        this.outputEl = document.createElement('pre'); this.outputEl.className='pythonoutput'; this.outputEl.style.minHeight='2em'; left.appendChild(this.outputEl);
        this.canvasEl = document.createElement('div'); this.canvasEl.id = `skulpt-canvas-${this.uniqueSuffix}`; this.canvasEl.style.border='1px solid #ccc'; this.canvasEl.style.width='95%'; this.canvasEl.style.height='400px'; right.appendChild(this.canvasEl);
        wrap.appendChild(left); wrap.appendChild(right); this.container.appendChild(wrap);
    }

    runCode() {
        let userCode = this.editor.getValue();
        this.outputEl.innerHTML = '';
        const mode = document.documentElement.getAttribute('data-mode');
        let forcedColor = 'black';
        if (mode === 'dark') forcedColor = 'white';
        else if (mode === 'auto') forcedColor = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'white' : 'black';
        const snippet = `\ntry:\n    import turtle\n    turtle.color("${forcedColor}")\n    screen = turtle.Screen()\nexcept: pass\n`;
        userCode = snippet + userCode;
        const outf = (text) => { this.outputEl.innerHTML += text; };
        const builtinRead = (filename) => { if (!Sk.builtinFiles || !Sk.builtinFiles['files'][filename]) { throw new Error('File not found: ' + filename); } return Sk.builtinFiles['files'][filename]; };
        Sk.pre = this.outputEl.id;
        Sk.configure({ output: outf, read: builtinRead, python3: true });
        (Sk.TurtleGraphics || (Sk.TurtleGraphics = {})).target = this.canvasEl.id;
        Sk.misceval.asyncToPromise(() => Sk.importMainWithBody('<stdin>', false, userCode, true)).catch(err => { this.outputEl.innerHTML = err.toString(); });
    }
}

function makeTurtleCode(containerId, initialCode = '', cmOptions = {}) { return new TurtleCode(containerId, initialCode, cmOptions); }
