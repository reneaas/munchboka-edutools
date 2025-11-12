from docutils import nodes
from docutils.parsers.rst import Directive, directives
from sphinx.util.docutils import SphinxDirective
import json
import uuid
import re
import os


class QuizDirective(SphinxDirective):
    """Directive for embedding interactive quizzes."""

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {
        "shuffle": directives.flag,
    }

    def run(self):

        # Parse the content
        # self.state.nested_parse(self.content, self.content_offset, admonition_node)
        self.quiz_id = uuid.uuid4().hex
        container_id = f"quiz-container-{self.quiz_id}"

        # Parse quiz content
        quiz_data = self._parse_quiz_content()

        # Create the HTML output
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
                const questionsData = {json.dumps(quiz_data, ensure_ascii=False)};

                // Initialize the multiple-choice quiz
                const quiz = new SequentialMultipleChoiceQuiz('{container_id}', questionsData);
            }});
        </script>
        """

        raw_node = nodes.raw("", html, format="html")

        return [raw_node]

    def _parse_quiz_content(self):
        """Parse the directive content into quiz questions data."""
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
        """Process code blocks to handle newlines properly."""

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
        """Replace Markdown images with HTML <img> tags, copy figures, and fix path."""
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
                print(f"⚠️ QuizDirective: Figure not found: {abs_fig_src}")
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
        """Parse figure options from alt text."""
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
        """Parse HTML-style attributes: width="60%" class="adaptive-figure" """
        options = {}
        # Match attribute="value" or attribute='value'
        pattern = r'(\w+)=(["\'])([^"\']*)\2'

        for match in re.finditer(pattern, alt_text):
            key = match.group(1)
            value = match.group(3)
            options[key] = value

        return options

    def _parse_simple_options(self, options_str):
        """Parse simple key: value syntax"""
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
        """Build the HTML for the figure with options."""

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
    app.add_directive("quiz", QuizDirective)
    # Also link shared figure styles in case only this submodule is loaded
    try:
        app.add_css_file("munchboka/css/general_style.css")
        app.add_css_file("munchboka/css/quiz.css")
        app.add_js_file("munchboka/js/quiz.js")
    except Exception:
        pass

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
