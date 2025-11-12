"""
GeoGebra icon role for inline SVG icons.

This role allows you to insert GeoGebra tool icons inline in text.
The icons are SVG files that represent various GeoGebra tools and modes.

Usage:
    This is the {ggb-icon}`mode_intersect` tool in GeoGebra.

    Click the {ggb-icon}`mode_solve` icon to solve equations.

Available icons:
    - mode_evaluate: Evaluate/compute icon
    - mode_extremum: Find extremum (min/max) icon
    - mode_intersect: Find intersection point icon
    - mode_nsolve: Numeric solve icon
    - mode_numeric: Numeric computation icon
    - mode_point: Point tool icon
    - mode_solve: Symbolic solve icon

The icons are rendered as inline images with appropriate alt text.
"""

from docutils import nodes
from docutils.parsers.rst import roles
from sphinx.util.osutil import relative_uri


# Custom node for GeoGebra icons
class ggb_icon_node(nodes.Inline, nodes.Element):
    """Custom node for GeoGebra icons."""

    pass


def ggb_icon_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    """
    Custom role for GeoGebra icons.

    Usage: {ggb-icon}`mode_intersect`

    This generates a custom node that will be rendered with relative paths.
    """
    # Clean up the icon name (remove any extra whitespace)
    icon_name = text.strip()

    # Create our custom node
    node = ggb_icon_node()
    node["icon_name"] = icon_name
    node["classes"] = ["inline-image"]

    return [node], []


def visit_ggb_icon_html(self, node):
    """HTML visitor for ggb_icon_node - generates relative path."""
    icon_name = node["icon_name"]

    # Get the relative path from current document to _static directory
    # self.builder.current_docname is like "examples/ggb_icon"
    # We want path from there to ../static/munchboka/icons/ggb/
    from os.path import relpath, dirname, join

    # Current document directory depth
    doc_dir = dirname(self.builder.current_docname) if "/" in self.builder.current_docname else ""

    # Calculate relative path
    if doc_dir:
        # For documents in subdirectories like "examples/ggb_icon"
        depth = doc_dir.count("/") + 1
        rel_prefix = "../" * depth
    else:
        # For top-level documents
        rel_prefix = ""

    img_path = f"{rel_prefix}_static/munchboka/icons/ggb/{icon_name}.svg"

    # Generate the HTML with relative path
    html = f'<img src="{img_path}" alt="GeoGebra {icon_name} icon" class="inline-image" />'
    self.body.append(html)
    raise nodes.SkipNode


def depart_ggb_icon_html(self, node):
    """Depart function (not needed as we raise SkipNode)."""
    pass


def setup(app):
    """Setup function to register the role with Sphinx."""
    # Register the custom node
    app.add_node(
        ggb_icon_node,
        html=(visit_ggb_icon_html, depart_ggb_icon_html),
    )

    # Register the role with both hyphenated and unhyphenated names
    roles.register_local_role("ggb-icon", ggb_icon_role)
    roles.register_local_role("ggbicon", ggb_icon_role)

    return {
        "version": "0.1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
