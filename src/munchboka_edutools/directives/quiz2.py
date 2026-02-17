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
        quiz_id = f"quiz-{uuid.uuid4().hex[:8]}"

        if not hasattr(self.env, "temp"):
            self.env.temp = {}
        self.env.temp["current_quiz2_id"] = quiz_id

        # Parse nested quiz-question content into native docutils nodes
        parsed = nodes.container()
        self.state.nested_parse(self.content, self.content_offset, parsed)

        # Clean up environment marker
        self.env.temp.pop("current_quiz2_id", None)

        container_id = f"quiz-container-{quiz_id}"
        source_id = f"quiz-source-{quiz_id}"

        # Hidden DOM source that contains fully-rendered question + answer markup
        source = nodes.container(classes=["quiz2-source"])
        source["ids"].append(source_id)
        source += parsed.children

        # Visible quiz mount point
        mount_html = f'<div id="{container_id}" class="quiz-main-container" data-quiz2-source="{source_id}"></div>'

        # Init script: parse source DOM into questionsData and boot the quiz
        init_html = f"""
        <script type=\"text/javascript\">
            document.addEventListener(\"DOMContentLoaded\", () => {{
                const sourceEl = document.getElementById({json.dumps(source_id)});
                const parseFn = (typeof window !== 'undefined') ? window.quiz2ParseDomSource : null;
                const questionsData = (typeof parseFn === 'function' && sourceEl) ? parseFn(sourceEl) : [];

                // Remove the source markup to avoid duplicate IDs/classes in the DOM.
                if (sourceEl && sourceEl.parentNode) {{
                    sourceEl.parentNode.removeChild(sourceEl);
                }}

                const quiz = new SequentialMultipleChoiceQuiz({json.dumps(container_id)}, questionsData);
            }});
        </script>
        """

        return [
            nodes.raw("", mount_html, format="html"),
            source,
            nodes.raw("", init_html, format="html"),
        ]


class QuizQuestionDirective(SphinxDirective):
    """Individual question directive for Quiz 2.0.

    Accepts content that can include any other directives (plot, code, etc.).
    Collects nested quiz-answer directives.
    """

    has_content = True
    required_arguments = 0
    option_spec = {}

    def run(self):
        if not hasattr(self.env, "temp"):
            self.env.temp = {}

        if self.env.temp.get("current_quiz2_id") is None:
            error_msg = self.state_machine.reporter.error(
                "quiz-question directive must be used inside a quiz-2 directive",
                nodes.literal_block(self.block_text, self.block_text),
                line=self.lineno,
            )
            return [error_msg]

        question_id = f"question-{uuid.uuid4().hex[:8]}"
        self.env.temp["current_quiz_question_id"] = question_id

        # Parse content to native nodes, including nested quiz-answer directives.
        parsed = nodes.container()
        self.state.nested_parse(self.content, self.content_offset, parsed)
        self.env.temp.pop("current_quiz_question_id", None)

        question_children: list[nodes.Node] = []
        answer_blocks: list[nodes.Node] = []
        for child in parsed.children:
            if isinstance(child, nodes.container) and "quiz2-answer-source" in child.get(
                "classes", []
            ):
                answer_blocks.append(child)
            else:
                question_children.append(child)

        wrapper = nodes.container(classes=["quiz2-question-source"])
        wrapper["data-question-id"] = question_id

        question_content = nodes.container(classes=["quiz2-question-content"])
        question_content += question_children

        answers_container = nodes.container(classes=["quiz2-answers-source"])
        answers_container += answer_blocks

        wrapper += question_content
        wrapper += answers_container

        return [wrapper]


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

        parsed = nodes.container()
        self.state.nested_parse(content_lines, self.content_offset, parsed)

        wrapper = nodes.container(classes=["quiz2-answer-source"])
        wrapper["data-correct"] = "true" if is_correct else "false"
        wrapper += parsed.children

        return [wrapper]

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
