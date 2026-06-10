r"""Plot3d directive — 3-dimensional vector-geometry figures.

Renders 3D geometric figures by projecting all objects onto the 2D plane via a
configurable oblique/axonometric projection, then drawing everything with standard
Matplotlib 2D artists.  This lets us reuse the same centered coordinate-system
aesthetics, colour palette, SVG caching, and Sphinx integration as the existing
``plot`` directive.

Projection
----------
The projection uses the standard educational oblique convention:

* x maps horizontally to the right
* z maps vertically upward
* y maps "into the screen", appearing as a lower-left vector

``azimuth`` (default 40) is the angle (°) the y-axis makes below horizontal-left.
``elevation`` (default 50) controls y-axis foreshortening: ``scale = cos(elevation)``.

With the defaults a unit-y vector appears at 40° below horizontal-left,
at roughly 64 % of its true length — a natural cabinet-oblique look.

Quick start (MyST)
------------------
:::{plot3d}
azimuth: 40
elevation: 25
xrange: 5
yrange: 5
zrange: 5
vector: (0,0,0), (2,1,3), blue
vector: (0,0,0), (-1,2,0), red
point: (2, 1, 3)
:::

Front matter keys
-----------------
Global layout (shared with ``plot``):
    width, figsize, align, class, name, nocache, alt, usetex, fontsize, lw

Projection:
    azimuth   Rotation of x/y plane in degrees (default 40).
    elevation Tilt of z-axis in degrees (default 25).

Axis bounds (symmetric — one value or per-axis):
    xrange    Max absolute value on x-axis (default 5); or ``(-a, b)``.
    yrange    Max absolute value on y-axis (default 5).
    zrange    Max absolute value on z-axis (default 5).

Axis labels:
    xlabel    Label for x-axis (default ``$x$``).
    ylabel    Label for y-axis (default ``$y$``).
    zlabel    Label for z-axis (default ``$z$``).

Axis appearance:
    ticks     ``true|false`` — show tick marks and numbers (default ``true``).
    grid-planes  Comma-separated list of ``xy``, ``xz``, ``yz`` (default none).
    grid-alpha   Alpha for grid-plane fills (default 0.07).

Primitives (repeatable keys):
    point:       ``(x,y,z)[, color][, label][, label-pos]``
    vector:      ``(x0,y0,z0), (dx,dy,dz)[, color][, label]``
                 or ``(x0,y0,z0), (x1,y1,z1), endpoint[, color][, label]``
    line-segment: ``(x0,y0,z0), (x1,y1,z1)[, linestyle][, color]``
    line:        ``(x0,y0,z0), (dx,dy,dz)[, linestyle][, color]`` — infinite line
    plane:       ``normal=(nx,ny,nz), through=(px,py,pz)[, color][, alpha]``
                 or ``points=((x1,y1,z1),(x2,y2,z2),(x3,y3,z3))[, color][, alpha]``
    sphere:      ``(cx,cy,cz), radius[, color][, alpha]``
    curve:       ``x(t), y(t), z(t), (t0,t1)[, linestyle][, color]``
    angle:       ``(vx,vy,vz), (ax,ay,az), (bx,by,bz)[, radius][, color]``
                 — arc at vertex V from direction A to direction B
    pyramid:     ``apex=(x,y,z), base=((x1,y1,z1),(x2,y2,z2),...)[, color][, alpha]``
    projection:  ``object=point:(x,y,z)|segment:(A),(B)|sphere:(c),r, onto=xy|xz|yz|(nx,ny,nz):(px,py,pz)[, color][, alpha][, drop=true]``
                 — orthogonal shadow of a point, line segment, or sphere onto a plane.
    text:        ``(x,y,z), "string"[, color]``
"""

from __future__ import annotations

import hashlib
import math
import os
import re
import shutil
import uuid
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective

# ---------------------------------------------------------------------------
# Colour palette (mirrors plot.py — resolved before matplotlib fallback)
# ---------------------------------------------------------------------------
_COLORS: Dict[str, str] = {
    "red": "#d62728",
    "blue": "#1f77b4",
    "green": "#2ca02c",
    "orange": "#ff7f0e",
    "purple": "#9467bd",
    "teal": "#17becf",
    "black": "#000000",
    "gray": "#7f7f7f",
    "grey": "#7f7f7f",
    "brown": "#8c564b",
    "pink": "#e377c2",
    "olive": "#bcbd22",
    "cyan": "#17becf",
    "indigo": "#5c6bc0",
}

_LINESTYLES = {"solid", "dotted", "dashed", "dashdot"}

# ---------------------------------------------------------------------------
# Projection helpers
# ---------------------------------------------------------------------------

def _make_proj(az_deg: float, el_deg: float) -> Callable[[float, float, float], Tuple[float, float]]:
    """Return a projection function (x,y,z) → (px,py).

    The projection uses the standard educational oblique convention:

    * **y** maps horizontally to the right  →  screen direction (1, 0)
    * **z** maps vertically upward          →  screen direction (0, 1)
    * **x** maps "into the screen", appearing as a vector going lower-left

    This convention satisfies the **right-hand rule**: x × y = z.

    Parameters
    ----------
    az_deg : float
        Angle (°) of the y-axis *below* the negative-x direction (horizontal-left).
        ``az=30`` gives the classic "cabinet-style" 3D view; ``az=45`` is steeper.
    el_deg : float
        Controls the y-axis foreshortening via ``scale = cos(el_deg)``.
        ``el=0``  → cavalier (no foreshortening, scale=1).
        ``el=45`` → isometric-style (scale≈0.71).
        ``el=60`` → cabinet (scale=0.5).
    """
    az = math.radians(az_deg)
    yscale = math.cos(math.radians(el_deg))
    cx = math.cos(az) * yscale   # y-screen-displacement per unit x
    sx = math.sin(az) * yscale   # z-screen-displacement per unit x

    def proj(x: float, y: float, z: float) -> Tuple[float, float]:
        # y → right, z → up, x → lower-left  (right-hand rule: x×y = z)
        px = y - x * cx
        py = z - x * sx
        return px, py

    # Expose cx/sx for vectorised callers
    proj._cx = cx  # type: ignore[attr-defined]
    proj._sx = sx  # type: ignore[attr-defined]
    return proj


def _make_sym_proj(el_deg: float = 30.0) -> Callable[[float, float, float], Tuple[float, float]]:
    """Return a **symmetric** projection function (x,y,z) → (px,py).

    The x-axis is horizontal and the y-axis is at +45°,
    creating a right-handed look:

    ::

              z  (up)
              |      y
              |    ↗  (+45°)
              +----------→
                          x  (0°)

    Projection formula (C45=S45=1/√2)::

        s  = cos(el_deg) / √2
        px = s · (x + C45·y)
        py = s · C45·y + z

    Properties:
    * x-axis screen angle:   0° (horizontal)  ✓
    * y-axis screen angle: +45° (upper-right)  ✓
    * right-hand rule obeyed (2-D cross product > 0)  ✓
    * z straight up  ✓

    ``el_deg`` controls foreshortening of the horizontal axes.

    * ``el_deg=0``  → cavalier (s ≈ 0.707, no foreshortening beyond the 45° angle)
    * ``el_deg=30`` → s ≈ 0.612, a natural appearance (default)
    * ``el_deg=45`` → isometric (s = 0.5, all three axis lengths equal per unit)

    Viewing direction (depth criterion): both x and y go equally "into the
    screen", so depth is proportional to ``x + y`` (z is ignored, same
    convention as the standard layout).
    """
    s = math.cos(math.radians(el_deg)) / math.sqrt(2)
    _C45 = math.sqrt(2) / 2     # cos(45°) = sin(45°) = 1/√2

    def proj(x: float, y: float, z: float) -> Tuple[float, float]:
        px = s * (x + _C45 * y)
        py = s * _C45 * y + z
        return px, py

    # Attributes used by vectorised callers and drawing helpers
    proj._layout   = "symmetric"       # type: ignore[attr-defined]
    proj._sym_s    = s                 # type: ignore[attr-defined]
    proj._sym_C45  = _C45              # type: ignore[attr-defined]
    # Viewing direction: x at 0°, y at 45° → view = (1, C45, s)
    proj._view_dir = (1.0, _C45, s)    # type: ignore[attr-defined]
    return proj


def _proj_array(
    xs: np.ndarray, ys: np.ndarray, zs: np.ndarray, proj: Callable
) -> Tuple[np.ndarray, np.ndarray]:
    """Vectorised projection of three coordinate arrays."""
    if getattr(proj, "_layout", "standard") == "symmetric":
        s   = proj._sym_s
        C45 = getattr(proj, "_sym_C45", math.sqrt(2) / 2)
        return s * (xs + C45 * ys), s * C45 * ys + zs
    cx = getattr(proj, "_cx", None)
    sx = getattr(proj, "_sx", None)
    if cx is not None:
        return ys - xs * cx, zs - xs * sx
    # fallback for any custom proj function
    pxs = np.empty(len(xs))
    pys = np.empty(len(xs))
    for i in range(len(xs)):
        pxs[i], pys[i] = proj(xs[i], ys[i], zs[i])
    return pxs, pys


# ---------------------------------------------------------------------------
# Expression evaluation (SymPy-based, restricted namespace)
# ---------------------------------------------------------------------------

def _sympy_ns() -> Dict[str, Any]:
    try:
        import sympy
        return {k: getattr(sympy, k) for k in [
            "pi", "E", "exp", "sqrt", "log",
            "sin", "cos", "tan", "asin", "acos", "atan", "Rational",
        ] if hasattr(sympy, k)}
    except ImportError:
        return {"pi": math.pi, "E": math.e}


def _eval_expr(s: str, extra: Dict[str, Any] | None = None) -> float:
    """Evaluate a numeric expression string via SymPy and return a float."""
    s = s.strip()
    ns = _sympy_ns()
    if extra:
        ns.update(extra)
    try:
        import sympy
        return float(sympy.sympify(s, locals=ns).evalf())
    except Exception:
        pass
    try:
        return float(s)
    except Exception:
        raise ValueError(f"Cannot evaluate expression: {s!r}")


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _split_top(text: str, sep: str = ",") -> List[str]:
    """Split *text* on *sep* that are not inside brackets/parens/braces."""
    out: List[str] = []
    cur: List[str] = []
    depth = 0
    for ch in text:
        if ch in "([{":
            depth += 1
            cur.append(ch)
        elif ch in ")]}":
            depth = max(0, depth - 1)
            cur.append(ch)
        elif ch == sep and depth == 0:
            tok = "".join(cur).strip()
            if tok:
                out.append(tok)
            cur = []
        else:
            cur.append(ch)
    tail = "".join(cur).strip()
    if tail:
        out.append(tail)
    return out


def _parse_triple(s: str) -> Tuple[float, float, float]:
    """Parse ``(a, b, c)`` or ``a, b, c`` into three floats."""
    s = s.strip().lstrip("(").rstrip(")")
    parts = _split_top(s)
    if len(parts) != 3:
        raise ValueError(f"Expected 3 values, got {len(parts)} in: {s!r}")
    return _eval_expr(parts[0]), _eval_expr(parts[1]), _eval_expr(parts[2])


def _parse_range(s: str, default: float = 5.0) -> Tuple[float, float]:
    """Parse ``5``, ``(−3, 7)``, or ``−3, 7`` into (lo, hi)."""
    s = s.strip()
    if s.startswith("(") or s.startswith("["):
        s = s.strip("()[]{}")
    parts = _split_top(s)
    if len(parts) == 1:
        v = _eval_expr(parts[0])
        return -abs(v), abs(v)
    elif len(parts) == 2:
        return _eval_expr(parts[0]), _eval_expr(parts[1])
    return -default, default


def _parse_bool(val: Any, default: bool = True) -> bool:
    if val is None:
        return default
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    if s in {"true", "yes", "on", "1"}:
        return True
    if s in {"false", "no", "off", "0"}:
        return False
    return default


