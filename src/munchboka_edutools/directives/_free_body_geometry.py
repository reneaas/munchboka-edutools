"""Pure geometry and `plot`-DSL generation for the free-body-diagram directive.

No Sphinx/docutils imports here (mirrors the ``_scene3d.py`` vs
``_interactive_scene3d.py`` split) so this stays testable with plain pytest.
"""

from __future__ import annotations

import math
import re
from typing import Any

from .plot3d_2 import _split_top_level_commas, _strip_wrapping_quotes

OBJECT_KINDS = {"ball", "square", "toy-car"}
FORCE_KINDS = {"gravity", "normal", "friction", "air-resistance", "custom"}

DEFAULT_FORCE_COLOR = {
    "gravity": "black",
    "normal": "blue",
    "friction": "orange",
    "air-resistance": "teal",
    "custom": "purple",
}
DEFAULT_FORCE_NAME = {
    "gravity": r"$\vec G$",
    "normal": r"$\vec N$",
    "friction": r"$\vec R$",
    "air-resistance": r"$\vec L$",
}


def _parse_kv_line(source: str) -> tuple[list[str], dict[str, str]]:
    """Split a `kind, key=value, ...` primitive line into (positional, keyword)."""
    pos: list[str] = []
    kw: dict[str, str] = {}
    for part in _split_top_level_commas(source):
        if "=" in part:
            key, value = part.split("=", 1)
            kw[key.strip()] = value.strip()
        elif part.strip():
            pos.append(part.strip())
    return pos, kw


def _parse_point(value: str) -> tuple[float, float]:
    text = value.strip()
    if not (text.startswith("(") and text.endswith(")")):
        raise ValueError(f"Expected a (x, y) point: {value}")
    parts = _split_top_level_commas(text[1:-1])
    if len(parts) != 2:
        raise ValueError(f"Expected a (x, y) point: {value}")
    return float(parts[0]), float(parts[1])


def _unit(dx: float, dy: float) -> tuple[float, float]:
    norm = math.hypot(dx, dy)
    if norm < 1e-9:
        raise ValueError("A direction cannot have zero length")
    return dx / norm, dy / norm


def parse_direction(value: str) -> tuple[float, float]:
    """A direction is a bare angle in degrees (CCW from +x) or an (dx, dy) pair."""
    text = value.strip()
    if text.startswith("(") and text.endswith(")"):
        return _unit(*_parse_point(text))
    radians = math.radians(float(text))
    return math.cos(radians), math.sin(radians)


def parse_velocity(source: str) -> tuple[float, float]:
    """`velocity:` is `angle=degrees` or an explicit `(dx, dy)` direction."""
    text = source.strip()
    if text.startswith("(") and text.endswith(")"):
        return _unit(*_parse_point(text))
    match = re.fullmatch(r"angle\s*=\s*(.+)", text)
    if not match:
        raise ValueError(f"Invalid velocity: {source}. Use angle=<deg> or (dx, dy)")
    radians = math.radians(float(match.group(1)))
    return math.cos(radians), math.sin(radians)


class FreeBodyObject:
    """Resolved object geometry handed to force placement."""

    def __init__(
        self,
        lines: list[str],
        centroid: tuple[float, float],
        contact: tuple[float, float],
        radius: float,
    ):
        self.lines = lines
        self.centroid = centroid
        self.contact = contact
        # Characteristic half-size, used to project air-resistance's leading point.
        self.radius = radius

    def leading_point(self, direction: tuple[float, float]) -> tuple[float, float]:
        ux, uy = direction
        cx, cy = self.centroid
        return (cx + ux * self.radius, cy + uy * self.radius)


