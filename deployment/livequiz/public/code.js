/* CodeMirror wiring shared by the question editor (editable) and question
   display (read-only), matching the highlighting used by interactive-code. */
(function () {
  'use strict';
  window.makeCodeEditor = function (textarea) {
    if (!window.CodeMirror || !textarea) return null;
    const cm = CodeMirror.fromTextArea(textarea, {
      mode: 'python',
      lineNumbers: true,
      tabSize: 4,
      indentUnit: 4,
      viewportMargin: Infinity
    });
    cm.on('change', () => { cm.save(); textarea.dispatchEvent(new Event('input')); });
    return cm;
  };
  window.renderCodeBlock = function (container, code) {
    if (!window.CodeMirror || !container) return null;
    return CodeMirror(container, {
      value: code,
      mode: 'python',
      lineNumbers: false,
      readOnly: 'nocursor',
      viewportMargin: Infinity
    });
  };
})();
