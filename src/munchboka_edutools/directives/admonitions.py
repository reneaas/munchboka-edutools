"""
Custom Admonition Directives
=============================

A collection of custom styled admonition directives for educational content.

Directives included:
- answer: For showing answers to problems (with dropdown option)
- example: For worked examples
- exercise: For exercise problems
- exercise-2: Styled h2 heading to mark exercise boundaries (no content)
- explore: For exploratory activities
- goals: For learning objectives/goals
- hints: For providing hints (with dropdown option)
- solution: For full solutions (with dropdown option, default on)
- solution-2: Inline non-admonition solution reveal (clickable button, full parent width)
- answer-2: Inline non-admonition answer reveal (clickable button, full parent width)
- summary: For chapter/section summaries
- theory: For theoretical content

All directives support MyST colon-fence syntax (:::).
"""

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from sphinx.util.docutils import SphinxDirective
from sphinx.util import logging
from sphinx.util.nodes import make_id
import re

logger = logging.getLogger(__name__)


def _slugify(text):
    """Convert a heading title to a URL-safe id attribute value."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'^-+|-+$', '', text)
    return text or 'heading'


class AnswerDirective(SphinxDirective):
    """
    Answer directive with optional dropdown.

    Usage:
        .. answer::
        .. answer:: Custom Title
        .. answer::
            :dropdown: 0
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True

    option_spec = {
        "dropdown": directives.unchanged,
    }

    def run(self):
        if len(self.arguments) > 0:
            title = self.arguments[0]
        else:
            title = "Fasit"

        # Create the admonition node
        admonition_node = nodes.admonition()
        admonition_node["classes"] = ["admonition", "answer"]

        if "dropdown" in self.options:
            dropdown_val = int(self.options["dropdown"])
        else:
            dropdown_val = 1

        if dropdown_val == 1:
            admonition_node["classes"].append("dropdown")

        # Create the title node
        title_node = nodes.title(text=title)
        admonition_node += title_node

        # Parse the content
        self.state.nested_parse(self.content, self.content_offset, admonition_node)

        return [admonition_node]


class ExampleDirective(SphinxDirective):
    """
    Example directive for worked examples.

    Usage:
        .. example:: Example Title
    """

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    def run(self):
        title = self.arguments[0]

        # Create the admonition node
        admonition_node = nodes.admonition()
        admonition_node["classes"] = ["admonition", "example"]

        # Create the title node
        title_node = nodes.title()
        parsed_title, _ = self.state.inline_text(title, self.lineno)
        title_node += parsed_title
        admonition_node += title_node

        # Parse the content
        self.state.nested_parse(self.content, self.content_offset, admonition_node)

        return [admonition_node]


class ExerciseDirective(SphinxDirective):
    """
    Exercise directive for problems.

    Usage:
        .. exercise:: Exercise Title
        .. exercise:: Exercise Title
            :level: 2
    """

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {
        "level": directives.unchanged,
        "aids": directives.unchanged,
    }

    def run(self):
        title = self.arguments[0]
        # Create the admonition node
        admonition_node = nodes.admonition()
        admonition_node["classes"] = ["admonition", "exercise"]

        aids_opt = self.options.get("aids")
        if isinstance(aids_opt, bool):
            aids_enabled = aids_opt
        elif aids_opt is None:
            aids_enabled = False
        else:
            aids_enabled = str(aids_opt).strip().lower() in {
                "1",
                "true",
                "yes",
                "y",
                "on",
            }

        if aids_enabled:
            admonition_node["classes"].append("exercise-aids")

        # Feature for future: difficulty levels based on option
        # level = self.options.get("level")
        # if level is not None:
        #     if level == "1":
        #         admonition_node["classes"].append("common")
        #     elif level == "2":
        #         admonition_node["classes"].append("rare")
        #     elif level == "3":
        #         admonition_node["classes"].append("epic")
        #     elif level == "4":
        #         admonition_node["classes"].append("legendary")

        # Create the title node
        title_node = nodes.title()
        parsed_title, _ = self.state.inline_text(title, self.lineno)
        title_node += parsed_title
        admonition_node += title_node

        # Parse the content
        self.state.nested_parse(self.content, self.content_offset, admonition_node)

        return [admonition_node]


