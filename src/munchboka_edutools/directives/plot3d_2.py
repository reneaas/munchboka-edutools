"""Experimental Matplotlib-backed 3D plot directive."""

from __future__ import annotations

import hashlib
import math
import os
import re
import shutil
from pathlib import Path
from typing import Any

from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective

from munchboka_edutools.directives._plot_common import (
    InlineSvgOptions,
    build_inline_svg_figure,
    parse_bool,
    parse_kv_block,
    prepare_inline_svg,
)


_MULTI_KEYS: set[str] = {
    "curve",
    "point",
    "plane",
    "prism",
    "pyramid",
    "sphere",
    "text",
    "vector",
    "solid-of-revolution",
}


def _split_top_level_commas(text: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    quote: str | None = None
    escaped = False
    for char in text:
        if escaped:
            current.append(char)
            escaped = False
        elif quote:
            current.append(char)
            if char == "\\":
                escaped = True
            elif char == quote:
                quote = None
        elif char in {"'", '"'}:
            quote = char
            current.append(char)
        elif char in "([{":
            depth += 1
            current.append(char)
        elif char in ")]}":
            depth = max(0, depth - 1)
            current.append(char)
        elif char == "," and depth == 0:
            token = "".join(current).strip()
            if token:
                parts.append(token)
            current = []
        else:
            current.append(char)
    tail = "".join(current).strip()
    if tail:
        parts.append(tail)
    return parts


def _strip_wrapping_quotes(value: str) -> str:
    text = value.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
        return text[1:-1].replace(f"\\{text[0]}", text[0])
    return text


def _eval_float(value: Any, default: float) -> float:
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


def _parse_range(value: Any, default: float) -> tuple[float, float]:
    if value in (None, ""):
        return -default, default

    text = str(value).strip()
    if text.startswith(("(", "[", "{")) and text.endswith((")", "]", "}")):
        text = text[1:-1]
    parts = [part.strip() for part in text.split(",") if part.strip()]
    if len(parts) == 1:
        radius = abs(_eval_float(parts[0], default))
        return -radius, radius
    if len(parts) >= 2:
        lo = _eval_float(parts[0], -default)
        hi = _eval_float(parts[1], default)
        if hi < lo:
            lo, hi = hi, lo
        return lo, hi
    return -default, default


def _parse_span(value: Any, default: tuple[float, float]) -> tuple[float, float]:
    if value in (None, ""):
        return default
    text = str(value).strip()
    if text.startswith(("(", "[", "{")) and text.endswith((")", "]", "}")):
        text = text[1:-1]
    parts = _split_top_level_commas(text)
    if len(parts) == 1:
        width = abs(_eval_float(parts[0], default[0]))
        return width, width
    if len(parts) >= 2:
        return (
            abs(_eval_float(parts[0], default[0])),
            abs(_eval_float(parts[1], default[1])),
        )
    return default


def _parse_alpha(value: Any, default: float = 0.35) -> float:
    alpha = _eval_float(value, default)
    return min(max(alpha, 0.0), 1.0)


def _resolve_color(value: str | None, default: str = "blue") -> Any:
    token = (value or default).strip()
    try:
        import plotmath  # type: ignore
    except Exception:
        try:
            from munchboka_edutools import _plotmath_shim as plotmath  # type: ignore
        except Exception:
            plotmath = None

    if plotmath is not None:
        mapped = getattr(plotmath, "COLORS", {}).get(token)
        if mapped is not None:
            return mapped
    return token


def _parse_primitive_kwargs(value: str) -> dict[str, str]:
    kwargs: dict[str, str] = {}
    for part in _split_top_level_commas(value):
        if "=" not in part:
            continue
        key, raw_value = part.split("=", 1)
        key = key.strip().lower()
        if key:
            kwargs[key] = raw_value.strip()
    return kwargs


def _parse_triple(value: str) -> tuple[float, float, float]:
    text = value.strip()
    if text.startswith("(") and text.endswith(")"):
        text = text[1:-1]
    parts = _split_top_level_commas(text)
    if len(parts) != 3:
        raise ValueError(f"Expected three coordinates, got: {value}")
    return (
        _eval_float(parts[0], 0.0),
        _eval_float(parts[1], 0.0),
        _eval_float(parts[2], 0.0),
    )


def _parse_triple_list(value: str) -> list[tuple[float, float, float]]:
    text = value.strip()
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1]
    points = [_parse_triple(part) for part in _split_top_level_commas(text)]
    if len(points) < 3:
        raise ValueError("Expected at least three points")
    return points


def _parse_vector_primitive(value: str) -> dict[str, Any] | None:
    try:
        parts = _split_top_level_commas(value)
        if len(parts) < 2:
            return None
        start = _parse_triple(parts[0])
        end = _parse_triple(parts[1])
        color = _resolve_color(parts[2] if len(parts) >= 3 else None)
        return {"start": start, "end": end, "color": color}
    except Exception:
        return None


def _parse_point_primitive(value: str) -> dict[str, Any] | None:
    try:
        parts = _split_top_level_commas(value)
        if not parts:
            return None
        coords = _parse_triple(parts[0])
        color = _resolve_color(parts[1] if len(parts) >= 2 else None)
        return {"coords": coords, "color": color}
    except Exception:
        return None


def _parse_text_primitive(value: str) -> dict[str, Any] | None:
    try:
        kwargs = _parse_primitive_kwargs(value)
        if "at" not in kwargs:
            return None
        raw_value = kwargs.get("value", kwargs.get("label"))
        if raw_value is None:
            return None
        ha = kwargs.get("ha", "center").strip().lower()
        va = kwargs.get("va", "center").strip().lower()
        if ha not in {"left", "center", "right"}:
            ha = "center"
        if va not in {"top", "center", "bottom", "baseline"}:
            va = "center"

        fontsize = None
        if "fontsize" in kwargs:
            fontsize = _eval_float(kwargs["fontsize"], 12.0)

        return {
            "at": _parse_triple(kwargs["at"]),
            "value": _strip_wrapping_quotes(raw_value),
            "color": _resolve_color(kwargs.get("color"), default="black"),
            "fontsize": fontsize,
            "offset": _parse_triple(kwargs.get("offset", "(0, 0, 0)")),
            "ha": ha,
            "va": va,
        }
    except Exception:
        return None


def _parse_solid_of_revolution_primitive(value: str) -> dict[str, Any] | None:
    try:
        parts = _split_top_level_commas(value)
        if len(parts) < 2:
            return None
        xmin, xmax = _parse_range(parts[1], 1.0)
        color = _resolve_color(parts[2] if len(parts) >= 3 else None)
        return {
            "expr": parts[0].strip(),
            "xrange": (xmin, xmax),
            "color": color,
        }
    except Exception:
        return None


def _parse_plane_primitive(value: str) -> dict[str, Any] | None:
    try:
        kwargs = _parse_primitive_kwargs(value)
        color = _resolve_color(kwargs.get("color"))
        alpha = _parse_alpha(kwargs.get("alpha"), 0.35)

        if "equation" in kwargs:
            plane: dict[str, Any] = {
                "kind": "equation",
                "equation": kwargs["equation"],
                "color": color,
                "alpha": alpha,
            }
            for axis in ("x", "y", "z"):
                key = f"{axis}range"
                if key in kwargs:
                    plane[key] = _parse_range(kwargs[key], 5.0)
            return plane

        if "normal" in kwargs and "point" in kwargs:
            return {
                "kind": "normal-point",
                "normal": _parse_triple(kwargs["normal"]),
                "point": _parse_triple(kwargs["point"]),
                "span": _parse_span(kwargs.get("span"), (4.0, 4.0)),
                "color": color,
                "alpha": alpha,
            }
    except Exception:
        return None
    return None


