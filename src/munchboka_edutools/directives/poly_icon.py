"""
Polynomial Icon Role for Munchboka Edutools
===========================================

This module provides a custom inline role for displaying polynomial/cubic function
icons in Sphinx documentation. It's designed for mathematical content where you need
to refer to cubic function shapes visually.

Usage in MyST Markdown:
    {poly-icon}`cubicup`
    {poly-icon}`cubicdown`
    {poly-icon}`smile`
    {poly-icon}`frown`

Available Icons:
    - cubicup: Cubic function going up (standard cubic)
    - cubicdown: Cubic function going down (negative cubic)
    - smile: Positive quadratic (parabola opening up)
    - frown: Negative quadratic (parabola opening down)

The icons are displayed inline with the text and adapt to the current theme
(light/dark mode). They use the .inline-image class for consistent styling.

Author: René Aasen (ported from matematikk_r1)
Date: November 2025
"""

from docutils import nodes
from docutils.parsers.rst import roles


def poly_icon_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    """
    Custom role for polynomial/cubic function icons.
    
    Args:
        name: The role name used in the document
        rawtext: The entire role markup string
        text: The icon name (e.g., 'cubicup', 'smile')
        lineno: Line number where the role appears
        inliner: The inliner instance
        options: Dictionary of directive options
        content: List of strings, the content of the role
        
    Returns:
        tuple: (list of nodes, list of system messages)
        
    Example:
        Input: {poly-icon}`cubicup`
        Output: <img src="/_static/munchboka/icons/polyicons/cubicup.svg" 
                     alt="Cubic cubicup icon" class="inline-image">
    """
    # Clean up the icon name (remove any extra whitespace)
    icon_name = text.strip()

    # Build the image path relative to the source directory
    # Note: Using /_static/munchboka/ path structure for built HTML
    img_src = f"/_static/munchboka/icons/polyicons/{icon_name}.svg"

    # Create a proper image node that Sphinx can process
    node = nodes.image(uri=img_src, alt=f"Cubic {icon_name} icon")

    # Add the inline-image class for consistent styling
    # (defined in figures.css with theme-aware styling)
    node["classes"] = ["inline-image"]

    return [node], []


def setup(app):
    """
    Setup function to register the role with Sphinx.
    
    This function is called automatically by Sphinx when the extension is loaded.
    It registers the poly-icon role for use in documentation.
    
    Args:
        app: The Sphinx application instance
        
    Returns:
        dict: Extension metadata including version and parallel processing flags
    """
    # Register the role with both hyphenated and unhyphenated names for compatibility
    roles.register_local_role("poly-icon", poly_icon_role)
    roles.register_local_role("polyicon", poly_icon_role)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
