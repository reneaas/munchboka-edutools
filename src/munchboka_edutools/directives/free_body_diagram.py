"""The ``free-body-diagram`` directive.

Composes a physics free-body diagram (object outline, force vectors with
correct points of attack, and a small corner axis indicator) from a compact
DSL, then delegates all actual rendering/caching to the existing ``plot``
directive by constructing one directly and returning its result \u2014 see
``interactive_graph.py`` for the established precedent of wrapping ``plot``
this way.

.. code-block:: text

   :::{free-body-diagram}
   object: ball, size=1, position=(0, 0), color=teal
   velocity: angle=20
   force: gravity, length=1, name="$\\vec G$"
   force: normal, length=1, name="$\\vec N$"
   force: friction, length=0.4, name="$\\vec R$"
   force: air-resistance, length=0.6, name="$\\vec L$"
   :::
"""

from __future__ import annotations

from typing import List

from docutils import nodes
from docutils.statemachine import StringList
from sphinx.util.docutils import SphinxDirective

from ._free_body_geometry import compile_scene
from ._plot_common import parse_bool, parse_kv_block
from .plot import PlotDirective

_MULTI_KEYS = {"force", "axis"}
_OWN_KEYS = {"object", "velocity", "axis-indicator"}


class FreeBodyDiagramDirective(SphinxDirective):
    """Build a free-body diagram and render it via the `plot` directive."""

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True

    option_spec = {**PlotDirective.option_spec}

    def run(self) -> List[nodes.Node]:
        content_lines = [str(line) for line in self.content]
        scalars, lists, caption_idx = parse_kv_block(content_lines, _MULTI_KEYS)

        if "object" not in scalars:
            return [
                self.state_machine.reporter.error(
                    "free-body-diagram requires an `object:` line", line=self.lineno
                )
            ]
        if not lists.get("force"):
            return [
                self.state_machine.reporter.error(
                    "free-body-diagram requires at least one `force:` line", line=self.lineno
                )
            ]

        try:
            scene = compile_scene(
                scalars["object"],
                lists["force"],
                scalars.get("velocity"),
                axis_indicator=bool(parse_bool(scalars.get("axis-indicator", "true"))),
            )
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            return [
                self.state_machine.reporter.error(
                    f"free-body-diagram: {exc}", line=self.lineno
                )
            ]

        xmin, xmax, ymin, ymax = scene["bounds"]
        plot_options = {
            key: value for key, value in scalars.items() if key not in _OWN_KEYS
        }
        plot_options.update(self.options)
        plot_options.setdefault("xmin", f"{xmin:g}")
        plot_options.setdefault("xmax", f"{xmax:g}")
        plot_options.setdefault("ymin", f"{ymin:g}")
        plot_options.setdefault("ymax", f"{ymax:g}")

        # The main plot frame is decorative here; our own corner indicator carries
        # the x/y directions, and `equal` keeps the object's real proportions.
        axis_lines = [f"axis: {mode}" for mode in lists["axis"]] or ["axis: off", "axis: equal"]

        caption_lines = content_lines[caption_idx:]
        plot_content = [*axis_lines, *scene["lines"]]
        if caption_lines:
            plot_content += ["", *caption_lines]

        plot_directive = PlotDirective(
            name="plot",
            arguments=[],
            options=plot_options,
            content=StringList(plot_content),
            lineno=self.lineno,
            content_offset=self.content_offset,
            block_text=self.block_text,
            state=self.state,
            state_machine=self.state_machine,
        )
        return plot_directive.run()


def setup(app):
    app.add_directive("free-body-diagram", FreeBodyDiagramDirective)
    return {"version": "0.1", "parallel_read_safe": True, "parallel_write_safe": True}
