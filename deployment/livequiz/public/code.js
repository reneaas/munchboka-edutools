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
    const cm = CodeMirror(container, {
      value: code,
      mode: 'python',
      lineNumbers: false,
      readOnly: 'nocursor',
      viewportMargin: Infinity
    });
    // The container may not be in the document yet; CodeMirror must re-measure once it is.
    setTimeout(() => cm.refresh(), 0);
    return cm;
  };
})();