def _resolve_color(tok: str) -> str | None:
    """Resolve a colour token through the palette then Matplotlib."""
    if not tok:
        return None
    t = tok.strip()
    if t in _COLORS:
        return _COLORS[t]
    if re.match(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$", t):
        return t
    try:
        import plotmath  # type: ignore
        c = getattr(plotmath, "COLORS", {}).get(t)
        if c:
            return c
    except ImportError:
        pass
    return t  # pass through to matplotlib as-is


def _split_style_color(tokens: List[str]) -> Tuple[str | None, str | None]:
    """Extract optional linestyle and color from a token list."""
    style = None
    color = None
    for tok in tokens:
        t = tok.strip()
        if t.lower() in _LINESTYLES:
            style = t.lower()
        else:
            c = _resolve_color(t)
            if c:
                color = c
    return style, color


# ---------------------------------------------------------------------------
# Primitive parsers
# ---------------------------------------------------------------------------

def _parse_point_primitive(val: str) -> Dict[str, Any] | None:
    """Parse ``(x,y,z)[, color][, label][, label-pos]``."""
    try:
        tokens = _split_top(val)
        # First token is always the coordinate triple
        coord_tok = tokens[0]
        rest = tokens[1:]
        x, y, z = _parse_triple(coord_tok)
        color = _COLORS["blue"]
        label: str | None = None
        label_pos: str = "top-right"
        for tok in rest:
            t = tok.strip()
            if t.startswith('"') or t.startswith("'"):
                label = t.strip("\"'")
            elif t.lower() in {"top-right", "top-left", "bottom-right", "bottom-left",
                               "top-center", "bottom-center", "center-right", "center-left"}:
                label_pos = t.lower()
            else:
                c = _resolve_color(t)
                if c:
                    color = c
        return {"type": "point", "pos": (x, y, z), "color": color,
                "label": label, "label_pos": label_pos}
    except Exception:
        return None


def _parse_vector_primitive(val: str) -> Dict[str, Any] | None:
    """Parse vector in three forms:
    1. ``(x0,y0,z0), (dx,dy,dz)[, color][, label]``
    2. ``(x0,y0,z0), (x1,y1,z1), endpoint[, color][, label]``
    3. Legacy: ``x0, y0, z0, dx, dy, dz[, color][, label]``
    """
    try:
        tokens = _split_top(val)
        color = _COLORS["black"]
        label: str | None = None

        # Detect if first token is a parenthesised triple
        if tokens and tokens[0].strip().startswith("("):
            start = _parse_triple(tokens[0])
            rest = tokens[1:]
            # Check for "endpoint" keyword
            endpoint_mode = False
            clean_rest = []
            for t in rest:
                if t.strip().lower() == "endpoint":
                    endpoint_mode = True
                elif t.strip().startswith('"') or t.strip().startswith("'"):
                    label = t.strip().strip("\"'")
                else:
                    clean_rest.append(t)
            # Extract style/color
            non_triple = [t for t in clean_rest if not t.strip().startswith("(")]
            triple_toks = [t for t in clean_rest if t.strip().startswith("(")]
            _, color_out = _split_style_color(non_triple)
            if color_out:
                color = color_out
            if triple_toks:
                second = _parse_triple(triple_toks[0])
                if endpoint_mode:
                    # second is an endpoint → compute components
                    dx = second[0] - start[0]
                    dy = second[1] - start[1]
                    dz = second[2] - start[2]
                else:
                    dx, dy, dz = second
                return {"type": "vector", "start": start, "components": (dx, dy, dz),
                        "color": color, "label": label}
        # Legacy flat format: x0, y0, z0, dx, dy, dz
        if len(tokens) >= 6:
            x0, y0, z0 = _eval_expr(tokens[0]), _eval_expr(tokens[1]), _eval_expr(tokens[2])
            dx, dy, dz = _eval_expr(tokens[3]), _eval_expr(tokens[4]), _eval_expr(tokens[5])
            rest = tokens[6:]
            for t in rest:
                s = t.strip()
                if s.startswith('"') or s.startswith("'"):
                    label = s.strip("\"'")
                else:
                    c = _resolve_color(s)
                    if c:
                        color = c
            return {"type": "vector", "start": (x0, y0, z0), "components": (dx, dy, dz),
                    "color": color, "label": label}
        return None
    except Exception:
        return None


def _parse_line_segment_primitive(val: str) -> Dict[str, Any] | None:
    """Parse ``(x0,y0,z0), (x1,y1,z1)[, linestyle][, color]``."""
    try:
        tokens = _split_top(val)
        triple_toks = [t for t in tokens if t.strip().startswith("(")]
        rest = [t for t in tokens if not t.strip().startswith("(")]
        if len(triple_toks) < 2:
            return None
        p0 = _parse_triple(triple_toks[0])
        p1 = _parse_triple(triple_toks[1])
        style, color = _split_style_color(rest)
        return {"type": "line-segment", "p0": p0, "p1": p1,
                "style": style or "solid", "color": color or _COLORS["black"]}
    except Exception:
        return None


def _parse_line_primitive(val: str) -> Dict[str, Any] | None:
    """Parse ``(x0,y0,z0), (dx,dy,dz)[, linestyle][, color]`` — infinite line."""
    try:
        tokens = _split_top(val)
        triple_toks = [t for t in tokens if t.strip().startswith("(")]
        rest = [t for t in tokens if not t.strip().startswith("(")]
        if len(triple_toks) < 2:
            return None
        p0 = _parse_triple(triple_toks[0])
        direction = _parse_triple(triple_toks[1])
        style, color = _split_style_color(rest)
        return {"type": "line", "point": p0, "direction": direction,
                "style": style or "dashed", "color": color or _COLORS["black"]}
    except Exception:
        return None


def _parse_plane_primitive(val: str) -> Dict[str, Any] | None:
    """Parse plane from named args:
    ``normal=(nx,ny,nz), through=(px,py,pz)[, color][, alpha]``
    or ``points=((x1,y1,z1),(x2,y2,z2),(x3,y3,z3))[, color][, alpha]``
    """
    try:
        # Extract named args
        normal_m = re.search(r"normal\s*=\s*(\([^)]+\))", val)
        through_m = re.search(r"through\s*=\s*(\([^)]+\))", val)
        alpha_m = re.search(r"\balpha\s*=\s*([0-9.]+)", val)
        color_m = re.search(r"\bcolor\s*=\s*(\w+)", val)

        alpha = float(alpha_m.group(1)) if alpha_m else 0.15
        color = _resolve_color(color_m.group(1)) if color_m else _COLORS["blue"]

        if normal_m and through_m:
            normal = _parse_triple(normal_m.group(1))
            through = _parse_triple(through_m.group(1))
            return {"type": "plane", "mode": "normal",
                    "normal": normal, "through": through,
                    "color": color, "alpha": alpha}

        points_m = re.search(r"points\s*=\s*\((.+)\)\s*$", val)
        if points_m:
            # Extract up to three triples
            inner = points_m.group(1)
            triples = re.findall(r"\(([^)]+)\)", inner)
            if len(triples) >= 3:
                p0 = _parse_triple(triples[0])
                p1 = _parse_triple(triples[1])
                p2 = _parse_triple(triples[2])
                return {"type": "plane", "mode": "points",
                        "points": (p0, p1, p2),
                        "color": color, "alpha": alpha}
        return None
    except Exception:
        return None


def _parse_limited_plane_primitive(val: str) -> Dict[str, Any] | None:
    """Parse a rectangular patch of a plane.

    Syntax::

        z = expr(x,y), (xmin,xmax), (ymin,ymax) [, color] [, alpha=0.2] [, border=true]
        y = expr(x,z), (xmin,xmax), (zmin,zmax) [, color] [, alpha=0.2] [, border=true]
        x = expr(y,z), (ymin,ymax), (zmin,zmax) [, color] [, alpha=0.2] [, border=true]
    """
    try:
        # Pull out keyword args before splitting on commas
        alpha_m = re.search(r"\balpha\s*=\s*([0-9.]+)", val)
        border_m = re.search(r"\bborder\s*=\s*(true|false|yes|no|1|0)", val, re.IGNORECASE)
        color_m = re.search(r"\bcolor\s*=\s*(\w+)", val)

        alpha = float(alpha_m.group(1)) if alpha_m else 0.2
        border = border_m.group(1).lower() not in {"false", "no", "0"} if border_m else True
        # color_m handled below; strip keyword tokens before further parsing
        clean = re.sub(r"\b(?:alpha|border|color)\s*=[^\,]+", "", val)

        # First token must be "var = expr"
        tokens = _split_top(clean)
        # The first token is the equation: "z = 2*x - y + 1"
        eq_tok = tokens[0].strip()
        eq_m = re.match(r"^\s*([xyz])\s*=\s*(.+)$", eq_tok)
        if not eq_m:
            return None
        dep_var = eq_m.group(1)       # "x", "y", or "z"
        expr_str = eq_m.group(2).strip()

        # Next two tokens are the domain ranges (parenthesised pairs)
        range_toks = [t.strip() for t in tokens[1:] if t.strip().startswith("(")]
        if len(range_toks) < 2:
            return None
        r0 = _parse_range(range_toks[0])  # (min0, max0)
        r1 = _parse_range(range_toks[1])  # (min1, max1)

        # Remaining tokens (non-parenthesised, non-keyword) → color
        rest = [t for t in tokens[1:] if not t.strip().startswith("(")]
        rest = [t for t in rest if not re.match(r"^\s*(alpha|border|color)\s*=", t)]
        if color_m:
            color = _resolve_color(color_m.group(1))
        else:
            _, color = _split_style_color(rest)
            color = color or _COLORS["blue"]

        return {
            "type": "limited-plane",
            "dep": dep_var,       # which variable is expressed
            "expr": expr_str,     # expression as string
            "range0": r0,         # first parameter range
            "range1": r1,         # second parameter range
            "color": color,
            "alpha": alpha,
            "border": border,
        }
    except Exception:
        return None


def _parse_sphere_primitive(val: str) -> Dict[str, Any] | None:
    """Parse ``(cx,cy,cz), radius[, color][, alpha]``."""
    try:
        tokens = _split_top(val)
        triple_toks = [t for t in tokens if t.strip().startswith("(")]
        rest = [t for t in tokens if not t.strip().startswith("(")]
        if not triple_toks:
            return None
        center = _parse_triple(triple_toks[0])
        # First non-triple numeric token is radius
        radius: float | None = None
        non_numeric = []
        for t in rest:
            try:
                radius = _eval_expr(t)
            except Exception:
                non_numeric.append(t)
        if radius is None:
            return None
        # alpha
        alpha = 0.4
        alpha_m = re.search(r"\balpha\s*=\s*([0-9.]+)", val)
        if alpha_m:
            alpha = float(alpha_m.group(1))
        _, color = _split_style_color(non_numeric)
        return {"type": "sphere", "center": center, "radius": radius,
                "color": color or _COLORS["blue"], "alpha": alpha}
    except Exception:
        return None


def _parse_curve_primitive(val: str) -> Dict[str, Any] | None:
    """Parse ``x(t), y(t), z(t), (t0,t1)[, linestyle][, color]``."""
    try:
        tokens = _split_top(val)
        if len(tokens) < 4:
            return None
        xt_expr = tokens[0].strip()
        yt_expr = tokens[1].strip()
        zt_expr = tokens[2].strip()
        dom_tok = tokens[3].strip()
        rest = tokens[4:]

        t0, t1 = _parse_range(dom_tok)
        style, color = _split_style_color(rest)
        return {"type": "curve", "xt": xt_expr, "yt": yt_expr, "zt": zt_expr,
                "t0": t0, "t1": t1, "style": style or "solid",
                "color": color or _COLORS["blue"]}
    except Exception:
        return None


def _parse_angle_primitive(val: str) -> Dict[str, Any] | None:
    """Parse ``(vx,vy,vz), (ax,ay,az), (bx,by,bz)[, radius][, color]``.
    Draws an arc at vertex V in the plane of directions A and B.
    """
    try:
        tokens = _split_top(val)
        triple_toks = [t for t in tokens if t.strip().startswith("(")]
        rest = [t for t in tokens if not t.strip().startswith("(")]
        if len(triple_toks) < 3:
            return None
        vertex = _parse_triple(triple_toks[0])
        dir_a = _parse_triple(triple_toks[1])
        dir_b = _parse_triple(triple_toks[2])

        radius = 0.5
        color = _COLORS["red"]
        for t in rest:
            try:
                radius = _eval_expr(t)
            except Exception:
                c = _resolve_color(t)
                if c:
                    color = c
        return {"type": "angle", "vertex": vertex, "dir_a": dir_a, "dir_b": dir_b,
                "radius": radius, "color": color}
    except Exception:
        return None


def _parse_pyramid_primitive(val: str) -> Dict[str, Any] | None:
    """Parse ``apex=(x,y,z), base=((x1,y1,z1),(x2,y2,z2),...)[, color][, alpha]``."""
    try:
        apex_m = re.search(r"apex\s*=\s*(\([^)]+\))", val)
        base_m = re.search(r"base\s*=\s*\((.+)\)\s*(?:,|$)", val)
        alpha_m = re.search(r"\balpha\s*=\s*([0-9.]+)", val)
        color_m = re.search(r"\bcolor\s*=\s*(\w+)", val)

        if not apex_m or not base_m:
            return None
        apex = _parse_triple(apex_m.group(1))
        alpha = float(alpha_m.group(1)) if alpha_m else 0.15
        color = _resolve_color(color_m.group(1)) if color_m else _COLORS["blue"]

        base_inner = base_m.group(1)
        base_triples = re.findall(r"\(([^)]+)\)", base_inner)
        base_pts = [_parse_triple(t) for t in base_triples]
        if len(base_pts) < 3:
            return None
        return {"type": "pyramid", "apex": apex, "base": base_pts,
                "color": color, "alpha": alpha}
    except Exception:
        return None


def _parse_projection_primitive(val: str) -> Dict[str, Any] | None:
    """Parse a projection primitive.

    Syntax::

        projection: object=point:(x,y,z), onto=xy[, color][, alpha][, drop=true]
        projection: object=segment:(x0,y0,z0),(x1,y1,z1), onto=xz[, color][, alpha][, drop=true]
        projection: object=sphere:(cx,cy,cz),r, onto=yz[, color][, alpha][, drop=true]
        # general plane: normal:(nx,ny,nz), anchor:(px,py,pz)
        projection: object=point:(x,y,z), onto=(0,0,1):(0,0,0)[, color][, alpha][, drop=true]

    *drop=true* draws a dashed perpendicular segment from the original
    geometry to its projection (only meaningful for points and segments).
    """
    try:
        # ── extract onto= ────────────────────────────────────────────────────
        onto_m = re.search(r'\bonto\s*=\s*(\S+)', val)
        if not onto_m:
            return None
        onto_raw = onto_m.group(1).strip().rstrip(',')
        if onto_raw in ("xy", "xz", "yz"):
            plane_spec = onto_raw
        else:
            # Expect "(nx,ny,nz):(px,py,pz)"
            parts = onto_raw.split(":")
            if len(parts) != 2:
                return None
            plane_spec = {
                "normal": _parse_triple(parts[0]),
                "anchor": _parse_triple(parts[1]),
            }

        # ── extract object= ──────────────────────────────────────────────────
        obj_m = re.search(r'\bobject\s*=\s*(\w+)\s*:\s*(.+?)(?=,\s*onto|,\s*color|,\s*alpha|,\s*drop|$)',
                          val, re.DOTALL)
        if not obj_m:
            return None
        obj_type = obj_m.group(1).strip().lower()
        obj_raw  = obj_m.group(2).strip()

        if obj_type == "point":
            geo = {"point": _parse_triple(obj_raw)}
        elif obj_type == "segment":
            toks = _split_top(obj_raw)
            triple_toks = [t for t in toks if t.strip().startswith("(")]
            if len(triple_toks) < 2:
                return None
            geo = {"a": _parse_triple(triple_toks[0]),
                   "b": _parse_triple(triple_toks[1])}
        elif obj_type == "sphere":
            toks = _split_top(obj_raw)
            triple_toks = [t for t in toks if t.strip().startswith("(")]
            rest = [t for t in toks if not t.strip().startswith("(")]
            if not triple_toks:
                return None
            center = _parse_triple(triple_toks[0])
            radius = _eval_expr(rest[0]) if rest else 1.0
            geo = {"center": center, "radius": radius}
        else:
            return None

        # ── optional color, alpha, drop ──────────────────────────────────────
        color = "#777777"   # neutral grey default
        alpha = 0.35
        drop  = False

        color_m = re.search(r'\bcolor\s*=\s*(\w+)', val)
        if color_m:
            c = _resolve_color(color_m.group(1))
            if c:
                color = c

        alpha_m = re.search(r'\balpha\s*=\s*([\d.]+)', val)
        if alpha_m:
            alpha = float(alpha_m.group(1))

        drop_m = re.search(r'\bdrop\s*=\s*(true|false|yes|no|1|0)', val, re.I)
        if drop_m:
            drop = drop_m.group(1).lower() in ("true", "yes", "1")

        return {
            "type": "projection",
            "object": obj_type,
            "geometry": geo,
            "plane": plane_spec,
            "color": color,
            "alpha": alpha,
            "drop": drop,
        }
    except Exception:
        return None


def _parse_text_primitive(val: str) -> Dict[str, Any] | None:
    """Parse ``(x,y,z), "string"[, color]``."""
    try:
        tokens = _split_top(val)
        if len(tokens) < 2:
            return None
        pos = _parse_triple(tokens[0])
        text = tokens[1].strip().strip("\"'")
        color = _COLORS["black"]
        for t in tokens[2:]:
            c = _resolve_color(t.strip())
            if c:
                color = c
        return {"type": "text", "pos": pos, "text": text, "color": color}
    except Exception:
        return None


def _parse_right_angle_primitive(val: str) -> Dict[str, Any] | None:
    """Parse ``(vx,vy,vz), (ax,ay,az), (bx,by,bz)[, size][, color]``.
    Draws a small right-angle square marker at vertex V in the plane of
    directions A and B.
    """
    try:
        tokens = _split_top(val)
        triple_toks = [t for t in tokens if t.strip().startswith("(")]
        rest = [t for t in tokens if not t.strip().startswith("(")]
        if len(triple_toks) < 3:
            return None
        vertex = _parse_triple(triple_toks[0])
        dir_a = _parse_triple(triple_toks[1])
        dir_b = _parse_triple(triple_toks[2])

        size = 0.25
        color = _COLORS["black"]
        for t in rest:
            try:
                size = _eval_expr(t)
            except Exception:
                c = _resolve_color(t)
                if c:
                    color = c
        return {"type": "right-angle", "vertex": vertex, "dir_a": dir_a,
                "dir_b": dir_b, "size": size, "color": color}
    except Exception:
        return None


def _parse_solid_of_revolution_primitive(val: str) -> Dict[str, Any] | None:
    """Parse ``f(x), (a, b)[, color][, alpha=0.35][, disks=5]``.

    *f(x)* is any sympy-compatible expression in ``x``.
    *(a, b)* is the x-interval over which the graph is rotated around the x-axis.
    *disks* controls how many interior disk cross-section outlines are drawn.
    """
    try:
        disks_m = re.search(r"\bdisks\s*=\s*(\d+)", val)
        disks = int(disks_m.group(1)) if disks_m else 5
        alpha_m = re.search(r"\balpha\s*=\s*([0-9.]+)", val)
        alpha = float(alpha_m.group(1)) if alpha_m else 0.35

        tokens = _split_top(val)
        if len(tokens) < 2:
            return None
        fx_expr = tokens[0].strip()
        dom_tok = tokens[1].strip()
        rest = tokens[2:]

        # Strip keyword-argument tokens (disks=N, alpha=N) before colour parsing
        rest = [t for t in rest if not re.match(r"^\s*(disks|alpha)\s*=", t)]

        a, b = _parse_range(dom_tok)
        _, color = _split_style_color(rest)
        return {
            "type": "solid-of-revolution",
            "fx": fx_expr,
            "a": a, "b": b,
            "color": color or _COLORS["blue"],
            "alpha": alpha,
            "disks": disks,
        }
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Drawing routines (each takes ax, proj, primitive dict)
# ---------------------------------------------------------------------------

_LS_MAP = {
    "solid": "-",
    "dashed": "--",
    "dotted": ":",
    "dashdot": "-.",
}


def _hidden_line(
    ax, xs3, ys3, zs3, proj, color, lw,
    zorder=4, alpha_front=1.0, alpha_back=0.35, lw_back_scale=0.7,
):
    """Draw a 3D polyline with depth-based solid/dashed splitting.

    Standard layout
        Depth criterion: ``d = x + cx·y`` (z ignored so helices split radially).
        Viewer is at direction (1, cx, sx); positive d = toward viewer = front.

    Symmetric layout
        Both x and y go equally into the screen, so depth is ``d = x + y``.

    d ≥ 0  →  front, solid, full lw.
    d < 0  →  back,  dashed, reduced lw/alpha.

    Crossing points are interpolated so the transition is smooth.
    """
    xs3 = np.asarray(xs3, float)
    ys3 = np.asarray(ys3, float)
    if getattr(proj, "_layout", "standard") == "symmetric":
        # Viewer at (1, C45, s) → depth = x + C45·y
        C45 = getattr(proj, "_sym_C45", math.sqrt(2) / 2)
        depth = xs3 + C45 * ys3
    else:
        cx_coeff = getattr(proj, "_cx", 0.5)
        depth = xs3 + cx_coeff * ys3
    pxs, pys = _proj_array(xs3, ys3, zs3, proj)
    n = len(pxs)
    if n < 2:
        return
    lw_back = lw * lw_back_scale

    # ------------------------------------------------------------------
    # Insert interpolated crossing points wherever depth changes sign
    # ------------------------------------------------------------------
    aug_px: List[float] = [pxs[0]]
    aug_py: List[float] = [pys[0]]
    aug_d:  List[float] = [depth[0]]
    for i in range(1, n):
        d0, d1 = depth[i - 1], depth[i]
        if (d0 > 0) != (d1 > 0):
            t = d0 / (d0 - d1)
            aug_px.append(float(pxs[i - 1] + t * (pxs[i] - pxs[i - 1])))
            aug_py.append(float(pys[i - 1] + t * (pys[i] - pys[i - 1])))
            aug_d.append(0.0)
        aug_px.append(float(pxs[i]))
        aug_py.append(float(pys[i]))
        aug_d.append(float(d1))

    apx = np.array(aug_px)
    apy = np.array(aug_py)
    ad  = np.array(aug_d)
    m = len(apx)

    # ------------------------------------------------------------------
    # Walk through runs of same sign and draw solid or dashed segments.
    # Each segment includes one extra point from the next run so the
    # transition is visually continuous (no gap at crossing).
    # ------------------------------------------------------------------
    i = 0
    while i < m - 1:
        is_front = ad[i] >= 0
        j = i + 1
        while j < m and (ad[j] >= 0) == is_front:
            j += 1
        end = min(j, m - 1)          # include first point of next run
        seg_x = apx[i: end + 1]
        seg_y = apy[i: end + 1]
        if is_front:
            ax.plot(seg_x, seg_y, color=color, lw=lw, alpha=alpha_front,
                    linestyle="-", zorder=zorder, solid_capstyle="round")
        else:
            ax.plot(seg_x, seg_y, color=color, lw=lw_back, alpha=alpha_back,
                    linestyle="--", dashes=(4, 4), zorder=zorder)
        i = j


def _draw_axes(
    ax,
    proj: Callable,
    xrange: Tuple[float, float],
    yrange: Tuple[float, float],
    zrange: Tuple[float, float],
    fontsize: float,
    ticks: bool,
    lw: float,
    xlabel: str,
    ylabel: str,
    zlabel: str,
):
    """Draw the 3D coordinate axes with tick marks and labels."""
    import matplotlib.patches as mpatches
    from matplotlib.patches import FancyArrowPatch

    xlo, xhi = xrange
    ylo, yhi = yrange
    zlo, zhi = zrange

    axis_color = "#333333"
    tick_len_frac = 0.04  # fraction of axis span
    tick_color = "#555555"

    def _axis_arrow(p_from, p_to, label, label_offset=(0.0, 0.0)):
        pf = proj(*p_from)
        pt = proj(*p_to)
        arrow = FancyArrowPatch(
            pf, pt,
            arrowstyle="-|>",
            color=axis_color,
            lw=lw,
            mutation_scale=12,
            zorder=3,
        )
        ax.add_patch(arrow)
        # Axis label slightly beyond the arrowhead
        lx = pt[0] + label_offset[0]
        ly = pt[1] + label_offset[1]
        ax.text(
            lx, ly, label,
            fontsize=fontsize * 0.85,
            ha="center", va="center",
            color=axis_color,
            zorder=4,
        )

    def _dashed_back(p_from, p_to):
        """Draw the negative (behind-origin) extension of an axis as a dashed line."""
        pf = proj(*p_from)
        pt = proj(*p_to)
        ax.plot([pf[0], pt[0]], [pf[1], pt[1]],
                color=axis_color, lw=lw * 0.7, alpha=0.4,
                linestyle="--", dashes=(4, 4), zorder=2)

    # Determine label offsets (nudge labels away from the axis ends)
    dx_label_x = 0.25
    dx_label_y = 0.25

    _sym = getattr(proj, "_layout", "standard") == "symmetric"

    if _sym:
        # x → horizontal (0°), y → upper-right (+45°), z → up
        _axis_arrow((0, 0, 0), (xhi * 1.12, 0, 0), xlabel, label_offset=(dx_label_x, -dx_label_y * 0.3))
        _axis_arrow((0, 0, 0), (0, yhi * 1.12, 0), ylabel, label_offset=(dx_label_x * 0.7, dx_label_y * 0.7))
        _axis_arrow((0, 0, 0), (0, 0, zhi * 1.12), zlabel, label_offset=(0, dx_label_y))
    else:
        # x → lower-left, y → right, z → up
        _axis_arrow((0, 0, 0), (xhi * 1.12, 0, 0), xlabel, label_offset=(-dx_label_x, -dx_label_y * 0.5))
        _axis_arrow((0, 0, 0), (0, yhi * 1.12, 0), ylabel, label_offset=(dx_label_x, 0))
        _axis_arrow((0, 0, 0), (0, 0, zhi * 1.12), zlabel, label_offset=(0, dx_label_y))

    # Negative portions dashed (only if the axis range extends below 0)
    if xlo < 0:
        _dashed_back((0, 0, 0), (xlo, 0, 0))
    if ylo < 0:
        _dashed_back((0, 0, 0), (0, ylo, 0))
    if zlo < 0:
        _dashed_back((0, 0, 0), (0, 0, zlo))

    # Origin
    ox, oy = proj(0, 0, 0)
    ax.plot(ox, oy, "o", color=axis_color, ms=3, zorder=4)

    if not ticks:
        return

    tick_xs = [i for i in range(int(math.ceil(xlo)), int(math.floor(xhi)) + 1) if i != 0]
    tick_ys = [i for i in range(int(math.ceil(ylo)), int(math.floor(yhi)) + 1) if i != 0]
    tick_zs = [i for i in range(int(math.ceil(zlo)), int(math.floor(zhi)) + 1) if i != 0]

    # Tick length in data units — derive from the projected axis span
    tick_half = (xhi - xlo) * tick_len_frac * 0.5

    if _sym:
        # x → horizontal (0°), y → upper-right (+45°)
        # Tick strokes in z-direction (vertical) for x and y axes.
        for xi in tick_xs:
            pz = proj(xi, 0, tick_half)
            mz = proj(xi, 0, -tick_half)
            ax.plot([mz[0], pz[0]], [mz[1], pz[1]], color=tick_color, lw=0.8, zorder=3)
            p0 = proj(xi, 0, 0)
            # x goes horizontal; label directly below tick
            ax.text(p0[0], p0[1] - tick_half * 0.8, f"{xi}",
                    fontsize=fontsize * 0.55, ha="center", va="top", color=tick_color, zorder=4)

        for yi in tick_ys:
            pz = proj(0, yi, tick_half)
            mz = proj(0, yi, -tick_half)
            ax.plot([mz[0], pz[0]], [mz[1], pz[1]], color=tick_color, lw=0.8, zorder=3)
            p0 = proj(0, yi, 0)
            # y goes upper-right; label below the tick (perpendicular)
            ax.text(p0[0] + tick_half * 0.5, p0[1] - tick_half * 0.8, f"{yi}",
                    fontsize=fontsize * 0.55, ha="left", va="top", color=tick_color, zorder=4)

        # Z-axis ticks — use x-direction strokes (lower-right/upper-left)
        for zi in tick_zs:
            px_tick = proj(tick_half, 0, zi)
            mx_tick = proj(-tick_half, 0, zi)
            ax.plot([mx_tick[0], px_tick[0]], [mx_tick[1], px_tick[1]], color=tick_color, lw=0.8, zorder=3)
            # upper-left endpoint → label further upper-left
            ax.text(mx_tick[0] - 0.05, mx_tick[1], f"{zi}",
                    fontsize=fontsize * 0.55, ha="right", va="center", color=tick_color, zorder=4)

    else:
        # Standard layout — x → lower-left, y → right, z → up
        # X-axis ticks: vertical (z-direction) strokes; labels left/right based on sign
        for xi in tick_xs:
            pz = proj(xi, 0, tick_half)
            mz = proj(xi, 0, -tick_half)
            ax.plot([mz[0], pz[0]], [mz[1], pz[1]], color=tick_color, lw=0.8, zorder=3)
            p0 = proj(xi, 0, 0)
            if xi > 0:
                ax.text(p0[0] - tick_half * 0.6, p0[1], f"{xi}",
                        fontsize=fontsize * 0.55, ha="right", va="center", color=tick_color, zorder=4)
            else:
                ax.text(p0[0] + tick_half * 0.6, p0[1], f"{xi}",
                        fontsize=fontsize * 0.55, ha="left", va="center", color=tick_color, zorder=4)

        # Y-axis ticks: vertical (z-direction) strokes; labels below
        for yi in tick_ys:
            pz = proj(0, yi, tick_half)
            mz = proj(0, yi, -tick_half)
            ax.plot([mz[0], pz[0]], [mz[1], pz[1]], color=tick_color, lw=0.8, zorder=3)
            p0 = proj(0, yi, 0)
            ax.text(p0[0], p0[1] - tick_half * 0.8, f"{yi}",
                    fontsize=fontsize * 0.55, ha="center", va="top", color=tick_color, zorder=4)

        # Z-axis ticks — use y-direction strokes (→ right) so ticks are horizontal
        for zi in tick_zs:
            py_tick = proj(0, tick_half, zi)
            my_tick = proj(0, -tick_half, zi)
            ax.plot([my_tick[0], py_tick[0]], [my_tick[1], py_tick[1]], color=tick_color, lw=0.8, zorder=3)
            ax.text(my_tick[0] - 0.05, my_tick[1], f"{zi}",
                    fontsize=fontsize * 0.55, ha="right", va="center", color=tick_color, zorder=4)


def _draw_grid_planes(
    ax, proj: Callable,
    planes: List[str],
    xrange: Tuple[float, float],
    yrange: Tuple[float, float],
    zrange: Tuple[float, float],
    alpha: float,
):
    """Draw translucent grid-plane fills for the given planes (xy, xz, yz)."""
    from matplotlib.patches import Polygon as MplPolygon
    from matplotlib.collections import PatchCollection

    xlo, xhi = xrange
    ylo, yhi = yrange
    zlo, zhi = zrange

    plane_defs = {
        "xy": [(xlo, ylo, 0), (xhi, ylo, 0), (xhi, yhi, 0), (xlo, yhi, 0)],
        "xz": [(xlo, 0, zlo), (xhi, 0, zlo), (xhi, 0, zhi), (xlo, 0, zhi)],
        "yz": [(0, ylo, zlo), (0, yhi, zlo), (0, yhi, zhi), (0, ylo, zhi)],
    }
    plane_colors = {"xy": "#aaaaff", "xz": "#aaffaa", "yz": "#ffaaaa"}

    for name in planes:
        name_l = name.strip().lower()
        if name_l not in plane_defs:
            continue
        corners_3d = plane_defs[name_l]
        verts2d = [proj(*c) for c in corners_3d]
        poly = MplPolygon(verts2d, closed=True,
                          facecolor=plane_colors.get(name_l, "#cccccc"),
                          edgecolor="none", alpha=alpha, zorder=1)
        ax.add_patch(poly)


def _draw_point(ax, proj: Callable, prim: Dict, fontsize: float):
    x, y, z = prim["pos"]
    px, py = proj(x, y, z)
    ax.plot(px, py, "o", color=prim["color"], ms=5, zorder=6)
    label = prim.get("label")
    if label:
        lpos = prim.get("label_pos", "top-right")
        offset = {"top-right": (0.12, 0.12), "top-left": (-0.12, 0.12),
                  "bottom-right": (0.12, -0.12), "bottom-left": (-0.12, -0.12),
                  "top-center": (0, 0.15), "bottom-center": (0, -0.15),
                  "center-right": (0.15, 0), "center-left": (-0.15, 0)}.get(lpos, (0.12, 0.12))
        ax.text(px + offset[0], py + offset[1], f"${label}$",
                fontsize=fontsize * 0.75, color=prim["color"],
                ha="center", va="center", zorder=7)


def _draw_vector(ax, proj: Callable, prim: Dict, fontsize: float, lw: float):
    import matplotlib.patches as mpatches

    x0, y0, z0 = prim["start"]
    dx, dy, dz = prim["components"]
    x1, y1, z1 = x0 + dx, y0 + dy, z0 + dz

    p0 = proj(x0, y0, z0)
    p1 = proj(x1, y1, z1)

    ax.annotate(
        "",
        xy=p1,
        xytext=p0,
        arrowprops=dict(
            arrowstyle="-|>",
            color=prim["color"],
            lw=lw,
            mutation_scale=12,
            shrinkA=0,
            shrinkB=0,
        ),
        zorder=5,
    )
    label = prim.get("label")
    if label:
        mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
        ax.text(mid[0] + 0.12, mid[1] + 0.12, f"${label}$",
                fontsize=fontsize * 0.75, color=prim["color"],
                ha="left", va="bottom", zorder=7)


def _draw_line_segment(ax, proj: Callable, prim: Dict, lw: float):
    x0, y0, z0 = prim["p0"]
    x1, y1, z1 = prim["p1"]
    xs = np.array([x0, x1], float)
    ys = np.array([y0, y1], float)
    zs = np.array([z0, z1], float)
    _hidden_line(ax, xs, ys, zs, proj, prim["color"], lw, zorder=4)


def _draw_line(
    ax, proj: Callable, prim: Dict, lw: float,
    xrange, yrange, zrange,
):
    """Draw an infinite line by clipping to a reasonable extent."""
    px, py, pz = prim["point"]
    dx, dy, dz = prim["direction"]
    # Determine parameter range to cover the visible box
    # Use bounding box diagonal as max t value
    diag = math.sqrt(
        (xrange[1] - xrange[0]) ** 2 +
        (yrange[1] - yrange[0]) ** 2 +
        (zrange[1] - zrange[0]) ** 2
    )
    t_vals = np.linspace(-diag * 1.5, diag * 1.5, 200)
    xs = px + dx * t_vals
    ys = py + dy * t_vals
    zs = pz + dz * t_vals
    _hidden_line(ax, xs, ys, zs, proj, prim["color"], lw, zorder=4)


def _plane_patch_from_normal(
    normal: Tuple[float, float, float],
    through: Tuple[float, float, float],
    xrange, yrange, zrange,
) -> List[Tuple[float, float, float]]:
    """Compute 4 corners of a plane bounded by the axis box."""
    nx, ny, nz = normal
    px, py, pz = through

    # Build two vectors spanning the plane
    # Pick a helper vector not parallel to normal
    n = np.array([nx, ny, nz], dtype=float)
    n_norm = np.linalg.norm(n)
    if n_norm < 1e-12:
        return []
    n = n / n_norm

    helper = np.array([1, 0, 0]) if abs(n[0]) < 0.9 else np.array([0, 1, 0])
    u = np.cross(n, helper)
    u = u / np.linalg.norm(u)
    v = np.cross(n, u)

    # Scale u and v to cover the visible extent
    extent = max(
        xrange[1] - xrange[0],
        yrange[1] - yrange[0],
        zrange[1] - zrange[0],
    ) * 0.75
    p = np.array([px, py, pz])
    c0 = p + extent * u + extent * v
    c1 = p - extent * u + extent * v
    c2 = p - extent * u - extent * v
    c3 = p + extent * u - extent * v
    return [tuple(c) for c in [c0, c1, c2, c3]]


def _draw_plane(ax, proj: Callable, prim: Dict, xrange, yrange, zrange):
    from matplotlib.patches import Polygon as MplPolygon

    if prim["mode"] == "normal":
        corners = _plane_patch_from_normal(
            prim["normal"], prim["through"], xrange, yrange, zrange
        )
    else:
        p0, p1, p2 = prim["points"]
        # Extend to a parallelogram: p0, p1, p1+(p2-p0), p2
        # (gives a reasonable flat polygon through the 3 points)
        a = np.array(p0)
        b = np.array(p1)
        c = np.array(p2)
        d = b + (c - a)
        corners = [tuple(a), tuple(b), tuple(d), tuple(c)]

    if not corners:
        return

    verts2d = [proj(*c) for c in corners]
    poly = MplPolygon(
        verts2d, closed=True,
        facecolor=prim["color"], edgecolor=prim["color"],
        alpha=prim["alpha"], linewidth=1, zorder=2,
    )
    ax.add_patch(poly)


def _draw_limited_plane(ax, proj: Callable, prim: Dict, lw: float):
    """Draw a rectangular patch of a plane over a bounded parameter domain.

    Supported forms (dep = dependent variable):
      dep='z'  → z = expr(x,y),  range0=(xmin,xmax), range1=(ymin,ymax)
      dep='y'  → y = expr(x,z),  range0=(xmin,xmax), range1=(zmin,zmax)
      dep='x'  → x = expr(y,z),  range0=(ymin,ymax), range1=(zmin,zmax)
    """
    from matplotlib.patches import Polygon as MplPolygon

    dep   = prim["dep"]
    expr  = prim["expr"]
    r0    = prim["range0"]   # (min0, max0)
    r1    = prim["range1"]   # (min1, max1)
    color = prim["color"]
    alpha = prim["alpha"]
    border = prim["border"]

    # Build a callable for the dependent variable expression
    import sympy as _sp
    _ns = _sympy_ns()
    if dep == "z":
        _u_sym, _v_sym = _sp.Symbol("x"), _sp.Symbol("y")
    elif dep == "y":
        _u_sym, _v_sym = _sp.Symbol("x"), _sp.Symbol("z")
    else:
        _u_sym, _v_sym = _sp.Symbol("y"), _sp.Symbol("z")
    _expr_sym = _sp.sympify(expr, locals=_ns)
    _dep_fn = _sp.lambdify((_u_sym, _v_sym), _expr_sym, "numpy")

    # Build the 4 corners of the rectangular domain
    params = [
        (r0[0], r1[0]),
        (r0[1], r1[0]),
        (r0[1], r1[1]),
        (r0[0], r1[1]),
    ]

    corners_3d = []
    for u, v in params:
        w = float(_dep_fn(u, v))
        if dep == "z":
            corners_3d.append((u, v, w))
        elif dep == "y":
            corners_3d.append((u, w, v))
        else:
            corners_3d.append((w, u, v))

    verts2d = [proj(*c) for c in corners_3d]
    edge_color = color if border else "none"
    poly = MplPolygon(
        verts2d, closed=True,
        facecolor=color, edgecolor=edge_color,
        alpha=alpha, linewidth=lw * 0.8, zorder=2,
        clip_on=False,
    )
    ax.add_patch(poly)


def _postprocess_spheres_svg(svg_str: str, sphere_defs: list) -> str:
    """Inject SVG radialGradient fills for sphere patches and add dark-mode CSS.

    Replaces each sphere's flat fill with a radial gradient that fades from a
    lighter tint (upper-left highlight) through the base colour to a darker,
    more transparent tint (lower-right shadow).  All stops use tints of the
    sphere's own colour — no pure white or black — so that the gradient survives
    dark-mode CSS colour-inversion filters with the hue roughly preserved and
    the sphere still reading as a round, shaded object.

    A ``<style>`` block is also injected that pre-inverts each sphere fill element
    under ``@media (prefers-color-scheme: dark)`` and ``[data-theme="dark"]``.
    When the page theme then applies ``filter: invert(1) hue-rotate(180deg)`` to
    the SVG, the double application cancels exactly and the original shading
    is restored — the sphere looks identical in light and dark mode.
    """
    import re as _re

    if not sphere_defs:
        return svg_str

    grad_defs_str = ""
    fill_pairs: list = []

    for sd in sphere_defs:
        gid = sd["gid"]
        rc, gc, bc = sd["rgb"]
        alpha = float(sd["alpha"])

        grad_id = f"sg_{gid}"

        # Highlight stop: blend sphere colour 42 % toward white (no pure white).
        mix = 0.42
        lr = rc + mix * (1.0 - rc)
        lg = gc + mix * (1.0 - gc)
        lb = bc + mix * (1.0 - bc)

        # Shadow stop: darken by multiplying (no pure black).
        dr, dg, db = rc * 0.52, gc * 0.52, bc * 0.52

        def _h(r: float, g: float, b: float) -> str:
            return "#{:02x}{:02x}{:02x}".format(
                int(min(r, 1.0) * 255), int(min(g, 1.0) * 255), int(min(b, 1.0) * 255)
            )

        # gradientUnits="objectBoundingBox": cx/cy/r are fractions of bbox.
        # SVG y-axis points DOWN, so cy=0.38 is in the upper portion of the circle.
        grad_defs_str += (
            f'\n  <radialGradient id="{grad_id}"'
            f' cx="0.38" cy="0.38" r="0.72" fx="0.28" fy="0.28"'
            f' gradientUnits="objectBoundingBox">'
            f'\n    <stop offset="0%"   stop-color="{_h(lr,lg,lb)}"'
            f' stop-opacity="{min(alpha * 1.05, 1.0):.3f}"/>'
            f'\n    <stop offset="45%"  stop-color="{_h(rc,gc,bc)}"'
            f' stop-opacity="{alpha:.3f}"/>'
            f'\n    <stop offset="100%" stop-color="{_h(dr,dg,db)}"'
            f' stop-opacity="{alpha * 0.35:.3f}"/>'
            f'\n  </radialGradient>'
        )
        fill_pairs.append((gid, grad_id))

    # ── inject gradient defs ──────────────────────────────────────────────────
    if "</defs>" in svg_str:
        svg_str = svg_str.replace("</defs>", grad_defs_str + "\n </defs>", 1)

    # ── inject dark-mode CSS counteraction ───────────────────────────────────
    # Pre-applying the same filter as the dark-mode theme means the two
    # applications cancel: identity transformation for the sphere fill.
    sel = ", ".join(f"#{g}" for g in [p[0] for p in fill_pairs])
    _inv = "invert(1) hue-rotate(180deg)"
    css = (
        "\n    /* plot3d: counteract dark-mode colour inversion on sphere fills */"
        f"\n    @media (prefers-color-scheme: dark) {{"
        f" {sel} {{ filter: {_inv}; }} }}"
        f"\n    [data-theme=\"dark\"] {sel},"
        f"\n    .dark {sel} {{ filter: {_inv}; }}"
    )
    svg_str = svg_str.replace("</style>", css + "\n  </style>", 1)

    # ── replace flat fill with gradient reference ─────────────────────────────
    for gid, grad_id in fill_pairs:
        def _replace_fill(m: "_re.Match", _gid: str = grad_id, _id: str = gid) -> str:
            inner = m.group(1)
            # style="... fill: #rrggbb; fill-opacity: N; opacity: N; ..."
            inner = _re.sub(r"fill:\s*#[0-9a-fA-F]{3,8}", f"fill: url(#{_gid})", inner)
            # gradient stop-opacity values already encode the alpha; clear any
            # element-level opacity so they are not applied twice.
            inner = _re.sub(r"fill-opacity:\s*[\d.]+", "fill-opacity: 1", inner)
            inner = _re.sub(r"\bopacity:\s*[\d.]+", "opacity: 1", inner)
            # attribute form: fill="#rrggbb"
            inner = _re.sub(r'\bfill="#[0-9a-fA-F]{3,8}"', f'fill="url(#{_gid})"', inner)
            return f'<g id="{_id}">{inner}</g>'

        svg_str = _re.sub(
            rf'<g id="{_re.escape(gid)}">(.*?)</g>',
            _replace_fill,
            svg_str,
            flags=_re.DOTALL,
        )

    return svg_str


def _draw_sphere(ax, proj: Callable, prim: Dict, lw: float):
    """Draw a sphere: circular outline + clipped wireframe with hidden-line splitting.

    Textbook convention: the outline is drawn as a perfect circle of radius r
    centred on the projected centre.  The interior wireframe (great circles and
    latitude parallels) is clipped to that circle so nothing bleeds out, and
    the hidden portions are dashed.  The circle outline is drawn last so it sits
    cleanly on top of the wireframe.
    """
    scx, scy, scz = prim["center"]
    r = prim["radius"]
    color = prim["color"]
    alpha = prim.get("alpha", 0.4)

    # Viewing direction (projected-area criterion), layout-dependent.
    # The visibility vector is the cross product of the two rows of the
    # projection Jacobian.  A surface normal n is front-facing when
    # vis_vec · n > 0 (projected patch area is positive / counter-clockwise).
    #
    # Standard   px=y−x·cx, py=z−x·sx → J rows (−cx,1,0),(−sx,0,1)
    #   cross product → (1, cx, sx)
    #
    # Symmetric  px=s·(x+C45·y), py=s·C45·y+z → J rows (s,s·C45,0),(0,s·C45,1)
    #   cross product → (s·C45, −s, s²·C45)  ∝  (C45, −1, s·C45)
    if getattr(proj, "_layout", "standard") == "symmetric":
        _s_sym  = proj._sym_s
        _C45    = proj._sym_C45
        _vx, _vy, _vz = _C45, -1.0, _s_sym * _C45
    else:
        _vx = 1.0
        _vy = getattr(proj, "_cx", 0.5)
        _vz = getattr(proj, "_sx", 0.4)

    pcx, pcy = proj(scx, scy, scz)   # projected centre

    # ------------------------------------------------------------------
    # 1.  Fill circle (SVG radialGradient injected by post-processing) + clip patch
    # ------------------------------------------------------------------
    # Strategy: instead of embedding a raster Phong image (which dark-mode CSS
    # colour-inversion filters break completely), we draw a plain filled circle
    # and tag it with a unique SVG id.  After fig.savefig() the directive calls
    # _postprocess_spheres_svg(), which injects a <radialGradient> into <defs>
    # and rewrites this circle's fill to reference it.  The gradient uses only
    # tints of the sphere's own colour (no white/black), so when a dark-mode
    # theme applies filter:invert(1) hue-rotate(180deg) the hue is approximately
    # preserved and the sphere still reads as a round, shaded object.
    # A companion <style> block in the SVG pre-inverts the gradient element so
    # themes that use that specific filter restore the original appearance exactly.
    from matplotlib.patches import Circle
    import matplotlib.colors as _mcolors

    _rc, _gc, _bc, _ = _mcolors.to_rgba(color)

    _sphere_gid = f"sphere_fill_{id(prim) & 0xFFFFFFFF:08x}"
    # alpha=1 here: the gradient's stop-opacity values encode the transparency.
    # Setting patch alpha would double-apply opacity (matplotlib uses element-level
    # opacity for patches), so we clear it via the SVG post-processor instead.
    _fill = Circle((pcx, pcy), r, facecolor=color, alpha=1.0,
                   edgecolor="none", zorder=3)
    _fill.set_gid(_sphere_gid)
    ax.add_patch(_fill)

    # Accumulate sphere metadata on the figure for SVG post-processing
    if not hasattr(ax.figure, "_plot3d_sphere_defs"):
        ax.figure._plot3d_sphere_defs = []
    ax.figure._plot3d_sphere_defs.append({
        "gid": _sphere_gid,
        "rgb": (_rc, _gc, _bc),
        "alpha": alpha,
    })

    clip_patch = Circle((pcx, pcy), r, transform=ax.transData)
    ax.add_patch(clip_patch)
    clip_patch.set_visible(False)

    # ------------------------------------------------------------------
    # 2.  Wireframe with hidden-line detection, clipped to the circle
    #     Visibility: outward normal n is visible when  vx*nx + vy*ny + vz*nz > 0
    # ------------------------------------------------------------------
    def _draw_split(xs3d, ys3d, zs3d, nxs, nys, nzs, lw_vis, a_vis, lw_hid, a_hid):
        vis = (_vx * nxs + _vy * nys + _vz * nzs) > 0
        pxs, pys = _proj_array(xs3d, ys3d, zs3d, proj)
        n = len(pxs)
        pxs_c = np.append(pxs, pxs[0])
        pys_c = np.append(pys, pys[0])
        vis_c = np.append(vis, vis[0])
        i = 0
        while i < n:
            j = i + 1
            while j < n and vis_c[j] == vis_c[i]:
                j += 1
            seg_x = pxs_c[i: j + 1]
            seg_y = pys_c[i: j + 1]
            if vis_c[i]:
                line, = ax.plot(seg_x, seg_y, color=color, lw=lw_vis, alpha=a_vis,
                                zorder=4, solid_capstyle="round")
            else:
                line, = ax.plot(seg_x, seg_y, color=color, lw=lw_hid, alpha=a_hid,
                                linestyle="--", dashes=(3, 4), zorder=3)
            line.set_clip_path(clip_patch)
            i = j

    def _great_circle(a1, a2):
        th2 = np.linspace(0, 2*math.pi, 720, endpoint=False)
        dx = r*(np.cos(th2)*a1[0] + np.sin(th2)*a2[0])
        dy = r*(np.cos(th2)*a1[1] + np.sin(th2)*a2[1])
        dz = r*(np.cos(th2)*a1[2] + np.sin(th2)*a2[2])
        _draw_split(scx+dx, scy+dy, scz+dz, dx/r, dy/r, dz/r,
                    lw*0.65, 0.70, lw*0.45, 0.30)

    _great_circle((1, 0, 0), (0, 1, 0))   # equator  (xy-plane)
    _great_circle((1, 0, 0), (0, 0, 1))   # meridian (xz-plane)

    # ------------------------------------------------------------------
    # 3.  Circle outline on top
    # ------------------------------------------------------------------
    ax.add_patch(Circle((pcx, pcy), r, facecolor="none",
                        edgecolor=color, lw=lw, zorder=5))


def _draw_curve(ax, proj: Callable, prim: Dict, lw: float):
    """Sample parametric curve x(t), y(t), z(t) and project."""
    try:
        import sympy
        t_sym = sympy.symbols("t")
        ns = _sympy_ns()
        ns["t"] = t_sym
        xt_fn = sympy.lambdify(t_sym, sympy.sympify(prim["xt"], locals=ns), "numpy")
        yt_fn = sympy.lambdify(t_sym, sympy.sympify(prim["yt"], locals=ns), "numpy")
        zt_fn = sympy.lambdify(t_sym, sympy.sympify(prim["zt"], locals=ns), "numpy")

        t_vals = np.linspace(prim["t0"], prim["t1"], 512)
        xs = np.asarray(xt_fn(t_vals), dtype=float)
        ys = np.asarray(yt_fn(t_vals), dtype=float)
        zs = np.asarray(zt_fn(t_vals), dtype=float)
    except Exception:
        return

    _hidden_line(ax, xs, ys, zs, proj, prim["color"], lw, zorder=4)


def _draw_angle(ax, proj: Callable, prim: Dict, lw: float):
    """Draw an angle arc at vertex between two direction vectors."""
    vx, vy, vz = prim["vertex"]
    ax_dir = np.array(prim["dir_a"], dtype=float)
    bx_dir = np.array(prim["dir_b"], dtype=float)

    # Normalise
    na = np.linalg.norm(ax_dir)
    nb = np.linalg.norm(bx_dir)
    if na < 1e-12 or nb < 1e-12:
        return
    ax_dir = ax_dir / na
    bx_dir = bx_dir / nb

    r = prim["radius"]
    # Sample arc in the plane of ax_dir and bx_dir using slerp
    # Use Gram-Schmidt to get an orthonormal frame
    u = ax_dir.copy()
    v = bx_dir - np.dot(bx_dir, u) * u
    v_norm = np.linalg.norm(v)
    if v_norm < 1e-12:
        return
    v = v / v_norm

    # Total angle between the two directions
    cos_angle = np.clip(np.dot(ax_dir, bx_dir), -1, 1)
    total_angle = math.acos(cos_angle)

    t_vals = np.linspace(0, total_angle, 64)
    xs = vx + r * (np.cos(t_vals)[:, None] * u + np.sin(t_vals)[:, None] * v)[:, 0]
    ys = vy + r * (np.cos(t_vals)[:, None] * u + np.sin(t_vals)[:, None] * v)[:, 1]
    zs = vz + r * (np.cos(t_vals)[:, None] * u + np.sin(t_vals)[:, None] * v)[:, 2]

    pxs, pys = _proj_array(xs, ys, zs, proj)
    ax.plot(pxs, pys, color=prim["color"], lw=lw, zorder=5)  # angle arcs are always solid


def _draw_pyramid(ax, proj: Callable, prim: Dict, lw: float):
    """Draw a pyramid: filled faces (painter's order) + visible/hidden edges.

    Faces are shaded using opacity-based Lambert shading (ambient + diffuse *
    NdotL).  Varying *opacity* rather than *colour brightness* means the 3-D
    shading effect is preserved identically in light mode and dark mode: a lit
    face is more opaque (the colour comes through fully), a shadow face is more
    transparent (the background shows through, darkening it in dark mode just as
    the background lightens it in light mode).  No SVG post-processing needed.

    Each edge is solid if it borders at least one front-facing face,
    dashed otherwise (hidden-line convention).
    """
    from matplotlib.patches import Polygon as MplPolygon

    apex = np.array(prim["apex"], float)
    base = [np.array(b, float) for b in prim["base"]]
    color = prim["color"]
    alpha = prim["alpha"]
    nb = len(base)

    # Viewing direction FROM scene TO eye — layout-dependent
    if getattr(proj, "_layout", "standard") == "symmetric":
        view = np.array(proj._view_dir)
    else:
        view = np.array([1.0, getattr(proj, "_cx", 0.5), getattr(proj, "_sx", 0.4)])

    # Build faces with outward normals
    # Base face (winding: base[0]→base[1]→... looking from below apex)
    base_arr = np.array(base)
    base_centroid = base_arr.mean(axis=0)
    b_e1 = base[1] - base[0]
    b_e2 = base[-1] - base[0]
    base_normal = np.cross(b_e1, b_e2)
    if np.dot(base_normal, apex - base_centroid) > 0:
        base_normal = -base_normal   # ensure it points away from apex

    # Lateral face normals
    lat_normals = []
    for i in range(nb):
        v0 = base[i]
        v1 = base[(i + 1) % nb]
        e1 = v1 - v0
        e2 = apex - v0
        n = np.cross(e1, e2)
        # Ensure it points outward (away from opposite base vertex)
        opp = base[(i + nb // 2) % nb]
        if np.dot(n, v0 - opp) < 0:
            n = -n
        lat_normals.append(n)

    def is_front(normal):
        return np.dot(normal, view) > 0

    base_front = is_front(base_normal)
    lat_front = [is_front(n) for n in lat_normals]

    # ---- Light direction (consistent with sphere shading) ----
    _Lx, _Ly, _Lz = -0.5, 0.55, 0.9
    _Lmag = math.sqrt(_Lx**2 + _Ly**2 + _Lz**2)
    L = np.array([_Lx / _Lmag, _Ly / _Lmag, _Lz / _Lmag])
    view_hat = view / (np.linalg.norm(view) + 1e-12)

    def _face_alpha(normal):
        """Opacity-based Lambert shading.

        Ambient 0.35 + diffuse 0.65*NdotL for front-facing geometry; back-facing
        geometry gets 0.12× (nearly invisible, as expected for a solid).
        Range in [0.12·α, α], so the user-specified alpha is the maximum achieved
        by the most lit front face pointing straight at the light.
        """
        n_hat = normal / (np.linalg.norm(normal) + 1e-12)
        if float(np.dot(n_hat, view_hat)) < 0:   # back-facing toward viewer
            return alpha * 0.12
        NdotL = float(np.clip(np.dot(n_hat, L), 0.0, 1.0))
        return alpha * (0.35 + 0.65 * NdotL)

    # ---- Filled faces (painter's algorithm, back to front) ----
    def face_depth_key(verts):
        return np.dot(np.mean(verts, axis=0), view)   # smaller = farther, drawn first

    face_list = [(base, base_normal)] + [
        ([base[i], base[(i + 1) % nb], apex], lat_normals[i]) for i in range(nb)
    ]
    face_list_sorted = sorted(face_list, key=lambda f: face_depth_key(np.array(f[0])))

    for face, normal in face_list_sorted:
        verts2d = [proj(*pt) for pt in face]
        ax.add_patch(MplPolygon(verts2d, closed=True,
                                facecolor=color, edgecolor="none",
                                alpha=_face_alpha(normal), zorder=2))

    # ---- Edges ----
    def _edge(p0, p1, front):
        xs = np.array([p0[0], p1[0]])
        ys = np.array([p0[1], p1[1]])
        zs = np.array([p0[2], p1[2]])
        if front:
            pxs, pys = _proj_array(xs, ys, zs, proj)
            ax.plot(pxs, pys, color=color, lw=lw, alpha=1.0,
                    linestyle="-", zorder=4, solid_capstyle="round")
        else:
            pxs, pys = _proj_array(xs, ys, zs, proj)
            ax.plot(pxs, pys, color=color, lw=lw*0.7, alpha=0.4,
                    linestyle="--", dashes=(4, 4), zorder=3)

    # Base edges: visible if base face is front OR the adjacent lateral face is front
    for i in range(nb):
        edge_front = base_front or lat_front[i] or lat_front[(i - 1) % nb]
        _edge(base[i], base[(i + 1) % nb], edge_front)

    # Lateral edges (base[i] → apex): visible if adjacent lateral faces are front
    for i in range(nb):
        edge_front = lat_front[i] or lat_front[(i - 1) % nb]
        _edge(base[i], apex, edge_front)


# ---------------------------------------------------------------------------
# Projection helpers
# ---------------------------------------------------------------------------

def _project_point_onto_plane(
    P: np.ndarray, plane_spec
) -> np.ndarray:
    """Orthogonal projection of point P onto the given plane.

    plane_spec is one of:
      - "xy"  → zero the z component
      - "xz"  → zero the y component
      - "yz"  → zero the x component
      - dict with keys "normal" and "anchor"
    """
    if plane_spec == "xy":
        return np.array([P[0], P[1], 0.0])
    if plane_spec == "xz":
        return np.array([P[0], 0.0, P[2]])
    if plane_spec == "yz":
        return np.array([0.0, P[1], P[2]])
    # General plane
    n = np.array(plane_spec["normal"], dtype=float)
    q = np.array(plane_spec["anchor"], dtype=float)
    n_hat = n / (np.linalg.norm(n) + 1e-15)
    return P - np.dot(P - q, n_hat) * n_hat


def _plane_basis(plane_spec):
    """Return (n_hat, e1, e2) — a right-hand orthonormal frame for the plane.

    e1 and e2 are two orthonormal vectors *inside* the plane; n_hat is the
    outward normal.  Used to parameterise circles/disks lying in the plane.
    """
    if plane_spec == "xy":
        return np.array([0., 0., 1.]), np.array([1., 0., 0.]), np.array([0., 1., 0.])
    if plane_spec == "xz":
        return np.array([0., 1., 0.]), np.array([1., 0., 0.]), np.array([0., 0., 1.])
    if plane_spec == "yz":
        return np.array([1., 0., 0.]), np.array([0., 1., 0.]), np.array([0., 0., 1.])
    # General plane
    n = np.array(plane_spec["normal"], dtype=float)
    n_hat = n / (np.linalg.norm(n) + 1e-15)
    # Pick a non-parallel seed vector to build e1
    seed = np.array([1., 0., 0.]) if abs(n_hat[0]) < 0.9 else np.array([0., 1., 0.])
    e1 = np.cross(n_hat, seed)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(n_hat, e1)
    return n_hat, e1, e2


def _sor_draw_circle(
    ax, proj, xi: float, ri: float, color, lw: float,
    zorder: int = 4, alpha_back: float = 0.35, lw_back_scale: float = 0.7,
):
    """Draw a circle (xi, ri·cosθ, ri·sinθ) with solid-front / dashed-back splitting.

    The visibility criterion is derived from the sign of the projected area of
    the surface patch, i.e. the 2-D cross product of the projected tangential
    vectors at each sample point.

    Standard layout  (proj(x,y,z) = (y − x·cx, z − x·sx)):
        Tangent along θ:  (0, −sinθ, cosθ) → screen (−cx·sinθ, cx·sinθ... wait)
        Cross product (screen z) = cx·cosθ + sx·sinθ  →  front when > 0.

    Symmetric layout  (proj(x,y,z) = (s·(x+C45·y), s·C45·y+z)):
        Tangent along θ:  dpx = −s·C45·sinθ,  dpy = −s·C45·sinθ + cosθ
        Tangent along x:  dpx =  s,            dpy = 0
        Cross product = dpx_θ·dpy_x − dpy_θ·dpx_x
                      = (−s·C45·sinθ)·0 − (cosθ − s·C45·sinθ)·s
                      = −s·(cosθ − s·C45·sinθ)
                      = s·(s·C45·sinθ − cosθ)
        → front when s·C45·sinθ − cosθ > 0, i.e. sinθ > cosθ/(s·C45).

    In both cases the criterion is linear in (cosθ, sinθ), so the
    solid/dashed boundary is analytically known (two crossing points).
    """
    n = 361
    th = np.linspace(0.0, 2.0 * math.pi, n, endpoint=True)

    if getattr(proj, "_layout", "standard") == "symmetric":
        s   = proj._sym_s
        C45 = proj._sym_C45
        # vis > 0 → front (projected area > 0)
        vis = s * C45 * np.sin(th) - np.cos(th)
    else:
        cx = getattr(proj, "_cx", 0.5)
        sx = getattr(proj, "_sx", 0.25)
        vis = cx * np.cos(th) + sx * np.sin(th)   # ≥ 0 → front

    pxs, pys = _proj_array(
        np.full(n, float(xi)), ri * np.cos(th), ri * np.sin(th), proj
    )

    lw_back = lw * lw_back_scale

    # Insert interpolated crossing points where sign changes
    aug_px: List[float] = [float(pxs[0])]
    aug_py: List[float] = [float(pys[0])]
    aug_v:  List[float] = [float(vis[0])]
    for i in range(1, n):
        v0, v1 = float(vis[i - 1]), float(vis[i])
        if (v0 > 0) != (v1 > 0):
            t = v0 / (v0 - v1)
            aug_px.append(float(pxs[i - 1]) + t * (float(pxs[i]) - float(pxs[i - 1])))
            aug_py.append(float(pys[i - 1]) + t * (float(pys[i]) - float(pys[i - 1])))
            aug_v.append(0.0)
        aug_px.append(float(pxs[i]))
        aug_py.append(float(pys[i]))
        aug_v.append(float(v1))

    apx = np.array(aug_px)
    apy = np.array(aug_py)
    av  = np.array(aug_v)
    m = len(apx)

    i = 0
    while i < m - 1:
        is_front = av[i] >= 0
        j = i + 1
        while j < m and (av[j] >= 0) == is_front:
            j += 1
        end = min(j, m - 1)
        seg_x = apx[i: end + 1]
        seg_y = apy[i: end + 1]
        if is_front:
            ax.plot(seg_x, seg_y, color=color, lw=lw, alpha=1.0,
                    linestyle="-", zorder=zorder, solid_capstyle="round")
        else:
            ax.plot(seg_x, seg_y, color=color, lw=lw_back, alpha=alpha_back,
                    linestyle="--", dashes=(4, 4), zorder=zorder)
        i = j


def _draw_solid_of_revolution(ax, proj: Callable, prim: Dict, lw: float):
    """Draw a solid of revolution (disk method).

    Rotates the graph of y = f(x) around the x-axis from x=a to x=b.
    The surface is parametrised as P(x, θ) = (x, r(x)·cos θ, r(x)·sin θ)
    where r(x) = |f(x)|.

    Visual elements:
    * Filled quad strips (painter's algorithm, Lambert-shaded front / faint back).
    * End-cap circles at x=a and x=b.
    * *disks* interior rim circles (disk-method cross-sections).
    * True silhouette generator curves that form the projected outline.
    * The original generator curve f(x) at θ=0 (shows what was revolved).
    """
    from matplotlib.patches import Polygon as MplPolygon
    import sympy

    fx_expr = prim["fx"]
    a = float(prim["a"])
    b = float(prim["b"])
    color = prim["color"]
    alpha = float(prim.get("alpha", 0.35))
    n_disks = int(prim.get("disks", 5))

    # --- Evaluate r(x) = |f(x)| ------------------------------------------
    try:
        x_sym = sympy.symbols("x")
        ns = _sympy_ns()
        fx_fn = sympy.lambdify(x_sym, sympy.sympify(fx_expr, locals=ns), "numpy")
    except Exception:
        return

    nx = 50       # strips along x
    ntheta = 36   # strips around the revolution (every 10°)

    xs = np.linspace(a, b, nx)
    try:
        rs = np.abs(np.asarray(fx_fn(xs), dtype=float))
        rs = np.where(np.isfinite(rs), rs, 0.0)
    except Exception:
        return

    # --- Viewing direction ------------------------------------------------
    if getattr(proj, "_layout", "standard") == "symmetric":
        vx, vy, vz = proj._view_dir
        # Projected-area visibility criterion: cross product (C45, -1, s·C45)
        # Front-facing when C45·nx - ny + s·C45·nz > 0; for body normal (0,c,s): -c + s·C45·s > 0
        _sym_s   = getattr(proj, "_sym_s",   0.5)
        _sym_C45 = getattr(proj, "_sym_C45", 1.0 / math.sqrt(2.0))
        vis_vy, vis_vz = -1.0, _sym_s * _sym_C45
    else:
        vx = 1.0
        vy = getattr(proj, "_cx", 0.5)
        vz = getattr(proj, "_sx", 0.4)
        # Projected-area visibility criterion: cross product (1, cx, sx)
        # Front-facing when cx·ny + sx·nz > 0; for body normal (0,c,s): cx·c + sx·s > 0
        vis_vy, vis_vz = vy, vz
    vlen = math.sqrt(vx**2 + vy**2 + vz**2)
    vis_mag = math.sqrt(vis_vy**2 + vis_vz**2)  # for normalising n_dot_v to [-1,1]

    # Light direction (consistent with sphere / pyramid shading)
    _Lx, _Ly, _Lz = -0.4, 0.55, 0.85
    _Lmag = math.sqrt(_Lx**2 + _Ly**2 + _Lz**2)
    _Ly, _Lz = _Ly / _Lmag, _Lz / _Lmag   # only y-z components used for body

    thetas = np.linspace(0.0, 2.0 * math.pi, ntheta, endpoint=False)

    # ================================================================
    # 1. Filled quad strips — painter's algorithm (back to front)
    # ================================================================
    quads = []  # (depth, face_alpha, P00, P10, P11, P01)
    for i in range(nx - 1):
        x0, x1 = float(xs[i]), float(xs[i + 1])
        r0, r1 = float(rs[i]), float(rs[i + 1])
        for j in range(ntheta):
            j1 = (j + 1) % ntheta
            c0, s0 = math.cos(thetas[j]),  math.sin(thetas[j])
            c1, s1 = math.cos(thetas[j1]), math.sin(thetas[j1])

            P00 = (x0, r0 * c0, r0 * s0)
            P10 = (x1, r1 * c0, r1 * s0)
            P11 = (x1, r1 * c1, r1 * s1)
            P01 = (x0, r0 * c1, r0 * s1)

            # Centroid depth in view direction
            xc  = (x0 + x1) * 0.5
            rc  = (r0 + r1) * 0.5
            avg_c = (c0 + c1) * 0.5
            avg_s = (s0 + s1) * 0.5
            depth = vx * xc + vy * rc * avg_c + vz * rc * avg_s

            # Visibility: projected-area criterion (layout-aware)
            n_dot_v = vis_vy * avg_c + vis_vz * avg_s
            n_dot_v_norm = n_dot_v / vis_mag   # in [-1, 1]; encodes "how directly facing viewer"
            is_front = n_dot_v_norm > 0

            # Lambert shading (y–z component of normal vs. light)
            NdotL = max(0.0, _Ly * avg_c + _Lz * avg_s)
            # Alpha: viewer-facing gradient (primary) mixed with Lambert (secondary)
            viewer_w = max(0.0, n_dot_v_norm)   # 0 (grazing) → 1 (directly facing)
            face_alpha = alpha * (0.10 + 0.55 * viewer_w + 0.35 * NdotL) if is_front else alpha * 0.04

            quads.append((depth, face_alpha, P00, P10, P11, P01))

    quads.sort(key=lambda q: q[0])   # back → front

    for _, face_alpha, P00, P10, P11, P01 in quads:
        verts2d = [proj(*P) for P in (P00, P10, P11, P01)]
        ax.add_patch(MplPolygon(verts2d, closed=True,
                                facecolor=color, edgecolor="none",
                                alpha=face_alpha, zorder=2))

    # ================================================================
    # 2. End caps at x=a and x=b
    # ================================================================
    for xi, ri_val, is_right in [(a, float(rs[0]), False), (b, float(rs[-1]), True)]:
        if ri_val < 1e-12:
            continue
        th = np.linspace(0.0, 2.0 * math.pi, 361)
        xs_cap = np.full(361, xi)
        ys_cap = ri_val * np.cos(th)
        zs_cap = ri_val * np.sin(th)
        pxs_c, pys_c = _proj_array(xs_cap, ys_cap, zs_cap, proj)
        # Right cap normal=(+1,0,0) → faces viewer when vx>0 (always for our projections)
        # Left  cap normal=(-1,0,0) → faces away
        cap_alpha = alpha * 0.50 if is_right else alpha * 0.08
        ax.fill(pxs_c, pys_c, color=color, alpha=cap_alpha, zorder=2)
        _sor_draw_circle(ax, proj, xi, ri_val, color, lw, zorder=4)

    # ================================================================
    # 3. Interior rim circles (disk cross-section outlines)
    # ================================================================
    if n_disks > 0:
        disk_xs = np.linspace(a, b, n_disks + 2)[1:-1]   # exclude endpoints
        for xi in disk_xs:
            try:
                ri = float(np.abs(fx_fn(xi)))
            except Exception:
                continue
            if ri < 1e-12:
                continue
            _sor_draw_circle(ax, proj, xi, ri, color, lw * 0.65, zorder=4)

    # ================================================================
    # 4. Generator curves (visual outline + original function)
    # ================================================================
    # True silhouette generators lie at the two θ values where the projected-
    # area criterion (same as _sor_draw_circle) equals zero.
    #
    # Standard layout:  cx·cosθ + sx·sinθ = 0  →  θ = atan2(−cx,  sx)
    # Symmetric layout: s·C45·sinθ − cosθ = 0  →  θ = atan2(  1, s·C45)
    #
    # Both generators lie on the silhouette edge → drawn solid throughout.
    if getattr(proj, "_layout", "standard") == "symmetric":
        _s   = proj._sym_s
        _C45 = proj._sym_C45
        theta_sil = math.atan2(1.0, _s * _C45)
    else:
        _cx = getattr(proj, "_cx", 0.5)
        _sx = getattr(proj, "_sx", 0.25)
        theta_sil = math.atan2(-_cx, _sx)
    for theta_g in (theta_sil, theta_sil + math.pi):
        cg, sg = math.cos(theta_g), math.sin(theta_g)
        pxg, pyg = _proj_array(xs, rs * cg, rs * sg, proj)
        ax.plot(pxg, pyg, color=color, lw=lw, alpha=1.0,
                linestyle="-", zorder=5, solid_capstyle="round")

    # The generating function at θ=0: P = (x, f(x), 0)
    # Drawn separately to show the curve that was revolved (pedagogical).
    try:
        rs_signed = np.asarray(fx_fn(xs), dtype=float)
        rs_signed = np.where(np.isfinite(rs_signed), rs_signed, 0.0)
    except Exception:
        rs_signed = rs
    _hidden_line(ax, xs, rs_signed, np.zeros_like(xs), proj, color, lw, zorder=5)


def _draw_projection(ax, proj: Callable, prim: Dict, lw: float):
    """Draw the orthogonal projection of a point, segment, or sphere onto a plane.

    Visual convention:
      - Projected geometry (shadow) is drawn with a dashed line style so it
        clearly reads as a secondary/derived object, not a real edge.
      - Drop lines (perpendiculars from original geometry to shadow) are also
        dashed.
      - The sphere shadow is a correctly projected circle (an ellipse in screen
        space) sampled in 3D and then projected, not a matplotlib Circle patch.
    """
    plane   = prim["plane"]
    color   = prim["color"]
    alpha   = prim["alpha"]
    drop    = prim["drop"]
    obj     = prim["object"]
    geo     = prim["geometry"]

    _dashes = (4, 4)

    def _dashed_drop(P3, Pp3):
        """Dashed perpendicular segment from 3-D point P3 to its shadow Pp3."""
        x0, y0 = proj(*P3)
        x1, y1 = proj(*Pp3)
        ax.plot([x0, x1], [y0, y1], color=color, lw=lw * 0.6,
                linestyle="--", dashes=_dashes, alpha=alpha, zorder=2)

    if obj == "point":
        P  = np.array(geo["point"], dtype=float)
        Pp = _project_point_onto_plane(P, plane)
        # Projected point dot
        px, py = proj(*Pp)
        ax.plot([px], [py], "o", color=color, markersize=5, alpha=alpha, zorder=2)
        # Dashed drop line
        if drop:
            _dashed_drop(P, Pp)

    elif obj == "segment":
        A  = np.array(geo["a"], dtype=float)
        B  = np.array(geo["b"], dtype=float)
        Ap = _project_point_onto_plane(A, plane)
        Bp = _project_point_onto_plane(B, plane)
        # Projected segment — dashed
        x0, y0 = proj(*Ap)
        x1, y1 = proj(*Bp)
        ax.plot([x0, x1], [y0, y1], color=color, lw=lw,
                linestyle="--", dashes=_dashes, alpha=alpha, zorder=2)
        # Dashed drop lines from each endpoint
        if drop:
            _dashed_drop(A, Ap)
            _dashed_drop(B, Bp)

    elif obj == "sphere":
        C  = np.array(geo["center"], dtype=float)
        r  = float(geo["radius"])
        Cp = _project_point_onto_plane(C, plane)
        # The orthogonal projection of a sphere (center C, radius r) onto a plane
        # is a disk of radius r centred at C'.  Its boundary is the circle
        #   Cp + r·cos(θ)·e1 + r·sin(θ)·e2
        # in 3-D, where e1,e2 are orthonormal vectors inside the plane.
        # We sample this circle in 3-D and project each point to screen space —
        # this correctly handles the oblique projection (the result is generally
        # an ellipse in screen space).
        _, e1, e2 = _plane_basis(plane)
        th = np.linspace(0.0, 2.0 * math.pi, 361)
        xs = Cp[0] + r * (np.cos(th) * e1[0] + np.sin(th) * e2[0])
        ys = Cp[1] + r * (np.cos(th) * e1[1] + np.sin(th) * e2[1])
        zs = Cp[2] + r * (np.cos(th) * e1[2] + np.sin(th) * e2[2])
        pxs, pys = _proj_array(xs, ys, zs, proj)
        # Faint filled shadow disk
        ax.fill(pxs, pys, color=color, alpha=alpha * 0.45, zorder=2)
        # Dashed outline
        ax.plot(pxs, pys, color=color, lw=lw * 0.7,
                linestyle="--", dashes=_dashes, alpha=alpha, zorder=2)
        # Dashed drop line from 3-D centre to shadow centre
        if drop:
            _dashed_drop(C, Cp)


def _draw_text(ax, proj: Callable, prim: Dict, fontsize: float):
    x, y, z = prim["pos"]
    px, py = proj(x, y, z)
    ax.text(px, py, prim["text"], color=prim["color"],
            fontsize=fontsize * 0.75, ha="left", va="bottom", zorder=7)


def _draw_right_angle(ax, proj: Callable, prim: Dict, lw: float):
    """Draw a right-angle square marker at vertex between two direction vectors."""
    vx, vy, vz = prim["vertex"]
    a = np.array(prim["dir_a"], dtype=float)
    b = np.array(prim["dir_b"], dtype=float)

    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na < 1e-12 or nb < 1e-12:
        return
    a = a / na
    b = b / nb

    s = prim["size"]
    v = np.array([vx, vy, vz], dtype=float)

    # Four corners of the square marker
    p1 = v + s * a               # along first leg
    p2 = v + s * b               # along second leg
    pc = v + s * a + s * b       # inner corner

    # Draw the two sides of the L (p1 → pc → p2)
    pts = np.array([p1, pc, p2])
    pxs, pys = _proj_array(pts[:, 0], pts[:, 1], pts[:, 2], proj)
    ax.plot(pxs, pys, color=prim["color"], lw=lw * 0.85, zorder=5, solid_capstyle="round")


# ---------------------------------------------------------------------------
# Core render function
# ---------------------------------------------------------------------------

def _render_plot3d(
    *,
    azimuth: float = 40.0,
    elevation: float = 50.0,
    layout: str = "standard",
    xrange: Tuple[float, float] = (-5.0, 5.0),
    yrange: Tuple[float, float] = (-5.0, 5.0),
    zrange: Tuple[float, float] = (-5.0, 5.0),
    xlabel: str = "$x$",
    ylabel: str = "$y$",
    zlabel: str = "$z$",
    ticks: bool = True,
    grid_planes: List[str] = (),
    grid_alpha: float = 0.07,
    fontsize: float = 20.0,
    lw: float = 2.5,
    figsize: Tuple[float, float] = (6.0, 6.0),
    use_usetex: bool = True,
    primitives: List[Dict],
):
    """Render the 3D figure and return a (fig, ax) pair."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    try:
        matplotlib.rcParams["text.usetex"] = use_usetex
        if not use_usetex:
            matplotlib.rcParams["mathtext.fontset"] = "cm"
    except Exception:
        pass

    if layout == "symmetric":
        proj = _make_sym_proj(elevation)
    else:
        proj = _make_proj(azimuth, elevation)

    fig, ax = plt.subplots(figsize=figsize)
    ax.set_aspect("equal")
    ax.axis("off")

    # Grid planes (drawn first, behind everything)
    if grid_planes:
        _draw_grid_planes(ax, proj, grid_planes, xrange, yrange, zrange, grid_alpha)

    # Coordinate axes
    _draw_axes(ax, proj, xrange, yrange, zrange, fontsize, ticks, lw,
               xlabel, ylabel, zlabel)

    # Primitives in declaration order (planes/spheres first for painter's algorithm)
    def _prim_zorder_key(p):
        return {"plane": 0, "limited-plane": 0, "projection": 0, "solid-of-revolution": 1, "sphere": 1, "pyramid": 2,
                "curve": 3, "line": 3, "line-segment": 4,
                "angle": 5, "right-angle": 5, "vector": 6, "point": 7, "text": 8}.get(p["type"], 3)

    for prim in sorted(primitives, key=_prim_zorder_key):
        t = prim["type"]
        try:
            if t == "point":
                _draw_point(ax, proj, prim, fontsize)
            elif t == "vector":
                _draw_vector(ax, proj, prim, fontsize, lw)
            elif t == "line-segment":
                _draw_line_segment(ax, proj, prim, lw)
            elif t == "line":
                _draw_line(ax, proj, prim, lw, xrange, yrange, zrange)
            elif t == "plane":
                _draw_plane(ax, proj, prim, xrange, yrange, zrange)
            elif t == "limited-plane":
                _draw_limited_plane(ax, proj, prim, lw)
            elif t == "sphere":
                _draw_sphere(ax, proj, prim, lw)
            elif t == "curve":
                _draw_curve(ax, proj, prim, lw)
            elif t == "angle":
                _draw_angle(ax, proj, prim, lw)
            elif t == "right-angle":
                _draw_right_angle(ax, proj, prim, lw)
            elif t == "pyramid":
                _draw_pyramid(ax, proj, prim, lw)
            elif t == "solid-of-revolution":
                _draw_solid_of_revolution(ax, proj, prim, lw)
            elif t == "projection":
                _draw_projection(ax, proj, prim, lw)
            elif t == "text":
                _draw_text(ax, proj, prim, fontsize)
        except Exception:
            pass  # skip broken primitives silently

    ax.autoscale_view()
    fig.tight_layout(pad=0.2)
    return fig, ax


# ---------------------------------------------------------------------------
# Directive
# ---------------------------------------------------------------------------

_MULTI_KEYS = {
    "point", "vector", "line-segment", "line",
    "plane", "limited-plane", "sphere", "curve", "angle", "right-angle", "pyramid", "projection", "text",
    "solid-of-revolution",
}

_PRIMITIVE_PARSERS: Dict[str, Callable[[str], Dict | None]] = {
    "point": _parse_point_primitive,
    "vector": _parse_vector_primitive,
    "line-segment": _parse_line_segment_primitive,
    "line": _parse_line_primitive,
    "plane": _parse_plane_primitive,
    "limited-plane": _parse_limited_plane_primitive,
    "sphere": _parse_sphere_primitive,
    "curve": _parse_curve_primitive,
    "angle": _parse_angle_primitive,
    "right-angle": _parse_right_angle_primitive,
    "pyramid": _parse_pyramid_primitive,
    "projection": _parse_projection_primitive,
    "solid-of-revolution": _parse_solid_of_revolution_primitive,
    "text": _parse_text_primitive,
}


class Plot3dDirective(SphinxDirective):
    has_content = True
    required_arguments = 0
    option_spec = {
        "width": directives.length_or_percentage_or_unitless,
        "align": lambda a: directives.choice(a, ["left", "center", "right"]),
        "class": directives.class_option,
        "name": directives.unchanged,
        "nocache": directives.flag,
        "alt": directives.unchanged,
        "usetex": directives.unchanged,
        "fontsize": directives.unchanged,
        "lw": directives.unchanged,
        "figsize": directives.unchanged,
        "azimuth": directives.unchanged,
        "elevation": directives.unchanged,
        "layout": directives.unchanged,
        "xrange": directives.unchanged,
        "yrange": directives.unchanged,
        "zrange": directives.unchanged,
        "xlabel": directives.unchanged,
        "ylabel": directives.unchanged,
        "zlabel": directives.unchanged,
        "ticks": directives.unchanged,
        "grid-planes": directives.unchanged,
        "grid-alpha": directives.unchanged,
    }

    def _parse_kv_block(self) -> Tuple[Dict[str, Any], Dict[str, List[str]], int]:
        lines = list(self.content)
        scalars: Dict[str, Any] = {}
        lists: Dict[str, List[str]] = {k: [] for k in _MULTI_KEYS}
        caption_idx = 0

        fenced = lines and lines[0].strip() == "---"
        if fenced:
            idx = 1
            while idx < len(lines) and lines[idx].strip() != "---":
                line = lines[idx].rstrip()
                if line.strip():
                    m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
                    if m:
                        key, value = m.group(1), m.group(2)
                        if key in lists:
                            lists[key].append(value)
                        else:
                            scalars[key] = value
                idx += 1
            if idx < len(lines) and lines[idx].strip() == "---":
                idx += 1
            while idx < len(lines) and not lines[idx].strip():
                idx += 1
            return scalars, lists, idx

        for i, line in enumerate(lines):
            if not line.strip():
                caption_idx = i + 1
                continue
            m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
            if m:
                key, value = m.group(1), m.group(2)
                if key in lists:
                    lists[key].append(value)
                else:
                    scalars[key] = value
                caption_idx = i + 1
            else:
                break
        return scalars, lists, caption_idx

    def run(self) -> list:
        env = self.state.document.settings.env
        app = env.app

        scalars, lists, caption_idx = self._parse_kv_block()
        merged = {**scalars, **self.options}

        def _f(key: str, default: float) -> float:
            v = merged.get(key)
            if v in (None, ""):
                return default
            try:
                return float(v)
            except Exception:
                try:
                    return _eval_expr(str(v))
                except Exception:
                    return default

        azimuth = _f("azimuth", 40.0)
        elevation = _f("elevation", 25.0)
        layout_raw = str(merged.get("layout", "standard")).strip().lower()
        layout = "symmetric" if layout_raw == "symmetric" else "standard"
        fontsize = _f("fontsize", 20.0)
        lw = _f("lw", 2.5)

        def _parse_rng(key: str, default: float) -> Tuple[float, float]:
            v = merged.get(key)
            if v in (None, ""):
                return -default, default
            try:
                return _parse_range(str(v), default)
            except Exception:
                return -default, default

        xrange = _parse_rng("xrange", 5.0)
        yrange = _parse_rng("yrange", 5.0)
        zrange = _parse_rng("zrange", 5.0)

        xlabel = str(merged.get("xlabel", "$x$"))
        ylabel = str(merged.get("ylabel", "$y$"))
        zlabel = str(merged.get("zlabel", "$z$"))
        ticks = _parse_bool(merged.get("ticks"), default=True)
        grid_alpha = _f("grid-alpha", 0.07)

        grid_planes_raw = str(merged.get("grid-planes", "")).strip()
        grid_planes: List[str] = (
            [p.strip() for p in grid_planes_raw.split(",") if p.strip()]
            if grid_planes_raw else []
        )

        # figsize
        figsize_raw = merged.get("figsize")
        figsize = (6.0, 6.0)
        if figsize_raw:
            try:
                parts = str(figsize_raw).strip("()[] ").split(",")
                figsize = (float(parts[0]), float(parts[1]))
            except Exception:
                pass

        # usetex
        usetex_raw = merged.get("usetex")
        if usetex_raw is None:
            use_usetex = bool(getattr(app.config, "plot_default_usetex", True))
        else:
            use_usetex = _parse_bool(usetex_raw, default=True)

        # Parse all primitives
        primitives: List[Dict] = []
        for key, parser in _PRIMITIVE_PARSERS.items():
            for val in lists.get(key, []):
                prim = parser(val)
                if prim is not None:
                    primitives.append(prim)

        # Build content hash for caching
        content_str = (
            f"{azimuth}|{elevation}|{layout}|{xrange}|{yrange}|{zrange}"
            f"|{xlabel}|{ylabel}|{zlabel}|{ticks}|{grid_planes}|{grid_alpha}"
            f"|{fontsize}|{lw}|{figsize}|{use_usetex}"
            f"|{[(p.get('type'), str(p)) for p in primitives]}"
        )
        content_hash = hashlib.sha1(content_str.encode()).hexdigest()[:16]

        explicit_name = merged.get("name", "").strip() or None
        stable_name = re.sub(r"[^A-Za-z0-9_-]", "_", explicit_name) if explicit_name else None
        base_name = stable_name or f"plot3d_{content_hash}"

        rel_dir = os.path.join("_static", "plot3d")
        abs_dir = os.path.join(app.srcdir, rel_dir)
        os.makedirs(abs_dir, exist_ok=True)
        svg_name = f"{base_name}.svg"
        abs_svg = os.path.join(abs_dir, svg_name)
        abs_meta = os.path.join(abs_dir, f"{base_name}.sha1")

        regenerate = ("nocache" in merged) or not os.path.exists(abs_svg)
        if (not regenerate) and stable_name:
            try:
                prev = open(abs_meta, "r", encoding="utf-8").read().strip()
            except Exception:
                prev = None
            if prev != str(content_hash):
                regenerate = True

        if regenerate:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as _plt

            fig = None
            _old_usetex = None
            _old_mathtext = None
            try:
                _old_usetex = matplotlib.rcParams.get("text.usetex")
                _old_mathtext = matplotlib.rcParams.get("mathtext.fontset")

                fig, ax = _render_plot3d(
                    azimuth=azimuth,
                    elevation=elevation,
                    layout=layout,
                    xrange=xrange,
                    yrange=yrange,
                    zrange=zrange,
                    xlabel=xlabel,
                    ylabel=ylabel,
                    zlabel=zlabel,
                    ticks=ticks,
                    grid_planes=grid_planes,
                    grid_alpha=grid_alpha,
                    fontsize=fontsize,
                    lw=lw,
                    figsize=figsize,
                    use_usetex=use_usetex,
                    primitives=primitives,
                )
                fig.savefig(abs_svg, format="svg", transparent=True)

                # Post-process: inject SVG radialGradient fills for any spheres
                _sphere_defs = getattr(fig, "_plot3d_sphere_defs", [])
                if _sphere_defs:
                    try:
                        with open(abs_svg, "r", encoding="utf-8") as _svgf:
                            _svg_raw = _svgf.read()
                        _svg_raw = _postprocess_spheres_svg(_svg_raw, _sphere_defs)
                        with open(abs_svg, "w", encoding="utf-8") as _svgf:
                            _svgf.write(_svg_raw)
                    except Exception:
                        pass  # fall back to flat fill silently

                if explicit_name:
                    try:
                        with open(abs_meta, "w", encoding="utf-8") as f:
                            f.write(str(content_hash))
                    except Exception:
                        pass
            except Exception as e:
                tb = ""
                try:
                    if os.environ.get("MUNCHBOKA_EDUTOOLS_PLOT_TRACEBACK"):
                        import traceback
                        tb = "\n\n" + traceback.format_exc()
                except Exception:
                    pass
                return [
                    self.state_machine.reporter.error(
                        f"plot3d: feil under generering av figur: {e}{tb}",
                        line=self.lineno,
                    )
                ]
            finally:
                if fig is not None:
                    try:
                        _plt.close(fig)
                    except Exception:
                        pass
                try:
                    if _old_usetex is not None:
                        matplotlib.rcParams["text.usetex"] = _old_usetex
                    if _old_mathtext is not None:
                        matplotlib.rcParams["mathtext.fontset"] = _old_mathtext
                except Exception:
                    pass

        if not os.path.exists(abs_svg):
            return [self.state_machine.reporter.error("plot3d: SVG mangler.", line=self.lineno)]

        env.note_dependency(abs_svg)
        try:
            out_static = os.path.join(app.outdir, "_static", "plot")
            os.makedirs(out_static, exist_ok=True)
            shutil.copy2(abs_svg, os.path.join(out_static, svg_name))
        except Exception:
            pass

        try:
            raw_svg = open(abs_svg, "r", encoding="utf-8").read()
        except Exception as e:
            return [
                self.state_machine.reporter.error(
                    f"plot3d: kunne ikke lese SVG: {e}", line=self.lineno
                )
            ]

        # Strip fixed width/height so CSS controls sizing
        def _strip_size(m):
            tag = m.group(0)
            tag = re.sub(r'\swidth="[^"]+"', "", tag)
            tag = re.sub(r'\sheight="[^"]+"', "", tag)
            return tag

        raw_svg = re.sub(r"<svg\b[^>]*>", _strip_size, raw_svg, count=1)

        # Inject CSS class + aria label + optional width
        alt = merged.get("alt", "3D-figur")
        width_opt = merged.get("width")

        def _augment(m):
            tag = m.group(0)
            if "class=" not in tag:
                tag = tag[:-1] + ' class="graph-inline-svg">'
            else:
                tag = tag.replace('class="', 'class="graph-inline-svg ')
            if alt and "aria-label=" not in tag:
                tag = tag[:-1] + f' role="img" aria-label="{alt}">'
            if width_opt:
                wval = width_opt.strip()
                if wval.isdigit():
                    wval += "px"
                style_frag = f"width:{wval}; height:auto; display:block; margin:0 auto;"
                if "style=" in tag:
                    tag = re.sub(
                        r'style="([^"]*)"',
                        lambda mm: f'style="{mm.group(1)}; {style_frag}"',
                        tag, count=1,
                    )
                else:
                    tag = tag[:-1] + f' style="{style_frag}">'
            return tag

        raw_svg = re.sub(r"<svg\b[^>]*>", _augment, raw_svg, count=1)

        # Stable ID prefix to avoid clashes between multiple figures on the same page
        id_prefix = f"p3d_{content_hash}_{uuid.uuid4().hex[:6]}_"
        ids_found = re.findall(r'\bid="([^"]+)"', raw_svg)
        skip_prefixes = ("DejaVu", "CM", "STIX", "Nimbus", "Arial", "Times", "Helvetica")
        id_map = {i: f"{id_prefix}{i}" for i in ids_found
                  if not i.startswith(skip_prefixes)}
        if id_map:
            def _repl_id(m):
                old = m.group(1)
                return f'id="{id_map.get(old, old)}"'
            raw_svg = re.sub(r'\bid="([^"]+)"', _repl_id, raw_svg)

            def _repl_url(m):
                old = m.group(1).strip()
                return f"url(#{id_map.get(old, old)})"
            raw_svg = re.sub(r"url\(#\s*([^\)\s]+)\s*\)", _repl_url, raw_svg)

            # Also fix xlink:href="#id" and href="#id" — used by matplotlib for
            # marker <use> elements.  Without this, marker symbols (circles,
            # triangles, etc.) are defined under a prefixed id but referenced by
            # the un-prefixed id, making all markers invisible.
            def _repl_href(m):
                old = m.group(2)
                new_id = id_map.get(old, old)
                return f'{m.group(1)}="#{new_id}"'
            raw_svg = re.sub(
                r'(xlink:href|href)="#([^"]+)"', _repl_href, raw_svg
            )

        figure = nodes.figure()
        figure.setdefault("classes", []).extend(
            ["adaptive-figure", "plot-figure", "no-click"]
        )
        raw_node = nodes.raw("", raw_svg, format="html")
        raw_node.setdefault("classes", []).extend(
            ["graph-image", "no-click", "no-scaled-link"]
        )
        figure += raw_node

        extra_classes = merged.get("class")
        if extra_classes:
            figure["classes"].extend(extra_classes)
        figure["align"] = merged.get("align", "center")

        # Caption
        caption_lines = list(self.content)[caption_idx:]
        while caption_lines and not caption_lines[0].strip():
            caption_lines.pop(0)
        if caption_lines:
            caption = nodes.caption()
            parsed_nodes, _ = self.state.inline_text(
                "\n".join(caption_lines), self.lineno
            )
            caption.extend(parsed_nodes)
            figure += caption

        if explicit_name:
            self.add_name(figure)

        return [figure]


# ---------------------------------------------------------------------------
# Sphinx setup
# ---------------------------------------------------------------------------

def setup(app):  # pragma: no cover
    app.add_directive("plot3d", Plot3dDirective)
    # Reuse the same usetex config value registered by plot.py (harmless duplicate)
    try:
        app.add_config_value("plot_default_usetex", True, "env")
    except Exception:
        pass
    return {"version": "0.1", "parallel_read_safe": True, "parallel_write_safe": True}
