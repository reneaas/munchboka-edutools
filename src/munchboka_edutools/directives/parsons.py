"""
Parsons Puzzle directive for creating code-reordering exercises.

This directive creates interactive puzzles where students must arrange shuffled
lines of code into the correct order through drag-and-drop.

Usage:
    ```{parsons-puzzle} puzzle-id
    :lang: python

    def fibonacci(n):
        if n <= 1:
            return n
        else:
            return fibonacci(n-1) + fibonacci(n-2)
    ```

Options:
    - lang (optional): Programming language for syntax highlighting (default: python)

Arguments:
    - Puzzle identifier (optional): If provided, creates a unique ID for the puzzle.
      Otherwise, a random ID is generated.

Features:
    - Drag-and-drop code lines into correct order
    - Syntax highlighting with highlight.js
    - Check solution button with visual feedback (toast notifications)
    - Reset button to reshuffle and try again
    - Modal popup showing complete code when solved
    - Copy to clipboard functionality
    - Theme-aware styling (light/dark mode)
"""

from docutils import nodes
from docutils.parsers.rst import Directive, directives
import uuid


class ParsonsPuzzleDirective(Directive):
    """
    Directive for creating Parsons puzzles (code reordering exercises).

    Students must drag and drop shuffled code lines into the correct order.
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {
        "lang": directives.unchanged,
    }

    def run(self):
        """Generate HTML for the Parsons puzzle."""
        # Generate a unique identifier or use the provided one
        if self.arguments:
            identifier = self.arguments[0]
        else:
            identifier = f"puzzle-{uuid.uuid4().hex[:8]}"

        puzzle_container_id = f"container-parsons-puzzle-{identifier}"
        editor_container_id = f"container-kode-{identifier}"

        # Get code content from the directive content
        code_content = "\n".join(self.content)

        # Escape code for JavaScript
        escaped_code = code_content.replace("`", "\\`").replace("$", "\\$")

        # Create the HTML with the template
        html = f"""
        <div id="{puzzle_container_id}" class="puzzle-container"></div>
        <div id="{editor_container_id}" style="display: none"></div>

        <script type="text/javascript">
            document.addEventListener("DOMContentLoaded", () => {{
                const code = 
`{escaped_code}`;

                const puzzleContainerId = '{puzzle_container_id}';
                const editorId = '{editor_container_id}';

                const switchToCodeEditor = makeCallbackFunction(puzzleContainerId, editorId);
                const puzzle = new ParsonsPuzzle(
                    puzzleContainerId,
                    code,
                    switchToCodeEditor,
                );
            }});    
        </script>
        """

        raw_node = nodes.raw("", html, format="html")
        return [raw_node]


def setup(app):
    """Register the parsons-puzzle directive with Sphinx."""
    app.add_directive("parsons-puzzle", ParsonsPuzzleDirective)
    # Also register without hyphen for MyST compatibility
    app.add_directive("parsonspuzzle", ParsonsPuzzleDirective)

    return {
        "version": "0.1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