def _regular_ngon_base(
    *,
    center: tuple[float, float, float],
    radius: float,
    sides: int,
    rotation: float,
) -> list[tuple[float, float, float]]:
    cx, cy, cz = center
    return [
        (
            cx + radius * math.cos(rotation + 2 * math.pi * idx / sides),
            cy + radius * math.sin(rotation + 2 * math.pi * idx / sides),
            cz,
        )
        for idx in range(sides)
    ]


def _parse_pyramid_primitive(value: str) -> dict[str, Any] | None:
    try:
        kwargs = _parse_primitive_kwargs(value)
        if "apex" not in kwargs:
            return None

        color = _resolve_color(kwargs.get("color"))
        edgecolor = _resolve_color(kwargs.get("edgecolor"), default="black")
        alpha = _parse_alpha(kwargs.get("alpha"), 0.45)
        apex = _parse_triple(kwargs["apex"])

        if "base" in kwargs:
            base = _parse_triple_list(kwargs["base"])
        elif {"center", "radius", "sides"}.issubset(kwargs):
            radius = abs(_eval_float(kwargs["radius"], 1.0))
            sides = max(3, int(round(_eval_float(kwargs["sides"], 4.0))))
            rotation = _eval_float(kwargs.get("rotation"), 0.0)
            base = _regular_ngon_base(
                center=_parse_triple(kwargs["center"]),
                radius=radius,
                sides=sides,
                rotation=rotation,
            )
        else:
            return None

        return {
            "base": base,
            "apex": apex,
            "color": color,
            "edgecolor": edgecolor,
            "alpha": alpha,
        }
    except Exception:
        return None


def _parse_prism_primitive(value: str) -> dict[str, Any] | None:
    try:
        kwargs = _parse_primitive_kwargs(value)
        color = _resolve_color(kwargs.get("color"))
        edgecolor = _resolve_color(kwargs.get("edgecolor"), default="black")
        alpha = _parse_alpha(kwargs.get("alpha"), 0.45)

        if "vector" in kwargs:
            extrusion = _parse_triple(kwargs["vector"])
        elif "height" in kwargs:
            extrusion = (0.0, 0.0, _eval_float(kwargs["height"], 1.0))
        else:
            return None

        if "base" in kwargs:
            base = _parse_triple_list(kwargs["base"])
        elif {"center", "radius", "sides"}.issubset(kwargs):
            radius = abs(_eval_float(kwargs["radius"], 1.0))
            sides = max(3, int(round(_eval_float(kwargs["sides"], 4.0))))
            rotation = _eval_float(kwargs.get("rotation"), 0.0)
            base = _regular_ngon_base(
                center=_parse_triple(kwargs["center"]),
                radius=radius,
                sides=sides,
                rotation=rotation,
            )
        else:
            return None

        dx, dy, dz = extrusion
        top = [(x + dx, y + dy, z + dz) for x, y, z in base]
        return {
            "base": base,
            "top": top,
            "color": color,
            "edgecolor": edgecolor,
            "alpha": alpha,
        }
    except Exception:
        return None


def _parse_sphere_primitive(value: str) -> dict[str, Any] | None:
    try:
        kwargs = _parse_primitive_kwargs(value)
        radius = abs(_eval_float(kwargs.get("radius"), 1.0))
        resolution = max(8, min(128, int(round(_eval_float(kwargs.get("resolution"), 48.0)))))
        return {
            "center": _parse_triple(kwargs.get("center", "(0, 0, 0)")),
            "radius": radius,
            "color": _resolve_color(kwargs.get("color")),
            "alpha": _parse_alpha(kwargs.get("alpha"), 0.55),
            "resolution": resolution,
        }
    except Exception:
        return None


def _parse_curve_primitive(value: str) -> dict[str, Any] | None:
    try:
        kwargs = _parse_primitive_kwargs(value)
        if not {"x", "y", "z"}.issubset(kwargs):
            return None
        samples = max(2, min(5000, int(round(_eval_float(kwargs.get("samples"), 300.0)))))
        trange = kwargs.get("trange", kwargs.get("t"))
        arrow_count = max(
            0,
            min(
                20,
                int(round(_eval_float(kwargs.get("arrow-count", kwargs.get("arrows-count")), 3.0))),
            ),
        )
        return {
            "x": kwargs["x"].strip(),
            "y": kwargs["y"].strip(),
            "z": kwargs["z"].strip(),
            "trange": _parse_range(trange, 5.0),
            "color": _resolve_color(kwargs.get("color")),
            "lw": _eval_float(kwargs["lw"], 1.5) if "lw" in kwargs else None,
            "samples": samples,
            "arrows": bool(parse_bool(kwargs.get("arrows"), default=True)),
            "arrow_count": arrow_count,
        }
    except Exception:
        return None


def _tick_values(lo: float, hi: float, step: float) -> list[float]:
    if step <= 0:
        step = 1.0
    start = math.ceil(lo / step) * step
    vals: list[float] = []
    cur = start
    guard = 0
    while cur <= hi + 1e-9 and guard < 1000:
        is_endpoint = abs(cur - lo) < 1e-9 or abs(cur - hi) < 1e-9
        if abs(cur) > 1e-9 and not is_endpoint:
            vals.append(0.0 if abs(cur) < 1e-9 else cur)
        cur += step
        guard += 1
    return vals


def _format_tick(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.3g}"


def _draw_centered_axes(
    ax,
    *,
    xrange: tuple[float, float],
    yrange: tuple[float, float],
    zrange: tuple[float, float],
    xlabel: str,
    ylabel: str,
    zlabel: str,
    ticks: bool,
    xstep: float,
    ystep: float,
    zstep: float,
    fontsize: float,
    lw: float,
) -> None:
    xlo, xhi = xrange
    ylo, yhi = yrange
    zlo, zhi = zrange
    axis_color = "#222222"
    tick_color = "#555555"

    ax.plot([xlo, xhi], [0, 0], [0, 0], color=axis_color, lw=lw)
    ax.plot([0, 0], [ylo, yhi], [0, 0], color=axis_color, lw=lw)
    ax.plot([0, 0], [0, 0], [zlo, zhi], color=axis_color, lw=lw)

    arrow_ratio = 0.08
    x_arrow = max((xhi - xlo) * arrow_ratio, 1e-9)
    y_arrow = max((yhi - ylo) * arrow_ratio, 1e-9)
    z_arrow = max((zhi - zlo) * arrow_ratio, 1e-9)
    ax.quiver(
        xhi - x_arrow,
        0,
        0,
        x_arrow,
        0,
        0,
        color=axis_color,
        linewidth=lw,
        arrow_length_ratio=0.45,
        normalize=False,
    )
    ax.quiver(
        0,
        yhi - y_arrow,
        0,
        0,
        y_arrow,
        0,
        color=axis_color,
        linewidth=lw,
        arrow_length_ratio=0.45,
        normalize=False,
    )
    ax.quiver(
        0,
        0,
        zhi - z_arrow,
        0,
        0,
        z_arrow,
        color=axis_color,
        linewidth=lw,
        arrow_length_ratio=0.45,
        normalize=False,
    )

    xpad = 0.08 * (xhi - xlo or 1.0)
    ypad = 0.08 * (yhi - ylo or 1.0)
    zpad = 0.08 * (zhi - zlo or 1.0)
    ax.text(xhi + xpad, 0, 0, xlabel, fontsize=fontsize, color=axis_color)
    ax.text(0, yhi + ypad, 0, ylabel, fontsize=fontsize, color=axis_color)
    ax.text(0, 0, zhi + zpad, zlabel, fontsize=fontsize, color=axis_color)

    if not ticks:
        return

    tick_len = 0.025 * max(xhi - xlo, yhi - ylo, zhi - zlo, 1.0)
    tick_fontsize = max(6.0, fontsize * 0.65)

    for x in _tick_values(xlo, xhi, xstep):
        ax.plot([x, x], [-tick_len, tick_len], [0, 0], color=tick_color, lw=0.8)
        ax.text(x, -2.5 * tick_len, 0, _format_tick(x), fontsize=tick_fontsize, color=tick_color)

    for y in _tick_values(ylo, yhi, ystep):
        ax.plot([-tick_len, tick_len], [y, y], [0, 0], color=tick_color, lw=0.8)
        ax.text(-2.5 * tick_len, y, 0, _format_tick(y), fontsize=tick_fontsize, color=tick_color)

    for z in _tick_values(zlo, zhi, zstep):
        ax.plot([0, 0], [-tick_len, tick_len], [z, z], color=tick_color, lw=0.8)
        ax.text(0, -2.5 * tick_len, z, _format_tick(z), fontsize=tick_fontsize, color=tick_color)


