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
        # Grid layout options
        "rows": directives.positive_int,
        "cols": directives.positive_int,
        "width": directives.length_or_percentage_or_unitless,
        "align": lambda a: directives.choice(a, ["left", "center", "right"]),
        "class": directives.class_option,
        "name": directives.unchanged,
        # Plot directive options that cascade to children
        "xmin": directives.unchanged,
        "xmax": directives.unchanged,
        "ymin": directives.unchanged,
        "ymax": directives.unchanged,
        "xstep": directives.unchanged,
        "ystep": directives.unchanged,
        "fontsize": directives.unchanged,
        "ticks": directives.unchanged,
        "grid": directives.unchanged,
        "xticks": directives.unchanged,
        "yticks": directives.unchanged,
        "lw": directives.unchanged,
        "alpha": directives.unchanged,
        "figsize": directives.unchanged,
        "xlabel": directives.unchanged,
        "ylabel": directives.unchanged,
        "usetex": directives.unchanged,
        "axis": directives.unchanged,
        "alt": directives.unchanged,
        "nocache": directives.flag,
        "debug": directives.flag,
    }

    def run(self) -> List[nodes.Node]:
        """Process the multi-plot2 directive."""

        # Grid layout options
        grid_options = {"rows", "cols", "width", "align", "class", "name"}

        # Get options with defaults
        rows = self.options.get("rows", 1)
        cols = self.options.get("cols", 1)
        width = self.options.get("width", "100%")
        align = self.options.get("align", "center")

        # Expected number of plot directives
        expected_plots = rows * cols

        # Collect plot options to cascade to children (exclude grid layout options)
        plot_defaults = {k: v for k, v in self.options.items() if k not in grid_options}

        # Inject default options into child plot directives
        modified_content = self._inject_plot_defaults(self.content, plot_defaults)

        # Simply let Sphinx parse the nested content normally
        # This will create all the plot directive nodes
        container = nodes.container()
        container["classes"].append("multi-plot2-container")

        # Add custom CSS class if provided
        if "class" in self.options:
            container["classes"].extend(self.options["class"])

        # Parse all nested content with injected defaults
        self.state.nested_parse(modified_content, self.content_offset, container)

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

    def _inject_plot_defaults(self, content, plot_defaults):
        """
        Inject default plot options into child plot directives.

        This method parses the content to find plot directives and adds
        default options to them, but only if those options are not already
        specified in the individual plot directive.

        Args:
            content: StringList of directive content
            plot_defaults: Dict of default options to inject

        Returns:
            Modified StringList with injected defaults
        """
        from docutils.statemachine import StringList

        if not plot_defaults:
            return content

        new_lines = []
        i = 0
        while i < len(content):
            line = content[i]

            # Check if this line starts a plot directive
            if re.match(r"^\s*:::\{plot\}\s*$", line):
                new_lines.append(line)
                i += 1

                # Collect existing options in this plot directive
                existing_options = set()
                plot_content_start = i

                # Scan ahead to find what options are already defined
                while i < len(content):
                    next_line = content[i]
                    # Stop if we hit the closing ::: or another directive
                    if re.match(r"^\s*:::\s*$", next_line) or re.match(r"^\s*:::\{", next_line):
                        break
                    # Extract option name from lines like "xmin: -4" or "function: x**2"
                    option_match = re.match(r"^\s*(\w+):\s*", next_line)
                    if option_match:
                        existing_options.add(option_match.group(1))
                    i += 1

                # Now inject defaults that aren't already present
                # We need to insert them right after the directive opening
                defaults_to_inject = []
                for key, value in plot_defaults.items():
                    if key not in existing_options:
                        # Format the option line based on value type
                        if isinstance(value, bool):
                            # For flags like nocache, debug
                            continue  # Flags are handled differently, skip for now
                        else:
                            defaults_to_inject.append(f"{key}: {value}")

                # Insert the defaults at the beginning of plot content
                for default_line in defaults_to_inject:
                    new_lines.append(default_line)

                # Now add the original plot content
                for j in range(plot_content_start, i):
                    new_lines.append(content[j])
            else:
                new_lines.append(line)
                i += 1

        # Convert back to StringList with proper source tracking
        result = StringList()
        for line in new_lines:
            result.append(line, source="<multi-plot2>")

        return result


def setup(app: Sphinx) -> Dict[str, Any]:
    """Register the multi-plot2 directive."""
    app.add_directive("multi-plot2", MultiPlot2Directive)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
