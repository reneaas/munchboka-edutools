"""
Escape Room 2.0 Directive System
=================================

A modular escape room system using nested directives:
- escape-room-2: Main container
- room: Individual room/puzzle with nested content support

Features:
- Supports nested directives (plot, code, cas-popup, etc.) in rooms
- Markdown/MyST formatting support
- Math rendering with KaTeX
- Preserves existing escape-room JavaScript functionality

Usage:
-----
::::::{escape-room-2}

::::{room}
---
code: 144
---
What is 12 × 12?

:::{plot}
:function: x**2
:::
::::

::::{room}
---
code: abc123
---
Next puzzle...
::::

::::::
"""

from docutils import nodes
from docutils.statemachine import StringList
from sphinx.util.docutils import SphinxDirective
from docutils.parsers.rst import directives
import json
import uuid
import html as _html


class EscapeRoom2Directive(SphinxDirective):
    """Main container directive for Escape Room 2.0.

    Collects nested room directives and generates the escape room HTML.
    """

    has_content = True
    required_arguments = 0
    option_spec = {
        "case_insensitive": directives.flag,
    }

    def run(self):
        # Generate unique ID for this escape room
        self.board_id = f"escape-room-{uuid.uuid4().hex[:8]}"

        # Store escape room ID in environment for nested directives
        if not hasattr(self.env, "temp"):
            self.env.temp = {}

        self.env.temp["current_escaperoom2_id"] = self.board_id

        # Parse nested content (room directives)
        container = nodes.container()
        self.state.nested_parse(self.content, self.content_offset, container)

        # Get rooms from environment
        rooms_key = f"escaperoom2_rooms_{self.board_id}"
        rooms = self.env.temp.get(rooms_key, [])

        # Generate HTML output
        container_id = f"escape-room-{self.board_id}"
        case_insensitive = "case_insensitive" in self.options
        html = self._generate_escape_room_html(container_id, rooms, case_insensitive)

        # Clean up environment
        self.env.temp.pop(rooms_key, None)
        if "current_escaperoom2_id" in self.env.temp:
            self.env.temp.pop("current_escaperoom2_id")

        return [nodes.raw("", html, format="html")]

    def _generate_escape_room_html(
        self, container_id: str, rooms: list, case_insensitive: bool
    ) -> str:
        """Generate the HTML for the escape room."""
        data = {"steps": rooms, "caseInsensitive": case_insensitive}

        # Escape </script> and </style> tags to prevent breaking the JSON script tag
        json_str = json.dumps(data, ensure_ascii=False)
        json_str = json_str.replace("</script>", "<\\/script>").replace("</style>", "<\\/style>")

        # Escape JSON for safe embedding in a double-quoted attribute
        attr_json = _html.escape(json_str, quote=True)

        html = f"""
        <div id="{container_id}" class="escape-room-container" data-config="{attr_json}">
          <script type="application/json" class="escape-room-data">{json_str}</script>
        </div>
        """

        return html


