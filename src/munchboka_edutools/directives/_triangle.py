from __future__ import annotations

import ast
import math
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Tuple


@dataclass(frozen=True)
class TrianglePrimitive:
    raw_spec: str
    vertices: Dict[str, Tuple[float, float]]
    side_lengths: Dict[str, float]
    side_exprs: Dict[str, Any | None]
    side_label_modes: Dict[str, str]
    angle_label_modes: Dict[str, str]
    angle_exprs: Dict[str, Any | None]
    angle_vertices: Tuple[str, ...]
    right_angle_mode: str
    edge_style: str | None
    edge_color: str | None
    angle_color: str | None
    label_color: str | None
    line_width: float | None
    angle_radius_px: float
    label_offset_px: float
    side_format: str
    side_format_explicit: bool
    side_text: Dict[str, str]
    corner_labels: Dict[str, str]
    angle_text: Dict[str, str]
    corner_label_offset_px: float
    angle_text_offset_px: float


def _split_top_level_commas(text: str) -> List[str]:
    if not text.strip():
        return []
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
        elif ch == "," and depth == 0:
            token = "".join(cur).strip()
            if token:
                out.append(token)
            cur = []
        else:
            cur.append(ch)
    tail = "".join(cur).strip()
    if tail:
        out.append(tail)
    return out


def _strip_container(text: str) -> str:
    s = text.strip()
    if len(s) >= 2 and ((s[0] == "(" and s[-1] == ")") or (s[0] == "[" and s[-1] == "]")):
        return s[1:-1].strip()
    return s


def _parse_named_options(raw: str) -> Dict[str, str]:
    options: Dict[str, str] = {}
    for token in _split_top_level_commas(raw):
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        key = key.strip().lower()
        value = value.strip()
        if key:
            options[key] = value
    return options


def _parse_point_tokens(points_value: str) -> List[Tuple[str, str]]:
    seq = _strip_container(points_value)
    pairs: List[Tuple[str, str]] = []
    i = 0
    n = len(seq)
    while i < n:
        if seq[i] == "(":
            depth = 0
            j = i
            while j < n:
                ch = seq[j]
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0:
                        inner = seq[i + 1 : j].strip()
                        parts = _split_top_level_commas(inner)
                        if len(parts) == 2:
                            pairs.append((parts[0], parts[1]))
                        i = j
                        break
                j += 1
        i += 1
    return pairs


def _parse_expr_triplet(value: str) -> List[str]:
    parts = _split_top_level_commas(_strip_container(value))
    if len(parts) != 3:
        raise ValueError("Expected three values")
    return parts


def _parse_origin(value: str, eval_num: Callable[[str], float]) -> Tuple[float, float]:
    pts = _parse_point_tokens(value)
    if pts:
        return (float(eval_num(pts[0][0])), float(eval_num(pts[0][1])))
    parts = _split_top_level_commas(_strip_container(value))
    if len(parts) == 2:
        return (float(eval_num(parts[0])), float(eval_num(parts[1])))
    return (0.0, 0.0)


def _parse_vertex_selection(value: str) -> Tuple[str, ...]:
    raw = value.strip()
    low = raw.lower()
    if low == "none":
        return ()
    if low == "all":
        return ("A", "B", "C")
    return tuple(
        part
        for part in (
            piece.strip().upper() for piece in _split_top_level_commas(_strip_container(raw))
        )
        if part in {"A", "B", "C"}
    )


def _parse_mirror(value: str) -> float:
    low = value.strip().lower()
    if low in {"down", "below", "-1"}:
        return -1.0
    return 1.0


def _parse_label_map(value: str, allowed_keys: set[str]) -> Dict[str, str]:
    if value.strip().lower() == "none":
        return {}
    out: Dict[str, str] = {}
    for token in _split_top_level_commas(_strip_container(value)):
        sep_index = -1
        for sep in ("=", ":"):
            idx = token.find(sep)
            if idx != -1 and (sep_index == -1 or idx < sep_index):
                sep_index = idx
        if sep_index == -1:
            continue
        key, raw_label = token[:sep_index], token[sep_index + 1 :]
        key = key.strip().upper()
        if key not in allowed_keys:
            continue
        label = raw_label.strip()
        if not label:
            continue
        try:
            parsed = ast.literal_eval(label)
            label = str(parsed)
        except Exception:
            if len(label) >= 2 and (
                (label.startswith('"') and label.endswith('"'))
                or (label.startswith("'") and label.endswith("'"))
            ):
                label = label[1:-1]
        out[key] = label
    return out


