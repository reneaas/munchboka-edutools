"""
Custom Admonition Directives
=============================

A collection of custom styled admonition directives for educational content.

Directives included:
- answer: For showing answers to problems (with dropdown option)
- example: For worked examples
- exercise: For exercise problems
- explore: For exploratory activities
- goals: For learning objectives/goals
- hints: For providing hints (with dropdown option)
- solution: For full solutions (with dropdown option, default on)
- summary: For chapter/section summaries
- theory: For theoretical content

All directives support MyST colon-fence syntax (:::).
"""

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from sphinx.util.docutils import SphinxDirective
from sphinx.util import logging

logger = logging.getLogger(__name__)


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
    }

    def run(self):
        title = self.arguments[0]
        # Create the admonition node
        admonition_node = nodes.admonition()
        admonition_node["classes"] = ["admonition", "exercise"]

        # Create the title node
        title_node = nodes.title()
        parsed_title, _ = self.state.inline_text(title, self.lineno)
        title_node += parsed_title
        admonition_node += title_node

        # Parse the content
        self.state.nested_parse(self.content, self.content_offset, admonition_node)

        return [admonition_node]


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


class GoalsDirective(SphinxDirective):
    """
    Goals directive for learning objectives.

    Usage:
        .. goals:: Learning Goals
    """

    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    def run(self):
        title = self.arguments[0]

        # Create the admonition node
        admonition_node = nodes.admonition()
        admonition_node["classes"] = ["admonition", "tip"]

        title_node = nodes.title()
        parsed_title, _ = self.state.inline_text(title, self.lineno)
        title_node += parsed_title
        admonition_node += title_node

        # Parse the content
        self.state.nested_parse(self.content, self.content_offset, admonition_node)

        return [admonition_node]


class HintsDirective(SphinxDirective):
    """
    Hints directive with optional dropdown.

    Usage:
        .. hints::
        .. hints:: Custom Title
        .. hints::
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
            title = "Hint"

        # Create the admonition node
        admonition_node = nodes.admonition()
        admonition_node["classes"] = ["admonition", "hints"]

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
    }

    def run(self):
        if len(self.arguments) > 0:
            title = self.arguments[0]
        else:
            title = "Løsning"

        # Create the admonition node
        admonition_node = nodes.admonition()
        admonition_node["classes"] = ["admonition", "solution"]

        if self.options.get("dropdown"):
            dropdown = self.options.get("dropdown")
            if dropdown == "1":
                admonition_node["classes"].append("dropdown")
            elif dropdown == "0":
                pass
        else:
            admonition_node["classes"].append("dropdown")

        # Create the title node
        title_node = nodes.title(text=title)
        admonition_node += title_node

        # Parse the content
        self.state.nested_parse(self.content, self.content_offset, admonition_node)

        return [admonition_node]


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


def setup(app):
    """
    Setup all custom admonition directives.

    Note: CSS files are registered in __init__.py with the munchboka/ prefix.
    The admonitions.css file contains all styling for these directives.
    """
    app.add_directive("answer", AnswerDirective)
    app.add_directive("example", ExampleDirective)
    app.add_directive("exercise", ExerciseDirective)
    app.add_directive("explore", ExploreDirective)
    app.add_directive("goals", GoalsDirective)
    app.add_directive("hints", HintsDirective)
    app.add_directive("solution", SolutionDirective)
    app.add_directive("summary", SummaryDirective)
    app.add_directive("theory", TheoryDirective)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