def _draw_vector(ax, vector: dict[str, Any], *, lw: float) -> None:
    x0, y0, z0 = vector["start"]
    x1, y1, z1 = vector["end"]
    dx = x1 - x0
    dy = y1 - y0
    dz = z1 - z0
    if abs(dx) < 1e-12 and abs(dy) < 1e-12 and abs(dz) < 1e-12:
        return
    ax.quiver(
        x0,
        y0,
        z0,
        dx,
        dy,
        dz,
        color=vector["color"],
        linewidth=lw,
        arrow_length_ratio=0.12,
        normalize=False,
    )


def _draw_point(ax, point: dict[str, Any]) -> None:
    x, y, z = point["coords"]
    ax.scatter(
        [x],
        [y],
        [z],
        color=point["color"],
        s=42,
        depthshade=False,
        zorder=20,
    )


def _draw_text(ax, text_item: dict[str, Any], *, default_fontsize: float) -> None:
    x, y, z = text_item["at"]
    dx, dy, dz = text_item["offset"]
    fontsize = text_item["fontsize"] if text_item["fontsize"] is not None else default_fontsize
    ax.text(
        x + dx,
        y + dy,
        z + dz,
        text_item["value"],
        color=text_item["color"],
        fontsize=fontsize,
        ha=text_item["ha"],
        va=text_item["va"],
        zorder=30,
    )


def _sympy_plane_locals() -> dict[str, Any]:
    import sympy

    allowed = {"x": sympy.symbols("x"), "y": sympy.symbols("y"), "z": sympy.symbols("z")}
    allowed.update(
        {
            name: getattr(sympy, name)
            for name in [
                "pi",
                "E",
                "sqrt",
                "exp",
                "log",
                "sin",
                "cos",
                "tan",
                "asin",
                "acos",
                "atan",
                "Rational",
            ]
            if hasattr(sympy, name)
        }
    )
    return allowed


def _plane_surface_grids(
    plane: dict[str, Any],
    *,
    xrange: tuple[float, float],
    yrange: tuple[float, float],
    zrange: tuple[float, float],
):
    import numpy as np

    if plane["kind"] == "normal-point":
        normal = np.asarray(plane["normal"], dtype=float)
        norm = float(np.linalg.norm(normal))
        if norm < 1e-12:
            return None
        normal = normal / norm
        reference = np.array([1.0, 0.0, 0.0])
        if abs(float(np.dot(normal, reference))) > 0.9:
            reference = np.array([0.0, 1.0, 0.0])
        u = np.cross(normal, reference)
        u = u / np.linalg.norm(u)
        v = np.cross(normal, u)

        width, height = plane["span"]
        s_values = np.linspace(-width / 2, width / 2, 2)
        t_values = np.linspace(-height / 2, height / 2, 2)
        s_grid, t_grid = np.meshgrid(s_values, t_values)
        center = np.asarray(plane["point"], dtype=float)
        coords = center + s_grid[..., None] * u + t_grid[..., None] * v
        return coords[..., 0], coords[..., 1], coords[..., 2]

    if plane["kind"] != "equation":
        return None

    import sympy

    locals_ = _sympy_plane_locals()
    x, y, z = locals_["x"], locals_["y"], locals_["z"]
    equation = str(plane["equation"]).replace("^", "**")
    if "=" in equation:
        lhs_raw, rhs_raw = equation.split("=", 1)
        lhs = sympy.sympify(lhs_raw.strip(), locals=locals_)
        rhs = sympy.sympify(rhs_raw.strip(), locals=locals_)
        expr = lhs - rhs
        lhs_symbol = lhs if lhs in {x, y, z} else None
        rhs_symbol = rhs if rhs in {x, y, z} else None
        target = lhs_symbol or rhs_symbol
    else:
        expr = sympy.sympify(equation, locals=locals_)
        target = None

    symbols = (x, y, z)
    if target is None:
        coeffs = {symbol: expr.coeff(symbol) for symbol in symbols}
        usable = [
            (symbol, abs(float(coeff.evalf())))
            for symbol, coeff in coeffs.items()
            if coeff != 0
        ]
        if not usable:
            return None
        target = max(usable, key=lambda item: item[1])[0]

    solutions = sympy.solve(sympy.Eq(expr, 0), target, dict=False)
    if not solutions:
        return None
    solution = solutions[0]
    if solution.has(target):
        return None

    ranges = {
        x: plane.get("xrange", xrange),
        y: plane.get("yrange", yrange),
        z: plane.get("zrange", zrange),
    }
    free_symbols = [symbol for symbol in symbols if symbol != target]
    first, second = free_symbols
    first_values = np.linspace(ranges[first][0], ranges[first][1], 2)
    second_values = np.linspace(ranges[second][0], ranges[second][1], 2)
    first_grid, second_grid = np.meshgrid(first_values, second_values)
    fn = sympy.lambdify((first, second), solution, modules=["numpy"])
    target_grid = np.asarray(fn(first_grid, second_grid), dtype=float)
    if target_grid.ndim == 0:
        target_grid = np.full_like(first_grid, float(target_grid), dtype=float)

    grids = {first: first_grid, second: second_grid, target: target_grid}
    return grids[x], grids[y], grids[z]


def _draw_plane(
    ax,
    plane: dict[str, Any],
    *,
    xrange: tuple[float, float],
    yrange: tuple[float, float],
    zrange: tuple[float, float],
) -> None:
    grids = _plane_surface_grids(plane, xrange=xrange, yrange=yrange, zrange=zrange)
    if grids is None:
        return
    x_grid, y_grid, z_grid = grids
    ax.plot_surface(
        x_grid,
        y_grid,
        z_grid,
        color=plane["color"],
        alpha=plane["alpha"],
        linewidth=0,
        antialiased=True,
        shade=False,
    )


def _view_direction(elev: float, azim: float):
    import numpy as np

    elev_rad = math.radians(elev)
    azim_rad = math.radians(azim)
    direction = np.array(
        [
            math.cos(elev_rad) * math.cos(azim_rad),
            math.cos(elev_rad) * math.sin(azim_rad),
            math.sin(elev_rad),
        ],
        dtype=float,
    )
    norm = float(np.linalg.norm(direction))
    if norm < 1e-12:
        return np.array([0.0, 0.0, 1.0], dtype=float)
    return direction / norm


