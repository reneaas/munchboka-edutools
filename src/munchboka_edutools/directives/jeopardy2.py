"""Jeopardy 2.0 - Redesigned jeopardy board with nested question structure.

This module provides a modular Jeopardy board implementation where:
- jeopardy-2: Main container directive
- jeopardy-question: Individual question directive that can contain any other directives

Example usage:
    :::::{jeopardy-2}
    ::::{jeopardy-question}
    ---
    category: Asymptotes
    points: 100
    ---
    What is the asymptotes of the function $f$ shown in the graph below?

    :::{plot}
    function: (2*x - 1) / (x + 3), f
    :::
    ::::
    :::::
"""

from __future__ import annotations

import html as _html
import json
import os
import uuid
from typing import Any, Dict, List

from docutils import nodes
from docutils.parsers.rst import directives
from docutils.statemachine import StringList
from sphinx.util.docutils import SphinxDirective
from sphinx.util.nodes import nested_parse_with_titles


class Jeopardy2Directive(SphinxDirective):
    """Main container directive for Jeopardy 2.0 board.

    Collects all nested jeopardy-question directives and renders them
    as an interactive Jeopardy board.
    """

    has_content = True
    required_arguments = 0
    option_spec = {
        "teams": directives.unchanged,
    }

    def run(self):
        # Generate unique board ID
        self.board_id = uuid.uuid4().hex
        container_id = f"jeopardy2-{self.board_id}"

        # Store the board ID in the environment for nested questions to access
        if not hasattr(self.env, "temp"):
            self.env.temp = {}
        self.env.temp["current_jeopardy2_id"] = self.board_id
        self.env.temp[f"jeopardy2_questions_{self.board_id}"] = []

        # Parse the content to process nested jeopardy-question directives
        container_node = nodes.container()
        container_node["classes"].append("jeopardy2-container")

        # Parse nested content
        self.state.nested_parse(self.content, self.content_offset, container_node)

        # Collect all questions from the environment
        questions = self.env.temp.get(f"jeopardy2_questions_{self.board_id}", [])

        # Get answers from environment
        answers = self.env.temp.get(f"jeopardy2_answers_{self.board_id}", [])

        # Organize questions and answers by category and points
        data = self._organize_board(questions, answers)

        # Parse teams option
        teams_opt = self.options.get("teams")
        try:
            teams = max(1, int(str(teams_opt).strip())) if teams_opt is not None else 2
        except Exception:
            teams = 2
        data["teams"] = teams

        # Generate HTML output
        html = self._generate_board_html(container_id, data)

        # Clean up environment
        self.env.temp.pop(f"jeopardy2_questions_{self.board_id}", None)
        self.env.temp.pop(f"jeopardy2_answers_{self.board_id}", None)
        if "current_jeopardy2_id" in self.env.temp:
            self.env.temp.pop("current_jeopardy2_id")

        return [nodes.raw("", html, format="html")]

    def _organize_board(
        self, questions: List[Dict[str, Any]], answers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Organize questions and answers into categories and point values.

        Matches answers to questions based on category and points.
        """
        categories: Dict[str, Dict[str, Any]] = {}
        all_points = set()

        # Create a lookup for answers by (category, points)
        answer_lookup: Dict[tuple, str] = {}
        for a in answers:
            cat_name = a.get("category", "General")
            points = a.get("points", 100)
            answer_lookup[(cat_name, points)] = a.get("answer", "")

        # Process questions and match with answers
        for q in questions:
            cat_name = q.get("category", "General")
            points = q.get("points", 100)
            all_points.add(points)

            if cat_name not in categories:
                categories[cat_name] = {"name": cat_name, "tiles": []}

            # Try to find matching answer
            matched_answer = answer_lookup.get((cat_name, points), q.get("answer", ""))

            categories[cat_name]["tiles"].append(
                {"value": points, "question": q.get("question", ""), "answer": matched_answer}
            )

        # Sort points and organize tiles
        sorted_points = sorted(all_points)
        for cat in categories.values():
            # Sort tiles by points
            cat["tiles"].sort(key=lambda t: t["value"])

        return {"categories": list(categories.values()), "values": sorted_points}

    def _generate_board_html(self, container_id: str, data: Dict[str, Any]) -> str:
        """Generate the HTML for the Jeopardy board."""
        cfg_str_attr = _html.escape(json.dumps(data, ensure_ascii=False), quote=True)
        json_str = json.dumps(data, ensure_ascii=False)
        # Escape </script> and </style> tags to prevent breaking the JSON script tag
        json_str = json_str.replace("</script>", "<\\/script>").replace("</style>", "<\\/style>")

        html = f"""
        <div id="{container_id}" class="jeopardy2-container jeopardy-container" lang="no" data-config="{cfg_str_attr}">
          <script type="application/json" class="jeopardy-data">{json_str}</script>
        </div>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex/dist/katex.min.css">
        <script defer src="https://cdn.jsdelivr.net/npm/katex/dist/katex.min.js"></script>
        <script defer src="https://cdn.jsdelivr.net/npm/katex/dist/contrib/auto-render.min.js"></script>
        """
        return html


class JeopardyQuestionDirective(SphinxDirective):
    """Individual question directive for Jeopardy 2.0.

    Accepts front matter (category, points) and content that can include
    any other directives (plot, interactive-code, etc.).
    """

    has_content = True
    required_arguments = 0
    option_spec = {
        "category": directives.unchanged,
        "points": directives.positive_int,
    }

    def run(self):
        # Get the current board ID from the environment
        if not hasattr(self.env, "temp"):
            self.env.temp = {}

        board_id = self.env.temp.get("current_jeopardy2_id")
        if board_id is None:
            # Not inside a jeopardy-2 directive
            error_msg = self.state_machine.reporter.error(
                "jeopardy-question directive must be used inside a jeopardy-2 directive",
                nodes.literal_block(self.block_text, self.block_text),
                line=self.lineno,
            )
            return [error_msg]

        # Parse front matter and content
        category, points, content_lines = self._parse_content()

        # Use options if provided, otherwise use front matter
        category = self.options.get("category", category or "General")
        points = self.options.get("points", points or 100)

        # Split content into question and answer
        question_html, answer_html = self._split_question_answer(content_lines)

        # Store question in environment
        questions_key = f"jeopardy2_questions_{board_id}"
        if questions_key not in self.env.temp:
            self.env.temp[questions_key] = []

        self.env.temp[questions_key].append(
            {
                "category": category,
                "points": points,
                "question": question_html,
                "answer": answer_html,
            }
        )

        # Return empty list - the parent jeopardy-2 directive will render everything
        return []

    def _parse_content(self):
        """Parse front matter and content from the directive body."""
        category = None
        points = None
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

                        if key == "category":
                            category = value
                        elif key == "points":
                            try:
                                points = int(value)
                            except ValueError:
                                pass

                content_start = end_idx + 1

        # Get content lines after front matter
        content_lines = self.content[content_start:] if content_start < len(self.content) else []

        return category, points, content_lines

    def _split_question_answer(self, content_lines: StringList):
        """Split content into question and answer sections.

        Looks for 'Answer:' marker. Everything before is question, after is answer.
        If no marker, everything is the question.
        """
        answer_start = None

        for i, line in enumerate(content_lines):
            stripped = line.strip().lower()
            if stripped.startswith("answer:"):
                answer_start = i
                # Check if there's content after 'Answer:' on the same line
                after_marker = line[line.lower().find("answer:") + 7 :].strip()
                if after_marker:
                    # Content on same line - include it
                    pass
                break

        if answer_start is None:
            # No answer section, everything is question
            question_lines = content_lines
            answer_lines = StringList()
        else:
            question_lines = content_lines[:answer_start]
            # Get content after 'Answer:' marker
            first_answer_line = content_lines[answer_start]
            after_marker = first_answer_line[
                first_answer_line.lower().find("answer:") + 7 :
            ].strip()

            answer_lines = StringList()
            if after_marker:
                # Content on the same line as 'Answer:'
                answer_lines.append(after_marker, content_lines.source(answer_start))
            # Add remaining lines
            for i in range(answer_start + 1, len(content_lines)):
                answer_lines.append(content_lines[i], content_lines.source(i))

        # Render both sections to HTML
        question_html = self._render_to_html(question_lines)
        answer_html = self._render_to_html(answer_lines)

        return question_html, answer_html

    def _render_to_html(self, content_lines: StringList) -> str:
        """Render content lines to HTML, processing any nested directives."""
        if not content_lines:
            return ""

        # Create a container node for the content
        container = nodes.container()

        # Parse the content, which will process nested directives
        self.state.nested_parse(content_lines, self.content_offset, container)

        # Convert to HTML
        from sphinx.writers.html5 import HTML5Translator
        from io import StringIO

        # Get the builder
        builder = self.env.app.builder

        # Simple approach: convert nodes to pseudo-HTML
        html_parts = []
        for node in container.children:
            html_parts.append(self._node_to_html(node))

        return "\n".join(html_parts)

    def _node_to_html(self, node) -> str:
        """Convert a docutils node to HTML string.

        This is a simplified converter. For production, you'd want to use
        the proper Sphinx HTML translator.
        """
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
            # Preserve the figure element and its classes for proper CSS styling
            content = "".join(self._node_to_html(child) for child in node.children)
            classes = " ".join(node.get("classes", []))
            align = node.get("align", "center")

            # Build figure element with all necessary classes and attributes
            attrs = []
            if classes:
                attrs.append(f'class="{classes}"')
            if align:
                attrs.append(f'align="{align}"')

            attrs_str = " ".join(attrs) if attrs else ""
            return f"<figure {attrs_str}>{content}</figure>"

        elif isinstance(node, nodes.caption):
            # Handle figure captions
            content = "".join(self._node_to_html(child) for child in node.children)
            return f"<figcaption>{content}</figcaption>"

        elif isinstance(node, nodes.bullet_list):
            # Handle bullet (unordered) lists
            content = "".join(self._node_to_html(child) for child in node.children)
            return f"<ul>{content}</ul>"

        elif isinstance(node, nodes.enumerated_list):
            # Handle enumerated (ordered) lists
            content = "".join(self._node_to_html(child) for child in node.children)
            return f"<ol>{content}</ol>"

        elif isinstance(node, nodes.list_item):
            # Handle list items
            content = "".join(self._node_to_html(child) for child in node.children)
            return f"<li>{content}</li>"

        elif isinstance(node, nodes.container):
            # Recursively process container contents
            content = "".join(self._node_to_html(child) for child in node.children)
            classes = " ".join(node.get("classes", []))
            if classes:
                return f'<div class="{classes}">{content}</div>'
            return content

        elif hasattr(node, "children"):
            # Generic handler for nodes with children
            return "".join(self._node_to_html(child) for child in node.children)

        else:
            # Fallback for unknown node types
            return ""


class JeopardyAnswerDirective(SphinxDirective):
    """Individual answer directive for Jeopardy 2.0.

    Accepts front matter (category, points) and content that can include
    any other directives (plot, interactive-code, etc.).

    This directive is matched with jeopardy-question based on category and points.
    """

    has_content = True
    required_arguments = 0
    option_spec = {
        "category": directives.unchanged,
        "points": directives.positive_int,
    }

    def run(self):
        # Get the current board ID from the environment
        if not hasattr(self.env, "temp"):
            self.env.temp = {}

        board_id = self.env.temp.get("current_jeopardy2_id")
        if board_id is None:
            # Not inside a jeopardy-2 directive
            error_msg = self.state_machine.reporter.error(
                "jeopardy-answer directive must be used inside a jeopardy-2 directive",
                nodes.literal_block(self.block_text, self.block_text),
                line=self.lineno,
            )
            return [error_msg]

        # Parse front matter and content
        category, points, content_lines = self._parse_content()

        # Use options if provided, otherwise use front matter
        category = self.options.get("category", category or "General")
        points = self.options.get("points", points or 100)

        # Render content to HTML
        answer_html = self._render_to_html(content_lines)

        # Add "Fasit" heading to the answer
        answer_html = f"<h3>Fasit</h3>\n{answer_html}"

        # Store answer in environment
        answers_key = f"jeopardy2_answers_{board_id}"
        if answers_key not in self.env.temp:
            self.env.temp[answers_key] = []

        self.env.temp[answers_key].append(
            {
                "category": category,
                "points": points,
                "answer": answer_html,
            }
        )

        # Return empty list - the parent jeopardy-2 directive will render everything
        return []

    def _parse_content(self):
        """Parse front matter and content from the directive body."""
        category = None
        points = None
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

                        if key == "category":
                            category = value
                        elif key == "points":
                            try:
                                points = int(value)
                            except ValueError:
                                pass

                content_start = end_idx + 1

        # Get content lines after front matter
        content_lines = self.content[content_start:] if content_start < len(self.content) else []

        return category, points, content_lines

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
        """Convert a docutils node to HTML string.

        This is a simplified converter. For production, you'd want to use
        the proper Sphinx HTML translator.
        """
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
            # Preserve the figure element and its classes for proper CSS styling
            content = "".join(self._node_to_html(child) for child in node.children)
            classes = " ".join(node.get("classes", []))
            align = node.get("align", "center")

            # Build figure element with all necessary classes and attributes
            attrs = []
            if classes:
                attrs.append(f'class="{classes}"')
            if align:
                attrs.append(f'align="{align}"')

            attrs_str = " ".join(attrs) if attrs else ""
            return f"<figure {attrs_str}>{content}</figure>"

        elif isinstance(node, nodes.caption):
            # Handle figure captions
            content = "".join(self._node_to_html(child) for child in node.children)
            return f"<figcaption>{content}</figcaption>"

        elif isinstance(node, nodes.bullet_list):
            # Handle bullet (unordered) lists
            content = "".join(self._node_to_html(child) for child in node.children)
            return f"<ul>{content}</ul>"

        elif isinstance(node, nodes.enumerated_list):
            # Handle enumerated (ordered) lists
            content = "".join(self._node_to_html(child) for child in node.children)
            return f"<ol>{content}</ol>"

        elif isinstance(node, nodes.list_item):
            # Handle list items
            content = "".join(self._node_to_html(child) for child in node.children)
            return f"<li>{content}</li>"

        elif isinstance(node, nodes.container):
            # Recursively process container contents
            content = "".join(self._node_to_html(child) for child in node.children)
            classes = " ".join(node.get("classes", []))
            if classes:
                return f'<div class="{classes}">{content}</div>'
            return content

        elif hasattr(node, "children"):
            # Generic handler for nodes with children
            return "".join(self._node_to_html(child) for child in node.children)

        else:
            # Fallback for unknown node types
            return ""


def setup(app):
    """Register the directives with Sphinx."""
    app.add_directive("jeopardy-2", Jeopardy2Directive)
    app.add_directive("jeopardy-question", JeopardyQuestionDirective)
    app.add_directive("jeopardy-answer", JeopardyAnswerDirective)

    # Reuse the same CSS/JS as original jeopardy
    try:
        app.add_css_file("munchboka/css/jeopardy.css")
        app.add_js_file("munchboka/js/jeopardy.js")
        app.add_css_file("munchboka/css/general_style.css")
    except Exception:
        pass

    return {"version": "0.2", "parallel_read_safe": True, "parallel_write_safe": True}