def parse_object(source: str) -> dict[str, Any]:
    pos, kw = _parse_kv_line(source)
    kind = kw.get("kind", pos[0] if pos else None)
    allowed = {"kind", "size", "position", "color", "alpha"}
    if set(kw) - allowed:
        raise ValueError(f"Unsupported object options: {', '.join(sorted(set(kw) - allowed))}")
    if kind not in OBJECT_KINDS:
        raise ValueError(f"Unknown object: {kind}. Expected one of {sorted(OBJECT_KINDS)}")
    return dict(
        kind=kind,
        size=float(kw.get("size", "1")),
        position=_parse_point(kw.get("position", "(0, 0)")),
        color=kw.get("color", "black"),
        alpha=float(kw["alpha"]) if "alpha" in kw else None,
    )


def build_object(
    kind: str, size: float, position: tuple[float, float], color: str, alpha: float | None
) -> FreeBodyObject:
    if size <= 0:
        raise ValueError("object size must be positive")
    cx, cy = position
    alpha_token = f", {alpha:g}" if alpha is not None else ""
    if kind == "ball":
        r = size / 2
        return FreeBodyObject(
            [f"circle: ({cx:g}, {cy:g}), {r:g}, fill, {color}"],
            centroid=(cx, cy),
            contact=(cx, cy - r),
            radius=r,
        )
    if kind == "square":
        half = size / 2
        corners = [
            (cx - half, cy - half),
            (cx + half, cy - half),
            (cx + half, cy + half),
            (cx - half, cy + half),
        ]
        points = ", ".join(f"({x:g}, {y:g})" for x, y in corners)
        return FreeBodyObject(
            [f"polygon: {points}, {color}{alpha_token}"],
            centroid=(cx, cy),
            contact=(cx, cy - half),
            radius=half,
        )
    if kind == "toy-car":
        # A deliberately simple schematic: one body rectangle plus two wheels,
        # nothing more detailed is needed for a free-body diagram.
        body_w, body_h, wheel_r = size, size * 0.45, size * 0.14
        body_bottom = cy - body_h / 2
        body_top = body_bottom + body_h
        corners = [
            (cx - body_w / 2, body_bottom),
            (cx + body_w / 2, body_bottom),
            (cx + body_w / 2, body_top),
            (cx - body_w / 2, body_top),
        ]
        points = ", ".join(f"({x:g}, {y:g})" for x, y in corners)
        wheel_x = body_w * 0.3
        lines = [
            f"polygon: {points}, {color}{alpha_token}",
            f"circle: ({cx - wheel_x:g}, {body_bottom:g}), {wheel_r:g}, fill, black",
            f"circle: ({cx + wheel_x:g}, {body_bottom:g}), {wheel_r:g}, fill, black",
        ]
        return FreeBodyObject(
            lines,
            centroid=(cx, cy),
            contact=(cx, body_bottom - wheel_r),
            radius=body_w / 2,
        )
    raise ValueError(f"Unknown object: {kind}")


def default_attachment(kind, obj: FreeBodyObject, velocity):
    """Return (point, direction) defaults for a standard force kind.

    Returns (None, None) for `custom`, or when a default genuinely depends on a
    `velocity:` that wasn't given \u2014 the caller must then require an explicit
    `point=`/`direction=` override.
    """
    if kind == "gravity":
        return obj.centroid, (0.0, -1.0)
    if kind == "normal":
        return obj.contact, (0.0, 1.0)
    if kind == "friction":
        if velocity is None or abs(velocity[0]) < 1e-9:
            return None, None
        # Kinetic friction opposes the surface-tangential component of motion.
        return obj.contact, (-1.0 if velocity[0] > 0 else 1.0, 0.0)
    if kind == "air-resistance":
        if velocity is None:
            return None, None
        direction = (-velocity[0], -velocity[1])
        return obj.leading_point(velocity), direction
    return None, None  # custom


