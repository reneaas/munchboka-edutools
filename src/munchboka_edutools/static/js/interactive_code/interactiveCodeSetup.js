class InteractiveCodeSetup {
	constructor(containerId, initialCode, preloadPackages = null) {
		this.containerId = containerId;
		this.initialCode = initialCode;
		this.preloadPackages = preloadPackages;
		this.uniqueId = this.generateUUID();

		// HTML element IDs
		this.editorId = `code-editor-${this.uniqueId}`;
		this.runButtonId = `run-button-${this.uniqueId}`;
		this.resetButtonId = `reset-button-${this.uniqueId}`;
		this.cancelButtonId = `cancel-button-${this.uniqueId}`;
		this.outputId = `output-${this.uniqueId}`;
		this.errorBoxId = `error-box-${this.uniqueId}`;

		this.editorInstance = null;
		this.runnerInstance = null;

		this.createEditorHTML();
		this.setupInteractiveEditor();
	}

	generateUUID() {
		return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
			const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
			return v.toString(16);
		});
	}

	createEditorHTML() {
		const container = document.getElementById(this.containerId);
		if (!container) return;

		const runIcon = `
<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
  <path stroke-linecap="round" stroke-linejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.347a1.125 1.125 0 0 1 0 1.972l-11.54 6.347a1.125 1.125 0 0 1-1.667-.986V5.653Z" />
 </svg>`;
		const resetIcon = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="size-6">
  <path fill-rule="evenodd" d="M9.53 2.47a.75.75 0 0 1 0 1.06L4.81 8.25H15a6.75 6.75 0 0 1 0 13.5h-3a.75.75 0 0 1 0-1.5h3a5.25 5.25 0 1 0 0-10.5H4.81l4.72 4.72a.75.75 0 1 1-1.06 1.06l-6-6a.75.75 0 0 1 0-1.06l6-6a.75.75 0 0 1 1.06 0Z" clip-rule="evenodd" />
</svg>`;
		const cancelIcon = `
<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
  <path stroke-linecap="round" stroke-linejoin="round" d="M5.25 7.5A2.25 2.25 0 0 1 7.5 5.25h9a2.25 2.25 0 0 1 2.25 2.25v9a2.25 2.25 0 0 1-2.25 2.25h-9a2.25 2.25 0 0 1-2.25-2.25v-9Z" />
</svg>`;

		const html = `
			<div>
				<textarea id="${this.editorId}" name="code-${this.uniqueId}">${this.initialCode}</textarea>
                
				<button id="${this.runButtonId}" class="button button-run">Kjør kode ${runIcon}</button>
				<button id="${this.resetButtonId}" class="button button-reset">Reset kode ${resetIcon}</button>
				<button id="${this.cancelButtonId}" class="button button-cancel">Avbryt kjøring ${cancelIcon}</button>
			</div>
			<div id="${this.errorBoxId}"></div>
			<pre id="${this.outputId}" class="pythonoutput"></pre>
		`;

		container.innerHTML = html;
	}

	setupInteractiveEditor() {
		this.editorInstance = new CodeEditor(this.editorId);
		this.runnerInstance = new PythonRunner(this.outputId, this.errorBoxId, this.preloadPackages);

		// Wait for editor to be ready before attaching listeners
		this.editorInstance.editorReady.then(() => {
			const runBtn = document.getElementById(this.runButtonId);
			const resetBtn = document.getElementById(this.resetButtonId);
			const cancelBtn = document.getElementById(this.cancelButtonId);
			
			if (runBtn) runBtn.addEventListener("click", () => this.runCode());
			if (resetBtn) resetBtn.addEventListener("click", () => this.resetCode());
			if (cancelBtn) cancelBtn.addEventListener("click", () => this.cancelCodeExecution());
		});
	}

	runCode() {
		this.clearOutput();
		this.runnerInstance.run(this.editorInstance);
	}

	resetCode() {
		this.clearOutput();
		this.editorInstance.resetEditor(this.initialCode);
	}

	cancelCodeExecution() {
		if (this.runnerInstance.workerManager) {
			this.runnerInstance.workerManager.restartWorker();
		}
	}

	clearOutput() {
		const out = document.getElementById(this.outputId);
		const err = document.getElementById(this.errorBoxId);
		if (out) out.textContent = "";
		if (err) err.textContent = "";
	}
}

function makeInteractiveCode(containerId, initialCode, preloadPackages = null) {
	return new InteractiveCodeSetup(containerId, initialCode, preloadPackages);
}

class PredictionInteractiveCodeSetup extends InteractiveCodeSetup {
	constructor(containerId, initialCode) {
		super(containerId, initialCode);
		this.predictionInputId = `prediction-input-${this.uniqueId}`;
		this.lockPredictionButtonId = `lock-prediction-button-${this.uniqueId}`;
		this.predictionDisplayId = `prediction-display-${this.uniqueId}`;
		this.predictionOutputId = `prediction-output-${this.uniqueId}`;
		this.predictionOutputContainerId = `prediction-output-container-${this.uniqueId}`;
		this.predictionContainerId = `prediction-container-${this.uniqueId}`;

		this.predictionDisplayed = false;

		this.addPredictionHTML();
		this.setupPredictionFeature();
	}

	addPredictionHTML() {
		const container = document.getElementById(this.containerId);
		if (!container) return;

		const predictionHtml = `
			<div id="${this.predictionContainerId}" class="prediction-container">
			<textarea id="${this.predictionInputId}" rows="3" placeholder="Skriv inn svaret ditt her! \n \nTrykk på Enter (&#9166;) for en ny linje."></textarea>
			<button id="${this.lockPredictionButtonId}" class="button button-run">Sjekk svaret!</button>
			</div>
		`;
		container.insertAdjacentHTML('beforeend', predictionHtml);

		const predictionOutputContainer = document.createElement('div');
		predictionOutputContainer.id = this.predictionOutputContainerId;
		predictionOutputContainer.className = 'prediction-output-container';
		predictionOutputContainer.style.display = 'none';

		const predictionDisplay = document.createElement('div');
		predictionDisplay.className = 'prediction-display';
		predictionDisplay.innerHTML = `
			<h3>Ditt svar:</h3>
			<pre id="${this.predictionDisplayId}"></pre>
		`;

		const outputDisplay = document.createElement('div');
		outputDisplay.className = 'output-display';
		outputDisplay.innerHTML = `
			<h3>Faktisk utskrift:</h3>
			<pre id="${this.predictionOutputId}" class="pythonoutput"></pre>
		`;

		predictionOutputContainer.appendChild(predictionDisplay);
		predictionOutputContainer.appendChild(outputDisplay);

		const errorBoxElement = document.getElementById(this.errorBoxId);
		if (errorBoxElement) {
			errorBoxElement.insertAdjacentElement('afterend', predictionOutputContainer);
		} else {
			container.appendChild(predictionOutputContainer);
		}

		this.originalOutputElement = document.getElementById(this.outputId);
	}

	setupPredictionFeature() {
		// Wait for editor to be ready before setting read-only and attaching listeners
		this.editorInstance.editorReady.then(() => {
			this.editorInstance.editor.setOption('readOnly', true);
			const rb = document.getElementById(this.runButtonId);
			const rsb = document.getElementById(this.resetButtonId);
			const cb = document.getElementById(this.cancelButtonId);
			if (rb) rb.style.display = 'none';
			if (rsb) rsb.style.display = 'none';
			if (cb) cb.style.display = 'none';
			
			const lockBtn = document.getElementById(this.lockPredictionButtonId);
			if (lockBtn) lockBtn.addEventListener("click", () => this.lockPrediction());
		});
	}

	lockPrediction() {
		const prediction = (document.getElementById(this.predictionInputId) || { value: '' }).value;
		this.prediction = prediction;

		const predictionContainer = document.getElementById(this.predictionContainerId);
		if (predictionContainer) predictionContainer.style.display = 'none';

		// Wait for editor to be ready before modifying
		this.editorInstance.editorReady.then(() => {
			this.editorInstance.editor.setOption('readOnly', false);

			const rb = document.getElementById(this.runButtonId);
			const rsb = document.getElementById(this.resetButtonId);
			const cb = document.getElementById(this.cancelButtonId);
			if (rb) rb.style.display = 'inline-block';
			if (rsb) rsb.style.display = 'inline-block';
			if (cb) cb.style.display = 'inline-block';

			this.runCode();
		});
	}

	runCode() {
		if (this.predictionDisplayed) {
			this.initialCode = this.editorInstance.getValue();
			this.replaceWithInteractiveCodeSetup();
		} else {
			this.clearOutput();
			this.runnerInstance.run(this.editorInstance, this.predictionOutputId);
			this.displayPredictionAndOutput();
			this.predictionDisplayed = true;
		}
	}

	resetCode() {
		if (this.predictionDisplayed) {
			this.replaceWithInteractiveCodeSetup();
		} else {
			this.clearOutput();
			this.editorInstance.resetEditor(this.initialCode);
		}
	}

	cancelCodeExecution() {
		if (this.predictionDisplayed) {
			this.replaceWithInteractiveCodeSetup();
		} else if (this.runnerInstance.workerManager) {
			this.runnerInstance.workerManager.restartWorker();
		}
	}

	replaceWithInteractiveCodeSetup() {
		const container = document.getElementById(this.containerId);
		if (container) {
			container.innerHTML = '';
			new InteractiveCodeSetup(this.containerId, this.initialCode);
		}
	}

	displayPredictionAndOutput() {
		const pred = document.getElementById(this.predictionDisplayId);
		if (pred) pred.textContent = this.prediction;
		if (this.originalOutputElement) this.originalOutputElement.style.display = 'none';
		const poc = document.getElementById(this.predictionOutputContainerId);
		if (poc) poc.style.display = 'flex';
	}
}

function makePredictionInteractiveCode(containerId, initialCode) {
	return new PredictionInteractiveCodeSetup(containerId, initialCode);
}
