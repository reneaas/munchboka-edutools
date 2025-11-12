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


def ggb_icon_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    """
    Custom role for GeoGebra icons.

    Usage: {ggb-icon}`mode_intersect`

    This generates an inline image using raw HTML to avoid path resolution issues.
    """
    # Clean up the icon name (remove any extra whitespace)
    icon_name = text.strip()

    # Build the image path - use absolute path from site root
    img_src = f"/_static/munchboka/icons/ggb/{icon_name}.svg"

    # Create raw HTML node instead of image node to avoid Sphinx path processing
    html = f'<img src="{img_src}" alt="GeoGebra {icon_name} icon" class="inline-image" />'
    node = nodes.raw("", html, format="html")

    return [node], []


def setup(app):
    """Setup function to register the role with Sphinx."""
    # Register the role with both hyphenated and unhyphenated names
    roles.register_local_role("ggb-icon", ggb_icon_role)
    roles.register_local_role("ggbicon", ggb_icon_role)

    return {
        "version": "0.1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