def _oriented_face_normal(face: list[tuple[float, float, float]], object_center: Any):
    import numpy as np

    pts = np.asarray(face, dtype=float)
    if len(pts) < 3:
        return np.array([0.0, 0.0, 0.0], dtype=float)

    normal = np.array([0.0, 0.0, 0.0], dtype=float)
    for idx in range(1, len(pts) - 1):
        normal = np.cross(pts[idx] - pts[0], pts[idx + 1] - pts[0])
        if float(np.linalg.norm(normal)) > 1e-12:
            break

    norm = float(np.linalg.norm(normal))
    if norm < 1e-12:
        return np.array([0.0, 0.0, 0.0], dtype=float)

    normal = normal / norm
    face_center = np.mean(pts, axis=0)
    if float(np.dot(normal, face_center - object_center)) < 0:
        normal = -normal
    return normal


def _front_back_poly_faces(
    faces: list[list[tuple[float, float, float]]],
    *,
    elev: float,
    azim: float,
) -> tuple[list[list[tuple[float, float, float]]], list[list[tuple[float, float, float]]]]:
    import numpy as np

    if not faces:
        return [], []

    view_direction = _view_direction(elev, azim)
    object_center = np.mean(
        np.concatenate([np.asarray(face, dtype=float) for face in faces], axis=0),
        axis=0,
    )

    front_faces: list[list[tuple[float, float, float]]] = []
    back_faces: list[list[tuple[float, float, float]]] = []
    for face in faces:
        normal = _oriented_face_normal(face, object_center)
        if float(np.dot(normal, view_direction)) >= 0:
            front_faces.append(face)
        else:
            back_faces.append(face)

    return front_faces, back_faces


def _poly_object_center(faces: list[list[tuple[float, float, float]]]):
    import numpy as np

    return np.mean(
        np.concatenate([np.asarray(face, dtype=float) for face in faces], axis=0),
        axis=0,
    )


def _poly_face_view_score(
    face: list[tuple[float, float, float]],
    *,
    object_center: Any,
    view_direction: Any,
) -> float:
    import numpy as np

    normal = _oriented_face_normal(face, object_center)
    norm = float(np.linalg.norm(normal))
    if norm < 1e-12:
        return 0.0
    return float(np.dot(normal / norm, view_direction))


def _front_back_poly_facecolors(
    faces: list[list[tuple[float, float, float]]],
    *,
    color: Any,
    alpha: float,
    elev: float,
    azim: float,
    front: bool,
) -> list[tuple[float, float, float, float]]:
    import numpy as np
    from matplotlib import colors as mcolors

    base_rgb = np.array(mcolors.to_rgb(color), dtype=float)
    gray_rgb = np.full(3, float(np.mean(base_rgb)), dtype=float)
    view_direction = _view_direction(elev, azim)
    object_center = _poly_object_center(faces)
    colors: list[tuple[float, float, float, float]] = []

    for face in faces:
        score = _poly_face_view_score(
            face,
            object_center=object_center,
            view_direction=view_direction,
        )
        if front:
            facing = max(0.0, score)
            # Front faces keep the base hue, with an intentionally exaggerated
            # brightness spread so adjacent visible sides read as different.
            rgb = base_rgb * (0.36 + 0.62 * facing)
            rgb = rgb + (1.0 - rgb) * (0.04 + 0.30 * facing)
            face_alpha = alpha * (0.62 + 0.38 * facing)
        else:
            facing_away = max(0.0, -score)
            # Back faces are deliberately muted and transparent, but still
            # vary by angle so the hidden solid structure remains legible.
            muted_rgb = base_rgb * 0.10 + gray_rgb * 0.90
            rgb = muted_rgb * (0.24 + 0.42 * facing_away)
            rgb = rgb + np.array([1.0, 1.0, 1.0]) * (0.08 + 0.12 * (1.0 - facing_away))
            face_alpha = alpha * (0.06 + 0.26 * facing_away)

        rgb = np.clip(rgb, 0.0, 1.0)
        colors.append((float(rgb[0]), float(rgb[1]), float(rgb[2]), float(face_alpha)))

    return colors


def _add_front_back_poly_collections(
    ax,
    faces: list[list[tuple[float, float, float]]],
    *,
    color: Any,
    edgecolor: Any,
    alpha: float,
    lw: float,
    elev: float,
    azim: float,
) -> None:
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    front_faces, back_faces = _front_back_poly_faces(faces, elev=elev, azim=azim)
    line_width = max(0.4, lw * 0.55)

    if back_faces:
        back_collection = Poly3DCollection(
            back_faces,
            facecolors=_front_back_poly_facecolors(
                back_faces,
                color=color,
                alpha=alpha,
                elev=elev,
                azim=azim,
                front=False,
            ),
            edgecolors="#999999",
            linewidths=line_width * 0.8,
            linestyles="dashed",
        )
        ax.add_collection3d(back_collection)

    if front_faces:
        front_collection = Poly3DCollection(
            front_faces,
            facecolors=_front_back_poly_facecolors(
                front_faces,
                color=color,
                alpha=alpha,
                elev=elev,
                azim=azim,
                front=True,
            ),
            edgecolors=edgecolor,
            linewidths=line_width,
            linestyles="solid",
        )
        ax.add_collection3d(front_collection)


def _draw_pyramid(ax, pyramid: dict[str, Any], *, lw: float, elev: float, azim: float) -> None:
    base = pyramid["base"]
    apex = pyramid["apex"]
    faces = [base] + [
        [base[idx], base[(idx + 1) % len(base)], apex]
        for idx in range(len(base))
    ]
    _add_front_back_poly_collections(
        ax,
        faces,
        color=pyramid["color"],
        edgecolor=pyramid["edgecolor"],
        alpha=pyramid["alpha"],
        lw=lw,
        elev=elev,
        azim=azim,
    )


def _draw_prism(ax, prism: dict[str, Any], *, lw: float, elev: float, azim: float) -> None:
    base = prism["base"]
    top = prism["top"]
    faces = [base, list(reversed(top))] + [
        [base[idx], base[(idx + 1) % len(base)], top[(idx + 1) % len(top)], top[idx]]
        for idx in range(len(base))
    ]
    _add_front_back_poly_collections(
        ax,
        faces,
        color=prism["color"],
        edgecolor=prism["edgecolor"],
        alpha=prism["alpha"],
        lw=lw,
        elev=elev,
        azim=azim,
    )