def _parse_label_modes(
    value: str | None,
    allowed_keys: Tuple[str, ...],
    default_mode: str = "none",
) -> Dict[str, str]:
    allowed_modes = {"none", "exact", "numeric"}
    if value is None:
        return {key: default_mode for key in allowed_keys}

    raw = value.strip()
    if not raw:
        return {key: default_mode for key in allowed_keys}

    low = raw.lower()
    if low in allowed_modes:
        return {key: low for key in allowed_keys}

    inner = _strip_container(raw)
    modes = {key: "none" for key in allowed_keys}
    for token in _split_top_level_commas(inner):
        sep_index = token.find("=")
        if sep_index == -1:
            sep_index = token.find(":")
        if sep_index == -1:
            continue
        key = token[:sep_index].strip().upper()
        mode = token[sep_index + 1 :].strip().lower()
        if key in modes and mode in allowed_modes:
            modes[key] = mode
    return modes


def _sympy_expr(sympy_mod, expr: str, sympy_locals: Dict[str, Any]) -> Any | None:
    try:
        return sympy_mod.sympify(expr, locals=sympy_locals)
    except Exception:
        return None


def _rotate_point(x: float, y: float, angle_deg: float) -> Tuple[float, float]:
    theta = math.radians(angle_deg)
    ct = math.cos(theta)
    st = math.sin(theta)
    return (ct * x - st * y, st * x + ct * y)


def _apply_transform(
    vertices: Dict[str, Tuple[float, float]],
    rotate_deg: float,
    origin: Tuple[float, float],
) -> Dict[str, Tuple[float, float]]:
    ox, oy = origin
    out: Dict[str, Tuple[float, float]] = {}
    for name, (x, y) in vertices.items():
        xr, yr = _rotate_point(x, y, rotate_deg)
        out[name] = (xr + ox, yr + oy)
    return out


def _distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def _angle_deg_from_sides(a: float, b: float, opp: float) -> float:
    denom = 2.0 * a * b
    if denom <= 0:
        raise ValueError("Invalid side length")
    cos_val = (a * a + b * b - opp * opp) / denom
    cos_val = max(-1.0, min(1.0, cos_val))
    return math.degrees(math.acos(cos_val))


def triangle_angles_deg(triangle: TrianglePrimitive) -> Dict[str, float]:
    ab = triangle.side_lengths["AB"]
    bc = triangle.side_lengths["BC"]
    ca = triangle.side_lengths["CA"]
    return {
        "A": _angle_deg_from_sides(ab, ca, bc),
        "B": _angle_deg_from_sides(ab, bc, ca),
        "C": _angle_deg_from_sides(bc, ca, ab),
    }


def _triangle_angle_exprs(sympy_mod, side_exprs: Dict[str, Any | None]) -> Dict[str, Any | None]:
    ab = side_exprs.get("AB")
    bc = side_exprs.get("BC")
    ca = side_exprs.get("CA")
    if ab is None or bc is None or ca is None:
        return {"A": None, "B": None, "C": None}

    def _expr(adj1, adj2, opp):
        return sympy_mod.simplify(
            180
            * sympy_mod.acos(sympy_mod.simplify((adj1**2 + adj2**2 - opp**2) / (2 * adj1 * adj2)))
            / sympy_mod.pi
        )

    return {
        "A": _expr(ab, ca, bc),
        "B": _expr(ab, bc, ca),
        "C": _expr(bc, ca, ab),
    }


