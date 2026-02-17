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

import json
from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective
import uuid


class ParsonsPuzzleDirective(SphinxDirective):
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
        "chunk-marker": directives.unchanged,
        "indentation": directives.unchanged,
        "indent-size": directives.nonnegative_int,
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

        # Prefer a nested {code-block} source if present; otherwise fall back to
        # using the raw directive body.
        parsed = nodes.container()
        self.state.nested_parse(self.content, self.content_offset, parsed)

        literal_blocks = list(parsed.findall(nodes.literal_block))
        literal_block = literal_blocks[0] if literal_blocks else None

        if literal_block is not None:
            code_content = literal_block.astext()
            inferred_lang = literal_block.get("language") or literal_block.get("lang")
        else:
            code_content = "\n".join(self.content)
            inferred_lang = None

        # Determine language (explicit option wins)
        lang = (self.options.get("lang") or inferred_lang or "python").strip()

        # Chunk marker used to split blocks; marker lines are excluded from the
        # final solved code (injected into interactive-code).
        chunk_marker = (self.options.get("chunk-marker") or "# chunk").strip()

        indentation_mode = (self.options.get("indentation") or "student").strip().lower()
        if indentation_mode not in {"fixed", "student"}:
            indentation_mode = "fixed"

        indent_size = self.options.get("indent-size")

        # Safely embed strings in JS (handles backslashes, quotes, etc.)
        code_json = json.dumps(code_content)
        lang_json = json.dumps(lang)
        chunk_marker_json = json.dumps(chunk_marker)
        indentation_mode_json = json.dumps(indentation_mode)
        indent_size_json = json.dumps(indent_size)

        # Create the HTML with the template
        html = f"""
        <div id="{puzzle_container_id}" class="puzzle-container"></div>
        <div id="{editor_container_id}" style="display: none"></div>

        <script type="text/javascript">
            document.addEventListener("DOMContentLoaded", () => {{
                const code = {code_json};

                const puzzleContainerId = '{puzzle_container_id}';
                const editorId = '{editor_container_id}';
                const options = {{
                    lang: {lang_json},
                    chunkMarker: {chunk_marker_json},
                    indentationMode: {indentation_mode_json},
                    indentSize: {indent_size_json},
                }};

                const switchToCodeEditor = makeCallbackFunction(puzzleContainerId, editorId);
                const puzzle = new ParsonsPuzzle(
                    puzzleContainerId,
                    code,
                    switchToCodeEditor,
                    options,
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
