"""Versioned, JSON-compatible scenes for the experimental live 3D renderer.

Expressions are a small arithmetic AST, never Python or JavaScript source to eval.
Scene data contains no renderer-specific objects. The legacy syntax helpers are
reused here while the static renderer is migrated incrementally.
"""

from __future__ import annotations

import ast
import math
import re
from typing import Any

from ._plot_common import parse_bool, parse_kv_block
from .plot3d_2 import _resolve_color, _split_top_level_commas, _strip_wrapping_quotes

FUNCTIONS = {
    name: getattr(math, name)
    for name in (
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
    )
}
FUNCTIONS["Abs"] = abs
CONSTANTS = {"pi": math.pi, "E": math.e}
PRIMITIVES = {
    "point",
    "line",
    "line-segment",
    "vector",
    "plane",
    "sphere",
    "circle",
    "angle",
    "right-angle",
    "text",
    "curve",
    "ngon",
    "normal-segment",
    "prism",
    "pyramid",
    "solid-of-revolution",
    "repeat",
}
MULTI_KEYS = PRIMITIVES | {"interactive-var", "let", "def"}
SCALARS = {
    "backend",
    "width",
    "height",
    "align",
    "class",
    "name",
    "alt",
    "caption",
    "nocache",
    "usetex",
    "figsize",
    "fontsize",
    "lw",
    "axis",
    "ticks",
    "grid",
    "elev",
    "azim",
    "zoom",
    "interactive-var-start",
    "interactive-max-frames",
    "interactive-workers",
    "parallel",
    "hidden-edges",
    "auto-intersections",
    "buttons",
} | {a + suffix for a in "xyz" for suffix in ("range", "step", "label", "ticks")}


class Expressions:
    def __init__(self, variables=()):
        self.variables = set(variables)
        self.bindings: dict[str, Any] = {}
        self.functions: dict[str, tuple[list[str], str]] = {}

    def compile(self, source: str, local=None, stack=()):
        try:
            root = ast.parse(str(source).strip(), mode="eval")
        except (SyntaxError, RecursionError) as exc:
            raise ValueError(f"Invalid expression: {source}") from exc
        if len(list(ast.walk(root))) > 256 or len(stack) > 16:
            raise ValueError("Expression is too complex")
        local = local or {}

        def visit(node):
            if isinstance(node, ast.Constant) and type(node.value) in (int, float):
                value = float(node.value)
                if not math.isfinite(value):
                    raise ValueError("Numbers must be finite")
                return value
            if isinstance(node, ast.Name):
                if node.id in local:
                    return local[node.id]
                if node.id in self.bindings:
                    return self.bindings[node.id]
                if node.id in CONSTANTS:
                    return CONSTANTS[node.id]
                if node.id in self.variables:
                    return ["var", node.id]
                raise ValueError(f"Unknown variable: {node.id}")
            binary = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/", ast.Pow: "**"}
            if isinstance(node, ast.BinOp) and type(node.op) in binary:
                return [binary[type(node.op)], visit(node.left), visit(node.right)]
            if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
                return (
                    visit(node.operand)
                    if isinstance(node.op, ast.UAdd)
                    else ["neg", visit(node.operand)]
                )
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and not node.keywords:
                name, args = node.func.id, [visit(arg) for arg in node.args]
                if name in FUNCTIONS and len(args) == 1:
                    return [name, *args]
                if name in self.functions and name not in stack:
                    params, body = self.functions[name]
                    if len(params) == len(args):
                        return self.compile(body, dict(zip(params, args)), (*stack, name))
            raise ValueError(f"Unsupported expression: {source}")

        return visit(root.body)

    def vector(self, source, count=3):
        text = str(source).strip()
        if text.startswith(("(", "[")) and text.endswith((")", "]")):
            text = text[1:-1]
        parts = _split_top_level_commas(text)
        if len(parts) != count:
            raise ValueError(f"Expected {count} coordinates: {source}")
        return [self.compile(p) for p in parts]


def evaluate(tree, variables=None):
    if isinstance(tree, (float, int)):
        return tree
    op, *args = tree
    if op == "var":
        return (variables or {})[args[0]]
    values = [evaluate(arg, variables) for arg in args]
    if op in FUNCTIONS:
        return FUNCTIONS[op](*values)
    if op == "neg":
        return -values[0]
    a, b = values
    return {
        "+": lambda: a + b,
        "-": lambda: a - b,
        "*": lambda: a * b,
        "/": lambda: a / b,
        "**": lambda: a**b,
    }[op]()


