"""A locally hosted, CW-style scientific calculator in a floating dialog."""
from hashlib import sha256
from html import escape
from pathlib import Path
import shutil

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective
from sphinx.util.osutil import relative_uri


class CalculatorPopupNode(nodes.General, nodes.Element):
    pass


class CalculatorPopupDirective(SphinxDirective):
    required_arguments = 0
    optional_arguments = 2
    has_content = False
    option_spec = {
        "width": directives.positive_int,
        "height": directives.positive_int,
        "button-text": directives.unchanged,
        "title": directives.unchanged,
        "layout": lambda value: directives.choice(value, ("inline", "sidebar")),
        "name": directives.unchanged,
    }

    def run(self):
        try:
            width = self.options.get("width", int(self.arguments[0]) if self.arguments else 390)
            height = self.options.get("height", int(self.arguments[1]) if len(self.arguments) > 1 else 850)
        except ValueError:
            raise self.error("Calculator width and height must be positive integers.")
        if width < 280 or height < 400:
            raise self.error("Calculator width must be at least 280 and height at least 400 pixels.")
        serial = self.env.new_serialno("calculator-popup")
        identity = f"{self.env.docname}:{self.options.get('name', serial)}"
        cid = "cw-" + sha256(identity.encode()).hexdigest()[:16]
        node = CalculatorPopupNode(
            "", cid=cid, width=width, height=height,
            label=self.options.get("button-text", "Åpne kalkulator"),
            title=self.options.get("title", "Kalkulator · fx-82CW"),
            layout=self.options.get("layout", "inline"),
        )
        self.set_source_info(node)
        self.add_name(node)
        return [node]


def visit_html(self, node):
    docname = self.builder.current_docname
    target = self.builder.get_target_uri(docname)
    url = relative_uri(target, "_static/munchboka/calculator/index.html")
    cid = node["cid"]
    self.body.append(
        f'<div class="cw-popup-launch cw-popup-{node["layout"]}">'
        f'<button type="button" class="cw-popup-button" aria-haspopup="dialog" '
        f'aria-controls="{cid}" aria-expanded="false" '
        f'data-cw-id="{cid}" data-cw-src="{escape(url, quote=True)}" '
        f'data-cw-width="{node["width"]}" data-cw-height="{node["height"]}" '
        f'data-cw-title="{escape(node["title"], quote=True)}">'
        f'{escape(node["label"])}</button>'
        f'<noscript><a href="{escape(url, quote=True)}">Kalkulator (krever JavaScript)</a></noscript>'
        '</div>'
    )
    raise nodes.SkipNode


def visit_text(self, node):
    self.add_text(f'[{node["label"]}: CW-style scientific calculator]')
    raise nodes.SkipNode


def skip(self, node):
    raise nodes.SkipNode


def copy_assets(app):
    if app.builder.format != "html":
        return
    static = Path(__file__).resolve().parents[1] / "static"
    target = Path(app.outdir) / "_static" / "munchboka"
    # Also support loading this extension on its own, without the umbrella package.
    shutil.copytree(static / "calculator", target / "calculator", dirs_exist_ok=True)
    for relative in ("js/calculator_popup.js", "css/calculator_popup.css"):
        dest = target / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(static / relative, dest)


def setup(app):
    app.add_node(CalculatorPopupNode, html=(visit_html, None), text=(visit_text, None),
                 latex=(skip, None), man=(skip, None), texinfo=(skip, None))
    app.add_directive("calculator-popup", CalculatorPopupDirective)
    app.add_css_file("munchboka/css/calculator_popup.css")
    app.add_js_file("munchboka/js/calculator_popup.js")
    app.connect("builder-inited", copy_assets)
    return {"version": "1.0", "parallel_read_safe": True, "parallel_write_safe": True}
