"""
Part Directive
==============

A directive for sub-parts of a problem or exercise, styled with a colored
left stripe and a label (e.g. "a)") sitting to the left of the content.
Parts labelled "a" start expanded; all others start collapsed.

Usage:
    :::{part} a
    Problem text in here.
    :::

    :::{part} b
    Another part with nested directives.

    :::{plot}
    :function: x**2
    :::
    :::
"""

from docutils import nodes
from sphinx.util.docutils import SphinxDirective


class PartDirective(SphinxDirective):
    """
    Part directive for labelled sub-parts of a problem.

    The argument is the label letter/number (e.g. ``a``, ``b``, ``1``).
    Parts labelled ``a`` are open by default; all other labels start collapsed
    behind a "Vis oppgaven" toggle button.
    """

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False

    def run(self):
        label_raw = self.arguments[0].strip()
        label_text = label_raw + ")"
        is_open = label_raw.lower() == "a"

        # Outer wrapper — flex column card
        outer = nodes.container()
        outer["classes"] = ["part"]
        if is_open:
            outer["classes"].append("part-open")

        # Header row: label column + toggle button
        header = nodes.container()
        header["classes"] = ["part-header"]

        label_node = nodes.container()
        label_node["classes"] = ["part-label"]
        label_node += nodes.Text(label_text)
        header += label_node

        toggle_text = "Skjul oppgaven" if is_open else "Vis oppgaven"
        toggle_html = (
            f'<button class="part-toggle"'
            f' data-open="Skjul oppgaven"'
            f' data-closed="Vis oppgaven">'
            f'{toggle_text}'
            f'</button>'
        )
        header += nodes.raw("", toggle_html, format="html")
        outer += header

        # Body column — nested_parse so any directive works inside
        body = nodes.container()
        body["classes"] = ["part-body"]
        self.state.nested_parse(self.content, self.content_offset, body)
        outer += body

        return [outer]


def setup(app):
    app.add_directive("part", PartDirective)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