class Exercise2Directive(SphinxDirective):

    has_content = True

    required_arguments = 1

    optional_arguments = 0

    final_argument_whitespace = True

    option_spec = {

        "level": directives.unchanged,

        "aids": directives.unchanged,

    }

    def run(self):

        title = self.arguments[0]
        section_node = nodes.section()
        section_id = make_id(self.env, self.state.document, "exercise", title)
        section_node["ids"].append(section_id)
        section_node["classes"].append("exercise-section")
        title_node = nodes.title()
        parsed_title, _ = self.state.inline_text(title, self.lineno)
        title_node += parsed_title
        section_node += title_node
        body_node = nodes.container()
        body_node["classes"] = ["exercise-body"]

        if self._aids_enabled():

            body_node["classes"].append("exercise-aids")

        self.state.nested_parse(self.content, self.content_offset, body_node)

        section_node += body_node

        return [section_node]

    def _aids_enabled(self):
        aids_opt = self.options.get("aids")

        if isinstance(aids_opt, bool):
            return aids_opt

        if aids_opt is None:
            return False

        return str(aids_opt).strip().lower() in {
            "1", "true", "yes", "y", "on"
        }


class ExploreDirective(SphinxDirective):
    """
    Explore directive for exploratory activities.

    Usage:
        .. explore:: Activity Title
    """

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    def run(self):
        title = self.arguments[0]

        # Create the admonition node
        admonition_node = nodes.admonition()
        admonition_node["classes"] = ["admonition", "explore"]

        # Create the title node
        title_node = nodes.title()
        parsed_title, _ = self.state.inline_text(title, self.lineno)
        title_node += parsed_title
        admonition_node += title_node

        # Parse the content
        self.state.nested_parse(self.content, self.content_offset, admonition_node)

        return [admonition_node]



class SolutionDirective(SphinxDirective):
    """
    Solution directive with dropdown (default on).

    Usage:
        .. solution::
        .. solution:: Custom Title
        .. solution::
            :dropdown: 0
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True

    option_spec = {
        "dropdown": directives.unchanged,
        "delay": directives.nonnegative_int,
    }

    def run(self):
        if len(self.arguments) > 0:
            title = self.arguments[0]
        else:
            title = "Løsning"

        delay_seconds = int(
            self.options.get(
                "delay", getattr(self.env.config, "munchboka_solution_delay_seconds", 300)
            )
        )
        solution_id = f"{self.env.docname.replace('/', '-')}-{self.lineno}"
        dropdown_enabled = True
        if self.options.get("dropdown") is not None:
            dropdown_enabled = self.options.get("dropdown") == "1"

        timed_enabled = delay_seconds > 0 and dropdown_enabled

        # Create the admonition node
        admonition_node = nodes.admonition()
        admonition_node["classes"] = ["admonition", "solution"]
        if timed_enabled:
            admonition_node["classes"].append("solution-timed")
            admonition_node["classes"].append(f"solution-delay-{delay_seconds}")
            admonition_node["classes"].append(f"solution-ref-{solution_id}")

        if dropdown_enabled:
            admonition_node["classes"].append("dropdown")

        # Create the title node
        title_node = nodes.title(text=title)
        admonition_node += title_node

        # Parse the content
        self.state.nested_parse(self.content, self.content_offset, admonition_node)

        return [admonition_node]


class Solution2Directive(SphinxDirective):
    """
    Solution-2 directive: inline, non-admonition solution reveal.

    Renders a clickable "Vis løsningsforslag" button that expands the
    solution content inline inside its parent container (e.g. an answer
    admonition), giving the content the full available horizontal width.

    Usage:
        .. solution-2::
        .. solution-2:: Custom button label
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True

    option_spec = {
        "open": directives.flag,
    }

    def run(self):
        label = self.arguments[0] if self.arguments else "Vis løsningsforslag"
        is_open = "open" in self.options
        aria_expanded = "true" if is_open else "false"
        button_label = "Skjul løsningsforslag" if is_open else label

        # Outer wrapper div.solution-2
        wrapper = nodes.container()
        wrapper["classes"] = ["solution-2"]
        if is_open:
            wrapper["classes"].append("is-open")

        # Clickable toggle button (raw HTML so we can set data attributes)
        button_html = (
            f'<button class="solution-2-toggle" aria-expanded="{aria_expanded}"'
            f' data-label="{label}">'
            f'{button_label}'
            f'</button>'
        )
        wrapper += nodes.raw("", button_html, format="html")

        # Content container — hidden by default via CSS, revealed by JS
        content_node = nodes.container()
        content_node["classes"] = ["solution-2-content"]
        self.state.nested_parse(self.content, self.content_offset, content_node)
        wrapper += content_node

        return [wrapper]