class RoomDirective(SphinxDirective):
    """Individual room directive for Escape Room 2.0.

    Accepts front matter (code, title) and content that can include any other directives.
    """

    has_content = True
    required_arguments = 0
    option_spec = {
        "code": directives.unchanged_required,
        "title": directives.unchanged,
    }

    def run(self):
        # Get the current escape room ID from the environment
        if not hasattr(self.env, "temp"):
            self.env.temp = {}

        escaperoom_id = self.env.temp.get("current_escaperoom2_id")
        if escaperoom_id is None:
            error_msg = self.state_machine.reporter.error(
                "room directive must be used inside an escape-room-2 directive",
                nodes.literal_block(self.block_text, self.block_text),
                line=self.lineno,
            )
            return [error_msg]

        # Parse front matter and content
        code, title, content_lines = self._parse_content()

        # Use options if provided, otherwise use front matter
        code = self.options.get("code", code)
        title = self.options.get("title", title or "")

        if not code:
            error_msg = self.state_machine.reporter.error(
                "room directive requires a 'code' (either in front matter or as option)",
                nodes.literal_block(self.block_text, self.block_text),
                line=self.lineno,
            )
            return [error_msg]

        # Parse codes (can be comma/semicolon separated)
        import re

        codes = [c.strip() for c in re.split(r"[,;]", code)] if code else []

        # Render content to HTML
        question_html = self._render_to_html(content_lines)

        # Store room in environment
        rooms_key = f"escaperoom2_rooms_{escaperoom_id}"
        if rooms_key not in self.env.temp:
            self.env.temp[rooms_key] = []

        self.env.temp[rooms_key].append({"title": title, "codes": codes, "question": question_html})

        # Return empty list - the parent escape-room-2 directive will render everything
        return []

    def _parse_content(self):
        """Parse front matter and content from the directive body."""
        code = None
        title = None
        content_start = 0

        # Check for YAML front matter (---)
        if len(self.content) > 0 and self.content[0].strip() == "---":
            # Find the closing ---
            end_idx = None
            for i in range(1, len(self.content)):
                if self.content[i].strip() == "---":
                    end_idx = i
                    break

            if end_idx is not None:
                # Parse front matter
                for i in range(1, end_idx):
                    line = self.content[i].strip()
                    if ":" in line:
                        key, value = line.split(":", 1)
                        key = key.strip().lower()
                        value = value.strip()

                        if key == "code":
                            code = value
                        elif key == "title":
                            title = value

                content_start = end_idx + 1

        # Get content lines after front matter
        content_lines = self.content[content_start:] if content_start < len(self.content) else []

        return code, title, content_lines

    def _render_to_html(self, content_lines: StringList) -> str:
        """Render content lines to HTML, processing any nested directives."""
        if not content_lines:
            return ""

        # Create a container node for the content
        container = nodes.container()

        # Parse the content, which will process nested directives
        self.state.nested_parse(content_lines, self.content_offset, container)

        # Convert to HTML
        html_parts = []
        for node in container.children:
            html_parts.append(self._node_to_html(node))

        return "\n".join(html_parts)

    def _node_to_html(self, node) -> str:
        """Convert a docutils node to HTML string."""
        if isinstance(node, nodes.paragraph):
            content = "".join(self._node_to_html(child) for child in node.children)
            return f"<p>{content}</p>"

        elif isinstance(node, nodes.Text):
            return _html.escape(str(node))

        elif isinstance(node, nodes.raw):
            if node.get("format") == "html":
                return node.astext()
            return ""

        elif isinstance(node, nodes.math):
            # Render inline math using KaTeX-compatible format
            math_text = node.astext()
            return f"${math_text}$"

        elif isinstance(node, nodes.math_block):
            # Render display math ($$...$$) using KaTeX-compatible format
            math_text = node.astext()
            return f"$${math_text}$$"

        elif isinstance(node, nodes.image):
            uri = node.get("uri", "")
            alt = node.get("alt", "")
            return f'<img src="{uri}" alt="{alt}" />'

        elif isinstance(node, nodes.literal_block):
            content = _html.escape(node.astext())
            language = node.get("language", "")
            return f'<pre><code class="{language}">{content}</code></pre>'

        elif isinstance(node, nodes.figure):
            # Handle figure nodes (e.g., from plot directive)
            content = "".join(self._node_to_html(child) for child in node.children)
            classes = " ".join(node.get("classes", []))
            align = node.get("align", "center")

            attrs = []
            if classes:
                attrs.append(f'class="{classes}"')
            if align:
                attrs.append(f'align="{align}"')

            attrs_str = " ".join(attrs) if attrs else ""
            return f"<figure {attrs_str}>{content}</figure>"

        elif isinstance(node, nodes.caption):
            content = "".join(self._node_to_html(child) for child in node.children)
            return f"<figcaption>{content}</figcaption>"

        elif isinstance(node, nodes.bullet_list):
            content = "".join(self._node_to_html(child) for child in node.children)
            return f"<ul>{content}</ul>"

        elif isinstance(node, nodes.enumerated_list):
            content = "".join(self._node_to_html(child) for child in node.children)
            return f"<ol>{content}</ol>"

        elif isinstance(node, nodes.list_item):
            content = "".join(self._node_to_html(child) for child in node.children)
            return f"<li>{content}</li>"

        elif isinstance(node, nodes.container):
            content = "".join(self._node_to_html(child) for child in node.children)
            classes = " ".join(node.get("classes", []))
            if classes:
                return f'<div class="{classes}">{content}</div>'
            return content

        elif hasattr(node, "children"):
            return "".join(self._node_to_html(child) for child in node.children)

        else:
            return ""


def setup(app):
    """Register the directives with Sphinx."""
    app.add_directive("escape-room-2", EscapeRoom2Directive)
    app.add_directive("room", RoomDirective)

    # Reuse the same CSS/JS as original escape-room
    try:
        app.add_css_file("munchboka/css/escapeRoom/escape-room.css")
        app.add_js_file("munchboka/js/escapeRoom/escape-room.js")
    except Exception:
        pass

    return {"version": "0.2", "parallel_read_safe": True, "parallel_write_safe": True}
