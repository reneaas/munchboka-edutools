"""
Clear Directive for Munchboka Edutools
======================================

This directive inserts a CSS clear:both element to clear floating elements.
Useful after floated images or other content to ensure proper layout flow.

Usage in MyST Markdown:
    ```{clear}
    ```

Purpose:
    The clear directive is commonly used in web layouts to clear CSS floats.
    When you have floated elements (like images with float:left or float:right),
    subsequent content can wrap around them. The clear directive ensures that
    content after it starts on a new line below all floated elements.

Common Use Cases:
    - After floating images to prevent text wrapping
    - Between sections to ensure proper spacing
    - To reset layout flow after floated elements

Features:
    - No arguments or options needed
    - Simply inserts a clearing div
    - Works with all CSS float properties

Example:
    ![Floating Image](image.png){.float-left}

    Some text that wraps around the image...

    ```{clear}
    ```

    This text starts below the image, not wrapped around it.

Author: René Aasen (ported from matematikk_r1)
Date: November 2025
"""

from docutils import nodes
from docutils.parsers.rst import Directive


class ClearDirective(Directive):
    """
    Sphinx directive for clearing CSS floats.

    This directive inserts a div with `clear: both` CSS property,
    which forces content to start below any floated elements.

    Arguments:
        None

    Options:
        None

    Example:
        After a floated image:
        ```{clear}
        ```

        Or between sections:
        ```{clear}
        ```
    """

    has_content = False
    required_arguments = 0
    optional_arguments = 0

    def run(self):
        """
        Generate the HTML for the clear element.

        Returns:
            list: List of docutils nodes (raw HTML node with clear div)
        """
        html = '<div style="clear: both;"></div>'
        return [nodes.raw("", html, format="html")]


def setup(app):
    """
    Setup function to register the directive with Sphinx.

    This function is called automatically by Sphinx when the extension is loaded.
    It registers the 'clear' directive for use in documentation.

    Args:
        app: The Sphinx application instance

    Returns:
        dict: Extension metadata including version and parallel processing flags
    """
    app.add_directive("clear", ClearDirective)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