class Answer2Directive(SphinxDirective):
    """
    Answer-2 directive: inline, non-admonition answer reveal.

    Renders a clickable "Vis fasit" button that expands the answer content
    inline inside its parent container, giving the content the full available
    horizontal width. Uses a green colour scheme to distinguish it from
    solution-2's purple scheme.

    Usage:
        .. answer-2::
        .. answer-2:: Custom button label
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True

    def run(self):
        label = self.arguments[0] if self.arguments else "Vis fasit"

        # Outer wrapper div.answer-2
        wrapper = nodes.container()
        wrapper["classes"] = ["answer-2"]

        # Clickable toggle button
        button_html = (
            f'<button class="answer-2-toggle" aria-expanded="false"'
            f' data-label="{label}">'
            f'{label}'
            f'</button>'
        )
        wrapper += nodes.raw("", button_html, format="html")

        # Content container — hidden by default via CSS, revealed by JS
        content_node = nodes.container()
        content_node["classes"] = ["answer-2-content"]
        self.state.nested_parse(self.content, self.content_offset, content_node)
        wrapper += content_node

        return [wrapper]


class SummaryDirective(SphinxDirective):
    """
    Summary directive for chapter/section summaries.

    Usage:
        .. summary:: Summary Title
    """

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    def run(self):
        title = self.arguments[0]

        # Create the admonition node
        admonition_node = nodes.admonition()
        admonition_node["classes"] = ["admonition", "summary"]

        title_node = nodes.title()
        parsed_title, _ = self.state.inline_text(title, self.lineno)
        title_node += parsed_title
        admonition_node += title_node

        # Parse the content
        self.state.nested_parse(self.content, self.content_offset, admonition_node)

        return [admonition_node]


class TheoryDirective(SphinxDirective):
    """
    Theory directive for theoretical content.

    Usage:
        .. theory:: Theory Title
    """

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    def run(self):
        title = self.arguments[0]

        # Create the admonition node
        admonition_node = nodes.admonition()
        admonition_node["classes"] = ["admonition", "theory"]

        # Create the title node
        title_node = nodes.title()
        parsed_title, _ = self.state.inline_text(title, self.lineno)
        title_node += parsed_title
        admonition_node += title_node

        # Parse the content
        self.state.nested_parse(self.content, self.content_offset, admonition_node)

        return [admonition_node]
    


class Summary2Directive(SphinxDirective):

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    def run(self):

        title = self.arguments[0]
        section_node = nodes.section()
        section_id = make_id(self.env, self.state.document, "summary", title)
        section_node["ids"].append(section_id)
        section_node["classes"].append("summary-section")
        title_node = nodes.title()
        parsed_title, _ = self.state.inline_text(title, self.lineno)
        title_node += parsed_title
        section_node += title_node
        body_node = nodes.container()
        body_node["classes"] = ["summary-body"]


        self.state.nested_parse(self.content, self.content_offset, body_node)

        section_node += body_node

        return [section_node]
    

class Example2Directive(SphinxDirective):

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    def run(self):

        title = self.arguments[0]
        section_node = nodes.section()
        section_id = make_id(self.env, self.state.document, "example", title)
        section_node["ids"].append(section_id)
        section_node["classes"].append("example-section")
        title_node = nodes.title()
        parsed_title, _ = self.state.inline_text(title, self.lineno)
        title_node += parsed_title
        section_node += title_node
        body_node = nodes.container()
        body_node["classes"] = ["example-body"]


        self.state.nested_parse(self.content, self.content_offset, body_node)

        section_node += body_node

        return [section_node]
    

class Explore2Directive(SphinxDirective):

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    def run(self):

        title = self.arguments[0]
        section_node = nodes.section()
        section_id = make_id(self.env, self.state.document, "explore", title)
        section_node["ids"].append(section_id)
        section_node["classes"].append("explore-section")
        title_node = nodes.title()
        parsed_title, _ = self.state.inline_text(title, self.lineno)
        title_node += parsed_title
        section_node += title_node
        body_node = nodes.container()
        body_node["classes"] = ["explore-body"]


        self.state.nested_parse(self.content, self.content_offset, body_node)

        section_node += body_node

        return [section_node]
    


class GoalsDirective(SphinxDirective):
    """
    Goals directive: inline, non-admonition goals reveal.

    Renders a clickable "Vis kompetansemål" button that expands the goals content
    inline inside its parent container, giving the content the full available
    horizontal width. Uses a green colour scheme to distinguish it from
    solution-2's purple scheme.

    Usage:
        .. goals::
        .. goals:: Custom button label
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True

    def run(self):
        label = self.arguments[0] if self.arguments else "Vis kompetansemål"

        # Outer wrapper div.answer-2
        wrapper = nodes.container()
        wrapper["classes"] = ["goals"]

        # Clickable toggle button
        button_html = (
            f'<button class="goals-toggle" aria-expanded="false"'
            f' data-label="{label}">'
            f'{label}'
            f'</button>'
        )
        wrapper += nodes.raw("", button_html, format="html")

        # Content container — hidden by default via CSS, revealed by JS
        content_node = nodes.container()
        content_node["classes"] = ["goals-content"]
        self.state.nested_parse(self.content, self.content_offset, content_node)
        wrapper += content_node

        return [wrapper]
    

