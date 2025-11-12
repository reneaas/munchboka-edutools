// Ported pythonRunner.js (simplified) - full version lives in original book assets
// This is a near-direct copy from matematikk_r1 interactiveCode/pythonRunner.js

class PythonRunner {
    constructor(outputId, errorBoxId, preloadPackages = ['casify']) {
        this.outputId = outputId;
        this.errorBoxId = errorBoxId;
        this.workerManager = WorkerManager.getInstance(preloadPackages);
        this.preloadPackages = preloadPackages;
    }

    async run(editor, outputId = null) {
        try {
            await this.workerManager.workerReadyPromise;
        } catch (error) {
            console.error("Worker failed to initialize:", error);
            this.handleErrorMessage("Failed to initialize Python environment.");
            return;
        }

        this.editorInstance = editor;
        this.editorInstance.clearLineHighlights();
        let code = editor.getValue();
        this.currentCode = code;
        if (outputId) this.outputId = outputId;

        const inputStatements = this.findInputStatements(this.currentCode);
        if (inputStatements.length > 0) {
            const userValues = await this.getUserInputs(inputStatements);
            this.currentCode = this.replaceInputStatements(this.currentCode, userValues);
        }

        const packages = this.extractPackageNames(this.currentCode);
        if (!packages.includes('matplotlib')) packages.push('matplotlib');
        if (packages.length > 0) {
            try { await this.workerManager.loadPackages(packages); } catch (error) {
                console.error("Failed to load packages:", error);
                this.handleErrorMessage(error.message);
                return;
            }
        }

        const callback = (data) => {
            if (data.type === 'stdout') {
                this.handleWorkerMessage(data);
            } else if (data.type === 'stderr') {
                this.handleErrorMessage(data.msg);
            } else if (data.type === 'plot') {
                const outputElement = document.getElementById(this.outputId);
                if (!outputElement) return;
                const img = document.createElement('img');
                img.src = 'data:image/png;base64,' + data.data;
                img.style.width = '100%';
                img.style.height = 'auto';
                img.style.maxHeight = '500px';
                outputElement.appendChild(img);
                this.scrollToBottom(outputElement);
            }
        };
        this.workerManager.runCode(this.currentCode, callback);
    }

    handleWorkerMessage(data) {
        const { type, msg } = data;
        const outputElement = document.getElementById(this.outputId);
        if (!outputElement) return;
        if (type === 'stdout') {
            let formattedMsg = msg
                .replace(/And\(([^)]+)\)/g, (match, p1) => {
                    const conditions = p1.split(',').map(cond => cond.trim());
                    return conditions.map(cond => `(${cond})`).join(' ∧ ');
                })
                .replace(/oo/g, '∞')
                .replace(/\|/g, '∨');
            outputElement.innerHTML += this.formatErrorMessage(formattedMsg);
            this.highlightLine(this.editorInstance, data.msg);
            this.scrollToBottom(outputElement);
        }
    }

    scrollToBottom(element) { element.scrollTop = element.scrollHeight; }

    handleErrorMessage(msg) {
        const errorElement = document.getElementById(this.errorBoxId);
        if (errorElement) errorElement.innerHTML = this.formatErrorMessage(msg);
        this.highlightLine(this.editorInstance, msg);
    }

    formatErrorMessage(errorMsg) {
        let formattedMessage = errorMsg;
        const fileLinePattern = /File "<exec>", line (\d+)/g;
        formattedMessage = formattedMessage.replace(fileLinePattern, (match, p1) => match.replace(`line ${p1}`, `<span class="error-line">line ${p1}</span>`));
        const errorTypeMatch = errorMsg.match(/(\w+Error):/);
        if (errorTypeMatch) formattedMessage = formattedMessage.replace(errorTypeMatch[1], `<span class="error-type">${errorTypeMatch[1]}</span>`);
        return formattedMessage;
    }

    extractPackageNames(code) {
        const importRegex = /^\s*import\s+([^;\s]+)\s*/gm;
        const fromImportRegex = /^\s*from\s+([^;\s]+)\s+import/gm;
        const packages = new Set();
        const standardLibs = new Set(['abc','argparse','array','ast','asyncio','base64','binascii','bisect','bz2','calendar','collections','contextlib','copy','csv','dataclasses','datetime','functools','hashlib','heapq','html','http','io','itertools','json','logging','math','operator','os','pathlib','pickle','platform','random','re','statistics','string','sys','textwrap','time','typing','unittest','urllib','uuid']);
        let match;
        while ((match = importRegex.exec(code)) !== null) { const pn = match[1].split('.')[0]; if (!standardLibs.has(pn)) packages.add(pn); }
        while ((match = fromImportRegex.exec(code)) !== null) { const pn = match[1].split('.')[0]; if (!standardLibs.has(pn)) packages.add(pn); }
        return Array.from(packages);
    }

    findInputStatements(code) {
        // Python identifiers with Unicode: first char letter/_ then letters/digits/_
        const inputRegex = /([\p{L}_][\p{L}\p{N}_]*)\s*=\s*(int|float|eval)?\(?input\(["'](.*?)["']\)\)?/gu;
        let match; const inputs = [];
        while ((match = inputRegex.exec(code)) !== null) { inputs.push({ variable: match[1], promptText: match[3] }); }
        return inputs;
    }

    async getUserInputs(inputs) {
        const userValues = {}; for (const input of inputs) { userValues[input.variable] = await this.promptUser(input.promptText.replace(/["']+/g, '')); } return userValues;
    }

    promptUser(promptText) { return new Promise((resolve) => { resolve(prompt(promptText)); }); }

    replaceInputStatements(code, userValues) {
        const escapeRe = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        let codeLines = code.split('\n');
        codeLines = codeLines.map(line => {
            for (let variable in userValues) {
                const vEsc = escapeRe(variable);
                // Match beginning or non-identifier char before var to avoid partial matches
                const inputRegex = new RegExp(`(^|[^\\p{L}\\p{N}_])(${vEsc})\\s*=\\s*(?:float|int|eval)?\\(?input\\(.*?\\)\\)?`, 'gu');
                line = line.replace(inputRegex, (m, prefix, v) => {
                    let userValue = userValues[variable];
                    if (isNaN(userValue) && typeof userValue === 'string') userValue = `"${userValue}"`;
                    return `${prefix}${v} = ${userValue}`;
                });
            }
            return line;
        });
        return codeLines.join('\n');
    }

    highlightLine(editor, msg) {
        const linePattern = /File "<exec>", line (\d+)/; const match = linePattern.exec(msg); if (match) { const lineNumber = parseInt(match[1]) - 1; editor.highlightLine(lineNumber); }
    }
}