def _triangle_side_exprs_from_points(
    sympy_mod,
    point_tokens: List[Tuple[str, str]],
    sympy_locals: Dict[str, Any],
) -> Dict[str, Any | None]:
    points: Dict[str, Tuple[Any, Any]] = {}
    for name, (x_raw, y_raw) in zip(("A", "B", "C"), point_tokens):
        x_expr = _sympy_expr(sympy_mod, x_raw, sympy_locals)
        y_expr = _sympy_expr(sympy_mod, y_raw, sympy_locals)
        if x_expr is None or y_expr is None:
            return {"AB": None, "BC": None, "CA": None}
        points[name] = (x_expr, y_expr)
    out: Dict[str, Any | None] = {}
    for p_name, q_name, side_name in (("A", "B", "AB"), ("B", "C", "BC"), ("C", "A", "CA")):
        px, py = points[p_name]
        qx, qy = points[q_name]
        out[side_name] = sympy_mod.simplify(sympy_mod.sqrt((qx - px) ** 2 + (qy - py) ** 2))
    return out


def _base_options(options: Dict[str, str], eval_num: Callable[[str], float]) -> Dict[str, Any]:
    default_corner_labels = {"A": "$A$", "B": "$B$", "C": "$C$"}
    raw_corner_labels = options.get("corner-labels", options.get("point-labels"))
    if raw_corner_labels is None:
        corner_labels = default_corner_labels
    else:
        parsed_corner_labels = _parse_label_map(raw_corner_labels, {"A", "B", "C"})
        if raw_corner_labels.strip().lower() == "none":
            corner_labels = {}
        else:
            corner_labels = {**default_corner_labels, **parsed_corner_labels}
    angle_text = _parse_label_map(options.get("angle-text", ""), {"A", "B", "C"})
    side_text = _parse_label_map(options.get("side-text", ""), {"AB", "BC", "CA"})
    return {
        "side_label_modes": _parse_label_modes(
            options.get("side-labels"),
            ("AB", "BC", "CA"),
            default_mode="none",
        ),
        "angle_label_modes": _parse_label_modes(
            options.get("angle-labels"),
            ("A", "B", "C"),
            default_mode="none",
        ),
        "angle_vertices": _parse_vertex_selection(options.get("angles", "all")),
        "right_angle_mode": options.get("right-angle", "auto").strip().lower(),
        "edge_style": options.get("linestyle", options.get("style")),
        "edge_color": options.get("color"),
        "angle_color": options.get("angle-color"),
        "label_color": options.get("label-color"),
        "line_width": float(eval_num(options["lw"])) if "lw" in options else None,
        "angle_radius_px": float(eval_num(options.get("angle-radius", "25"))),
        "label_offset_px": float(
            eval_num(options.get("side-offset", options.get("label-offset", "12")))
        ),
        "side_format": options.get("side-format", "g").strip() or "g",
        "side_format_explicit": "side-format" in options,
        "side_text": side_text,
        "corner_labels": corner_labels,
        "angle_text": angle_text,
        "corner_label_offset_px": float(
            eval_num(options.get("corner-offset", options.get("corner-label-offset", "12")))
        ),
        "angle_text_offset_px": float(
            eval_num(options.get("angle-offset", options.get("angle-text-offset", "18")))
        ),
    }


def _build_points_triangle(
    raw: str,
    options: Dict[str, str],
    eval_num: Callable[[str], float],
    sympy_mod,
    sympy_locals: Dict[str, Any],
) -> TrianglePrimitive:
    point_tokens = _parse_point_tokens(options["points"])
    if len(point_tokens) != 3:
        raise ValueError("points requires exactly three coordinate pairs")
    vertices = {
        name: (float(eval_num(x_raw)), float(eval_num(y_raw)))
        for name, (x_raw, y_raw) in zip(("A", "B", "C"), point_tokens)
    }
    ax, ay = vertices["A"]
    bx, by = vertices["B"]
    cx, cy = vertices["C"]
    area2 = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
    if abs(area2) <= 1e-9:
        raise ValueError("Triangle points must be non-collinear")
    side_lengths = {
        "AB": _distance(vertices["A"], vertices["B"]),
        "BC": _distance(vertices["B"], vertices["C"]),
        "CA": _distance(vertices["C"], vertices["A"]),
    }
    return TrianglePrimitive(
        raw_spec=raw,
        vertices=vertices,
        side_lengths=side_lengths,
        side_exprs=_triangle_side_exprs_from_points(sympy_mod, point_tokens, sympy_locals),
        angle_exprs=_triangle_angle_exprs(
            sympy_mod,
            _triangle_side_exprs_from_points(sympy_mod, point_tokens, sympy_locals),
        ),
        **_base_options(options, eval_num),
    )