class ProofDirective(SphinxDirective):
    """
    Proof directive: inline, non-admonition goals reveal.

    Renders a clickable "Vis proof" button that expands the goals content
    inline inside its parent container, giving the content the full available
    horizontal width. Uses a green colour scheme to distinguish it from
    solution-2's purple scheme.

    Usage:
        .. goals::
        .. goals:: Custom button label
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True

    def run(self):
        label = self.arguments[0] if self.arguments else "Vis forklaring"

        # Outer wrapper div.proof
        wrapper = nodes.container()
        wrapper["classes"] = ["proof"]

        # Clickable toggle button
        button_html = (
            f'<button class="proof-toggle" aria-expanded="false"'
            f' data-label="{label}">'
            f'{label}'
            f'</button>'
        )
        wrapper += nodes.raw("", button_html, format="html")

        # Content container — hidden by default via CSS, revealed by JS
        content_node = nodes.container()
        content_node["classes"] = ["proof-content"]
        self.state.nested_parse(self.content, self.content_offset, content_node)
        wrapper += content_node

        return [wrapper]
    

class HintDirective(SphinxDirective):
    """
    Hint directive: inline, non-admonition goals reveal.

    Renders a clickable "Vis hint" button that expands the goals content
    inline inside its parent container, giving the content the full available
    horizontal width. Uses a green colour scheme to distinguish it from
    solution-2's purple scheme.

    Usage:
        .. goals::
        .. goals:: Custom button label
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = True

    def run(self):
        label = self.arguments[0] if self.arguments else "Vis hint"

        # Outer wrapper div.proof
        wrapper = nodes.container()
        wrapper["classes"] = ["hint"]

        # Clickable toggle button
        button_html = (
            f'<button class="hint-toggle" aria-expanded="false"'
            f' data-label="{label}">'
            f'{label}'
            f'</button>'
        )
        wrapper += nodes.raw("", button_html, format="html")

        # Content container — hidden by default via CSS, revealed by JS
        content_node = nodes.container()
        content_node["classes"] = ["hint-content"]
        self.state.nested_parse(self.content, self.content_offset, content_node)
        wrapper += content_node

        return [wrapper]



def setup(app):
    """
    Setup all custom admonition directives.

    Note: CSS files are registered in __init__.py with the munchboka/ prefix.
    The admonitions.css file contains all styling for these directives.
    """
    app.add_config_value("munchboka_solution_delay_seconds", 300, "html")
    app.add_directive("answer", Answer2Directive)
    app.add_directive("answer-2", Answer2Directive)
    app.add_directive("example", Example2Directive)
    app.add_directive("example-2", Example2Directive)
    app.add_directive("exercise", Exercise2Directive)
    app.add_directive("exercise-2", Exercise2Directive)
    app.add_directive("explore", Explore2Directive)
    app.add_directive("explore-2", Explore2Directive)
    app.add_directive("goals", GoalsDirective)
    app.add_directive("solution", Solution2Directive)
    app.add_directive("solution-2", Solution2Directive)
    app.add_directive("summary", Summary2Directive)
    app.add_directive("summary-2", Summary2Directive)
    app.add_directive("theory", TheoryDirective)
    app.add_directive("proof", ProofDirective)
    app.add_directive("hint", HintDirective)
    app.add_directive("hints", HintDirective)
    app.add_js_file("munchboka/js/solution_timer.js")

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
