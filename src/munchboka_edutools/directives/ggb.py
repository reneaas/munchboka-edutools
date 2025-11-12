"""
GeoGebra Directive for Munchboka Edutools
=========================================

This directive embeds interactive GeoGebra applets in the documentation.
It uses the GeoGebra API to create fully functional mathematics tools
directly in the browser.

Usage in MyST Markdown:
    ```{ggb} 720 600
    :material_id: abcdef123
    :toolbar: true
    :menubar: true
    :algebra: true
    ```

Or with defaults (empty applet):
    ```{ggb} 800 600
    ```

Or with perspective:
    ```{ggb} 720 600
    :material_id: xyz789
    :perspective: graphing
    ```

Features:
    - Embed existing GeoGebra materials by ID
    - Configure toolbar, menubar, and algebra view visibility
    - Set custom dimensions (width × height)
    - Multiple perspective options (graphing, geometry, 3d, etc.)
    - Automatic fullscreen and reset buttons
    - Norwegian language interface

Arguments:
    width (optional): Width in pixels (default: 720)
    height (optional): Height in pixels (default: 600)

Options:
    material_id (optional): GeoGebra material ID to load
    toolbar (optional): Show toolbar ("true"/"false", default: "false")
    menubar (optional): Show menubar ("true"/"false", default: "false")
    algebra (optional): Show algebra view ("true"/"false", default: "false")
    perspective (optional): Perspective to use (e.g., "graphing", "geometry", "3d")

Dependencies:
    - GeoGebra API: Loaded via deployggb.js (already registered in __init__.py)
    - geogebra-setup.js: Theme management and initialization

Author: René Aasen (ported from matematikk_r1)
Date: November 2025
"""

from docutils import nodes
from sphinx.util.docutils import SphinxDirective
from docutils.parsers.rst import directives
import uuid


class GGBDirective(SphinxDirective):
    """
    Sphinx directive for embedding interactive GeoGebra applets.

    This directive creates a container div and uses the GeoGebra API
    (deployggb.js) to inject an interactive mathematics applet.

    Arguments:
        width (optional): Width in pixels (default: 720)
        height (optional): Height in pixels (default: 600)

    Options:
        material_id: GeoGebra material ID (e.g., from geogebra.org/m/xyz)
        toolbar: Show toolbar ("true"/"false")
        menubar: Show menubar ("true"/"false")
        algebra: Show algebra view ("true"/"false")
        perspective: Perspective to use ("graphing", "geometry", "3d", etc.)

    Examples:
        Embed a specific GeoGebra material:
        ```{ggb} 720 600
        :material_id: abcdef123
        :toolbar: true
        :menubar: true
        :algebra: true
        ```

        Create an empty applet:
        ```{ggb} 800 600
        ```

        Use a specific perspective:
        ```{ggb} 720 600
        :material_id: xyz789
        :perspective: graphing
        ```
    """

    required_arguments = 0
    optional_arguments = 2  # width and height
    has_content = False

    option_spec = {
        "material_id": directives.unchanged,
        "toolbar": directives.unchanged,
        "menubar": directives.unchanged,
        "algebra": directives.unchanged,
        "perspective": directives.unchanged,
    }

    def run(self):
        """
        Generate the HTML for the GeoGebra applet.

        Returns:
            list: List of docutils nodes (raw HTML node)
        """
        # Convert arguments to integers (with defaults if conversion fails)
        try:
            width = int(self.arguments[0])
        except (IndexError, ValueError):
            width = 720
        try:
            height = int(self.arguments[1])
        except (IndexError, ValueError):
            height = 600

        # Get options
        material_id = self.options.get("material_id", None)
        toolbar = self.options.get("toolbar", "false")
        menubar = self.options.get("menubar", "false")
        algebra = self.options.get("algebra", "false")
        perspective = self.options.get("perspective", None)

        # Format perspective option
        if perspective:
            perspective_option = f"perspective: '{perspective}'"
        else:
            perspective_option = "'': ''"

        # Format material_id option
        if material_id:
            material_id_option = f"material_id: '{material_id}'"
        else:
            # If no material_id is provided, enable all controls by default
            # This creates an empty applet with full functionality
            material_id_option = "'': ''"
            toolbar = "true"
            menubar = "true"
            algebra = "true"

        # Generate a unique container ID using a short UUID
        container_id = f"ggb-cas-{uuid.uuid4().hex[:8]}"

        # Create the raw HTML
        # Note: GeoGebra API (deployggb.js) is already loaded via __init__.py
        html = f"""
<div id="{container_id}" style="width: {width}px; height: {height}px;" class="ggb-window"></div>
<script>
document.addEventListener("DOMContentLoaded", function() {{
    var options = {{
        appName: 'classic',
        width: {width},
        height: {height},
        showToolBar: {toolbar},
        showAlgebraInput: {algebra},
        showMenuBar: {menubar},
        language: 'nb',
        borderRadius: 8,
        borderColor: '#000000',
        showFullscreenButton: true,
        showResetIcon: true,
        scale: 1,
        rounding: 2,
        showKeyboardOnFocus: false,
        preventFocus: true,
        id: '{container_id}',
        {material_id_option},
        {perspective_option},
    }};

    var applet = new GGBApplet(options, true);
    applet.inject('{container_id}');
}});
</script>
        """

        return [nodes.raw("", html, format="html")]


def setup(app):
    """
    Setup function to register the directive with Sphinx.

    This function is called automatically by Sphinx when the extension is loaded.
    It registers the 'ggb' directive for use in documentation.

    Args:
        app: The Sphinx application instance

    Returns:
        dict: Extension metadata including version and parallel processing flags
    """
    app.add_directive("ggb", GGBDirective)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