def _build_sss_triangle(
    raw: str,
    options: Dict[str, str],
    eval_num: Callable[[str], float],
    sympy_mod,
    sympy_locals: Dict[str, Any],
) -> TrianglePrimitive:
    ab_raw, bc_raw, ca_raw = _parse_expr_triplet(options["sss"])
    ab = float(eval_num(ab_raw))
    bc = float(eval_num(bc_raw))
    ca = float(eval_num(ca_raw))
    if min(ab, bc, ca) <= 0:
        raise ValueError("Triangle side lengths must be positive")
    if ab + bc <= ca or ab + ca <= bc or bc + ca <= ab:
        raise ValueError("Triangle inequality violated")
    x_c = (ab * ab + ca * ca - bc * bc) / (2.0 * ab)
    y_sq = max(0.0, ca * ca - x_c * x_c)
    y_c = _parse_mirror(options.get("mirror", "up")) * math.sqrt(y_sq)
    vertices = _apply_transform(
        {"A": (0.0, 0.0), "B": (ab, 0.0), "C": (x_c, y_c)},
        rotate_deg=float(eval_num(options.get("rotate", "0"))),
        origin=_parse_origin(options.get("origin", "(0,0)"), eval_num),
    )
    return TrianglePrimitive(
        raw_spec=raw,
        vertices=vertices,
        side_lengths={"AB": ab, "BC": bc, "CA": ca},
        side_exprs={
            "AB": _sympy_expr(sympy_mod, ab_raw, sympy_locals),
            "BC": _sympy_expr(sympy_mod, bc_raw, sympy_locals),
            "CA": _sympy_expr(sympy_mod, ca_raw, sympy_locals),
        },
        angle_exprs=_triangle_angle_exprs(
            sympy_mod,
            {
                "AB": _sympy_expr(sympy_mod, ab_raw, sympy_locals),
                "BC": _sympy_expr(sympy_mod, bc_raw, sympy_locals),
                "CA": _sympy_expr(sympy_mod, ca_raw, sympy_locals),
            },
        ),
        **_base_options(options, eval_num),
    )


def _build_svs_triangle(
    raw: str,
    options: Dict[str, str],
    eval_num: Callable[[str], float],
    sympy_mod,
    sympy_locals: Dict[str, Any],
) -> TrianglePrimitive:
    side1_raw, angle_raw, side2_raw = _parse_expr_triplet(options["svs"])
    side1 = float(eval_num(side1_raw))
    angle_deg = float(eval_num(angle_raw))
    side2 = float(eval_num(side2_raw))
    if side1 <= 0 or side2 <= 0:
        raise ValueError("SVS side lengths must be positive")
    if not (0.0 < angle_deg < 180.0):
        raise ValueError("SVS angle must lie strictly between 0 and 180 degrees")
    angle_rad = math.radians(angle_deg)
    mirror = _parse_mirror(options.get("mirror", "up"))
    at = options.get("at", "A").strip().upper()
    if at == "A":
        base_vertices = {
            "A": (0.0, 0.0),
            "B": (side1, 0.0),
            "C": (side2 * math.cos(angle_rad), mirror * side2 * math.sin(angle_rad)),
        }
        side_exprs = {
            "AB": _sympy_expr(sympy_mod, side1_raw, sympy_locals),
            "BC": None,
            "CA": _sympy_expr(sympy_mod, side2_raw, sympy_locals),
        }
    elif at == "B":
        base_vertices = {
            "A": (side1, 0.0),
            "B": (0.0, 0.0),
            "C": (side2 * math.cos(angle_rad), mirror * side2 * math.sin(angle_rad)),
        }
        side_exprs = {
            "AB": _sympy_expr(sympy_mod, side1_raw, sympy_locals),
            "BC": _sympy_expr(sympy_mod, side2_raw, sympy_locals),
            "CA": None,
        }
    elif at == "C":
        base_vertices = {
            "A": (side1, 0.0),
            "B": (side2 * math.cos(angle_rad), mirror * side2 * math.sin(angle_rad)),
            "C": (0.0, 0.0),
        }
        side_exprs = {
            "AB": None,
            "BC": _sympy_expr(sympy_mod, side2_raw, sympy_locals),
            "CA": _sympy_expr(sympy_mod, side1_raw, sympy_locals),
        }
    else:
        raise ValueError("SVS option 'at' must be A, B, or C")
    vertices = _apply_transform(
        base_vertices,
        rotate_deg=float(eval_num(options.get("rotate", "0"))),
        origin=_parse_origin(options.get("origin", "(0,0)"), eval_num),
    )
    side_lengths = {
        "AB": _distance(vertices["A"], vertices["B"]),
        "BC": _distance(vertices["B"], vertices["C"]),
        "CA": _distance(vertices["C"], vertices["A"]),
    }
    theta_expr = _sympy_expr(sympy_mod, angle_raw, sympy_locals)
    side1_expr = _sympy_expr(sympy_mod, side1_raw, sympy_locals)
    side2_expr = _sympy_expr(sympy_mod, side2_raw, sympy_locals)
    if theta_expr is not None and side1_expr is not None and side2_expr is not None:
        derived = sympy_mod.simplify(
            sympy_mod.sqrt(
                side1_expr**2
                + side2_expr**2
                - 2 * side1_expr * side2_expr * sympy_mod.cos(sympy_mod.pi * theta_expr / 180)
            )
        )
        for side_name, expr in list(side_exprs.items()):
            if expr is None:
                side_exprs[side_name] = derived
                break
    angle_exprs = _triangle_angle_exprs(sympy_mod, side_exprs)
    if theta_expr is not None:
        angle_exprs[at] = sympy_mod.simplify(theta_expr)
    return TrianglePrimitive(
        raw_spec=raw,
        vertices=vertices,
        side_lengths=side_lengths,
        side_exprs=side_exprs,
        angle_exprs=angle_exprs,
        **_base_options(options, eval_num),
    )


