"""Experimental plot-2 directive.

This module intentionally leaves the existing ``plot`` directive untouched.
For now, ``plot-2`` is a feature-parity entrypoint that delegates to the
current implementation.  It gives us a separate directive name where the plot
refactor can proceed without changing behaviour for existing books.
"""

from __future__ import annotations

from typing import Any

from munchboka_edutools.directives._plot_build import Plot2BuildContext
from munchboka_edutools.directives._plot_common import parse_kv_block
from munchboka_edutools.directives._plot_config import PLOT_MULTI_KEYS, PLOT_OPTION_SPEC
from munchboka_edutools.directives.plot import PlotDirective


class Plot2Directive(PlotDirective):
    """Compatibility entrypoint for the refactored plot directive."""

    option_spec = PLOT_OPTION_SPEC

    def _build_context(self) -> Plot2BuildContext:
        return Plot2BuildContext.from_directive(self)

    def _parse_kv_block(
        self, lines: list[str] | None = None
    ) -> tuple[dict[str, Any], dict[str, list[str]], int]:
        return parse_kv_block(
            list(self.content) if lines is None else list(lines),
            PLOT_MULTI_KEYS,
        )

    def run(self):
        # Assemble and retain the refactored input/config context before
        # delegating rendering to the legacy implementation.  Subsequent
        # plot-2 refactors can consume this context while plot.py remains
        # untouched.
        self._plot2_build_context = self._build_context()
        return super().run()


def setup(app):  # pragma: no cover
    app.add_directive("plot-2", Plot2Directive)
    app.add_directive("plot2", Plot2Directive)
    return {"version": "0.1", "parallel_read_safe": True, "parallel_write_safe": True}
