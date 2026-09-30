"""Natural-height cards laid out independently in responsive columns."""

import re
import shutil
from pathlib import Path
from typing import ClassVar

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective


def columns_option(value):
    values = value.split()
    if len(values) not in (1, 3) or any(not v.isdecimal() or not 1 <= int(v) <= 12 for v in values):
        raise ValueError("columns must contain one or three integers between 1 and 12")
    return " ".join(str(int(v)) for v in values)


def gap_option(value):
    value = value.strip()
    if not re.fullmatch(r"(?:0|(?:\d+(?:\.\d+)?|\.\d+)(?:px|rem|em))", value):
        raise ValueError("gap must be a nonnegative length in px, rem or em (or 0)")
    return value


class MasonryNode(nodes.container):
    pass


class MasonryDirective(SphinxDirective):
    has_content = True
    option_spec: ClassVar[dict] = {
        "columns": columns_option,
        "gap": gap_option,
        "placement": lambda value: directives.choice(value, ("shortest", "alternating")),
        "class": directives.class_option,
        "name": directives.unchanged,
    }

    def run(self):
        node = MasonryNode(classes=["mb-masonry", *self.options.get("class", [])])
        node["columns"] = self.options.get("columns", "1 2 3")
        node["gap"] = self.options.get("gap", "1rem")
        node["placement"] = self.options.get("placement", "shortest")
        self.set_source_info(node)
        self.add_name(node)
        self.state.nested_parse(self.content, self.content_offset, node)
        for child in node.children:
            if isinstance(child, nodes.system_message):
                continue
            if "mb-masonry-card" not in child.get("classes", []):
                raise self.error("masonry accepts only masonry-card directives as direct children")
        return [node]


class MasonryCardDirective(SphinxDirective):
    has_content = True
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec: ClassVar[dict] = {"class": directives.class_option, "name": directives.unchanged}

    def run(self):
        card = nodes.container(classes=["mb-masonry-card", *self.options.get("class", [])])
        self.set_source_info(card)
        self.add_name(card)
        messages = []
        if self.arguments:
            title = nodes.rubric(classes=["mb-masonry-title"])
            title_nodes, messages = self.state.inline_text(self.arguments[0], self.lineno)
            title.extend(title_nodes)
            card += title
        body = nodes.container(classes=["mb-masonry-body"])
        self.state.nested_parse(self.content, self.content_offset, body)
        card += body
        return [card, *messages]


def visit_html(self, node):
    self.body.append(
        self.starttag(
            node,
            "div",
            **{
                "data-columns": node["columns"],
                "data-placement": node["placement"],
                "style": f"--mb-masonry-gap: {node['gap']}",
            },
        )
    )


def depart_html(self, node):
    self.body.append("</div>\n")


def visit_container(self, node):
    self.visit_container(node)


def depart_container(self, node):
    self.depart_container(node)


def copy_assets(app):
    if app.builder.format != "html":
        return
    static = Path(__file__).resolve().parents[1] / "static"
    target = Path(app.outdir) / "_static" / "munchboka"
    for relative in ("css/masonry.css", "js/masonry.js"):
        dest = target / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(static / relative, dest)


def setup(app):
    fallback = (visit_container, depart_container)
    app.add_node(
        MasonryNode,
        html=(visit_html, depart_html),
        text=fallback,
        latex=fallback,
        man=fallback,
        texinfo=fallback,
    )
    app.add_directive("masonry", MasonryDirective)
    app.add_directive("masonry-card", MasonryCardDirective)
    app.add_css_file("munchboka/css/masonry.css")
    app.add_js_file("munchboka/js/masonry.js", defer="defer")
    app.connect("builder-inited", copy_assets)
    return {"version": "1.0", "parallel_read_safe": True, "parallel_write_safe": True}
