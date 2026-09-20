"""Open the interactive Python editor in a movable, non-modal dialog."""

import json
import shlex
import uuid
from html import escape

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective


class PopupCodeDirective(SphinxDirective):
    has_content = True
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {
        "width": directives.positive_int,
        "height": directives.positive_int,
        "button-text": directives.unchanged,
        "title": directives.unchanged,
        "name": directives.unchanged,
        "layout": lambda value: directives.choice(value, ("inline", "sidebar")),
        "lang": lambda value: directives.choice(value, ("python",)),
        "predict": directives.flag,
    }

    def run(self):
        try:
            args = shlex.split(self.arguments[0]) if self.arguments else []
            if len(args) > 4:
                raise ValueError("expected width, height, button text, and title")
            width = directives.positive_int(args[0]) if args else 500
            height = directives.positive_int(args[1]) if len(args) > 1 else 550
        except ValueError as exc:
            raise self.error(f"Invalid popup-code arguments: {exc}")

        identifier = self.options.get("name") or uuid.uuid4().hex
        # Include the document name so named editors on different pages do not
        # share the interactive editor's localStorage entry.
        cid = "popup-code-" + nodes.make_id(f"{self.env.docname}-{identifier}")
        label = self.options.get("button-text", args[2] if len(args) > 2 else "Åpne kodevindu")
        title = self.options.get("title", args[3] if len(args) > 3 else "Kodevindu")
        config = {
            "width": self.options.get("width", width),
            "height": self.options.get("height", height),
            "title": title,
            "predict": "predict" in self.options,
            "code": "\n".join(self.content),
        }
        sidebar = " sidebar-cas" if self.options.get("layout") == "sidebar" else ""
        html = (
            f'<div class="popup-code-launcher{sidebar}">'
            f'<button type="button" class="popup-code-button ggb-cas-button" '
            f'aria-haspopup="dialog" aria-controls="{escape(cid, quote=True)}" '
            f'aria-expanded="false" data-popup-code="{escape(json.dumps(config), quote=True)}">'
            f'{escape(label)}</button>'
            f'<div id="{escape(cid, quote=True)}" class="popup-code-content" '
            f'style="display:none"><div id="{escape(cid, quote=True)}-editor"></div></div>'
            '</div>'
        )
        return [nodes.raw("", html, format="html")]


def ensure_assets(app):
    # The umbrella extension already installs the shared editor and dialog assets.
    if "munchboka_edutools" not in app.extensions:
        from munchboka_edutools import _copy_static

        _copy_static(app)


def setup(app):
    app.add_directive("popup-code", PopupCodeDirective)
    app.add_css_file("munchboka/css/popup_code.css")
    app.add_js_file("munchboka/js/popup_code.js", priority=910)
    app.connect("builder-inited", ensure_assets)
    return {"version": "0.1", "parallel_read_safe": True, "parallel_write_safe": True}
