"""
Quiz 2.0 Directive System
=========================

A modular quiz system using nested directives:
- quiz-2: Main container
- quiz-question: Individual question with nested content support
- quiz-answer: Answer option with correct/incorrect flag

Features:
- Supports nested directives (plot, code, etc.) in questions
- Markdown/MyST formatting support
- Answer shuffling
- Math rendering with KaTeX
- Preserves existing quiz JavaScript functionality

Usage:
-----
:::::{quiz-2}

::::{quiz-question}
What is 2 + 2?

:::{quiz-answer}
---
correct: false
---
3
:::

:::{quiz-answer}
---
correct: true
---
4
:::
::::

:::::
"""

from docutils import nodes
from docutils.statemachine import StringList
from sphinx.util.docutils import SphinxDirective
from docutils.parsers.rst import directives
import json
import uuid
import html as _html


class Quiz2Directive(SphinxDirective):
    """Main container directive for Quiz 2.0.

    Collects nested quiz-question directives and generates the quiz HTML.
    """

    has_content = True
    required_arguments = 0
    option_spec = {
        "shuffle": directives.flag,
    }

    def run(self):
        # Generate unique ID for this quiz
        self.quiz_id = f"quiz-{uuid.uuid4().hex[:8]}"

        # Store quiz ID in environment for nested directives
        if not hasattr(self.env, "temp"):
            self.env.temp = {}

        self.env.temp["current_quiz2_id"] = self.quiz_id

        # Parse nested content (quiz-question directives)
        container = nodes.container()
        self.state.nested_parse(self.content, self.content_offset, container)

        # Get questions from environment
        questions_key = f"quiz2_questions_{self.quiz_id}"
        questions = self.env.temp.get(questions_key, [])

        # Generate HTML output
        container_id = f"quiz-container-{self.quiz_id}"
        html = self._generate_quiz_html(container_id, questions)

        # Clean up environment
        self.env.temp.pop(questions_key, None)
        if "current_quiz2_id" in self.env.temp:
            self.env.temp.pop("current_quiz2_id")

        return [nodes.raw("", html, format="html")]

    def _generate_quiz_html(self, container_id: str, questions: list) -> str:
        """Generate the HTML for the quiz."""
        # Escape </script> and </style> tags to prevent breaking the JSON script tag
        json_str = json.dumps(questions, ensure_ascii=False)
        json_str = json_str.replace("</script>", "<\\/script>").replace("</style>", "<\\/style>")

        html = f"""
        <!-- Container for the quiz -->
        <div id="{container_id}" class="quiz-main-container"></div>
        <!-- Include KaTeX for LaTeX rendering -->
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex/dist/katex.min.css">
        <script defer src="https://cdn.jsdelivr.net/npm/katex/dist/katex.min.js"></script>
        <script defer src="https://cdn.jsdelivr.net/npm/katex/dist/contrib/auto-render.min.js"></script>

        <script type="text/javascript">
            document.addEventListener("DOMContentLoaded", () => {{
                // Define your questions and answers
                const questionsData = {json_str};

                // Initialize the multiple-choice quiz
                const quiz = new SequentialMultipleChoiceQuiz('{container_id}', questionsData);
            }});
        </script>
        """

        return html


class QuizQuestionDirective(SphinxDirective):
    """Individual question directive for Quiz 2.0.

    Accepts content that can include any other directives (plot, code, etc.).
    Collects nested quiz-answer directives.
    """

    has_content = True
    required_arguments = 0
    option_spec = {}

    def run(self):
        # Get the current quiz ID from the environment
        if not hasattr(self.env, "temp"):
            self.env.temp = {}

        quiz_id = self.env.temp.get("current_quiz2_id")
        if quiz_id is None:
            error_msg = self.state_machine.reporter.error(
                "quiz-question directive must be used inside a quiz-2 directive",
                nodes.literal_block(self.block_text, self.block_text),
                line=self.lineno,
            )
            return [error_msg]

        # Generate unique ID for this question
        question_id = f"question-{uuid.uuid4().hex[:8]}"
        self.env.temp["current_quiz_question_id"] = question_id

        # Parse and render question content
        question_html = self._render_to_html(self.content)

        # Get answers from environment
        answers_key = f"quiz2_answers_{question_id}"
        answers = self.env.temp.get(answers_key, [])

        # Store question in environment
        questions_key = f"quiz2_questions_{quiz_id}"
        if questions_key not in self.env.temp:
            self.env.temp[questions_key] = []

        self.env.temp[questions_key].append({"content": question_html, "answers": answers})

        # Clean up
        self.env.temp.pop(answers_key, None)
        self.env.temp.pop("current_quiz_question_id", None)

        # Return empty list - the parent quiz-2 directive will render everything
        return []

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


class QuizAnswerDirective(SphinxDirective):
    """Individual answer directive for Quiz 2.0.

    Accepts front matter (correct: true/false) and content.
    """

    has_content = True
    required_arguments = 0
    option_spec = {
        "correct": directives.flag,
    }

    def run(self):
        # Get the current question ID from the environment
        if not hasattr(self.env, "temp"):
            self.env.temp = {}

        question_id = self.env.temp.get("current_quiz_question_id")
        if question_id is None:
            error_msg = self.state_machine.reporter.error(
                "quiz-answer directive must be used inside a quiz-question directive",
                nodes.literal_block(self.block_text, self.block_text),
                line=self.lineno,
            )
            return [error_msg]

        # Parse front matter and content
        is_correct, content_lines = self._parse_content()

        # Use option if provided, otherwise use front matter
        if "correct" in self.options:
            is_correct = True

        # Render content to HTML
        answer_html = self._render_to_html(content_lines)

        # Store answer in environment
        answers_key = f"quiz2_answers_{question_id}"
        if answers_key not in self.env.temp:
            self.env.temp[answers_key] = []

        self.env.temp[answers_key].append({"content": answer_html, "isCorrect": is_correct})

        # Return empty list
        return []

    def _parse_content(self):
        """Parse front matter and content from the directive body."""
        is_correct = False
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
                        value = value.strip().lower()

                        if key == "correct":
                            is_correct = value in ["true", "yes", "1"]

                content_start = end_idx + 1

        # Get content lines after front matter
        content_lines = self.content[content_start:] if content_start < len(self.content) else []

        return is_correct, content_lines

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
            math_text = node.astext()
            return f"${math_text}$"

        elif isinstance(node, nodes.math_block):
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
    app.add_directive("quiz-2", Quiz2Directive)
    app.add_directive("quiz-question", QuizQuestionDirective)
    app.add_directive("quiz-answer", QuizAnswerDirective)

    # Reuse the same CSS/JS as original quiz
    try:
        app.add_css_file("munchboka/css/quiz.css")
        app.add_js_file("munchboka/js/quiz.js")
    except Exception:
        pass

    return {"version": "0.2", "parallel_read_safe": True, "parallel_write_safe": True}
