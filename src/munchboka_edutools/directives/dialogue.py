"""
Dialogue directive for creating conversation-style content.

This directive creates a dialogue between two speakers with chat-bubble styling.
Each speaker's messages are aligned left or right and styled with different colors.

Usage:
    ```{dialogue}
    :name1: Alice
    :name2: Bob
    :speaker1: left
    :speaker2: right

    Alice: Hello! How are you?
    Bob: I'm great, thanks for asking!
    Alice: That's wonderful to hear.
    ```

Options:
    - name1 (required): Name of the first speaker
    - name2 (required): Name of the second speaker
    - speaker1 (required): Alignment for first speaker ("left" or "right")
    - speaker2 (required): Alignment for second speaker ("left" or "right")

Content:
    Each line should be in the format: "SpeakerName: Message text"
    Lines not matching this format are ignored.
    Messages can contain math notation and will be parsed as normal content.
"""

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from sphinx.directives import optional_int


class DialogueWrapperNode(nodes.General, nodes.Element):
    """Container node for the entire dialogue."""

    pass


class DialogueEntryNode(nodes.Admonition, nodes.Element):
    """Node for a single dialogue entry (one message from one speaker)."""

    pass


def visit_dialogue_wrapper_node_html(self, node):
    """Open the dialogue container div."""
    self.body.append('<div class="dialogue">')


def depart_dialogue_wrapper_node_html(self, node):
    """Close the dialogue container div."""
    self.body.append("</div>")


def visit_dialogue_entry_node_html(self, node):
    """Open a dialogue entry with speaker name."""
    self.body.append(f'<div class="dialogue-entry {node["css_class"]}">')
    self.body.append(f'<div class="speaker-name">{node["speaker_name"]}</div>')


def depart_dialogue_entry_node_html(self, node):
    """Close the dialogue entry div."""
    self.body.append("</div>")


class DialogueDirective(Directive):
    """
    Directive for creating dialogue between two speakers.

    Creates chat-bubble styled conversations with left/right alignment.
    """

    has_content = True
    required_arguments = 0
    option_spec = {
        "name1": directives.unchanged_required,
        "name2": directives.unchanged_required,
        "speaker1": lambda s: directives.choice(s, ("left", "right")),
        "speaker2": lambda s: directives.choice(s, ("left", "right")),
    }

    def run(self):
        """Parse dialogue content and create dialogue nodes."""
        name1 = self.options.get("name1")
        name2 = self.options.get("name2")
        class1 = "speaker1" if self.options.get("speaker1") == "left" else "speaker2"
        class2 = "speaker1" if self.options.get("speaker2") == "left" else "speaker2"

        wrapper_node = DialogueWrapperNode()

        for line in self.content:
            line = line.strip()
            if not line or ":" not in line:
                continue

            speaker_name, message = line.split(":", 1)
            speaker_name = speaker_name.strip()
            message = message.strip()

            if speaker_name == name1:
                css_class = class1
            elif speaker_name == name2:
                css_class = class2
            else:
                continue

            entry_node = DialogueEntryNode()
            entry_node["css_class"] = css_class
            entry_node["speaker_name"] = speaker_name

            # Parse the message line like normal content so math works
            self.state.nested_parse([message], self.content_offset, entry_node)
            wrapper_node += entry_node

        return [wrapper_node]


def setup(app):
    """Register the dialogue directive and nodes with Sphinx."""
    app.add_node(
        DialogueWrapperNode,
        html=(visit_dialogue_wrapper_node_html, depart_dialogue_wrapper_node_html),
    )
    app.add_node(
        DialogueEntryNode,
        html=(visit_dialogue_entry_node_html, depart_dialogue_entry_node_html),
    )
    app.add_directive("dialogue", DialogueDirective)

    return {
        "version": "0.1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
