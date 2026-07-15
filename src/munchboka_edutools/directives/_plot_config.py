"""Scalar configuration parsing for the experimental plot-2 directive."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from typing import Any

from docutils.parsers.rst import directives

from munchboka_edutools.directives._plot_common import parse_bool


PLOT_MULTI_KEYS = {
    "function",
    "point",
    "annotate",
    "text",
    "vline",
    "hline",
    "line",
    "tangent",
    "polygon",
    "axis",
    "fill-polygon",
    "fill-between",
    "bar",
    "vector",
    "line-segment",
    "angle-arc",
    "circle",
    "ellipse",
    "curve",
    "implicit-curve",
    "triangle",
}


PLOT_OPTION_SPEC = {
    "width": directives.length_or_percentage_or_unitless,
    "align": lambda value: directives.choice(value, ["left", "center", "right"]),
    "class": directives.class_option,
    "name": directives.unchanged,
    "nocache": directives.flag,
    "debug": directives.flag,
    "alt": directives.unchanged,
    "usetex": directives.unchanged,
    "handdrawn": directives.unchanged,
    "xmin": directives.unchanged,
    "xmax": directives.unchanged,
    "ymin": directives.unchanged,
    "ymax": directives.unchanged,
    "xstep": directives.unchanged,
    "ystep": directives.unchanged,
    "fontsize": directives.unchanged,
    "ticks": directives.unchanged,
    "grid": directives.unchanged,
    "xticks": directives.unchanged,
    "yticks": directives.unchanged,
    "xtick-format": directives.unchanged,
    "lw": directives.unchanged,
    "alpha": directives.unchanged,
    "figsize": directives.unchanged,
    "endpoint_markers": directives.unchanged,
    "function-endpoints": directives.unchanged,
    "xlabel": directives.unchanged,
    "ylabel": directives.unchanged,
}


@dataclass(frozen=True)
class PlotConfig:
    """Parsed scalar options for a 2D plot directive."""

    merged: dict[str, Any]
    xmin: float = -6.0
    xmax: float = 6.0
    ymin: float = -6.0
    ymax: float = 6.0
    xstep: float = 1.0
    ystep: float = 1.0
    fontsize: float = 20.0
    lw: float = 2.5
    alpha: float | None = None
    ticks: bool = True
    grid: bool = True
    endpoint_markers: bool = False
    xticks: str | None = None
    yticks: str | None = None
    xtick_format: str | None = None
    xlabel: str | None = None
    ylabel: str | None = None
    figsize: tuple[float, float] | None = None
    use_usetex: bool = True
    handdrawn: bool = False
    width: str | None = None
    align: str = "center"
    classes: list[str] | None = None
    explicit_name: str | None = None
    internal_mode: bool = False
    internal_name: str | None = None
    stable_name: str | None = None
    debug_mode: bool = False
    nocache: bool = False
    alt: str = "Tilpasset figur"

    @classmethod
    def from_values(
        cls,
        scalars: dict[str, Any],
        options: dict[str, Any] | None = None,
        *,
        default_usetex: bool = True,
    ) -> "PlotConfig":
        """Parse merged front-matter scalars and directive options."""

        merged = {**scalars, **(options or {})}

        ticks_flag = parse_bool(merged.get("ticks"), default=None)
        grid_flag = parse_bool(merged.get("grid"), default=None)
        if ticks_flag is None and grid_flag is None:
            ticks_flag = True
            grid_flag = True
        else:
            ticks_flag = True if ticks_flag is None else bool(ticks_flag)
            grid_flag = True if grid_flag is None else bool(grid_flag)

        usetex_opt = parse_bool(merged.get("usetex"), default=None)
        use_usetex = bool(usetex_opt) if usetex_opt is not None else bool(default_usetex)

        handdrawn = bool(parse_bool(merged.get("handdrawn"), default=False))
        if handdrawn and use_usetex:
            use_usetex = False

        explicit_name = merged.get("name")
        internal_mode = "internal" in merged
        internal_name = merged.get("internal-name") if internal_mode else None
        stable_name = explicit_name or internal_name

        return cls(
            merged=merged,
            xmin=_float_option(merged, "xmin", -6.0),
            xmax=_float_option(merged, "xmax", 6.0),
            ymin=_float_option(merged, "ymin", -6.0),
            ymax=_float_option(merged, "ymax", 6.0),
            xstep=_float_option(merged, "xstep", 1.0),
            ystep=_float_option(merged, "ystep", 1.0),
            fontsize=_float_option(merged, "fontsize", 20.0),
            lw=_float_option(merged, "lw", 2.5),
            alpha=_optional_float(merged.get("alpha")),
            ticks=bool(ticks_flag),
            grid=bool(grid_flag),
            endpoint_markers=bool(
                parse_bool(
                    merged.get("function-endpoints") or merged.get("endpoint_markers"),
                    default=False,
                )
            ),
            xticks=_optional_string(merged.get("xticks")),
            yticks=_optional_string(merged.get("yticks")),
            xtick_format=_optional_string(merged.get("xtick-format")),
            xlabel=_optional_string(merged.get("xlabel")),
            ylabel=_optional_string(merged.get("ylabel")),
            figsize=parse_figsize(merged.get("figsize")),
            use_usetex=use_usetex,
            handdrawn=handdrawn,
            width=_optional_string(merged.get("width")),
            align=str(merged.get("align", "center")),
            classes=_parse_classes(merged.get("class")),
            explicit_name=_optional_string(explicit_name),
            internal_mode=internal_mode,
            internal_name=_optional_string(internal_name),
            stable_name=_optional_string(stable_name),
            debug_mode="debug" in merged,
            nocache="nocache" in merged,
            alt=str(merged.get("alt", "Tilpasset figur")),
        )


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _parse_classes(value: Any) -> list[str] | None:
    if not value:
        return None
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return [part for part in str(value).split() if part]


def _float_option(values: dict[str, Any], key: str, default: float) -> float:
    value = values.get(key)
    if value in (None, ""):
        return default
    try:
        return float(value)
    except Exception:
        pass
    try:
        import sympy

        allowed = {
            name: getattr(sympy, name)
            for name in ["pi", "E", "sqrt", "exp", "log", "sin", "cos", "tan"]
            if hasattr(sympy, name)
        }
        return float(sympy.sympify(str(value), locals=allowed).evalf())
    except Exception:
        return default


def _optional_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except Exception:
        return None


def parse_figsize(value: Any) -> tuple[float, float] | None:
    """Parse ``figsize`` as accepted by the legacy plot directive."""

    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None

    try:
        literal = ast.literal_eval(text)
    except Exception:
        literal = None
    if isinstance(literal, (list, tuple)) and len(literal) >= 2:
        try:
            width = float(literal[0])
            height = float(literal[1])
        except Exception:
            return None
        return (width, height) if width > 0 and height > 0 else None

    match = re.match(
        r"\(\s*([0-9]+(?:\.[0-9]+)?)\s*,\s*([0-9]+(?:\.[0-9]+)?)\s*\)",
        text,
    )
    if not match:
        return None
    try:
        width = float(match.group(1))
        height = float(match.group(2))
    except Exception:
        return None
    return (width, height) if width > 0 and height > 0 else None


__all__ = [
    "PLOT_MULTI_KEYS",
    "PLOT_OPTION_SPEC",
    "PlotConfig",
    "parse_figsize",
]