def parse_triangle_primitive(
    raw: str,
    eval_num: Callable[[str], float],
    sympy_locals: Dict[str, Any],
) -> TrianglePrimitive | None:
    import sympy

    options = _parse_named_options(raw)
    geometry_keys = [key for key in ("points", "sss", "svs") if key in options]
    if len(geometry_keys) != 1:
        return None
    try:
        if geometry_keys[0] == "points":
            tri = _build_points_triangle(raw, options, eval_num, sympy, sympy_locals)
        elif geometry_keys[0] == "sss":
            tri = _build_sss_triangle(raw, options, eval_num, sympy, sympy_locals)
        else:
            tri = _build_svs_triangle(raw, options, eval_num, sympy, sympy_locals)
        _ = triangle_angles_deg(tri)
        return tri
    except Exception:
        return None


def triangle_side_label_text(triangle: TrianglePrimitive, side_name: str) -> str | None:
    import sympy

    override = triangle.side_text.get(side_name)
    if override:
        return override

    mode = triangle.side_label_modes.get(side_name, "none")
    if mode == "none":
        return None
    if mode == "exact":
        expr = triangle.side_exprs.get(side_name)
        if expr is not None:
            try:
                return f"${sympy.latex(sympy.simplify(expr))}$"
            except Exception:
                pass
    value = triangle.side_lengths.get(side_name)
    if value is None:
        return None
    if not triangle.side_format_explicit:
        return f"{value:.2f}".rstrip("0").rstrip(".")
    try:
        return format(value, triangle.side_format)
    except Exception:
        return f"{value:g}"


def triangle_corner_label_text(triangle: TrianglePrimitive, vertex_name: str) -> str | None:
    return triangle.corner_labels.get(vertex_name)


def triangle_angle_label_text(triangle: TrianglePrimitive, vertex_name: str) -> str | None:
    import sympy

    override = triangle.angle_text.get(vertex_name)
    if override:
        return override

    mode = triangle.angle_label_modes.get(vertex_name, "none")
    if mode == "none":
        return None
    if mode == "exact":
        expr = triangle.angle_exprs.get(vertex_name)
        if expr is not None:
            try:
                return f"${sympy.latex(sympy.simplify(expr))}^\\circ$"
            except Exception:
                pass
    angle_val = triangle_angles_deg(triangle).get(vertex_name)
    if angle_val is None:
        return None
    rounded = f"{angle_val:.2f}".rstrip("0").rstrip(".")
    return f"${rounded}^\\circ$"