def plane_coefficients(source, expressions):
    """Extract a*x+b*y+c*z+d=0 using only previously validated syntax."""
    import sympy as sp

    compiler = Expressions(expressions.variables | set("xyz"))
    compiler.bindings = expressions.bindings
    compiler.functions = expressions.functions
    sides = source.split("=")
    if len(sides) != 2:
        raise ValueError("Plane equation must contain one equals sign")

    def symbolic(tree):
        if isinstance(tree, (float, int)):
            return sp.Float(tree)
        op, *args = tree
        if op == "var":
            return sp.Symbol(args[0])
        args = [symbolic(a) for a in args]
        if op == "neg":
            return -args[0]
        if op in FUNCTIONS:
            return getattr(sp, op)(*args)
        a, b = args
        return {
            "+": lambda: a + b,
            "-": lambda: a - b,
            "*": lambda: a * b,
            "/": lambda: a / b,
            "**": lambda: a**b,
        }[op]()

    x, y, z = sp.symbols("x y z")
    try:
        poly = sp.Poly(
            symbolic(compiler.compile(sides[0])) - symbolic(compiler.compile(sides[1])), x, y, z
        )
    except sp.PolynomialError as exc:
        raise ValueError("Plane equation must be linear in x, y, z") from exc
    if poly.total_degree() != 1:
        raise ValueError("Plane equation must be linear in x, y, z")
    return [expressions.compile(str(poly.coeff_monomial(m))) for m in (x, y, z, 1)]


