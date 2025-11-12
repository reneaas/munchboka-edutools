// Ported workerManager.js from matematikk_r1 interactiveCode

class WorkerManager {
    static instance = null;

    static getInstance(preloadPackages = null) {
        if (!WorkerManager.instance) {
            const defaultPreloadPackages = ['matplotlib', 'numpy', 'scipy', 'sympy', 'micropip'];
            const combinedPreloadPackages = Array.from(new Set(preloadPackages ? [...defaultPreloadPackages, ...preloadPackages] : defaultPreloadPackages));
            WorkerManager.instance = new WorkerManager(combinedPreloadPackages);
            setTimeout(() => {
                WorkerManager.instance.warmUpPyodide().catch(err => console.warn('Pyodide warm-up failed:', err));
            }, 1000);
        } else if (preloadPackages) {
            const packagesToLoad = preloadPackages.filter(pkg => !WorkerManager.instance.loadedPackages.has(pkg));
            const combinedPreloadPackages = Array.from(new Set(['matplotlib', 'numpy', 'scipy', 'sympy', 'micropip', ...packagesToLoad]));
            if (combinedPreloadPackages.length > 0) WorkerManager.instance.loadPackages(combinedPreloadPackages);
        }
        return WorkerManager.instance;
    }

    constructor(preloadPackages = []) {
        if (WorkerManager.instance) return WorkerManager.instance;
        this.worker = null;
        this.callbacks = {};
        this.preloadPackages = preloadPackages;
        this.loadedPackages = new Set();
        this.packageLoadPromises = {};
        this.workerReadyPromise = new Promise((resolve, reject) => { this.workerReadyResolve = resolve; this.workerReadyReject = reject; });
        this.initWorker();
        WorkerManager.instance = this;
    }

    initWorker() {
        // Inline Python template kept inside JS string carefully escaped.
            const workerScript = `importScripts('https://cdn.jsdelivr.net/pyodide/v0.26.2/full/pyodide.js');

let pyodideReadyPromise = loadPyodide();
let initialGlobals = new Set();

async function resetPyodide(pyodide, initialGlobals) {
    const currentGlobals = new Set(pyodide.globals.keys());
    const globalsToClear = Array.from(currentGlobals).filter(x => !initialGlobals.has(x));
    for (const key of globalsToClear) { pyodide.globals.delete(key); }
}

async function installPackages(pyodide, packages) {
    if (packages.length > 0) {
        await pyodide.loadPackage('micropip');
        const micropip = pyodide.pyimport('micropip');
        await micropip.install(packages);
    }
}

onmessage = async (event) => {
    const messageId = event.data.messageId;
    if (event.data.type === 'init') {
        const { preloadPackages } = event.data;
        const pyodide = await pyodideReadyPromise;
        initialGlobals = new Set(pyodide.globals.keys());
        const pyodidePackages = preloadPackages.filter(pkg => ['matplotlib','numpy','scipy','sympy','micropip'].includes(pkg));
        const pypiPackages = preloadPackages.filter(pkg => !['matplotlib','numpy','scipy','sympy','micropip'].includes(pkg));
        if (pyodidePackages.length > 0) await pyodide.loadPackage(pyodidePackages);
        await installPackages(pyodide, pypiPackages);
        postMessage(JSON.stringify({ type: 'initReady' }));
    }

    if (event.data.type === 'runCode') {
        const { code } = event.data;
        try {
            const pyodide = await pyodideReadyPromise;
            await resetPyodide(pyodide, initialGlobals);
            const pyCode = \`import sys, json, io, base64
from js import postMessage
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

MESSAGE_ID = "${messageId}"

class PyConsole:
    def __init__(self, message_id):
        self.message_id = message_id
        self.buffer = ''
    def write(self, msg):
        self.buffer += msg
        if '\\\\\\\\n' in msg:
            self.flush()
    def flush(self):
        if self.buffer:
            postMessage(json.dumps({'type':'stdout','msg':self.buffer,'messageId':self.message_id}))
            self.buffer = ''

sys.stdout = PyConsole(MESSAGE_ID)
sys.stderr = PyConsole(MESSAGE_ID)

def show_override():
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    fig = plt.gcf()
    width_in = fig.get_figwidth(); height_in = fig.get_figheight(); dpi = fig.get_dpi()
    width_px = int(width_in * dpi); height_px = int(height_in * dpi)
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    postMessage(json.dumps({'type':'plot','data':image_base64,'messageId':MESSAGE_ID,'width':width_px,'height':height_px}))
    plt.clf()
    sys.stdout.write('\\\\\\\\n')
    sys.stdout.write('\\\\\\\\n')
    sys.stdout.flush()

plt.show = lambda: show_override()\`;
            // Send back the Python code for debugging before execution
            postMessage(JSON.stringify({ type: 'debugPyCode', messageId, pyCode }));
            await pyodide.runPythonAsync(pyCode);
            await pyodide.runPythonAsync(code);
            // Ensure any buffered output gets emitted even if no trailing newline
            await pyodide.runPythonAsync('import sys; sys.stdout.flush(); sys.stderr.flush()');
            postMessage(JSON.stringify({ type: 'executionComplete', messageId }));
        } catch (err) {
            postMessage(JSON.stringify({ type: 'stderr', msg: String(err), messageId }));
        }
    }

    if (event.data.type === 'loadPackage') {
        const { packages, packageRequestId } = event.data;
        try {
            const pyodide = await pyodideReadyPromise;
            const pyodidePackages = packages.filter(pkg => ['matplotlib','numpy','scipy','sympy','micropip'].includes(pkg));
            const pypiPackages = packages.filter(pkg => !['matplotlib','numpy','scipy','sympy','micropip'].includes(pkg));
            if (pyodidePackages.length > 0) await pyodide.loadPackage(pyodidePackages);
            await installPackages(pyodide, pypiPackages);
            postMessage(JSON.stringify({ type: 'packagesLoaded', packageRequestId }));
        } catch (err) {
            postMessage(JSON.stringify({ type: 'stderr', msg: String(err), packageRequestId }));
        }
    }
};
`;
                const workerBlob = new Blob([workerScript], { type: 'application/javascript' });
        this.worker = new Worker(URL.createObjectURL(workerBlob));
        this.worker.onmessage = this.handleMessage.bind(this);
        this.worker.onerror = this.handleError.bind(this);
        this.worker.postMessage({ type: 'init', preloadPackages: this.preloadPackages });
        this.pyodideWarmedUp = false;
    }

