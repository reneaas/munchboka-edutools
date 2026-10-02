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
        # Contact forces (normal/friction) act on one actual wheel — not the gap
        # between them — per the standard convention for this kind of schematic.
        return FreeBodyObject(
            lines,
            centroid=(cx, cy),
            contact=(cx + wheel_x, body_bottom - wheel_r),
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
    allowed = {"kind", "length", "name", "color", "point", "direction", "offset"}
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
    offset = float(kw["offset"]) if "offset" in kw else None
    return dict(
        kind=kind,
        length=length,
        name=name,
        color=color,
        point=point,
        direction=direction,
        offset=offset,
    )


def _perpendicular(direction: tuple[float, float]) -> tuple[float, float]:
    dx, dy = direction
    return (-dy, dx)


def _collinear_groups(forces: list[dict[str, Any]], tol: float = 1e-6) -> list[list[int]]:
    """Cluster force indices whose line of action coincides: parallel (or
    antiparallel) directions whose attachment points also lie on that same
    infinite line, e.g. gravity and normal for an object resting symmetrically
    on flat ground. Preserves each group's original relative order."""
    groups: list[list[int]] = []
    assigned = [False] * len(forces)
    for i, force in enumerate(forces):
        if assigned[i]:
            continue
        group = [i]
        assigned[i] = True
        px, py = force["point"]
        dx, dy = force["direction"]
        for j in range(i + 1, len(forces)):
            if assigned[j]:
                continue
            other = forces[j]
            ox, oy = other["point"]
            odx, ody = other["direction"]
            if abs(dx * ody - dy * odx) > tol:
                continue
            vx, vy = ox - px, oy - py
            if math.hypot(vx, vy) > tol and abs(dx * vy - dy * vx) > tol:
                continue
            group.append(j)
            assigned[j] = True
        groups.append(group)
    return groups


def _assign_draw_points(forces: list[dict[str, Any]], spacing: float) -> list[dict[str, Any]]:
    """Offset every force's vector perpendicular to its own line of action, by
    an amount that grows with its rank inside any group it shares a line with
    (e.g. gravity and normal for an object resting symmetrically on flat
    ground). Each force keeps its true `point` (marked with a dot) and gains a
    `draw_point` (where its vector is actually drawn from), connected by a
    short line-segment \u2014 the standard textbook convention for concurrent/
    collinear forces, and also what keeps the point mark itself visible:
    `plot`'s own `point:` primitive is drawn before `vector:` (which always
    renders on top), so a point left exactly at its vector's own tail would be
    fully covered. Offsetting therefore defaults to on, even for a lone force
    with nothing to avoid overlapping, but a force's own explicit `offset=`
    (parsed in `parse_force`) always wins over the auto-computed amount \u2014
    including `offset=0` to disable it entirely for a force that's already
    clearly visible on its own.
    """
    for group in _collinear_groups(forces):
        perp = _perpendicular(forces[group[0]]["direction"])
        for rank, index in enumerate(group):
            force = forces[index]
            offset = force["offset"] if force.get("offset") is not None else (rank + 1) * spacing
            px, py = force["point"]
            force["draw_point"] = (px + perp[0] * offset, py + perp[1] * offset)
    return forces


def build_force_lines(
    color: str,
    name: str,
    length: float,
    true_point: tuple[float, float],
    direction: tuple[float, float],
    draw_point: tuple[float, float],
) -> tuple[list[str], tuple[float, float]]:
    tpx, tpy = true_point
    dpx, dpy = draw_point
    ux, uy = direction
    tip = (dpx + ux * length, dpy + uy * length)
    # Always mark the actual point of action on the object, and connect it to
    # the (always slightly offset, see _assign_draw_points) vector with a thin
    # leader segment so the dot isn't hidden under the vector's own tail.
    # `point:` only ever accepts a bare `(x, y)` — plot.py's own regex is
    # anchored right after the closing paren, so a trailing color token here
    # would make the whole line fail to parse and get silently dropped.
    lines = [f"point: ({tpx:g}, {tpy:g})"]
    if math.hypot(dpx - tpx, dpy - tpy) > 1e-9:
        lines.append(f"line-segment: ({tpx:g}, {tpy:g}), ({dpx:g}, {dpy:g}), dotted, {color}")
    lines.append(f"vector: ({dpx:g}, {dpy:g}), ({tip[0]:g}, {tip[1]:g}), {color}")
    if name:
        offset = length * 0.18 + 0.12
        lx, ly = dpx + ux * (length + offset), dpy + uy * (length + offset)
        lines.append(f'text: {lx:g}, {ly:g}, "{name}", center-center')
    return lines, tip


def axis_indicator_lines(xmin: float, ymin: float, extent: float, margin: float) -> list[str]:
    ox, oy = xmin + margin, ymin + margin
    # A small gap beyond each arrowhead, plus `plot`'s own "the text sits away
    # from the anchor" position tokens (`center-right`/`top-center`, NOT
    # `center-left`/`bottom-center` which place the text on the near side,
    # overlapping the arrow) so the labels clear the arrowheads entirely.
    gap = extent * 0.2
    return [
        f"vector: ({ox:g}, {oy:g}), ({ox + extent:g}, {oy:g}), black",
        f'text: {ox + extent + gap:g}, {oy:g}, "$x$", center-right',
        f"vector: ({ox:g}, {oy:g}), ({ox:g}, {oy + extent:g}), black",
        f'text: {ox:g}, {oy + extent + gap:g}, "$y$", top-center',
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
    forces = [parse_force(raw, obj, velocity) for raw in force_sources]
    spacing = max(r * 0.22, 0.08)
    _assign_draw_points(forces, spacing)
    for force in forces:
        force_lines, tip = build_force_lines(
            force["color"],
            force["name"],
            force["length"],
            force["point"],
            force["direction"],
            force["draw_point"],
        )
        lines.extend(force_lines)
        points.append(force["point"])
        points.append(force["draw_point"])
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
