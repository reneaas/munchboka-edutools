"""An interactive, in-browser builder for composing `plot`-style 2D figures.

Lets an author set up a coordinate system (ranges + tick spacing), add function
graphs, points, and text labels, and download the resulting figure as an SVG.
Rendering happens entirely client-side via the vendored JSXGraph library, so
this directive does not delegate to `plot`/matplotlib and its visual style is
only an approximation of the real `plot` directive's output.
"""
from hashlib import sha256
from pathlib import Path
import shutil

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective
from sphinx.util.osutil import relative_uri


class PlotBuilderNode(nodes.General, nodes.Element):
    pass


class PlotBuilderDirective(SphinxDirective):
    required_arguments = 0
    optional_arguments = 0
    has_content = False
    option_spec = {
        "width": directives.unchanged,
        "height": directives.positive_int,
        "name": directives.unchanged,
    }

    def run(self):
        serial = self.env.new_serialno("plot-builder")
        identity = f"{self.env.docname}:{self.options.get('name', serial)}"
        pid = "plot-builder-" + sha256(identity.encode()).hexdigest()[:12]

        pages = self.env.temp_data.setdefault("plot_builder_pages", set())
        first_on_page = self.env.docname not in pages
        pages.add(self.env.docname)

        node = PlotBuilderNode(
            "",
            pid=pid,
            # Matches matplotlib's default figsize (6.4in x 4.8in) at 100 dpi.
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
            f'<link rel="stylesheet" href="{asset_url("css/plot_builder.css")}">'
        )
    self.body.append(
        f'<div class="munch-plot-builder" id="{node["pid"]}" '
        f'data-board-width="{node["width"]}" data-board-height="{node["height"]}">'
        '<noscript>Denne interaktive figurbyggeren krever JavaScript.</noscript>'
        '</div>'
    )
    if node["first_on_page"]:
        self.body.append(f'<script src="{asset_url("js/plot_builder.js")}"></script>')
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
    for relative in ("css/plot_builder.css", "js/plot_builder.js"):
        dest = target / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(static / relative, dest)
    for vendor in ("jsxgraph", "katex", "mathjax-fbd"):
        vendor_src = static / "vendor" / vendor
        if vendor_src.is_dir():
            shutil.copytree(vendor_src, target / "vendor" / vendor, dirs_exist_ok=True)


def setup(app):
    app.add_node(PlotBuilderNode, html=(visit_html, None), text=(visit_text, None),
                 latex=(skip, None), man=(skip, None), texinfo=(skip, None))
    app.add_directive("plot-builder", PlotBuilderDirective)
    app.connect("builder-inited", copy_assets)
    return {"version": "1.0", "parallel_read_safe": True, "parallel_write_safe": True}
