"""
Polynomial function shape icon role for inline SVG icons.

This role allows you to insert icons representing different polynomial function shapes.
The icons help visualize the general shape of polynomial functions.

Usage:
    A quadratic function with positive leading coefficient has a {poly-icon}`smile` shape.

    A cubic function with negative leading coefficient has a {poly-icon}`cubicdown` shape.

Available icons:
    - smile: U-shaped (parabola opening upward, like a smile)
    - frown: ∩-shaped (parabola opening downward, like a frown)
    - cubicup: Cubic function starting low and ending high (∪∩ shape)
    - cubicdown: Cubic function starting high and ending low (∩∪ shape)

The icons are rendered as inline images with appropriate alt text.
"""

from docutils import nodes
from docutils.parsers.rst import roles


# Custom node for polynomial icons
class poly_icon_node(nodes.Inline, nodes.Element):
    """Custom node for polynomial icons."""

    pass


def poly_icon_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    """
    Custom role for polynomial function shape icons.

    Usage: {poly-icon}`smile`

    This generates a custom node that will be rendered with relative paths.
    """
    # Clean up the icon name (remove any extra whitespace)
    icon_name = text.strip().lower()

    # Validate icon name
    valid_icons = ["smile", "frown", "cubicup", "cubicdown"]
    if icon_name not in valid_icons:
        msg = inliner.reporter.error(
            f'Invalid poly-icon name "{icon_name}". Must be one of: {", ".join(valid_icons)}',
            line=lineno,
        )
        prb = inliner.problematic(rawtext, rawtext, msg)
        return [prb], [msg]

    # Create our custom node
    node = poly_icon_node()
    node["icon_name"] = icon_name
    node["classes"] = ["inline-image"]

    return [node], []


def visit_poly_icon_html(self, node):
    """HTML visitor for poly_icon_node - generates relative path."""
    icon_name = node["icon_name"]

    # Get the relative path from current document to _static directory
    # self.builder.current_docname is like "examples/poly_icon"
    # We want path from there to ../_static/munchboka/icons/polyicons/
    from os.path import dirname

    # Current document directory depth
    doc_dir = dirname(self.builder.current_docname) if "/" in self.builder.current_docname else ""

    # Calculate relative path
    if doc_dir:
        # For documents in subdirectories like "examples/poly_icon"
        depth = doc_dir.count("/") + 1
        rel_prefix = "../" * depth
    else:
        # For top-level documents
        rel_prefix = ""

    img_path = f"{rel_prefix}_static/munchboka/icons/polyicons/{icon_name}.svg"

    # Generate the HTML with relative path
    html = f'<img src="{img_path}" alt="{icon_name} polynomial icon" class="inline-image" />'
    self.body.append(html)
    raise nodes.SkipNode


def depart_poly_icon_html(self, node):
    """Depart function (not needed as we raise SkipNode)."""
    pass


def setup(app):
    """Setup function to register the role with Sphinx."""
    # Register the custom node
    app.add_node(
        poly_icon_node,
        html=(visit_poly_icon_html, depart_poly_icon_html),
    )

    # Register the role with both hyphenated and unhyphenated names
    roles.register_local_role("poly-icon", poly_icon_role)
    roles.register_local_role("polyicon", poly_icon_role)

    return {
        "version": "0.1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
