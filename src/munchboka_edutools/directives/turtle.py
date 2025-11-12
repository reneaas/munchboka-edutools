"""
Turtle Graphics Directive for Munchboka Edutools
================================================

This directive creates an interactive Python turtle graphics environment where
students can write and execute turtle code directly in the browser.

Usage in MyST Markdown:
    ```{turtle}
    import turtle

    t = turtle.Turtle()
    t.forward(100)
    t.right(90)
    t.forward(100)
    ```

Or with custom identifier:
    ```{turtle} my-turtle-1
    import turtle

    for i in range(4):
        turtle.forward(100)
        turtle.right(90)
    ```

Features:
    - Live code editor with syntax highlighting (CodeMirror)
    - Immediate execution with "Run" button
    - Visual turtle graphics canvas
    - Full Python turtle module support (via Skulpt)
    - Automatic canvas setup and coordinate system
    - Error display in output area

Dependencies:
    - CodeMirror: Code editor with Python syntax highlighting
    - Skulpt: Python-in-browser implementation
    - turtleCode.js: Turtle graphics environment setup
    - CodeEditor class: Interactive code editing

Author: René Aasen (ported from matematikk_r1)
Date: November 2025
"""

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from sphinx.util.docutils import SphinxDirective
import uuid


class TurtleDirective(SphinxDirective):
    """
    Sphinx directive for embedding interactive turtle graphics code.

    This directive creates a side-by-side layout with a code editor on the left
    and a turtle graphics canvas on the right. Students can write turtle code
    and see the results immediately.

    Arguments:
        identifier (optional): Custom identifier for the turtle environment.
                              If not provided, a unique ID is generated.

    Options:
        width (optional): Width of the container (not commonly used)
        height (optional): Height of the container (not commonly used)

    Example:
        ```{turtle}
        import turtle

        t = turtle.Turtle()
        t.color('blue')
        t.forward(100)
        t.left(120)
        t.forward(100)
        t.left(120)
        t.forward(100)
        ```

        Or with identifier:

        ```{turtle} drawing-square
        import turtle

        for i in range(4):
            turtle.forward(100)
            turtle.right(90)
        ```
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 1  # Optional identifier
    final_argument_whitespace = True
    option_spec = {
        "width": directives.unchanged,
        "height": directives.unchanged,
    }

    def run(self):
        """
        Generate the HTML for the turtle graphics environment.

        Returns:
            list: List of docutils nodes (raw HTML node)
        """
        # Generate a unique ID or use the provided one
        if self.arguments:
            identifier = self.arguments[0].replace(" ", "-").lower()
        else:
            identifier = f"turtle-{uuid.uuid4().hex[:8]}"

        container_id = f"container-kode-{identifier}"

        # Get the code content
        code_content = "\n".join(self.content)

        # Escape backticks and dollar signs for JavaScript template literals
        escaped_code = code_content.replace("`", "\\`").replace("$", "\\$")

        # Create the HTML output
        # Note: turtleCode.js and its dependencies (CodeMirror, Skulpt, CodeEditor)
        # are already loaded globally via __init__.py
        html = f"""
        <div id="{container_id}"></div>
        <script type="text/javascript">
            document.addEventListener("DOMContentLoaded", () => {{
                const code = `{escaped_code}`;
                makeTurtleCode("{container_id}", code);
            }});
        </script>
        """

        raw_node = nodes.raw("", html, format="html")
        return [raw_node]


def setup(app):
    """
    Setup function to register the directive with Sphinx.

    This function is called automatically by Sphinx when the extension is loaded.
    It registers the 'turtle' directive for use in documentation.

    Args:
        app: The Sphinx application instance

    Returns:
        dict: Extension metadata including version and parallel processing flags
    """
    app.add_directive("turtle", TurtleDirective)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
