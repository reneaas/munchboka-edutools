"""
Part Directive
==============

A directive for sub-parts of a problem or exercise, styled with a colored
left stripe and a label (e.g. "a)") sitting to the left of the content.

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
    It is rendered as "a)", "b)", etc. to the left of the content,
    separated by a colored vertical stripe.
    """

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False

    def run(self):
        label_text = self.arguments[0].strip() + ")"

        # Outer wrapper — carries the stripe and flex layout
        outer = nodes.container()
        outer["classes"] = ["part"]

        # Label column
        label_node = nodes.container()
        label_node["classes"] = ["part-label"]
        label_node += nodes.Text(label_text)
        outer += label_node

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
