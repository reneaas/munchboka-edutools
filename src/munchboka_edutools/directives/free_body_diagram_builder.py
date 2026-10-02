"""An interactive, in-browser builder for composing `free-body-diagram`-style figures.

Lets an author set up an object (ball/square/toy-car), an optional velocity,
and one or more forces (with the same kinds/defaults as the real
`free-body-diagram` directive), then download the resulting sketch as an SVG.
Rendering happens entirely client-side via the vendored JSXGraph library, so
this directive does not delegate to `free-body-diagram`/matplotlib and its
visual style is only an approximation of the real directive's output.
"""
from hashlib import sha256
from pathlib import Path
import shutil

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective
from sphinx.util.osutil import relative_uri


class FreeBodyDiagramBuilderNode(nodes.General, nodes.Element):
    pass


class FreeBodyDiagramBuilderDirective(SphinxDirective):
    required_arguments = 0
    optional_arguments = 0
    has_content = False
    option_spec = {
        "width": directives.unchanged,
        "height": directives.positive_int,
        "name": directives.unchanged,
    }

    def run(self):
        serial = self.env.new_serialno("free-body-diagram-builder")
        identity = f"{self.env.docname}:{self.options.get('name', serial)}"
        pid = "fbd-builder-" + sha256(identity.encode()).hexdigest()[:12]

        pages = self.env.temp_data.setdefault("fbd_builder_pages", set())
        first_on_page = self.env.docname not in pages
        pages.add(self.env.docname)

        node = FreeBodyDiagramBuilderNode(
            "",
            pid=pid,
            width=self.options.get("width", "640px"),
            height=self.options.get("height", 480),
            first_on_page=first_on_page,
        )
        self.set_source_info(node)
        self.add_name(node)
        return [node]


def visit_html(self, node):
    docname = self.builder.current_docname
    target = self.builder.get_target_uri(docname)

    def asset_url(relative):
        return relative_uri(target, f"_static/munchboka/{relative}")

    if node["first_on_page"]:
        self.body.append(
            f'<link rel="stylesheet" href="{asset_url("vendor/katex/dist/katex.min.css")}">'
            f'<script src="{asset_url("vendor/katex/dist/katex.min.js")}"></script>'
            f'<link rel="stylesheet" href="{asset_url("vendor/jsxgraph/jsxgraph.css")}">'
            f'<script src="{asset_url("vendor/jsxgraph/jsxgraphcore.js")}"></script>'
            f'<link rel="stylesheet" href="{asset_url("css/free_body_diagram_builder.css")}">'
        )
    self.body.append(
        f'<div class="munch-fbd-builder" id="{node["pid"]}" '
        f'data-board-width="{node["width"]}" data-board-height="{node["height"]}">'
        '<noscript>Denne interaktive figurbyggeren krever JavaScript.</noscript>'
        '</div>'
    )
    if node["first_on_page"]:
        self.body.append(f'<script src="{asset_url("js/free_body_diagram_builder.js")}"></script>')
    raise nodes.SkipNode


def visit_text(self, node):
    self.add_text("[Interaktiv figurbygger: krever JavaScript]")
    raise nodes.SkipNode


def skip(self, node):
    raise nodes.SkipNode


def copy_assets(app):
    if app.builder.format != "html":
        return
    static = Path(__file__).resolve().parents[1] / "static"
    target = Path(app.outdir) / "_static" / "munchboka"
    for relative in ("css/free_body_diagram_builder.css", "js/free_body_diagram_builder.js"):
        dest = target / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(static / relative, dest)
    for vendor in ("jsxgraph", "katex", "mathjax-fbd"):
        vendor_src = static / "vendor" / vendor
        if vendor_src.is_dir():
            shutil.copytree(vendor_src, target / "vendor" / vendor, dirs_exist_ok=True)


def setup(app):
    app.add_node(FreeBodyDiagramBuilderNode, html=(visit_html, None), text=(visit_text, None),
                 latex=(skip, None), man=(skip, None), texinfo=(skip, None))
    app.add_directive("free-body-diagram-builder", FreeBodyDiagramBuilderDirective)
    app.connect("builder-inited", copy_assets)
    return {"version": "1.0", "parallel_read_safe": True, "parallel_write_safe": True}