def _sphere_surface_grids(sphere: dict[str, Any], *, elev: float, azim: float):
    import numpy as np
    from matplotlib import colors as mcolors

    cx, cy, cz = sphere["center"]
    radius = sphere["radius"]
    resolution = sphere["resolution"]
    u = np.linspace(0, 2 * np.pi, resolution)
    v = np.linspace(0, np.pi, max(8, resolution // 2))
    u_grid, v_grid = np.meshgrid(u, v)

    normal_x = np.cos(u_grid) * np.sin(v_grid)
    normal_y = np.sin(u_grid) * np.sin(v_grid)
    normal_z = np.cos(v_grid)
    x_grid = cx + radius * normal_x
    y_grid = cy + radius * normal_y
    z_grid = cz + radius * normal_z

    base_rgb = np.array(mcolors.to_rgb(sphere["color"]), dtype=float)
    view_direction = _view_direction(elev, azim)
    view_score = (
        normal_x * view_direction[0]
        + normal_y * view_direction[1]
        + normal_z * view_direction[2]
    )
    facing = np.clip(view_score, 0.0, 1.0)
    depth_weight = (view_score + 1.0) / 2.0
    intensity = 0.38 + 0.34 * facing + 0.16 * depth_weight
    rgb = base_rgb[None, None, :] * intensity[..., None]
    highlight = np.clip(facing - 0.62, 0.0, 1.0)[..., None] * 0.22
    rgb = rgb + (1.0 - rgb) * highlight
    rgb = np.clip(rgb, 0.0, 1.0)

    alpha = np.full((*rgb.shape[:2], 1), sphere["alpha"], dtype=float)
    facecolors = np.concatenate([rgb, alpha], axis=2)
    return x_grid, y_grid, z_grid, facecolors


def _sphere_guide_segments(sphere: dict[str, Any], *, elev: float, azim: float):
    import numpy as np

    center = np.asarray(sphere["center"], dtype=float)
    radius = sphere["radius"]
    view_direction = _view_direction(elev, azim)
    angles = np.linspace(0, 2 * np.pi, 193)
    circle_normals = [
        np.column_stack([np.cos(angles), np.sin(angles), np.zeros_like(angles)]),
        np.column_stack([np.cos(angles), np.zeros_like(angles), np.sin(angles)]),
        np.column_stack([np.zeros_like(angles), np.cos(angles), np.sin(angles)]),
    ]
    front_segments: list[Any] = []
    back_segments: list[Any] = []

    for normals in circle_normals:
        points = center + radius * normals
        scores = normals @ view_direction
        current: list[Any] = [points[0]]
        current_front = scores[0] >= 0
        for idx in range(1, len(points)):
            is_front = scores[idx] >= 0
            if is_front != current_front:
                if len(current) >= 2:
                    (front_segments if current_front else back_segments).append(np.asarray(current))
                current = [points[idx - 1], points[idx]]
                current_front = is_front
            else:
                current.append(points[idx])
        if len(current) >= 2:
            (front_segments if current_front else back_segments).append(np.asarray(current))

    return front_segments, back_segments


def _sphere_guide_colors(color: Any) -> tuple[Any, str]:
    import numpy as np
    from matplotlib import colors as mcolors

    base_rgb = np.array(mcolors.to_rgb(color), dtype=float)
    front_rgb = np.clip(base_rgb * 0.45, 0.0, 1.0)
    return mcolors.to_hex(front_rgb), "#9a9a9a"


def _draw_sphere_guides(ax, sphere: dict[str, Any], *, elev: float, azim: float, lw: float) -> None:
    front_segments, back_segments = _sphere_guide_segments(sphere, elev=elev, azim=azim)
    front_color, back_color = _sphere_guide_colors(sphere["color"])
    guide_lw = max(0.6, lw * 0.65)

    for segment in back_segments:
        ax.plot(
            segment[:, 0],
            segment[:, 1],
            segment[:, 2],
            color=back_color,
            lw=guide_lw,
            alpha=0.55,
            linestyle="dashed",
        )
    for segment in front_segments:
        ax.plot(
            segment[:, 0],
            segment[:, 1],
            segment[:, 2],
            color=front_color,
            lw=guide_lw * 1.15,
            alpha=0.95,
            linestyle="solid",
        )


def _draw_sphere(ax, sphere: dict[str, Any], *, elev: float, azim: float, lw: float) -> None:
    x_grid, y_grid, z_grid, facecolors = _sphere_surface_grids(
        sphere,
        elev=elev,
        azim=azim,
    )
    ax.plot_surface(
        x_grid,
        y_grid,
        z_grid,
        facecolors=facecolors,
        linewidth=0,
        antialiased=True,
        shade=False,
    )
    _draw_sphere_guides(ax, sphere, elev=elev, azim=azim, lw=lw)


def _sympy_curve_locals() -> dict[str, Any]:
    import sympy

    allowed = {"t": sympy.symbols("t")}
    allowed.update(
        {
            name: getattr(sympy, name)
            for name in [
                "pi",
                "E",
                "sqrt",
                "exp",
                "log",
                "sin",
                "cos",
                "tan",
                "asin",
                "acos",
                "atan",
                "sinh",
                "cosh",
                "tanh",
                "Rational",
                "Abs",
            ]
            if hasattr(sympy, name)
        }
    )
    return allowed


def _curve_points(curve: dict[str, Any]):
    import numpy as np
    import sympy

    locals_ = _sympy_curve_locals()
    t = locals_["t"]
    tmin, tmax = curve["trange"]
    t_values = np.linspace(tmin, tmax, curve["samples"])
    coords = []
    for key in ("x", "y", "z"):
        expr = sympy.sympify(str(curve[key]).replace("^", "**"), locals=locals_)
        fn = sympy.lambdify(t, expr, modules=["numpy"])
        values = np.asarray(fn(t_values), dtype=float)
        if values.ndim == 0:
            values = np.full_like(t_values, float(values), dtype=float)
        values = np.where(np.isfinite(values), values, np.nan)
        coords.append(values)
    return tuple(coords)


def _curve_depth_weights(points: Any, finite: Any, *, elev: float, azim: float):
    import numpy as np

    view_direction = _view_direction(elev, azim)
    weights = np.full(len(points), np.nan, dtype=float)
    if not np.any(finite):
        return weights

    depths = points[finite] @ view_direction
    depth_span = float(np.ptp(depths))
    if depth_span < 1e-12:
        weights[finite] = 0.5
    else:
        weights[finite] = (depths - float(np.min(depths))) / depth_span
    return np.clip(weights, 0.0, 1.0)


def _curve_local_depth_weights(
    points: Any,
    finite: Any,
    *,
    elev: float,
    azim: float,
    global_weights: Any | None = None,
):
    import numpy as np

    view_direction = _view_direction(elev, azim)
    weights = np.full(len(points), np.nan, dtype=float)
    if not np.any(finite):
        return weights

    if global_weights is None:
        global_weights = _curve_depth_weights(points, finite, elev=elev, azim=azim)

    depths = points @ view_direction
    finite_indices = np.flatnonzero(finite)
    run_start = 0
    for run_end in range(1, len(finite_indices) + 1):
        if run_end < len(finite_indices) and finite_indices[run_end] == finite_indices[run_end - 1] + 1:
            continue

        run_indices = finite_indices[run_start:run_end]
        run_depths = depths[run_indices]
        radius = max(4, min(24, len(run_indices) // 8))
        for run_pos, point_idx in enumerate(run_indices):
            left = max(0, run_pos - radius)
            right = min(len(run_indices), run_pos + radius + 1)
            window = run_depths[left:right]
            span = float(np.ptp(window))
            if span < 1e-12:
                local_weight = float(global_weights[point_idx])
            else:
                local_weight = (float(depths[point_idx]) - float(np.min(window))) / span

            local_weight = float(np.clip(local_weight, 0.0, 1.0))
            local_weight = local_weight * local_weight * (3.0 - 2.0 * local_weight)
            weights[point_idx] = 0.25 * float(global_weights[point_idx]) + 0.75 * local_weight

        run_start = run_end

    return np.clip(weights, 0.0, 1.0)


def _curve_depth_color(base_rgb: Any, shade_weight: float):
    import numpy as np

    weight = float(np.clip(shade_weight, 0.0, 1.0))
    visible_weight = weight**0.7
    rgb = base_rgb * (0.2 + 0.8 * visible_weight)
    rgb = rgb + (1.0 - rgb) * (0.04 + 0.14 * visible_weight)
    rgb = np.clip(rgb, 0.0, 1.0)
    alpha = 0.74 + 0.24 * visible_weight
    return (float(rgb[0]), float(rgb[1]), float(rgb[2]), float(alpha))


_CURVE_DEPTH_STYLES: tuple[dict[str, Any], ...] = (
    {
        "max_weight": 0.18,
        "linestyle": (0, (1.4, 3.8)),
        "linewidth_scale": 1.35,
    },
    {
        "max_weight": 0.36,
        "linestyle": (0, (2.2, 3.0)),
        "linewidth_scale": 1.25,
    },
    {
        "max_weight": 0.54,
        "linestyle": (0, (3.5, 2.4)),
        "linewidth_scale": 1.16,
    },
    {
        "max_weight": 0.72,
        "linestyle": (0, (6.0, 1.7)),
        "linewidth_scale": 1.08,
    },
    {
        "max_weight": 0.86,
        "linestyle": (0, (10.0, 1.2)),
        "linewidth_scale": 1.03,
    },
    {
        "max_weight": 1.0,
        "linestyle": "solid",
        "linewidth_scale": 1.0,
    },
)


def _curve_depth_style_index(depth_weight: float) -> int:
    weight = float(depth_weight)
    for idx, style in enumerate(_CURVE_DEPTH_STYLES):
        if weight <= float(style["max_weight"]):
            return idx
    return len(_CURVE_DEPTH_STYLES) - 1


def _curve_front_back_segments(curve: dict[str, Any], *, elev: float, azim: float):
    import numpy as np

    xs, ys, zs = _curve_points(curve)
    points = np.column_stack([xs, ys, zs])
    finite = np.all(np.isfinite(points), axis=1)
    if len(points) < 2 or not np.any(finite):
        return [], []

    depth_weights = _curve_depth_weights(points, finite, elev=elev, azim=azim)
    front_segments: list[Any] = []
    back_segments: list[Any] = []
    current: list[Any] = []
    current_front: bool | None = None

    def flush() -> None:
        nonlocal current
        if len(current) >= 2:
            (front_segments if current_front else back_segments).append(np.asarray(current))
        current = []

    for idx in range(len(points) - 1):
        if not finite[idx] or not finite[idx + 1]:
            flush()
            current_front = None
            continue

        segment_weight = float((depth_weights[idx] + depth_weights[idx + 1]) / 2)
        is_front = segment_weight >= 0.5
        if current_front is None:
            current_front = is_front
            current = [points[idx], points[idx + 1]]
        elif is_front == current_front:
            current.append(points[idx + 1])
        else:
            flush()
            current_front = is_front
            current = [points[idx], points[idx + 1]]

    flush()
    return front_segments, back_segments


def _curve_segment_collections(curve: dict[str, Any], *, elev: float, azim: float):
    import numpy as np
    from matplotlib import colors as mcolors

    xs, ys, zs = _curve_points(curve)
    points = np.column_stack([xs, ys, zs])
    finite = np.all(np.isfinite(points), axis=1)
    if len(points) < 2:
        return []

    base_rgb = np.array(mcolors.to_rgb(curve["color"]), dtype=float)
    depth_weights = _curve_depth_weights(points, finite, elev=elev, azim=azim)
    shade_weights = _curve_local_depth_weights(
        points,
        finite,
        elev=elev,
        azim=azim,
        global_weights=depth_weights,
    )
    groups: list[dict[str, Any]] = [
        {
            "segments": [],
            "colors": [],
            "linestyle": style["linestyle"],
            "linewidth_scale": style["linewidth_scale"],
        }
        for style in _CURVE_DEPTH_STYLES
    ]

    current: list[Any] = []
    current_shade_weights: list[float] = []
    current_style_idx: int | None = None
    current_shade_idx: int | None = None

    def flush() -> None:
        nonlocal current, current_shade_weights, current_style_idx, current_shade_idx
        if current_style_idx is not None and len(current) >= 2:
            groups[current_style_idx]["segments"].append(np.asarray(current, dtype=float))
            groups[current_style_idx]["colors"].append(
                _curve_depth_color(base_rgb, float(np.mean(current_shade_weights)))
            )
        current = []
        current_shade_weights = []
        current_shade_idx = None

    for idx in range(len(points) - 1):
        if not finite[idx] or not finite[idx + 1]:
            flush()
            current_style_idx = None
            continue

        start_weight = float(depth_weights[idx])
        end_weight = float(depth_weights[idx + 1])
        segment_weight = (start_weight + end_weight) / 2
        style_idx = _curve_depth_style_index(segment_weight)
        start_shade_weight = float(shade_weights[idx])
        end_shade_weight = float(shade_weights[idx + 1])
        segment_shade_weight = (start_shade_weight + end_shade_weight) / 2
        shade_idx = max(0, min(9, int(segment_shade_weight * 10)))
        if current_style_idx is None:
            current_style_idx = style_idx
            current_shade_idx = shade_idx
            current = [points[idx], points[idx + 1]]
            current_shade_weights = [start_shade_weight, end_shade_weight]
        elif style_idx == current_style_idx and shade_idx == current_shade_idx:
            current.append(points[idx + 1])
            current_shade_weights.append(end_shade_weight)
        else:
            flush()
            current_style_idx = style_idx
            current_shade_idx = shade_idx
            current = [points[idx], points[idx + 1]]
            current_shade_weights = [start_shade_weight, end_shade_weight]

    flush()
    return [group for group in groups if group["segments"]]


def _curve_local_color(curve: dict[str, Any], point: Any, points: Any, *, elev: float, azim: float):
    import numpy as np
    from matplotlib import colors as mcolors

    finite = np.all(np.isfinite(points), axis=1)
    base_rgb = np.array(mcolors.to_rgb(curve["color"]), dtype=float)
    if not np.any(finite):
        return _curve_depth_color(base_rgb, 0.5)
    shade_weights = _curve_local_depth_weights(points, finite, elev=elev, azim=azim)
    point_idx = int(np.nanargmin(np.linalg.norm(points - np.asarray(point, dtype=float), axis=1)))
    return _curve_depth_color(base_rgb, float(shade_weights[point_idx]))


def _curve_arrow_faces(curve: dict[str, Any], *, elev: float, azim: float):
    import numpy as np

    if not curve.get("arrows", True) or curve.get("arrow_count", 1) <= 0:
        return [], []

    xs, ys, zs = _curve_points(curve)
    points = np.column_stack([xs, ys, zs])
    finite_indices = np.flatnonzero(np.all(np.isfinite(points), axis=1))
    if len(finite_indices) < 3:
        return [], []

    finite_points = points[finite_indices]
    extent = float(np.max(np.ptp(finite_points, axis=0)))
    if extent < 1e-12:
        return [], []

    view_direction = _view_direction(elev, azim)
    arrow_length = 0.045 * extent
    arrow_width = 0.012 * extent
    faces = []
    colors = []
    count = curve.get("arrow_count", 1)
    fractions = np.linspace(0.28, 0.86, count)
    for fraction in fractions:
        finite_pos = min(max(1, int(round(fraction * (len(finite_indices) - 1)))), len(finite_indices) - 2)
        idx = int(finite_indices[finite_pos])
        tip = points[idx]

        prev_idx = int(finite_indices[finite_pos - 1])
        next_idx = int(finite_indices[finite_pos + 1])
        direction = points[next_idx] - points[prev_idx]
        direction_norm = float(np.linalg.norm(direction))
        if direction_norm < 1e-12:
            continue
        direction = direction / direction_norm

        base_center = tip - direction * arrow_length
        side = np.cross(view_direction, direction)
        side_norm = float(np.linalg.norm(side))
        if side_norm < 1e-12:
            side = np.cross(np.array([0.0, 0.0, 1.0]), direction)
            side_norm = float(np.linalg.norm(side))
        if side_norm < 1e-12:
            continue
        side = side / side_norm
        faces.append(
            [
                tuple(tip),
                tuple(base_center + side * arrow_width),
                tuple(base_center - side * arrow_width),
            ]
        )
        colors.append(_curve_local_color(curve, tip, points, elev=elev, azim=azim))
    return faces, colors


def _draw_curve(ax, curve: dict[str, Any], *, default_lw: float, elev: float, azim: float) -> None:
    from mpl_toolkits.mplot3d.art3d import Line3DCollection, Poly3DCollection

    segment_groups = _curve_segment_collections(curve, elev=elev, azim=azim)
    lw = curve["lw"] if curve["lw"] is not None else default_lw
    for group in segment_groups:
        for segment, color in zip(group["segments"], group["colors"]):
            ax.add_collection3d(
                Line3DCollection(
                    [segment],
                    colors=[color],
                    linewidths=lw * float(group["linewidth_scale"]),
                    linestyles=group["linestyle"],
                )
            )

    arrow_faces, arrow_colors = _curve_arrow_faces(curve, elev=elev, azim=azim)
    if arrow_faces:
        ax.add_collection3d(
            Poly3DCollection(
                arrow_faces,
                facecolors=arrow_colors,
                edgecolors=arrow_colors,
                linewidths=max(0.3, lw * 0.35),
                alpha=0.98,
            )
        )


def _draw_solid_of_revolution(ax, solid: dict[str, Any]) -> None:
    import numpy as np
    import sympy
    from matplotlib import colors as mcolors

    x = sympy.symbols("x")
    allowed = {
        name: getattr(sympy, name)
        for name in [
            "pi",
            "E",
            "sqrt",
            "exp",
            "log",
            "sin",
            "cos",
            "tan",
            "asin",
            "acos",
            "atan",
            "Rational",
            "erf",
        ]
        if hasattr(sympy, name)
    }
    expr = sympy.sympify(solid["expr"], locals=allowed)
    fn = sympy.lambdify(x, expr, modules=["numpy"])

    xmin, xmax = solid["xrange"]
    xs = np.linspace(xmin, xmax, 96)
    theta = np.linspace(0, 2 * np.pi, 64)
    x_grid, theta_grid = np.meshgrid(xs, theta)
    radius = np.asarray(fn(xs), dtype=float)
    if radius.ndim == 0:
        radius = np.full_like(xs, float(radius), dtype=float)
    radius = np.nan_to_num(np.abs(radius), nan=0.0, posinf=0.0, neginf=0.0)
    radius_grid = np.tile(radius, (len(theta), 1))
    y_grid = radius_grid * np.cos(theta_grid)
    z_grid = radius_grid * np.sin(theta_grid)

    base_rgb = np.array(mcolors.to_rgb(solid["color"]), dtype=float)
    dark_rgb = base_rgb * 0.42
    light_rgb = base_rgb + (1.0 - base_rgb) * 0.55
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "plot3d2_solid_depth",
        [dark_rgb, base_rgb, light_rgb],
    )
    norm = mcolors.Normalize(vmin=float(np.nanmin(z_grid)), vmax=float(np.nanmax(z_grid)))
    facecolors = cmap(norm(z_grid))
    facecolors[..., 3] = 0.68

    ax.plot_surface(
        x_grid,
        y_grid,
        z_grid,
        facecolors=facecolors,
        linewidth=0,
        antialiased=True,
        shade=False,
    )


def _render_plot3d2(
    *,
    xrange: tuple[float, float] = (-5.0, 5.0),
    yrange: tuple[float, float] = (-5.0, 5.0),
    zrange: tuple[float, float] = (-5.0, 5.0),
    xlabel: str = "x",
    ylabel: str = "y",
    zlabel: str = "z",
    ticks: bool = True,
    xstep: float = 1.0,
    ystep: float = 1.0,
    zstep: float = 1.0,
    elev: float = 22.0,
    azim: float = -55.0,
    zoom: float = 1.28,
    fontsize: float = 12.0,
    lw: float = 1.5,
    figsize: tuple[float, float] = (6.0, 5.0),
    curves: list[dict[str, Any]] | None = None,
    points: list[dict[str, Any]] | None = None,
    planes: list[dict[str, Any]] | None = None,
    prisms: list[dict[str, Any]] | None = None,
    pyramids: list[dict[str, Any]] | None = None,
    spheres: list[dict[str, Any]] | None = None,
    texts: list[dict[str, Any]] | None = None,
    vectors: list[dict[str, Any]] | None = None,
    solids_of_revolution: list[dict[str, Any]] | None = None,
):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=figsize, frameon=False)
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0], projection="3d")
    ax.view_init(elev=elev, azim=azim)
    try:
        ax.set_proj_type("ortho")
    except Exception:
        pass

    ax.set_xlim(*xrange)
    ax.set_ylim(*yrange)
    ax.set_zlim(*zrange)
    box_aspect = (
        max(xrange[1] - xrange[0], 1e-9),
        max(yrange[1] - yrange[0], 1e-9),
        max(zrange[1] - zrange[0], 1e-9),
    )
    try:
        ax.set_box_aspect(
            box_aspect,
            zoom=max(0.1, zoom),
        )
    except TypeError:
        ax.set_box_aspect(box_aspect)
    ax.set_axis_off()
    ax.margins(0)

    for solid in solids_of_revolution or []:
        try:
            _draw_solid_of_revolution(ax, solid)
        except Exception:
            pass

    for plane in planes or []:
        try:
            _draw_plane(ax, plane, xrange=xrange, yrange=yrange, zrange=zrange)
        except Exception:
            pass

    for prism in prisms or []:
        try:
            _draw_prism(ax, prism, lw=lw, elev=elev, azim=azim)
        except Exception:
            pass

    for pyramid in pyramids or []:
        try:
            _draw_pyramid(ax, pyramid, lw=lw, elev=elev, azim=azim)
        except Exception:
            pass

    for sphere in spheres or []:
        try:
            _draw_sphere(ax, sphere, elev=elev, azim=azim, lw=lw)
        except Exception:
            pass

    _draw_centered_axes(
        ax,
        xrange=xrange,
        yrange=yrange,
        zrange=zrange,
        xlabel=xlabel,
        ylabel=ylabel,
        zlabel=zlabel,
        ticks=ticks,
        xstep=xstep,
        ystep=ystep,
        zstep=zstep,
        fontsize=fontsize,
        lw=lw,
    )

    for curve in curves or []:
        try:
            _draw_curve(ax, curve, default_lw=lw, elev=elev, azim=azim)
        except Exception:
            pass

    for vector in vectors or []:
        _draw_vector(ax, vector, lw=lw)

    for point in points or []:
        _draw_point(ax, point)

    for text_item in texts or []:
        _draw_text(ax, text_item, default_fontsize=fontsize)

    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    return fig, ax