def parse_primitive(kind, source, ex, defaults, depth=0):
    if depth > 8:
        raise ValueError("Repeats may nest at most eight levels")
    if kind == "repeat":
        match = re.fullmatch(
            r"([A-Za-z]\w*)\s*=\s*(.+?)\.\.(.+?);\s*([\w-]+):\s*(.+)", source.strip()
        )
        if not match:
            raise ValueError("Expected repeat: i=lo..hi; primitive: arguments")
        name, lo, hi, child_kind, body = match.groups()
        if child_kind not in PRIMITIVES:
            raise ValueError("repeat must contain a drawing primitive")
        child_ex = Expressions(ex.variables | {name})
        child_ex.bindings, child_ex.functions = dict(ex.bindings), dict(ex.functions)
        child_ex.bindings.pop(name, None)
        return dict(
            type="repeat",
            variable=name,
            lower=ex.compile(lo),
            upper=ex.compile(hi),
            child=parse_primitive(child_kind, body, child_ex, defaults, depth + 1),
        )
    parts = _split_top_level_commas(source)
    kw, pos = {}, []
    for part in parts:
        if "=" in part:
            k, v = part.split("=", 1)
            kw[k.strip()] = v.strip()
        else:
            pos.append(part)
    allowed = {"color", "lw", "style", "linestyle", "alpha", "hidden-edges"} | {
        "point": {"at"},
        "line": {"point", "direction", "through", "from", "to", "start", "end"},
        "line-segment": {"from", "to", "start", "end"},
        "vector": {"from", "to", "start", "end"},
        "sphere": {"center", "radius"},
        "circle": {"center", "radius", "plane", "equation", "normal", "point"},
        "plane": {"equation", "normal", "point", "span", "xrange", "yrange", "zrange"},
        "angle": {
            "at",
            "dir1",
            "dir2",
            "direction1",
            "direction2",
            "v1",
            "v2",
            "to1",
            "to2",
            "radius",
            "r",
        },
        "right-angle": {"at", "dir1", "dir2", "to1", "to2", "size"},
        "text": {"at", "offset", "value", "label", "fontsize", "ha", "va"},
        "curve": {"x", "y", "z", "t", "trange", "samples", "arrows", "arrow-count", "arrows-count"},
        "ngon": {"points", "vertices", "edgecolor"},
        "normal-segment": {
            "point",
            "p",
            "plane",
            "equation",
            "plane-normal",
            "normal",
            "plane-point",
            "plane_point",
            "on-plane",
            "on_plane",
            "point1",
            "p1",
            "point2",
            "p2",
            "direction1",
            "dir1",
            "v1",
            "direction2",
            "dir2",
            "v2",
            "right-angles",
            "right-angle-color",
            "right-angle-size",
            "size",
            "points",
            "endpoint-points",
            "endpoint-color",
            "point-color",
        },
        "prism": {"base", "center", "radius", "sides", "rotation", "vector", "height", "edgecolor"},
        "pyramid": {
            "base",
            "center",
            "radius",
            "sides",
            "rotation",
            "apex",
            "edgecolor",
            "base-color",
            "side-color",
            "body-color",
        },
        "solid-of-revolution": {"samples", "radial-samples"},
    }[kind]
    if set(kw) - allowed:
        raise ValueError(f"Unsupported options: {', '.join(sorted(set(kw) - allowed))}")
    from matplotlib.colors import to_hex

    color_index = {
        "point": 1,
        "vector": 2,
        "line-segment": 2,
        "ngon": 1,
        "solid-of-revolution": 2,
    }.get(kind)
    color = kw.get(
        "color", pos[color_index] if color_index is not None and len(pos) > color_index else None
    )
    item = {
        "type": kind,
        "color": to_hex(
            _resolve_color(color, "black" if kind in {"angle", "right-angle", "text"} else "blue")
        ),
        "lw": ex.compile(kw.get("lw", defaults.get("lw", "1.5"))),
        "alpha": ex.compile(
            kw.get("alpha", "0.45" if kind in {"ngon", "pyramid", "prism"} else "0.35")
        ),
        "style": kw.get("style", kw.get("linestyle", "dashed" if kind == "circle" else "solid")),
        "hiddenEdges": kw.get("hidden-edges", defaults.get("hidden-edges", "off")),
    }
    if item["hiddenEdges"] not in {"off", "dashed"}:
        raise ValueError("hidden-edges must be off or dashed")
    if item["style"] not in {"solid", "dashed", "dashdot", "dotted"}:
        raise ValueError(f"Invalid line style: {item['style']}")

    def vec(key, default=None):
        value = kw.get(key, default)
        if value is None:
            raise ValueError(f"{kind} requires {key}")
        return ex.vector(value)

    if kind == "point":
        item["coords"] = vec("at", pos[0] if pos else None)
    elif kind in {"vector", "line-segment", "line"}:
        if kind == "line" and "direction" in kw:
            item.update(start=vec("point"), direction=vec("direction"))
        else:
            if "through" in kw:
                pos = _split_top_level_commas(kw["through"].strip("[]"))
            item["start"] = vec("from", kw.get("start", pos[0] if pos else None))
            item["end"] = vec("to", kw.get("end", pos[1] if len(pos) > 1 else None))
    elif kind == "sphere":
        item.update(center=vec("center"), radius=ex.compile(kw.get("radius", "1")))
    elif kind == "circle":
        item.update(center=vec("center"), radius=ex.compile(kw.get("radius", "1")))
        if "plane" in kw or "equation" in kw:
            item["coefficients"] = plane_coefficients(kw.get("plane", kw.get("equation")), ex)
        else:
            item.update(normal=vec("normal"), planePoint=vec("point"))
    elif kind == "plane":
        if "equation" in kw:
            item["coefficients"] = plane_coefficients(kw["equation"], ex)
            item["ranges"] = [
                ex.vector(kw.get(a + "range", defaults.get(a + "range", "(-5,5)")), 2)
                for a in "xyz"
            ]
        else:
            item.update(normal=vec("normal"), point=vec("point"))
            span = kw.get("span", "(4,4)")
            if "," not in span:
                span = f"({span},{span})"
            item["span"] = ex.vector(span, 2)
    elif kind in {"angle", "right-angle"}:
        item["at"] = vec("at", "(0,0,0)" if kind == "angle" else None)
        for i in (1, 2):
            key = f"dir{i}"
            if f"to{i}" in kw:
                item[f"to{i}"] = vec(f"to{i}")
            else:
                item[key] = vec(key, kw.get(f"direction{i}", kw.get(f"v{i}")))
        item["radius"] = ex.compile(
            kw.get("size" if kind == "right-angle" else "radius", kw.get("r", "0.35"))
        )
    elif kind == "text":
        item.update(
            at=vec("at"),
            offset=vec("offset", "(0,0,0)"),
            text=_strip_wrapping_quotes(kw.get("value", kw.get("label", ""))),
            fontsize=ex.compile(kw.get("fontsize", defaults.get("fontsize", "12"))),
            ha=kw.get("ha", "center"),
            va=kw.get("va", "center"),
        )
    elif kind == "curve":
        curve_ex = Expressions(ex.variables | {"t"})
        curve_ex.bindings, curve_ex.functions = ex.bindings, ex.functions
        item["coordinates"] = [curve_ex.compile(kw[a]) for a in "xyz"]
        item["range"] = ex.vector(kw.get("t", kw.get("trange", "(0,1)")), 2)
        item["samples"] = min(2000, max(2, int(kw.get("samples", "300"))))
        item["arrows"] = bool(parse_bool(kw.get("arrows", "true")))
        item["arrowCount"] = max(
            0, min(20, int(kw.get("arrow-count", kw.get("arrows-count", "3"))))
        )
    elif kind == "ngon":
        raw = kw.get("points", kw.get("vertices", pos[0] if pos else ""))
        item["points"] = [ex.vector(p) for p in _split_top_level_commas(raw.strip("[]"))]
        if len(item["points"]) < 3:
            raise ValueError("ngon needs at least three vertices")
        item["edgecolor"] = to_hex(_resolve_color(kw.get("edgecolor"), "black"))
    elif kind in {"prism", "pyramid"}:
        if "base" in kw:
            item["base"] = [ex.vector(p) for p in _split_top_level_commas(kw["base"].strip("[]"))]
            if len(item["base"]) < 3:
                raise ValueError("The base needs at least three vertices")
        else:
            item.update(
                center=vec("center"),
                radius=ex.compile(kw["radius"]),
                sides=ex.compile(kw["sides"]),
                rotation=ex.compile(kw.get("rotation", "0")),
            )
        item["edgecolor"] = to_hex(_resolve_color(kw.get("edgecolor"), "black"))
        if kind == "prism":
            item["extrusion"] = (
                vec("vector") if "vector" in kw else [0.0, 0.0, ex.compile(kw["height"])]
            )
        else:
            item["apex"] = vec("apex")
            for name in ("base", "side"):
                raw = kw.get(
                    "color",
                    kw.get(name + "-color", kw.get("body-color") if name == "side" else None),
                )
                item[name + "Color"] = (
                    None if str(raw).lower() == "none" else to_hex(_resolve_color(raw, "blue"))
                )
    elif kind == "solid-of-revolution":
        if len(pos) < 2:
            raise ValueError("Expected f(x), (xmin, xmax), color")
        function_ex = Expressions(ex.variables | {"x"})
        function_ex.bindings, function_ex.functions = ex.bindings, ex.functions
        item.update(
            expression=function_ex.compile(pos[0]),
            range=ex.vector(pos[1], 2),
            samples=max(2, min(160, int(kw.get("samples", "40")))),
            radialSamples=max(8, min(96, int(kw.get("radial-samples", "32")))),
        )
    elif kind == "normal-segment":
        for i in (1, 2):
            if f"point{i}" in kw or f"p{i}" in kw:
                item[f"point{i}"] = vec(f"point{i}", kw.get(f"p{i}"))
                item[f"direction{i}"] = vec(f"direction{i}", kw.get(f"dir{i}", kw.get(f"v{i}")))
        if "point1" in item:
            if "point2" not in item:
                raise ValueError("Both lines are required")
        else:
            item["point"] = vec("point", kw.get("p"))
            if "plane" in kw or "equation" in kw:
                item["coefficients"] = plane_coefficients(kw.get("plane", kw.get("equation")), ex)
            else:
                item["normal"] = vec("plane-normal", kw.get("normal"))
                item["planePoint"] = vec(
                    "plane-point", kw.get("plane_point", kw.get("on-plane", kw.get("on_plane")))
                )
        item.update(
            rightAngles=bool(parse_bool(kw.get("right-angles", "true"))),
            endpointPoints=bool(parse_bool(kw.get("points", kw.get("endpoint-points", "true")))),
            markerSize=ex.compile(kw.get("right-angle-size", kw.get("size", "0.35"))),
            markerColor=to_hex(_resolve_color(kw.get("right-angle-color"), "black")),
            endpointColor=to_hex(
                _resolve_color(kw.get("endpoint-color", kw.get("point-color")), "black")
            ),
        )
    return item