    warmUpPyodide() {
        if (this.pyodideWarmedUp) return Promise.resolve();
        return this.workerReadyPromise.then(() => new Promise((resolve) => {
            const messageId = this.generateMessageId();
            this.callbacks[messageId] = (data) => { if (data.type === 'executionComplete') { this.pyodideWarmedUp = true; resolve(); } };
            this.worker.postMessage({ type: 'runCode', code: '# warmup', messageId });
        }));
    }

    generateMessageId() { return 'msg-' + Math.random().toString(36).substr(2, 9); }

    loadPackages(packages) {
        const packagesToLoad = packages.filter(pkg => !this.loadedPackages.has(pkg));
        if (packagesToLoad.length === 0) return Promise.resolve();
        const packageRequestId = 'pkg-' + Math.random().toString(36).substr(2, 9);
        return new Promise((resolve, reject) => {
            this.packageLoadPromises[packageRequestId] = { resolve, reject, packages: packagesToLoad };
            this.worker.postMessage({ type: 'loadPackage', packages: packagesToLoad, packageRequestId });
        });
    }

    runCode(code, onMessageCallback) {
        const messageId = this.generateMessageId();
        this.callbacks[messageId] = onMessageCallback;
        this.worker.postMessage({ type: 'runCode', code, messageId });
        return messageId;
    }

    handleMessage(event) {
        let data; try { data = JSON.parse(event.data); } catch (e) { console.error('Worker message JSON parse failed:', e, event.data); return; }
        const { messageId, packageRequestId } = data;
        if (data.type === 'debugPyCode') {
            // Surface embedded Python for inspection
            console.log('Embedded Python received (messageId=' + data.messageId + '):\n' + data.pyCode);
        }
        if (messageId && this.callbacks[messageId]) {
            this.callbacks[messageId](data);
            if (data.type === 'executionComplete') delete this.callbacks[messageId];
        } else if (packageRequestId && this.packageLoadPromises[packageRequestId]) {
            const pkgPromise = this.packageLoadPromises[packageRequestId];
            if (data.type === 'packagesLoaded') { for (const pkg of pkgPromise.packages) this.loadedPackages.add(pkg); pkgPromise.resolve(); }
            else if (data.type === 'stderr') { pkgPromise.reject(new Error(data.msg)); }
            delete this.packageLoadPromises[packageRequestId];
        } else if (data.type === 'initReady') {
            this.workerReadyResolve();
        }
    }

    handleError(error) { console.error('Worker error:', error); if (this.workerReadyReject) this.workerReadyReject(error); }

    restartWorker() {
        if (this.worker) { this.worker.terminate(); this.worker = null; }
        this.loadedPackages = new Set(); this.pyodideWarmedUp = false;
        this.workerReadyPromise = new Promise((resolve, reject) => { this.workerReadyResolve = resolve; this.workerReadyReject = reject; });
        this.initWorker();
        setTimeout(() => { this.warmUpPyodide().catch(err => console.warn('Warm-up failed after restart:', err)); }, 1000);
    }
}
