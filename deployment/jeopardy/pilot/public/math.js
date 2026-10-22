/* Local, safe KaTeX rendering shared by editor previews and the Jeopardy runtime. */
(function () {
  'use strict';
  function escaped(text, at) {
    let n = 0;
    while (at > 0 && text[--at] === '\\') n++;
    return n % 2 === 1;
  }
  window.renderMathInElement = function (root) {
    if (!window.katex || !root) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        return node.parentElement.closest('.katex,textarea,script,style,code,pre') ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT;
      }
    });
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    for (const node of nodes) {
      const text = node.nodeValue;
      const fragment = document.createDocumentFragment();
      let start = 0, pos = 0, changed = false;
      while (pos < text.length) {
        if (text[pos] !== '$' || escaped(text, pos)) { pos++; continue; }
        const delim = text[pos + 1] === '$' ? '$$' : '$';
        let end = pos + delim.length;
        while (end < text.length && (text.slice(end, end + delim.length) !== delim || escaped(text, end))) end++;
        if (end >= text.length) { pos += delim.length; continue; }
        fragment.append(document.createTextNode(text.slice(start, pos)));
        const span = document.createElement('span');
        const latex = text.slice(pos + delim.length, end);
        try {
          katex.render(latex, span, {displayMode: delim === '$$', throwOnError: true, trust: false, maxSize: 20, maxExpand: 1000, strict: 'ignore'});
        } catch (error) {
          span.className = 'math-error';
          span.textContent = text.slice(pos, end + delim.length);
          span.title = 'Kontroller LaTeX-uttrykket: ' + error.message;
        }
        fragment.append(span);
        pos = end + delim.length;
        start = pos;
        changed = true;
      }
      if (changed) {
        fragment.append(document.createTextNode(text.slice(start)));
        node.replaceWith(fragment);
      }
    }
  };
})();