def parse_force(source: str, obj: FreeBodyObject, velocity) -> dict[str, Any]:
    pos, kw = _parse_kv_line(source)
    kind = pos[0] if pos else kw.get("kind")
    allowed = {"kind", "length", "name", "color", "point", "direction"}
    if set(kw) - allowed:
        raise ValueError(f"Unsupported force options: {', '.join(sorted(set(kw) - allowed))}")
    if kind not in FORCE_KINDS:
        raise ValueError(f"Unknown force: {kind}. Expected one of {sorted(FORCE_KINDS)}")
    if "length" not in kw:
        raise ValueError(f"force: {kind} requires length=")
    length = float(kw["length"])
    if length <= 0:
        raise ValueError(f"force: {kind} requires a positive length")

    point, direction = default_attachment(kind, obj, velocity)
    if "point" in kw:
        point = _parse_point(kw["point"])
    if "direction" in kw:
        direction = parse_direction(kw["direction"])
    if point is None or direction is None:
        hint = (
            "add a `velocity:` line, or give this force an explicit point=/direction="
            if kind in {"friction", "air-resistance"}
            else "give this force an explicit point= and direction="
        )
        raise ValueError(f"force: {kind} has no default attachment point here \u2014 {hint}")

    name = _strip_wrapping_quotes(kw["name"]) if "name" in kw else DEFAULT_FORCE_NAME.get(kind, "")
    color = kw.get("color", DEFAULT_FORCE_COLOR.get(kind, "black"))
    return dict(kind=kind, length=length, name=name, color=color, point=point, direction=direction)


def build_force_lines(
    length: float, name: str, color: str, point: tuple[float, float], direction: tuple[float, float]
) -> tuple[list[str], tuple[float, float]]:
    px, py = point
    ux, uy = direction
    tip = (px + ux * length, py + uy * length)
    lines = [f"vector: ({px:g}, {py:g}), ({tip[0]:g}, {tip[1]:g}), {color}"]
    if name:
        offset = length * 0.18 + 0.12
        lx, ly = px + ux * (length + offset), py + uy * (length + offset)
        lines.append(f'text: {lx:g}, {ly:g}, "{name}", center-center')
    return lines, tip


def axis_indicator_lines(xmin: float, ymin: float, extent: float, margin: float) -> list[str]:
    ox, oy = xmin + margin, ymin + margin
    return [
        f"vector: ({ox:g}, {oy:g}), ({ox + extent:g}, {oy:g}), black",
        f'text: {ox + extent:g}, {oy:g}, "$x$", center-left',
        f"vector: ({ox:g}, {oy:g}), ({ox:g}, {oy + extent:g}), black",
        f'text: {ox:g}, {oy + extent:g}, "$y$", bottom-center',
    ]


def compile_scene(
    object_source: str,
    force_sources: list[str],
    velocity_source: str | None = None,
    axis_indicator: bool = True,
) -> dict[str, Any]:
    """Build everything needed to delegate to the `plot` directive.

    Returns ``{"lines": [...], "bounds": (xmin, xmax, ymin, ymax)}``.
    """
    obj = build_object(**parse_object(object_source))
    velocity = parse_velocity(velocity_source) if velocity_source else None

    lines = list(obj.lines)
    r = obj.radius
    points = [
        obj.centroid,
        obj.contact,
        (obj.centroid[0] - r, obj.centroid[1] - r),
        (obj.centroid[0] + r, obj.centroid[1] + r),
    ]

    if not force_sources:
        raise ValueError("free-body-diagram requires at least one force:")
    for raw in force_sources:
        force = parse_force(raw, obj, velocity)
        force_lines, tip = build_force_lines(
            force["length"], force["name"], force["color"], force["point"], force["direction"]
        )
        lines.extend(force_lines)
        points.append(force["point"])
        points.append(tip)

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    span = max(xmax - xmin, ymax - ymin, 1e-6)
    margin = span * 0.25
    xmin, xmax, ymin, ymax = xmin - margin, xmax + margin, ymin - margin, ymax + margin

    if axis_indicator:
        lines = lines + axis_indicator_lines(xmin, ymin, span * 0.18, margin * 0.5)

    return dict(lines=lines, bounds=(xmin, xmax, ymin, ymax))
