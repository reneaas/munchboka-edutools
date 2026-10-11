"""Recovery for transient failures of independent browser assets."""

# Keep this on the resource itself: a separate recovery script could also fail,
# and stylesheets can fail before Sphinx's first script executes. Replacing the
# element in place preserves CSS cascade order and re-executes failed scripts.
# Create a fresh element rather than cloning: script clones inherit the
# browser's "already started" flag and will not make another request.
# Only use for scripts that can initialize after DOMContentLoaded and do not
# depend on execution order relative to other scripts.
ASSET_RETRY_ONERROR = """\
if (!this.dataset.munchbokaRetryPending) {
  var attempt = Number(this.dataset.munchbokaRetry || 0) + 1;
  if (attempt <= 2) {
    var replacement = document.createElement(this.tagName);
    for (var i = 0; i < this.attributes.length; i++) {
      replacement.setAttribute(this.attributes[i].name, this.attributes[i].value);
    }
    if (this.nonce) replacement.nonce = this.nonce;
    replacement.dataset.munchbokaRetry = String(attempt);
    var attribute = this.tagName === 'LINK' ? 'href' : 'src';
    var url = new window.URL(this.getAttribute(attribute), document.baseURI);
    url.searchParams.set('munchboka_retry', String(attempt));
    replacement.setAttribute(attribute, url.href);
    this.dataset.munchbokaRetryPending = 'true';
    var failed = this;
    window.setTimeout(function () {
      if (failed.parentNode) failed.parentNode.replaceChild(replacement, failed);
    }, attempt * 300);
  }
}
"""
