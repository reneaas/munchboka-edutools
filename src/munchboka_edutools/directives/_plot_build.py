"""Build-context assembly for the experimental plot-2 directive."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from munchboka_edutools.directives._plot_common import parse_kv_block
from munchboka_edutools.directives._plot_config import PLOT_MULTI_KEYS, PlotConfig
from munchboka_edutools.directives._plot_macros import PlotMacroContext, parse_plot_macros


@dataclass(frozen=True)
class Plot2BuildContext:
    """Parsed non-rendering input for a ``plot-2`` directive."""

    raw_lines: list[str]
    expanded_lines: list[str]
    macro_ctx: PlotMacroContext
    scalars: dict[str, Any]
    lists: dict[str, list[str]]
    caption_idx: int
    config: PlotConfig

    @property
    def merged(self) -> dict[str, Any]:
        return self.config.merged

    @property
    def caption_lines(self) -> list[str]:
        return list(self.expanded_lines[self.caption_idx :])

    @classmethod
    def from_values(
        cls,
        lines: list[str],
        options: dict[str, Any] | None = None,
        *,
        default_usetex: bool = True,
    ) -> "Plot2BuildContext":
        raw_lines = list(lines)
        expanded_lines, macro_ctx = parse_plot_macros(raw_lines)
        scalars, lists, caption_idx = parse_kv_block(expanded_lines, PLOT_MULTI_KEYS)
        config = PlotConfig.from_values(
            scalars,
            options or {},
            default_usetex=default_usetex,
        )
        return cls(
            raw_lines=raw_lines,
            expanded_lines=expanded_lines,
            macro_ctx=macro_ctx,
            scalars=scalars,
            lists=lists,
            caption_idx=caption_idx,
            config=config,
        )

    @classmethod
    def from_directive(cls, directive: Any) -> "Plot2BuildContext":
        env = directive.state.document.settings.env
        default_usetex = bool(getattr(env.config, "plot_default_usetex", True))
        return cls.from_values(
            list(directive.content),
            dict(directive.options),
            default_usetex=default_usetex,
        )


__all__ = ["Plot2BuildContext"]
