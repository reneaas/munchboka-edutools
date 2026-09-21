"""Embed the optional Norwegian notebook application in Sphinx books."""

import shutil
import tempfile
from html import escape
from pathlib import Path
from typing import ClassVar
from urllib.parse import urlencode

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.errors import ExtensionError
from sphinx.util.docutils import SphinxDirective
from sphinx.util.osutil import relative_uri

from ..notebook.site import build_site

SITE = "_static/munchboka/notebook"


class NotebookNode(nodes.General, nodes.Element):
    pass


class NotebookDirective(SphinxDirective):
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True
    has_content = False
    option_spec: ClassVar[dict] = {
        "title": directives.unchanged,
        "button-text": directives.unchanged,
        "height": directives.length_or_percentage_or_unitless,
        "embed": directives.flag,
        "fullscreen": directives.flag,
        "files": directives.unchanged,
    }

    def run(self):
        root = Path(self.env.srcdir).resolve()
        source = Path(self.state.document.current_source).parent

        def resolve(value):
            path = (root / value.lstrip("/") if value.startswith("/") else source / value).resolve()
            if root not in path.parents or not path.is_file():
                raise self.error(f"Notebook-filen må finnes innenfor bokas kildemappe: {value}")
            self.env.note_dependency(str(path))
            return path.relative_to(root).as_posix()

        # No argument: embed a blank notebook, without authoring a .ipynb file.
        notebook = resolve(self.arguments[0]) if self.arguments else None
        if notebook and not notebook.lower().endswith(".ipynb"):
            raise self.error("Notebook-direktivet krever en .ipynb-fil.")
        files = [notebook] if notebook else []
        for value in self.options.get("files", "").splitlines():
            if value.strip():
                files.append(resolve(value.strip()))
        fullscreen = "fullscreen" in self.options
        if "height" in self.options:
            height = self.options["height"]
        elif fullscreen:
            # Fullscreen pages let CSS (vh units) control height instead of the
            # RST length option, which docutils rejects for "vh".
            height = None
        else:
            height = "720px"
        node = NotebookNode(
            "",
            notebook=notebook,
            title=self.options.get("title", "Notebook med Python"),
            label=self.options.get("button-text", "Åpne notebook" if notebook else "Åpne blank notebook"),
            height=height,
            embed=fullscreen or "embed" in self.options,
            fullscreen=fullscreen,
        )
        self.set_source_info(node)
        records = getattr(self.env, "munchboka_notebooks", {})
        # Registering the docname (even with an empty file list) tells
        # build_notebooks() this page needs the site built, blank notebook or not.
        records.setdefault(self.env.docname, []).extend(files)
        self.env.munchboka_notebooks = records
        return [node]


def visit_html(self, node):
    target = self.builder.get_target_uri(self.builder.current_docname)
    query = {"notebook": node["notebook"]} if node["notebook"] else {"new": "1"}
    href = relative_uri(target, SITE + "/index.html") + "?" + urlencode(query)
    url = escape(href, quote=True)
    title = escape(node["title"], quote=True)
    label = escape(node["label"])
    wrapper_class = "munchboka-notebook"
    if node["fullscreen"]:
        wrapper_class += " munchboka-notebook-fullscreen"
    self.body.append(f'<div class="{wrapper_class}">')
    if not node["embed"]:
        # Embedded notebooks carry their own "Åpne i ny fane" toolbar button.
        self.body.append(
            f'<p class="munchboka-notebook-link">'
            f'<a href="{url}" target="_blank" rel="noopener">{label}</a></p>'
        )
    if node["embed"]:
        style = "width:100%;border:1px solid #d2ded7;border-radius:8px"
        if node["height"]:
            height = node["height"]
            if height.isdigit():
                height += "px"
            style = f"width:100%;height:{escape(height)};" + style.split(';', 1)[1]
        self.body.append(
            f'<iframe class="munchboka-notebook-frame" title="{title}" '
            f'src="{url}" loading="lazy" style="{style}" '
            'allow="clipboard-read; clipboard-write"></iframe>'
        )
    self.body.append("</div>")
    raise nodes.SkipNode


def visit_text(self, node):
    self.add_text(f'{node["title"]} — {node["label"]}: {node["notebook"] or "(blank notebook)"}')
    raise nodes.SkipNode


def visit_latex(self, node):
    target = node["notebook"] or "blank notebook"
    self.body.append(self.encode(f'{node["title"]}: {target} (nettutgaven)'))
    raise nodes.SkipNode


def skip(self, node):
    raise nodes.SkipNode


def purge(app, env, docname):
    getattr(env, "munchboka_notebooks", {}).pop(docname, None)


def merge(app, env, docnames, other):
    records = getattr(env, "munchboka_notebooks", {})
    for docname in docnames:
        if docname in getattr(other, "munchboka_notebooks", {}):
            records[docname] = other.munchboka_notebooks[docname]
    env.munchboka_notebooks = records


def build_notebooks(app, exception):
    if exception or app.builder.format != "html":
        return
    records = getattr(app.env, "munchboka_notebooks", {})
    # A page can use the directive with no .ipynb (blank notebook); the site
    # must still be built even when the combined file set ends up empty.
    active = {docname for docname in records if docname in app.env.found_docs}
    if not active:
        return
    paths = sorted({path for docname in active for path in records[docname]})
    try:
        with tempfile.TemporaryDirectory(prefix="munch-notebooks-") as temporary:
            contents = Path(temporary)
            for relative in paths:
                source = (Path(app.srcdir) / relative).resolve()
                if Path(app.srcdir).resolve() not in source.parents:
                    raise ValueError(f"Filen er utenfor kildemappen: {relative}")
                destination = contents / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
            build_site(Path(app.outdir) / SITE, contents, app.config.munchboka_notebook_title)
    except (ValueError, OSError, RuntimeError) as exc:
        raise ExtensionError(f"Notebook: {exc}") from exc


def setup(app):
    app.add_config_value("munchboka_notebook_title", "Munchboka · Notebook", "html")
    app.add_node(
        NotebookNode,
        html=(visit_html, None),
        text=(visit_text, None),
        latex=(visit_latex, None),
        man=(skip, None),
        texinfo=(skip, None),
    )
    app.add_directive("notebook", NotebookDirective)
    # The umbrella extension copies static assets; standalone use needs this too.
    app.add_css_file("munchboka/css/notebook.css")
    app.connect("builder-inited", copy_css)
    app.connect("env-purge-doc", purge)
    app.connect("env-merge-info", merge)
    app.connect("build-finished", build_notebooks)
    return {"version": "1.0", "parallel_read_safe": True, "parallel_write_safe": True}


def copy_css(app):
    if app.builder.format != "html":
        return
    destination = Path(app.outdir) / "_static/munchboka/css/notebook.css"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(Path(__file__).parents[1] / "static/css/notebook.css", destination)
