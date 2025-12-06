"""
multi-plot2 directive: A container directive that arranges multiple plot directives in a grid.

Usage:
    ::::{multi-plot2}
    ---
    rows: 2
    cols: 2
    width: 100%
    align: center
    ---

    :::{plot}
    function: x**2, f
    :::

    :::{plot}
    function: x**3, g
    :::

    ::::

The directive creates a grid layout and renders each nested plot directive in order (row-major).
"""

import re
from typing import Any, Dict, List

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective


class MultiPlot2Directive(SphinxDirective):
    """Container directive that arranges multiple plot directives in a grid layout."""

    has_content = True
    required_arguments = 0
    option_spec = {
        "rows": directives.positive_int,
        "cols": directives.positive_int,
        "width": directives.length_or_percentage_or_unitless,
        "align": lambda a: directives.choice(a, ["left", "center", "right"]),
        "class": directives.class_option,
        "name": directives.unchanged,
    }

    def run(self) -> List[nodes.Node]:
        """Process the multi-plot2 directive."""

        # Get options with defaults
        rows = self.options.get("rows", 1)
        cols = self.options.get("cols", 1)
        width = self.options.get("width", "100%")
        align = self.options.get("align", "center")

        # Expected number of plot directives
        expected_plots = rows * cols

        # Simply let Sphinx parse the nested content normally
        # This will create all the plot directive nodes
        container = nodes.container()
        container["classes"].append("multi-plot2-container")

        # Add custom CSS class if provided
        if "class" in self.options:
            container["classes"].extend(self.options["class"])

        # Parse all nested content
        self.state.nested_parse(self.content, self.content_offset, container)

        # Count how many plot figures we got
        plot_count = sum(1 for child in container.traverse(nodes.figure))

        # Warn if count doesn't match
        if plot_count != expected_plots:
            warning = self.state_machine.reporter.warning(
                f"multi-plot2: Expected {expected_plots} plot directives "
                f"({rows}×{cols}), but found {plot_count}",
                line=self.lineno,
            )
            return [warning, container]

        # Wrap the container in a div with CSS grid styling
        grid_style = (
            f"display: grid; "
            f"grid-template-columns: repeat({cols}, 1fr); "
            f"grid-template-rows: repeat({rows}, auto); "
            f"gap: 0; "
            f"width: {width}; "
        )

        if align == "center":
            grid_style += "margin-left: auto; margin-right: auto; "
        elif align == "left":
            grid_style += "margin-right: auto; "
        elif align == "right":
            grid_style += "margin-left: auto; "

        # Create wrapper with inline styles
        wrapper = nodes.container()
        wrapper["classes"].append("multi-plot2-grid")

        # Add CSS to constrain child figures/SVGs to grid cells
        # This ensures plots without explicit width fit properly
        css_node = nodes.raw(
            "",
            """<style>
.multi-plot2-grid { }
.multi-plot2-grid > * { max-width: 100%; }
.multi-plot2-grid figure { margin: 0; max-width: 100%; }
.multi-plot2-grid svg { max-width: 100%; height: auto; }
</style>""",
            format="html",
        )

        # Add raw HTML opening
        raw_open = nodes.raw(
            "", f'<div class="multi-plot2-grid" style="{grid_style}">', format="html"
        )

        # Add raw HTML closing
        raw_close = nodes.raw("", "</div>", format="html")

        # Build result: open tag, content, close tag
        result_container = nodes.container()
        result_container.append(css_node)
        result_container.append(raw_open)
        result_container.extend(container.children)
        result_container.append(raw_close)

        return [result_container]


def setup(app: Sphinx) -> Dict[str, Any]:
    """Register the multi-plot2 directive."""
    app.add_directive("multi-plot2", MultiPlot2Directive)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
