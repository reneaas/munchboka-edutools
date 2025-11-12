"""
Timed Quiz Directive for Munchboka Edutools
===========================================

This directive creates interactive timed quizzes with multiple-choice questions.
Students race against the clock to answer as many questions as possible correctly.

Usage in MyST Markdown:
    ```{timed-quiz}
    Q: What is 2 + 2?
    + 4
    - 3
    - 5
    - 6

    Q: What is the capital of France?
    + Paris
    - London
    - Berlin
    - Madrid
    ```

Features:
    - Countdown timer with visual progress bar
    - Automatic question shuffling
    - Answer shuffling for each question
    - Score tracking and feedback
    - Support for LaTeX math rendering
    - Support for code blocks with syntax highlighting
    - Support for images in questions and answers
    - Theme-aware styling (light/dark modes)

Dependencies:
    - KaTeX: For LaTeX math rendering
    - highlight.js: For code syntax highlighting
    - timedMultipleChoiceQuiz.js: Main quiz logic
    - multipleChoiceQuestion.js: Question rendering logic
    - utils.js: Utility functions

Author: René Aasen (ported from matematikk_r1)
Date: November 2025
"""

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from sphinx.util.docutils import SphinxDirective
import json
import uuid
import re
import os


class TimedQuizDirective(SphinxDirective):
    """
    Sphinx directive for embedding interactive timed quizzes.

    The directive parses quiz content in a simple text format:
    - Questions start with "Q:"
    - Correct answers start with "+"
    - Incorrect answers start with "-"

    Options:
        shuffle (flag): Shuffle the order of questions (default behavior)

    Example:
        ```{timed-quiz}
        Q: What is 2 + 2?
        + 4
        - 3
        - 5

        Q: Solve: $x^2 = 9$
        + $x = \\pm 3$
        - $x = 3$
        - $x = 9$
        ```
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {
        "shuffle": directives.flag,
    }

    def run(self):
        """
        Generate the HTML for the timed quiz.

        Returns:
            list: List of docutils nodes (raw HTML node)
        """
        # Generate unique ID for this quiz instance
        self.quiz_id = uuid.uuid4().hex
        container_id = f"quiz-container-{self.quiz_id}"

        # Parse quiz content
        quiz_data = self._parse_quiz_content()

        # Create the HTML output
        # Note: KaTeX is already loaded globally via __init__.py
        html = f"""
        <!-- Container for the timed quiz -->
        <div id="{container_id}" class="quiz-main-container"></div>

        <script type="text/javascript">
            document.addEventListener("DOMContentLoaded", () => {{
                // Define your questions and answers
                const questionsData = {json.dumps(quiz_data, ensure_ascii=False)};

                // Initialize the timed multiple-choice quiz
                const quiz = new TimedMultipleChoiceQuiz('{container_id}', questionsData);
            }});
        </script>
        """

        raw_node = nodes.raw("", html, format="html")

        return [raw_node]

    def _parse_quiz_content(self):
        """
        Parse the directive content into quiz questions data.

        The parser recognizes:
        - Q: question text
        - + correct answer
        - - incorrect answer

        Returns:
            list: List of question dictionaries with content and answers
        """
        questions = []
        current_question = None
        current_answers = []

        for line in self.content:
            line = self._process_figures(line)
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # New question starts with Q:
            if line.startswith("Q:"):
                # Save previous question if exists
                if current_question:
                    questions.append({"content": current_question, "answers": current_answers})

                # Start new question and process newlines
                question_text = line[2:].strip()
                # Replace \\n with actual newlines for code blocks
                question_text = self._process_code_blocks(question_text)
                current_question = question_text
                current_answers = []

            # Correct answer starts with +
            elif line.startswith("+"):
                answer_text = line[1:].strip()
                # Process code blocks in answers too
                answer_text = self._process_code_blocks(answer_text)
                current_answers.append({"content": answer_text, "isCorrect": True})

            # Incorrect answer starts with -
            elif line.startswith("-"):
                answer_text = line[1:].strip()
                # Process code blocks in answers too
                answer_text = self._process_code_blocks(answer_text)
                current_answers.append({"content": answer_text, "isCorrect": False})

        # Add the last question
        if current_question:
            questions.append({"content": current_question, "answers": current_answers})

        return questions

    def _process_code_blocks(self, text):
        """
        Process code blocks to handle newlines properly.

        Converts escaped newlines (\\n) to actual newlines within <pre><code> blocks.

        Args:
            text: Text that may contain code blocks

        Returns:
            str: Text with properly formatted code blocks
        """

        # Helper function to process code blocks by type
        def replace_newlines(match):
            code = match.group(2)  # The actual code content
            lang = match.group(1)  # The language class (python or console)

            # Replace escaped newlines with actual newlines
            code = code.replace("\\n", "\n")
            return f'<pre><code class="{lang}">{code}</code></pre>'

        # Find all code blocks with any class and process them
        pattern = r'<pre><code class="([\w-]+)">(.*?)</code></pre>'
        text = re.sub(pattern, replace_newlines, text, flags=re.DOTALL)

        return text

    def _process_figures(self, text):
        """
        Replace Markdown images with HTML <img> tags, copy figures, and fix path.

        This function:
        1. Parses Markdown image syntax: ![alt](src)
        2. Copies the image to _static/figurer/<quiz_path>/
        3. Generates unique filenames to avoid conflicts
        4. Returns HTML img tags with proper paths

        Args:
            text: Text that may contain Markdown image syntax

        Returns:
            str: Text with images converted to HTML <img> tags
        """
        import shutil
        import re
        import json

        # Add a counter to track images within this quiz
        if not hasattr(self, "_image_counter"):
            self._image_counter = 0

        def replace(match):
            alt_or_options = match.group(1).strip()  # Alt text or options
            raw_src = match.group(2)  # Image source path

            # Increment image counter for unique naming
            self._image_counter += 1

            # Parse options from alt text
            options = self._parse_figure_options(alt_or_options)

            # Path of the source .md/.rst file
            source_file = self.state.document["source"]
            source_dir = os.path.dirname(source_file)
            app_src_dir = self.env.srcdir  # Root of source directory

            # Absolute source path of the image file
            abs_fig_src = os.path.normpath(os.path.join(source_dir, raw_src))

            if not os.path.exists(abs_fig_src):
                print(f"⚠️ TimedQuizDirective: Figure not found: {abs_fig_src}")
                return f'<img src="{raw_src}" class="quiz-image adaptive-figure" alt="Quiz figure (missing)">'

            # Determine quiz-local static path: _static/figurer/<path to .md>/<filename>
            relative_doc_path = os.path.relpath(source_dir, app_src_dir)
            figure_dest_dir = os.path.join(app_src_dir, "_static", "figurer", relative_doc_path)
            os.makedirs(figure_dest_dir, exist_ok=True)

            # Create unique filename using the full relative path to avoid conflicts
            # Convert the relative path from source to a safe filename part
            rel_path_from_source = os.path.relpath(abs_fig_src, source_dir)
            safe_path = rel_path_from_source.replace(os.sep, "_").replace("/", "_")
            base_name, ext = os.path.splitext(safe_path)

            # Use quiz_id, image counter, and the safe path for uniqueness
            fig_filename = f"{self.quiz_id}_img{self._image_counter}_{base_name}{ext}"
            fig_dest_path = os.path.join(figure_dest_dir, fig_filename)

            # Copy image
            shutil.copy2(abs_fig_src, fig_dest_path)

            # Now calculate relative path from output HTML to _static
            depth = os.path.relpath(source_dir, app_src_dir).count(os.sep)
            rel_prefix = "../" * (depth + 1)

            html_img_path = f"{rel_prefix}_static/figurer/{relative_doc_path}/{fig_filename}"

            # Build HTML with options
            html_img = self._build_figure_html(html_img_path, options)

            return html_img

        # Updated regex to capture both alt text and source
        return re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", replace, text)

    def _parse_figure_options(self, alt_text):
        """
        Parse figure options from alt text.

        Supports three formats:
        1. JSON-like: {width: 60%, class: adaptive-figure}
        2. HTML-style: width="60%" class="adaptive-figure"
        3. Plain text: Just alt text

        Args:
            alt_text: Alt text string that may contain options

        Returns:
            dict: Parsed options dictionary
        """
        options = {}

        # Method 1: JSON-like syntax {width: 60%, class: adaptive-figure}
        if alt_text.startswith("{") and alt_text.endswith("}"):
            try:
                # Clean up the syntax for JSON parsing
                json_str = alt_text
                # Add quotes to keys: width: -> "width":
                json_str = re.sub(r"(\w+):", r'"\1":', json_str)
                # Add quotes to unquoted values
                json_str = re.sub(r':\s*([^",}]+)', r': "\1"', json_str)
                options = json.loads(json_str)
            except:
                # Fallback to simple parsing
                options = self._parse_simple_options(alt_text[1:-1])

        # Method 2: HTML-style attributes: width="60%" class="adaptive-figure"
        elif "=" in alt_text:
            options = self._parse_html_style_options(alt_text)

        # Method 3: Plain alt text (traditional)
        else:
            if alt_text:
                options["alt"] = alt_text

        return options

    def _parse_html_style_options(self, alt_text):
        """
        Parse HTML-style attributes: width="60%" class="adaptive-figure"

        Args:
            alt_text: String with HTML-style attributes

        Returns:
            dict: Parsed options
        """
        options = {}
        # Match attribute="value" or attribute='value'
        pattern = r'(\w+)=(["\'])([^"\']*)\2'

        for match in re.finditer(pattern, alt_text):
            key = match.group(1)
            value = match.group(3)
            options[key] = value

        return options

    def _parse_simple_options(self, options_str):
        """
        Parse simple key: value syntax.

        Args:
            options_str: String with comma-separated key:value pairs

        Returns:
            dict: Parsed options
        """
        options = {}
        pairs = options_str.split(",")

        for pair in pairs:
            if ":" in pair:
                key, value = pair.split(":", 1)
                key = key.strip()
                value = value.strip()
                # Remove quotes if present
                if (value.startswith('"') and value.endswith('"')) or (
                    value.startswith("'") and value.endswith("'")
                ):
                    value = value[1:-1]
                options[key] = value

        return options

    def _build_figure_html(self, html_img_path, options):
        """
        Build the HTML for the figure with options.

        Args:
            html_img_path: Path to the image file
            options: Dictionary of image options (width, class, alt, etc.)

        Returns:
            str: HTML markup for the image
        """

        # Default options
        default_options = {"class": "quiz-image adaptive-figure", "alt": "Quiz figure"}

        # Merge with user options (user options override defaults)
        final_options = {**default_options, **options}

        # Build img attributes
        img_attrs = []
        img_attrs.append(f'src="{html_img_path}"')

        for key, value in final_options.items():
            if key == "width":
                img_attrs.append(f'style="width: {value};"')
            elif key == "height":
                img_attrs.append(f'style="height: {value};"')
            elif key in ["class", "alt", "title"]:
                img_attrs.append(f'{key}="{value}"')

        img_tag = f'<img {" ".join(img_attrs)}>'

        # Wrap in container
        html_img = f"""<div class="quiz-image-container">
            {img_tag}
        </div>
        """

        return html_img


def setup(app):
    """
    Setup function to register the directive with Sphinx.

    This function is called automatically by Sphinx when the extension is loaded.
    It registers both 'timed-quiz' and 'timedquiz' directives for compatibility.

    Args:
        app: The Sphinx application instance

    Returns:
        dict: Extension metadata including version and parallel processing flags
    """
    app.add_directive("timed-quiz", TimedQuizDirective)
    app.add_directive("timedquiz", TimedQuizDirective)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