def _save_plot3d2_svg(fig, path: str | os.PathLike[str]) -> None:
    """Save a 3D figure with a tight canvas around the visible artists."""

    try:
        fig.canvas.draw()
    except Exception:
        pass
    try:
        for ax in fig.axes:
            ax.set_position([0.0, 0.0, 1.0, 1.0])
        fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    except Exception:
        pass
    fig.savefig(
        Path(path),
        format="svg",
        transparent=True,
        bbox_inches="tight",
        pad_inches=0,
    )


class Plot3d2Directive(SphinxDirective):
    has_content = True
    required_arguments = 0
    option_spec = {
        "width": directives.length_or_percentage_or_unitless,
        "align": lambda value: directives.choice(value, ["left", "center", "right"]),
        "class": directives.class_option,
        "name": directives.unchanged,
        "nocache": directives.flag,
        "alt": directives.unchanged,
        "fontsize": directives.unchanged,
        "lw": directives.unchanged,
        "figsize": directives.unchanged,
        "xrange": directives.unchanged,
        "yrange": directives.unchanged,
        "zrange": directives.unchanged,
        "xstep": directives.unchanged,
        "ystep": directives.unchanged,
        "zstep": directives.unchanged,
        "xlabel": directives.unchanged,
        "ylabel": directives.unchanged,
        "zlabel": directives.unchanged,
        "ticks": directives.unchanged,
        "elev": directives.unchanged,
        "azim": directives.unchanged,
        "zoom": directives.unchanged,
    }

    def _parse_kv_block(self) -> tuple[dict[str, Any], dict[str, list[str]], int]:
        return parse_kv_block(list(self.content), _MULTI_KEYS)

    def run(self):
        env = self.state.document.settings.env
        app = env.app
        scalars, lists, caption_idx = self._parse_kv_block()
        merged = {**scalars, **self.options}

        def _f(key: str, default: float) -> float:
            return _eval_float(merged.get(key), default)

        figsize = (6.0, 5.0)
        figsize_raw = merged.get("figsize")
        if figsize_raw:
            parts = [part.strip() for part in str(figsize_raw).strip("()[] ").split(",")]
            if len(parts) >= 2:
                figsize = (_eval_float(parts[0], 6.0), _eval_float(parts[1], 5.0))

        curves = [
            curve
            for raw_curve in lists.get("curve", [])
            if (curve := _parse_curve_primitive(raw_curve)) is not None
        ]
        points = [
            point
            for raw_point in lists.get("point", [])
            if (point := _parse_point_primitive(raw_point)) is not None
        ]
        planes = [
            plane
            for raw_plane in lists.get("plane", [])
            if (plane := _parse_plane_primitive(raw_plane)) is not None
        ]
        prisms = [
            prism
            for raw_prism in lists.get("prism", [])
            if (prism := _parse_prism_primitive(raw_prism)) is not None
        ]
        pyramids = [
            pyramid
            for raw_pyramid in lists.get("pyramid", [])
            if (pyramid := _parse_pyramid_primitive(raw_pyramid)) is not None
        ]
        spheres = [
            sphere
            for raw_sphere in lists.get("sphere", [])
            if (sphere := _parse_sphere_primitive(raw_sphere)) is not None
        ]
        texts = [
            text_item
            for raw_text in lists.get("text", [])
            if (text_item := _parse_text_primitive(raw_text)) is not None
        ]
        vectors = [
            vector
            for raw_vector in lists.get("vector", [])
            if (vector := _parse_vector_primitive(raw_vector)) is not None
        ]
        solids_of_revolution = [
            solid
            for raw_solid in lists.get("solid-of-revolution", [])
            if (solid := _parse_solid_of_revolution_primitive(raw_solid)) is not None
        ]

        params = {
            "xrange": _parse_range(merged.get("xrange"), 5.0),
            "yrange": _parse_range(merged.get("yrange"), 5.0),
            "zrange": _parse_range(merged.get("zrange"), 5.0),
            "xlabel": str(merged.get("xlabel", "x")),
            "ylabel": str(merged.get("ylabel", "y")),
            "zlabel": str(merged.get("zlabel", "z")),
            "ticks": bool(parse_bool(merged.get("ticks"), default=True)),
            "xstep": _f("xstep", 1.0),
            "ystep": _f("ystep", 1.0),
            "zstep": _f("zstep", 1.0),
            "elev": _f("elev", 22.0),
            "azim": _f("azim", -55.0),
            "zoom": _f("zoom", 1.28),
            "fontsize": _f("fontsize", 12.0),
            "lw": _f("lw", 1.5),
            "figsize": figsize,
            "curves": curves,
            "points": points,
            "planes": planes,
            "prisms": prisms,
            "pyramids": pyramids,
            "spheres": spheres,
            "texts": texts,
            "vectors": vectors,
            "solids_of_revolution": solids_of_revolution,
        }

        content_hash = hashlib.sha1(repr(sorted(params.items())).encode("utf-8")).hexdigest()[:16]
        explicit_name = str(merged.get("name", "")).strip() or None
        stable_name = re.sub(r"[^A-Za-z0-9_-]", "_", explicit_name) if explicit_name else None
        base_name = stable_name or f"plot3d2_{content_hash}"

        rel_dir = os.path.join("_static", "plot3d-2")
        abs_dir = os.path.join(app.srcdir, rel_dir)
        os.makedirs(abs_dir, exist_ok=True)
        svg_name = f"{base_name}.svg"
        abs_svg = os.path.join(abs_dir, svg_name)
        abs_meta = os.path.join(abs_dir, f"{base_name}.sha1")

        regenerate = "nocache" in merged or not os.path.exists(abs_svg)
        if not regenerate and stable_name:
            try:
                previous_hash = open(abs_meta, "r", encoding="utf-8").read().strip()
            except Exception:
                previous_hash = None
            regenerate = previous_hash != content_hash

        if regenerate:
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            old_svg_fonttype = matplotlib.rcParams.get("svg.fonttype")
            fig = None
            try:
                matplotlib.rcParams["svg.fonttype"] = "none"
                fig, _ax = _render_plot3d2(**params)
                _save_plot3d2_svg(fig, abs_svg)
                if stable_name:
                    with open(abs_meta, "w", encoding="utf-8") as f:
                        f.write(content_hash)
            except Exception as exc:
                return [
                    self.state_machine.reporter.error(
                        f"plot3d-2: feil under generering av figur: {exc}",
                        line=self.lineno,
                    )
                ]
            finally:
                if fig is not None:
                    plt.close(fig)
                try:
                    matplotlib.rcParams["svg.fonttype"] = old_svg_fonttype
                except Exception:
                    pass

        if not os.path.exists(abs_svg):
            return [self.state_machine.reporter.error("plot3d-2: SVG mangler.", line=self.lineno)]

        env.note_dependency(abs_svg)
        try:
            out_static = os.path.join(app.outdir, "_static", "plot3d-2")
            os.makedirs(out_static, exist_ok=True)
            shutil.copy2(abs_svg, os.path.join(out_static, svg_name))
        except Exception:
            pass

        try:
            raw_svg = open(abs_svg, "r", encoding="utf-8").read()
        except Exception as exc:
            return [
                self.state_machine.reporter.error(
                    f"plot3d-2: kunne ikke lese SVG: {exc}",
                    line=self.lineno,
                )
            ]

        raw_svg = prepare_inline_svg(
            raw_svg,
            content_hash=content_hash,
            alt=str(merged.get("alt", "3D-koordinatsystem")),
            width=str(merged.get("width")) if merged.get("width") else None,
            id_prefix_base="p3d2",
        )

        caption_lines = list(self.content)[caption_idx:]
        return [
            build_inline_svg_figure(
                self,
                raw_svg,
                caption_lines=caption_lines,
                options=InlineSvgOptions(
                    alt=str(merged.get("alt", "3D-koordinatsystem")),
                    width=str(merged.get("width")) if merged.get("width") else None,
                    align=str(merged.get("align", "center")),
                    classes=merged.get("class"),
                    explicit_name=bool(explicit_name),
                ),
            )
        ]


def setup(app):  # pragma: no cover
    app.add_directive("plot3d-2", Plot3d2Directive)
    app.add_directive("plot3d2", Plot3d2Directive)
    return {"version": "0.1", "parallel_read_safe": True, "parallel_write_safe": True}