def build_scene(lines, options=None):
    from ._scene3d_macros import expand_macros

    original_length = len(lines)
    lines, locations = expand_macros(lines)
    scalars, lists, caption_idx = parse_kv_block(lines, MULTI_KEYS)
    settings = {**scalars, **(options or {})}
    unknown = set(settings) - SCALARS - {"interactive-var"}
    if unknown:
        raise ValueError(
            f"Not supported by the live renderer: {', '.join(sorted(unknown))}. Use backend: frames for legacy features."
        )
    ex = Expressions()
    sliders = []
    starts = str(settings.get("interactive-var-start", ""))
    start_map = dict(p.split("=", 1) for p in _split_top_level_commas(starts) if "=" in p)
    specs = lists["interactive-var"] or (
        [settings["interactive-var"]] if settings.get("interactive-var") else []
    )
    for spec in specs:
        parts = _split_top_level_commas(spec)
        if len(parts) != 4:
            raise ValueError("interactive-var requires name, min, max, frames")
        name, lo, hi, count = parts
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", name) or name in ex.variables | set(
            CONSTANTS
        ) | set(FUNCTIONS) | {"x", "y", "z", "constructor", "prototype"}:
            raise ValueError(f"Invalid, duplicate, or reserved slider name: {name}")
        low, high = (float(evaluate(Expressions().compile(v))) for v in (lo, hi))
        count = int(count)
        if not all(map(math.isfinite, (low, high))) or low >= high or not 2 <= count <= 10000:
            raise ValueError("Slider requires finite min < max and 2–10000 steps")
        step = (high - low) / (count - 1)
        requested = start_map.get(
            name, starts if len(specs) == 1 and "=" not in starts else ""
        ).strip()
        initial = count // 2
        if requested:
            target = evaluate(Expressions().compile(requested))
            initial = min(range(count), key=lambda i: abs(low + i * step - target))
        sliders.append(dict(name=name, min=low, max=high, count=count, initial=initial))
        ex.variables.add(name)
    # Preserve declaration order for let/def, including dependencies between bindings.
    for line in lines[:caption_idx]:
        match = re.match(r"\s*(let|def):\s*(.*?)\s*=\s*(.*)", line)
        if not match:
            continue
        kind, lhs, rhs = match.groups()
        if kind == "let":
            if not re.fullmatch(r"[A-Za-z]\w*", lhs) or lhs in ex.variables | set(CONSTANTS) | set(
                FUNCTIONS
            ):
                raise ValueError(f"Invalid or reserved binding: {lhs}")
            ex.bindings[lhs] = ex.compile(rhs)
        else:
            signature = re.fullmatch(r"([A-Za-z]\w*)\((.*?)\)", lhs)
            if not signature:
                raise ValueError(f"Invalid function definition: {lhs}")
            name, params = signature.groups()
            params = [p.strip() for p in params.split(",")]
            if (
                name in FUNCTIONS
                or not all(re.fullmatch(r"[A-Za-z]\w*", p) for p in params)
                or len(set(params)) != len(params)
            ):
                raise ValueError(f"Invalid function definition: {lhs}")
            ex.compile(rhs, {p: 0.0 for p in params})
            ex.functions[name] = (params, rhs)
    ranges = [ex.vector(settings.get(a + "range", "(-5,5)"), 2) for a in "xyz"]
    # Bounding boxes and tick topology are fixed in this first backend version.
    numeric_ranges = [[evaluate(v) for v in r] for r in ranges]
    if any(not all(map(math.isfinite, r)) or r[0] >= r[1] for r in numeric_ranges):
        raise ValueError("Axis ranges must be finite and increasing")
    steps = [evaluate(ex.compile(settings.get(a + "step", "1"))) for a in "xyz"]
    if any(
        not math.isfinite(s) or s <= 0 or (r[1] - r[0]) / s > 200
        for r, s in zip(numeric_ranges, steps)
    ):
        raise ValueError("Tick spacing must be positive, with at most 200 intervals per axis")
    scene = dict(
        version=1,
        sliders=sliders,
        ranges=numeric_ranges,
        steps=steps,
        axis=parse_bool(settings.get("axis", "true")),
        grid=parse_bool(settings.get("grid", "false")),
        autoIntersections=parse_bool(settings.get("auto-intersections", "false")),
        buttons=parse_bool(settings.get("buttons", "false")),
        ticks=[parse_bool(settings.get(a + "ticks", settings.get("ticks", "true"))) for a in "xyz"],
        labels=[str(settings.get(a + "label", f"${a}$")) for a in "xyz"],
        camera={
            k: ex.compile(settings.get(k, d))
            for k, d in (("elev", "22"), ("azim", "-55"), ("zoom", "1.28"))
        },
        fontsize=evaluate(ex.compile(settings.get("fontsize", "12"))),
        primitives=[],
    )
    for kind in sorted(PRIMITIVES):
        for raw in lists[kind]:
            try:
                scene["primitives"].append(parse_primitive(kind, raw, ex, settings))
            except (ValueError, KeyError, IndexError) as exc:
                raise ValueError(f"{kind}: {exc}") from exc
    if len(scene["primitives"]) > 1000:
        raise ValueError("A scene may contain at most 1000 primitives")
    original_caption_idx = (
        locations[caption_idx] if caption_idx < len(locations) else original_length
    )
    return scene, settings, original_caption_idx
