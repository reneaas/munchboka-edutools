"""multi-plot directive
=================================

Create a responsive grid (rows × cols) of mathematical function plots using
``plotmath.multiplot`` and a collection of numpy / matplotlib transformations.
The directive focuses on pedagogical clarity, robust domain / exclusion handling,
and clean SVG output (sanitized IDs, no fixed width/height, optional width styling).

Quick Example (MyST)
--------------------
:::{multi-plot}
functions: [x**2 - 2*x, -x + 2, x - 3]
rows: 1
cols: 3
width: 100%
alt: Tre grafer som sammenligner funksjoner
:::

Minimal Example
---------------
:::{multi-plot}
functions: [x**2, sin(x), exp(x)]
:::

Front‑Matter vs Inline Options
------------------------------
You can either:

1. Supply key/value pairs directly at the top (each ``key: value`` line) until a
     blank or non-matching line is encountered.
2. Use a fenced *YAML-like* block delimited by ``---`` lines, then an empty line,
     followed by an optional caption.

Example with front‑matter + caption:
:::{multi-plot}
---
functions: [x**2, -x, x**3]
rows: 1
cols: 3
width: 80%
alt: Tre forskjellige funksjoner
---
Sammenligning av tre funksjoner.
:::

Caching & Regeneration
----------------------
All parameters (functions, domains, lines, style flags, etc.) are hashed to form
an SVG cache filename under ``_static/multi_plot``. Use ``:nocache:`` (or
``nocache:`` in front‑matter) to force regeneration. The hash includes axis
limits, domain exclusions, per-axis lines, and labeling flags to minimize stale
outputs.

Safety & ID Rewriting
---------------------
All non-font glyph IDs within the generated SVG are rewritten with a unique
prefix to avoid collisions when embedding multiple multi-plot figures on the
same page. URL and href references (including gradients, clips, etc.) are
updated accordingly.

Accessibility
-------------
The root ``<svg>`` receives ``role="img"`` and ``aria-label="..."`` (from the
``alt`` option or a generated default) instead of a ``<title>`` tag to avert
hover tooltips while retaining screen reader context.

Width & Layout
--------------
``width`` may be a percentage (e.g. ``60%``, ``100%``) or an absolute size
(``400`` or ``400px``). Percent widths get ``display:block; margin:0 auto;`` for
centering. If you need left/right alignment, supply ``align: left`` or
``align: right`` (the directive's figure container alignment plus CSS handles the rest).

Function Expressions
--------------------
Provide a comma-separated or bracketed list (``[ ... ]``). Each expression is
sympified via SymPy, then vectorized with ``lambdify``. Example accepted forms:
* ``x**2 - 2*x``
* ``sin(x)``
* ``exp(x)``

Labels
------
Use either ``fn_labels`` or its alias ``function-names``. If the number of
labels matches the number of functions, they are shown (LaTeX math wrapped in
``$...$``). Otherwise, labels are auto-inferred / hidden depending on plotmath
defaults. Example:
``fn_labels: [f(x)=x^2, g(x)=-x, h(x)=x^3]``

Per-Function Domains & Exclusions
---------------------------------
``domains`` accepts top-level comma-separated domain specs with optional
exclusion points using a set difference notation ``(a,b) \ {x1, x2, ...}``.
Example:
``domains: [( -5,5 ) \ {0}, ( -2,2 ), (0, 6) \ {1,2}]``

Excluded x-values are widened internally (with a small numeric halo + neighbor
NaNs) to create visible breaks instead of spuriously connecting across
discontinuities.

Vertical & Horizontal Lines
---------------------------
``vlines`` / ``hlines`` accept lists of x or y locations per function panel. Each
panel’s list is expressed as a top-level comma-separated group. Example:
``vlines: [[-2,0,2], None, [1]]`` or ``vlines: [-2; None; 1]`` (semicolons treated as commas).

Axis-Specific Limits
--------------------
``xlims`` / ``ylims`` allow per-plot overrides: ``xlims: [(-3,3), None, (-1,5)]``.
Where omitted or ``None``, the global ``xmin/xmax`` or ``ymin/ymax`` apply.

Reference Line (y = a*x + b)
----------------------------
``lines`` takes per-axis slope/intercept specs. Each element may be a two-element
sequence ``[a, b]`` or ``(a, b)``, or an extended form ``[a, (x0,y0)]`` from which
``b`` is derived as ``y0 - a*x0``.

Alpha / Line Width / Font Size
------------------------------
* ``alpha`` – global transparency for function curves.
* ``lw`` – line width (float-like).
* ``fontsize`` – base font size applied to axes labels, tick labels, and legends.

Ticks & Grid
------------
* ``ticks`` – truthy/falsey values (``true``, ``false``, ``on``, ``off``...). Defaults to True.
* ``grid`` – same parsing as ``ticks``.

Rows & Cols Auto Layout
-----------------------
``rows`` and ``cols`` determine the subplot grid. If you omit ``cols`` we compute a
default that fits all functions given the specified rows.

Parsing Nuances
---------------
The directive tolerates:
* Bracketed lists ``[a, b, c]`` or raw ``a, b, c`` strings.
* Semicolons as separators (converted to commas).
* Per-item parentheses / brackets / braces inside domain or line specs.

Debug Mode
----------
``:debug:`` (or ``debug:``) disables ID rewriting and size stripping so you can
inspect the raw produced SVG. (A PDF sidecar snippet is present in code but
commented out.)

No Hover Tooltips
-----------------
We intentionally do not inject ``<title>`` elements; they created distracting
hover popups. Accessibility is preserved through ``aria-label``.

Error Handling
--------------
If an expression fails SymPy parsing or evaluation, the build emits a Sphinx
error node indicating which function failed. Numerical issues (NaNs, infs) are
neutralized into ``NaN`` gaps, avoiding Matplotlib from drawing misleading spikes.

Option Reference (Summary)
--------------------------
Required:
* ``functions`` – list of function expressions.

Styling & Layout:
* ``width`` – percentage or px (auto-centers if %).
* ``rows`` / ``cols`` – grid shape.
* ``align`` – left | center | right (figure alignment class).
* ``class`` – extra CSS classes appended to figure container.
* ``alt`` – accessible description (defaults to generic text).

Axes & Appearance:
* ``xmin``, ``xmax``, ``ymin``, ``ymax`` – global ranges.
* ``xstep``, ``ystep`` – tick spacing.
* ``fontsize`` – base font size.
* ``lw`` – line width.
* ``alpha`` – line alpha (float).
* ``grid`` – toggle grid.
* ``ticks`` – toggle ticks.

Per-Function / Per-Axis:
* ``domains`` – list of domain specs with optional exclusions ``(a,b) \ {e1,e2}``.
* ``points`` – (legacy) per-axis point lists. Each element can be ``None`` (or omitted) or a
    single tuple ``(x,y)`` or a list/tuple of tuples ``[(x1,y1),(x2,y2)]``. Examples:
    ``points: [ (0,0), None, [(1,2),(2,3)] ]`` or using bracketless top-level splitting
    ``points: [(0,0), None, ((1,2),(2,3))]``. Points are drawn as filled blue circles
    with black edges after the function curve so they appear on top.
* ``point`` – (new) single point with axis targeting. Format: ``point: (x, y), axis_spec``
    where ``axis_spec`` is either an integer (1-indexed flattened row-major index) or
    a tuple ``(row, col)`` (1-indexed). Supports expression evaluation and function calls.
    Examples: ``point: (1, f(2)), 1`` (axis 1) or ``point: (1, h(2)), (2, 1)`` (row 2, col 1).
    Multiple ``point:`` lines can be used to add points to different axes.
* ``vlines`` / ``hlines`` – (legacy) per-axis vertical / horizontal reference lines.
* ``hline`` – (new) single horizontal line with axis targeting. Format: ``hline: y, axis_spec``
    or ``hline: y, x1, x2, axis_spec`` where y is the line height and optional x1, x2 define
    the horizontal extent (defaults to global xmin/xmax). Supports expression evaluation.
    Examples: ``hline: 2, 1`` (full width at y=2 on axis 1) or ``hline: f(3), -2, 2, (1, 2)``
    (from x=-2 to x=2 at y=f(3) on row 1, col 2).
* ``vline`` – (new) single vertical line with axis targeting. Format: ``vline: x, axis_spec``
    or ``vline: x, y1, y2, axis_spec`` where x is the line position and optional y1, y2 define
    the vertical extent (defaults to global ymin/ymax). Supports expression evaluation.
    Examples: ``vline: 1, 1`` (full height at x=1 on axis 1) or ``vline: sqrt(2), -3, 3, (2, 1)``
    (from y=-3 to y=3 at x=sqrt(2) on row 2, col 1).
* ``lines`` – (legacy) per-axis reference lines y = a*x + b or derived from basepoint.
* ``line`` – (new) single line with axis targeting. Format: ``line: a, b, axis_spec`` for y = a*x + b
    or ``line: a, (x0, y0), axis_spec`` for point-slope form y = y0 + a*(x - x0).
    Supports expression evaluation and function calls.
    Examples: ``line: 2, 1, 1`` (y = 2x + 1 on axis 1) or ``line: f(3), (1, 2), (2, 1)``
    (slope f(3) through point (1, 2) on row 2, col 1).
* ``tangent`` – (new) tangent line with axis targeting. Format: ``tangent: x0, function_label, axis_spec``
    where x0 is the point of tangency and function_label is one of the function labels (f, g, h, etc.).
    Computes derivative automatically using SymPy.
    Examples: ``tangent: 2, f, 1`` (tangent to f at x=2 on axis 1) or ``tangent: sqrt(3), g, (2, 1)``
    (tangent to g at x=sqrt(3) on row 2, col 1).
* ``text`` – (new) text annotation with axis targeting. Format: ``text: x, y, "text"[, placement], axis_spec``
    where placement is optional (default ``top-left``) and axis_spec is optional (applies to all if omitted).
    Position tokens: ``top-left``, ``top-right``, ``bottom-left``, ``bottom-right``, ``top-center``, ``bottom-center``,
    ``center-left``, ``center-right``, ``center-center``. Long variants shift further from point: ``longtop-left``, etc.
    Supports expression evaluation for x and y coordinates.
    Examples: ``text: 1, 2, "Point A", 1`` or ``text: pi/2, sin(pi/2), "Peak", top-center, (1, 2)``.
* ``annotate`` – (new) arrow annotation with axis targeting. Format: ``annotate: (x_text, y_text), (x_target, y_target), "text"[, arc], axis_spec``
    where arc is optional (default 0.3) and axis_spec is optional (applies to all if omitted).
    Supports expression evaluation for all coordinates and arc curvature.
    Examples: ``annotate: (1, 3), (2, 4), "Arrow", 1`` or ``annotate: (0, f(0)), (pi, f(pi)), "Peak", 0.5, (1, 1)``.
* ``xlims`` / ``ylims`` – (legacy) per-axis limits as tuples.
* ``xmin`` / ``xmax`` / ``ymin`` / ``ymax`` – (new) per-axis or global limits. Format: ``xmin: value, axis_spec``
    or ``xmin: value`` (applies to all axes). Supports expression evaluation.
    Examples: ``xmin: -10, 1`` (set xmin=-10 for axis 1) or ``ymax: 5`` (set ymax=5 for all axes).
* ``fn_labels`` / ``function-names`` – labels.

Meta / Control:
* ``nocache`` – force regeneration.
* ``debug`` – keep raw SVG + skip ID rewriting.
* ``name`` – explicit figure base name (influences cache filename).

Caption
-------
Any content after the parsed key/value block (or after inline key/value lines)
is treated as the caption and wrapped in a Sphinx ``<caption>`` node.

Implementation Notes
--------------------
* Expressions are compiled once per build variant and cached.
* Domain exclusions create widened gaps (± a few samples) for visual clarity.
* ID rewriting avoids collisions of gradients / clips when multiple multi-plot
    images exist on the same page.
* Inline width styling is injected only once by a regex match on the first
    ``<svg>`` tag; subsequent styling merges if a style attribute already exists.

This directive is specifically tuned for the pedagogical needs of the material
in this repository; tweak or extend as needed. If you add new options, please
update this docstring to keep the self-documenting pattern intact.
"""

from __future__ import annotations

import os
import re
import uuid
import hashlib
import shutil
from typing import Callable, Dict, Any, Tuple, List

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _hash_key(*parts) -> str:
    h = hashlib.sha1()
    for p in parts:
        if p is None:
            p = "__NONE__"
        h.update(str(p).encode("utf-8"))
        h.update(b"||")
    return h.hexdigest()[:12]


def _compile_function(expr: str) -> Callable:
    import sympy, numpy as np  # local import
    from scipy import special as sp_special

    expr = expr.strip()
    x = sympy.symbols("x")
    try:
        sym = sympy.sympify(expr)
    except Exception as e:  # pragma: no cover - user error path
        raise ValueError(f"Ugyldig funksjonsuttrykk '{expr}': {e}")

    # Map special functions like erf to scipy implementations for numpy arrays
    fn_np = sympy.lambdify(x, sym, modules=[{"erf": sp_special.erf}, "numpy"])

    def f(arr):
        return fn_np(np.asarray(arr, dtype=float))

    # simple vectorization test
    _ = f([0.0, 1.0])
    return f


# ---------------------------------------------------------------------------
# Directive
# ---------------------------------------------------------------------------


def _strip_root_svg_size(svg_text: str) -> str:
    """Remove width/height only on the root <svg> tag for responsiveness."""

    def repl(m):
        tag = m.group(0)
        tag = re.sub(r'\swidth="[^"]+"', "", tag)
        tag = re.sub(r'\sheight="[^"]+"', "", tag)
        return tag

    return re.sub(r"<svg\b[^>]*>", repl, svg_text, count=1)


def _parse_bool(val, default: bool | None = None) -> bool | None:
    if val is None:
        return default
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    if s == "":  # option present with no value => treat as True
        return True
    if s in {"true", "yes", "on", "1"}:
        return True
    if s in {"false", "no", "off", "0"}:
        return False
    return default


def _split_expr_list(val: str) -> List[str]:
    if not isinstance(val, str):
        return []
    s = val.strip()
    if not s:
        return []
    # allow [a,b,c] or a;b;c or a,b,c
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]
    s = s.replace(";", ",")
    parts = [p.strip() for p in s.split(",")]
    return [p for p in parts if p]


def _split_top_level(val: str) -> List[str]:
    """Split by commas at top level only (ignores commas inside (), [], {})."""
    if not isinstance(val, str):
        return []
    s = val.strip()
    if not s:
        return []
    # Strip surrounding brackets if present
    if (s.startswith("[") and s.endswith("]")) or (s.startswith("(") and s.endswith(")")):
        s = s[1:-1].strip()
    out: List[str] = []
    cur = []
    depth = 0
    pairs = {")": "(", "]": "[", "}": "{"}
    stack: List[str] = []
    i = 0
    while i < len(s):
        ch = s[i]
        if ch in "([{":
            depth += 1
            stack.append(ch)
            cur.append(ch)
        elif ch in ")]}":
            depth = max(0, depth - 1)
            if stack:
                stack.pop()
            cur.append(ch)
        elif ch == "," and depth == 0:
            part = "".join(cur).strip()
            if part:
                out.append(part)
            cur = []
        else:
            cur.append(ch)
        i += 1
    tail = "".join(cur).strip()
    if tail:
        out.append(tail)
    return out


def _safe_literal(val: str):
    try:
        import ast as _ast

        return _ast.literal_eval(val)
    except Exception:
        return None


def _parse_values_list_or_none(s: str):
    """Parse a scalar number or a tuple/list of numbers; return list[float] or None."""
    if not isinstance(s, str):
        return None
    st = s.strip()
    if not st or st.lower() == "none":
        return None
    lit = _safe_literal(st)
    if isinstance(lit, (int, float)):
        try:
            return [float(lit)]
        except Exception:
            return None
    if isinstance(lit, (list, tuple)):
        out: List[float] = []
        for v in lit:
            try:
                out.append(float(v))
            except Exception:
                pass
        return out if out else None
    # fallback: split by commas
    parts = [p.strip() for p in st.split(",") if p.strip()]
    out2: List[float] = []
    for p in parts:
        try:
            out2.append(float(p))
        except Exception:
            return None
    return out2 if out2 else None


class MultiPlotDirective(SphinxDirective):
    has_content = True
    required_arguments = 0
    option_spec = {
        "functions": directives.unchanged_required,  # list of expressions
        "fn_labels": directives.unchanged,  # optional list of labels
        "function-names": directives.unchanged,  # alias for fn_labels in examples
        "domains": directives.unchanged,  # per-function domain (a,b) or (a,b) \ {..}
        "vlines": directives.unchanged,  # per-function vline x or None
        "hlines": directives.unchanged,  # per-function hline y or None
        "xlims": directives.unchanged,  # per-function xlim tuple or None
        "ylims": directives.unchanged,  # per-function ylim tuple or None
        "lines": directives.unchanged,  # per-axis line spec: (a,b) or (a,(x,y)) or None
        "points": directives.unchanged,  # per-axis point lists: [(x,y),(x,y)] or None
        "point": directives.unchanged,  # single point with axis target: (x,y), axis_spec
        "hline": directives.unchanged,  # single hline with axis target: y, x1, x2, axis_spec
        "vline": directives.unchanged,  # single vline with axis target: x, y1, y2, axis_spec
        "line": directives.unchanged,  # single line with axis target: a, b, axis_spec or a, (x0,y0), axis_spec
        "tangent": directives.unchanged,  # single tangent line: x0, function_label, axis_spec
        "xmin": directives.unchanged,
        "xmax": directives.unchanged,
        "ymin": directives.unchanged,
        "ymax": directives.unchanged,
        "text": directives.unchanged,  # text annotation: x, y, "text"[, placement], axis_spec
        "annotate": directives.unchanged,  # arrow annotation: (xytext), (xy), "text"[, arc], axis_spec
        "xstep": directives.unchanged,
        "ystep": directives.unchanged,
        "fontsize": directives.unchanged,
        "lw": directives.unchanged,
        "alpha": directives.unchanged,
        "grid": directives.unchanged,
        "ticks": directives.unchanged,
        "rows": directives.unchanged,
        "cols": directives.unchanged,
        "align": lambda a: directives.choice(a, ["left", "center", "right"]),
        "class": directives.class_option,
        "name": directives.unchanged,
        "nocache": directives.flag,
        "alt": directives.unchanged,
        "width": directives.length_or_percentage_or_unitless,
        "debug": directives.flag,
    }

    # -----------------------------
    # Content key/value parsing
    # -----------------------------
    def _gather_kv_from_content(self) -> Tuple[Dict[str, str], int]:
        kv: Dict[str, str] = {}
        lines = list(self.content)
        idx = 0
        # YAML front matter style
        if lines and lines[0].strip() == "---":
            idx = 1
            while idx < len(lines) and lines[idx].strip() != "---":
                line = lines[idx].rstrip()
                m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
                if m:
                    kv[m.group(1)] = m.group(2)
                idx += 1
            if idx < len(lines) and lines[idx].strip() == "---":
                idx += 1
            while idx < len(lines) and not lines[idx].strip():
                idx += 1
            return kv, idx
        # flat key: value lines until first non-matching or blank separation
        caption_start = 0
        for i, line in enumerate(lines):
            if not line.strip():
                caption_start = i + 1
                continue
            m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
            if m:
                kv[m.group(1)] = m.group(2)
                caption_start = i + 1
            else:
                break
        return kv, caption_start

    # -----------------------------
    # Main run
    # -----------------------------
    def run(self):  # noqa: C901 (complexity OK for directive)
        env = self.state.document.settings.env
        app = env.app
        try:
            import plotmath  # type: ignore
        except Exception as e:  # pragma: no cover - dependency missing
            err = nodes.error()
            err += nodes.paragraph(text=f"Kunne ikke importere plotmath: {e}")
            return [err]

        kv, caption_idx = self._gather_kv_from_content()
        merged: Dict[str, Any] = {**kv, **self.options}
        if "functions" not in merged:
            return [
                self.state_machine.reporter.error(
                    "Directive 'multi-plot' krever 'functions:'", line=self.lineno
                )
            ]

        exprs = _split_expr_list(str(merged["functions"]))
        if not exprs:
            return [
                self.state_machine.reporter.error(
                    "'functions' var tomt eller ugyldig.", line=self.lineno
                )
            ]
        # compile all
        functions: List[Callable] = []
        for e in exprs:
            try:
                functions.append(_compile_function(e))
            except Exception as ex:
                return [
                    self.state_machine.reporter.error(
                        f"Ugyldig funksjon '{e}': {ex}", line=self.lineno
                    )
                ]

        def _f(name, default):
            v = merged.get(name)
            if v in (None, ""):
                return default
            try:
                return float(v)
            except Exception:
                return default

        xmin = _f("xmin", -6)
        xmax = _f("xmax", 6)
        ymin = _f("ymin", -6)
        ymax = _f("ymax", 6)
        xstep = _f("xstep", 1)
        ystep = _f("ystep", 1)
        fontsize = _f("fontsize", 20)
        lw = _f("lw", 2.5)
        alpha_raw = merged.get("alpha")
        grid_flag = _parse_bool(merged.get("grid"), default=True)
        ticks_flag = _parse_bool(merged.get("ticks"), default=True)

        try:
            alpha = float(alpha_raw) if alpha_raw not in (None, "") else None
        except Exception:
            alpha = None

        # Accept both fn_labels and function-names; function-names takes precedence if provided
        labels_list: List[str] = _split_expr_list(
            str(merged.get("function-names", merged.get("fn_labels", "")))
        )
        if labels_list and len(labels_list) == len(functions):
            labels_arg: Any = labels_list
        else:
            labels_arg = True

        # Per-function domains with optional exclusions, vlines, hlines, and axis limits
        # Helper to parse domain with optional set-difference exclusions
        def _parse_domain_with_exclusions(s: str):
            if not isinstance(s, str):
                return None, []
            s = s.strip()
            if not s or s.lower() == "none":
                return None, []
            num_re = r"[+-]?\d+(?:\.\d+)?"
            dom_ex_pat = re.compile(
                rf"\(\s*({num_re})\s*,\s*({num_re})\s*\)\s*(?:\\\s*\{{\s*([^}}]*)\s*\}})?"
            )
            m = dom_ex_pat.search(s)
            if not m:
                return None, []
            try:
                d0 = float(m.group(1))
                d1 = float(m.group(2))
                dom = (d0, d1)
            except Exception:
                dom = None
            excludes: List[float] = []
            excl_str = m.group(3) if m.lastindex and m.lastindex >= 3 else None
            if excl_str:
                for tok in [t.strip() for t in excl_str.split(",") if t.strip()]:
                    try:
                        excludes.append(float(tok))
                    except Exception:
                        pass
            return dom, excludes

        def _parse_tuple_or_none(s: str):
            if not isinstance(s, str):
                return None
            st = s.strip()
            if not st or st.lower() == "none":
                return None
            lit = _safe_literal(st)
            if isinstance(lit, (list, tuple)) and len(lit) == 2:
                try:
                    return (float(lit[0]), float(lit[1]))
                except Exception:
                    return None
            m = re.match(r"\(\s*([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)\s*\)", st)
            if m:
                try:
                    return (float(m.group(1)), float(m.group(2)))
                except Exception:
                    return None
            return None

        def _parse_scalar_or_none(s: str):
            if not isinstance(s, str):
                return None
            st = s.strip()
            if not st or st.lower() == "none":
                return None
            try:
                return float(st)
            except Exception:
                return None

        domains_raw = _split_top_level(str(merged.get("domains", "")))
        vlines_raw = _split_top_level(str(merged.get("vlines", "")))
        hlines_raw = _split_top_level(str(merged.get("hlines", "")))
        xlims_raw = _split_top_level(str(merged.get("xlims", "")))
        ylims_raw = _split_top_level(str(merged.get("ylims", "")))
        lines_raw = _split_top_level(str(merged.get("lines", "")))
        points_raw = _split_top_level(str(merged.get("points", "")))

        # Normalize sizes to match number of functions
        n = len(functions)

        def _pad(lst, fill="None"):
            return lst + [fill] * max(0, n - len(lst))

        domains_raw = _pad(domains_raw)
        vlines_raw = _pad(vlines_raw)
        hlines_raw = _pad(hlines_raw)
        xlims_raw = _pad(xlims_raw)
        ylims_raw = _pad(ylims_raw)
        lines_raw = _pad(lines_raw)
        points_raw = _pad(points_raw)

        dom_list: List[Tuple[float, float] | None] = []
        excl_list: List[List[float]] = []
        for s in domains_raw[:n]:
            dom, ex = _parse_domain_with_exclusions(s)
            dom_list.append(dom)
            excl_list.append(ex)

        vline_vals: List[List[float] | None] = [
            _parse_values_list_or_none(s) for s in vlines_raw[:n]
        ]
        hline_vals: List[List[float] | None] = [
            _parse_values_list_or_none(s) for s in hlines_raw[:n]
        ]
        xlim_vals: List[Tuple[float, float] | None] = [
            _parse_tuple_or_none(s) for s in xlims_raw[:n]
        ]
        ylim_vals: List[Tuple[float, float] | None] = [
            _parse_tuple_or_none(s) for s in ylims_raw[:n]
        ]

        # Parse per-axis line specs
        def _parse_line_spec(s: str):
            if not isinstance(s, str):
                return None
            st = s.strip()
            if not st or st.lower() == "none":
                return None
            lit = _safe_literal(st)
            a_val = None
            b_val = None
            if isinstance(lit, (list, tuple)) and len(lit) >= 2:
                try:
                    a_val = float(lit[0])
                except Exception:
                    a_val = None
                second = lit[1]
                if isinstance(second, (list, tuple)) and len(second) == 2:
                    try:
                        x0p = float(second[0])
                        y0p = float(second[1])
                        if a_val is not None:
                            b_val = y0p - a_val * x0p
                    except Exception:
                        b_val = None
                else:
                    try:
                        b_val = float(second)
                    except Exception:
                        b_val = None
                if a_val is not None and b_val is not None:
                    return (a_val, b_val)
            return None

        line_specs: List[Tuple[float, float] | None] = [_parse_line_spec(s) for s in lines_raw[:n]]

        # Parse per-axis points. Each entry can be:
        #  - "None" or empty => no points for that axis
        #  - a single tuple like (x,y)
        #  - a list/tuple of tuples: [(x1,y1),(x2,y2)] or ((x1,y1),(x2,y2))
        #  - a loose comma form: (x1,y1); (x2,y2)
        def _parse_points_entry(s: str):
            if not isinstance(s, str):
                return None
            st = s.strip()
            if not st or st.lower() == "none":
                return None
            lit = _safe_literal(st)
            points_list: List[Tuple[float, float]] = []

            def _coerce_pair(obj):
                try:
                    if (
                        isinstance(obj, (list, tuple))
                        and len(obj) == 2
                        and all(isinstance(v, (int, float)) for v in obj)
                    ):
                        return (float(obj[0]), float(obj[1]))
                except Exception:
                    return None
                return None

            if isinstance(lit, (list, tuple)):
                # Could be list of pairs or a single pair
                if len(lit) == 2 and all(isinstance(v, (int, float)) for v in lit):
                    p = _coerce_pair(lit)
                    if p:
                        points_list.append(p)
                else:
                    for item in lit:
                        p = _coerce_pair(item)
                        if p:
                            points_list.append(p)
                return points_list or None
            # Fallback: find all (x,y) pattern occurrences
            import re as _re

            matches = _re.findall(
                r"\(\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*,\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*\)",
                st,
            )
            for a, b in matches:
                try:
                    points_list.append((float(a), float(b)))
                except Exception:
                    pass
            return points_list or None

        points_vals: List[List[Tuple[float, float]] | None] = [
            _parse_points_entry(s) for s in points_raw[:n]
        ]

        # Parse new-style point keyword with axis targeting
        # Gather all point: entries from content
        point_entries_raw = []
        if "point" in merged:
            # Single point from options
            point_entries_raw.append(merged["point"])
        # Also check content for multiple point: lines
        for line_idx, line in enumerate(self.content):
            m = re.match(r"^point\s*:\s*(.+)$", line.strip())
            if m:
                point_entries_raw.append(m.group(1))

        explicit_name = merged.get("name")
        debug_mode = "debug" in merged
        rows = int(float(merged.get("rows", 1)))
        # If cols not provided, default to enough columns to fit all functions over the given rows
        default_cols = max(1, (len(functions) + rows - 1) // max(1, rows))
        cols = int(float(merged.get("cols", default_cols)))

        # Expression evaluator with function call support (similar to plot directive)
        def _eval_expr_multiplot(val) -> float:
            import sympy

            if val is None:
                raise ValueError("Empty value")
            if isinstance(val, (int, float)):
                return float(val)
            s0 = str(val).strip()
            if not s0:
                raise ValueError("Blank numeric expression")
            s = s0

            # Replace function label calls with their values
            # e.g., f(2) where 'f' is a function label
            for _ in range(50):  # iteration limit
                m = re.search(r"([A-Za-z_][A-Za-z0-9_]*)\(", s)
                if not m:
                    break
                lbl = m.group(1)
                if lbl not in labels_list:
                    # Skip this label
                    start_next = m.start() + 1
                    n = re.search(r"([A-Za-z_][A-Za-z0-9_]*)\(", s[start_next:])
                    if not n:
                        break
                    m = n
                    lbl = m.group(1)
                    if lbl not in labels_list:
                        break

                # Find matching closing parenthesis
                start = m.end() - 1  # position of '('
                depth = 0
                end = None
                for i in range(start, len(s)):
                    if s[i] == "(":
                        depth += 1
                    elif s[i] == ")":
                        depth -= 1
                        if depth == 0:
                            end = i
                            break
                if end is None:
                    break

                arg_expr = s[start + 1 : end]
                try:
                    arg_val = _eval_expr_multiplot(arg_expr)
                    idx = labels_list.index(lbl)
                    f = functions[idx]
                    import numpy as np

                    yv = float(f(np.array([arg_val]))[0])
                    s = s[: m.start()] + f"{yv}" + s[end + 1 :]
                    continue
                except Exception:
                    break

            # Evaluate remaining expression with sympy
            allowed = {
                k: getattr(sympy, k)
                for k in [
                    "pi",
                    "E",
                    "exp",
                    "sqrt",
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
                if hasattr(sympy, k)
            }
            try:
                expr = sympy.sympify(s, locals=allowed)
                return float(expr.evalf())
            except Exception:
                raise ValueError(f"Could not evaluate: {s0}")

        # Parse point entries after rows/cols are determined
        # Format: (x, y), axis_spec where axis_spec is either:
        #   - integer (1-indexed flattened, row-major)
        #   - (row, col) tuple (1-indexed)
        def _parse_point_with_axis(s: str, rows: int, cols: int):
            """Parse '(x, y), axis_spec' and return (x, y, flat_idx) or None."""
            if not isinstance(s, str):
                return None
            s = s.strip()
            if not s:
                return None

            # Split at top-level comma to separate (x,y) from axis_spec
            parts = []
            current = []
            depth = 0
            for ch in s:
                if ch in "([{":
                    depth += 1
                    current.append(ch)
                elif ch in ")]}":
                    depth -= 1
                    current.append(ch)
                elif ch == "," and depth == 0:
                    parts.append("".join(current).strip())
                    current = []
                else:
                    current.append(ch)
            if current:
                parts.append("".join(current).strip())

            if len(parts) < 2:
                return None

            # First part should be (x, y) - can contain expressions or function calls
            coord_str = parts[0].strip()

            # Extract x and y expressions from (x_expr, y_expr)
            if not (coord_str.startswith("(") and coord_str.endswith(")")):
                return None

            inner = coord_str[1:-1].strip()
            # Split on top-level comma
            comma_parts = []
            current_part = []
            depth = 0
            for ch in inner:
                if ch in "([{":
                    depth += 1
                    current_part.append(ch)
                elif ch in ")]}":
                    depth -= 1
                    current_part.append(ch)
                elif ch == "," and depth == 0:
                    comma_parts.append("".join(current_part).strip())
                    current_part = []
                else:
                    current_part.append(ch)
            if current_part:
                comma_parts.append("".join(current_part).strip())

            if len(comma_parts) != 2:
                return None

            x_expr, y_expr = comma_parts[0], comma_parts[1]

            # Evaluate expressions (supports function calls like f(2))
            try:
                x_val = _eval_expr_multiplot(x_expr)
                y_val = _eval_expr_multiplot(y_expr)
            except Exception:
                return None

            # Second part is axis specifier
            axis_str = parts[1]
            lit_axis = _safe_literal(axis_str)

            flat_idx = None
            if isinstance(lit_axis, int):
                # Direct flattened index (1-indexed)
                flat_idx = lit_axis - 1  # Convert to 0-indexed
            elif isinstance(lit_axis, (list, tuple)) and len(lit_axis) == 2:
                # (row, col) format (1-indexed)
                try:
                    row = int(lit_axis[0]) - 1  # Convert to 0-indexed
                    col = int(lit_axis[1]) - 1
                    if 0 <= row < rows and 0 <= col < cols:
                        flat_idx = row * cols + col
                except Exception:
                    return None
            else:
                # Try to parse as int or (row, col)
                try:
                    flat_idx = int(axis_str) - 1
                except Exception:
                    # Try tuple
                    m = re.match(r"\(\s*(\d+)\s*,\s*(\d+)\s*\)", axis_str)
                    if m:
                        try:
                            row = int(m.group(1)) - 1
                            col = int(m.group(2)) - 1
                            if 0 <= row < rows and 0 <= col < cols:
                                flat_idx = row * cols + col
                        except Exception:
                            return None

            if flat_idx is not None and 0 <= flat_idx < rows * cols:
                return (x_val, y_val, flat_idx)
            return None

        # Process point entries and add to points_vals
        for pt_entry in point_entries_raw:
            parsed = _parse_point_with_axis(pt_entry, rows, cols)
            if parsed:
                x_val, y_val, flat_idx = parsed
                # Add point to the appropriate axis
                if flat_idx < len(points_vals):
                    if points_vals[flat_idx] is None:
                        points_vals[flat_idx] = []
                    points_vals[flat_idx].append((x_val, y_val))

        # Parse new-style hline keyword with axis targeting
        # Gather all hline: entries from content
        hline_entries_raw = []
        if "hline" in merged:
            hline_entries_raw.append(merged["hline"])
        for line_idx, line in enumerate(self.content):
            m = re.match(r"^hline\s*:\s*(.+)$", line.strip())
            if m:
                hline_entries_raw.append(m.group(1))

        # Helper to parse axis specifier (used by both point and hline)
        def _parse_axis_spec(axis_str: str, rows: int, cols: int):
            """Parse axis specifier and return flat index (0-indexed) or None."""
            lit_axis = _safe_literal(axis_str)
            flat_idx = None

            if isinstance(lit_axis, int):
                flat_idx = lit_axis - 1
            elif isinstance(lit_axis, (list, tuple)) and len(lit_axis) == 2:
                try:
                    row = int(lit_axis[0]) - 1
                    col = int(lit_axis[1]) - 1
                    if 0 <= row < rows and 0 <= col < cols:
                        flat_idx = row * cols + col
                except Exception:
                    return None
            else:
                try:
                    flat_idx = int(axis_str) - 1
                except Exception:
                    m = re.match(r"\(\s*(\d+)\s*,\s*(\d+)\s*\)", axis_str)
                    if m:
                        try:
                            row = int(m.group(1)) - 1
                            col = int(m.group(2)) - 1
                            if 0 <= row < rows and 0 <= col < cols:
                                flat_idx = row * cols + col
                        except Exception:
                            return None

            if flat_idx is not None and 0 <= flat_idx < rows * cols:
                return flat_idx
            return None

        # Parse hline entries: y, x1, x2, axis_spec or y, axis_spec
        # Format: y [, x1, x2], axis_spec
        def _parse_hline_with_axis(
            s: str, rows: int, cols: int, xmin_global: float, xmax_global: float
        ):
            """Parse 'y, [x1, x2,] axis_spec' and return (y, x1, x2, flat_idx) or None."""
            if not isinstance(s, str):
                return None
            s = s.strip()
            if not s:
                return None

            # Split at top-level commas
            parts = []
            current = []
            depth = 0
            for ch in s:
                if ch in "([{":
                    depth += 1
                    current.append(ch)
                elif ch in ")]}":
                    depth -= 1
                    current.append(ch)
                elif ch == "," and depth == 0:
                    parts.append("".join(current).strip())
                    current = []
                else:
                    current.append(ch)
            if current:
                parts.append("".join(current).strip())

            if len(parts) < 2:
                return None

            # Last part is always axis specifier
            axis_str = parts[-1]
            flat_idx = _parse_axis_spec(axis_str, rows, cols)
            if flat_idx is None:
                return None

            # Parse y value (first part, supports expressions)
            try:
                y_val = _eval_expr_multiplot(parts[0])
            except Exception:
                return None

            # Parse optional x1, x2
            x1_val, x2_val = None, None
            if len(parts) == 4:  # y, x1, x2, axis_spec
                try:
                    x1_val = _eval_expr_multiplot(parts[1])
                    x2_val = _eval_expr_multiplot(parts[2])
                except Exception:
                    pass
            elif (
                len(parts) == 3
            ):  # y, x1, axis_spec (treat as y, axis_spec if x1 looks like axis spec)
                # Check if parts[1] could be axis spec
                test_idx = _parse_axis_spec(parts[1], rows, cols)
                if test_idx is not None:
                    # parts[1] is actually the axis spec, parts[2] is extra
                    return None
                # Otherwise parts[1] might be x1 - but we need x2 too for it to make sense
                # So treat as malformed for now
                pass

            # Use global xmin/xmax if x1, x2 not specified
            if x1_val is None:
                x1_val = xmin_global
            if x2_val is None:
                x2_val = xmax_global

            return (y_val, x1_val, x2_val, flat_idx)

        # Convert hline_vals from list of lists to dict for easy axis-specific updates
        hline_dict: Dict[int, List[Tuple[float, float | None, float | None]]] = {}
        for idx in range(len(hline_vals)):
            if hline_vals[idx] is not None:
                # Legacy hlines are just y values - convert to (y, None, None)
                hline_dict[idx] = [(y, None, None) for y in hline_vals[idx]]
            else:
                hline_dict[idx] = []

        # Process hline entries
        for hl_entry in hline_entries_raw:
            parsed = _parse_hline_with_axis(hl_entry, rows, cols, xmin, xmax)
            if parsed:
                y_val, x1_val, x2_val, flat_idx = parsed
                if flat_idx not in hline_dict:
                    hline_dict[flat_idx] = []
                hline_dict[flat_idx].append((y_val, x1_val, x2_val))

        # Convert back to list format for plotting code
        for idx in range(len(hline_vals)):
            if idx in hline_dict and hline_dict[idx]:
                # Keep only y values for backward compatibility with existing plotting code
                # But we need to handle x1, x2 differently - let's store tuples
                hline_vals[idx] = hline_dict[idx]
            elif idx in hline_dict:
                hline_vals[idx] = None

        # Parse new-style vline keyword with axis targeting
        # Gather all vline: entries from content
        vline_entries_raw = []
        if "vline" in merged:
            vline_entries_raw.append(merged["vline"])
        for line_idx, line in enumerate(self.content):
            m = re.match(r"^vline\s*:\s*(.+)$", line.strip())
            if m:
                vline_entries_raw.append(m.group(1))

        # Parse vline entries: x, y1, y2, axis_spec or x, axis_spec
        # Format: x [, y1, y2], axis_spec
        def _parse_vline_with_axis(
            s: str, rows: int, cols: int, ymin_global: float, ymax_global: float
        ):
            """Parse 'x, [y1, y2,] axis_spec' and return (x, y1, y2, flat_idx) or None."""
            if not isinstance(s, str):
                return None
            s = s.strip()
            if not s:
                return None

            # Split at top-level commas
            parts = []
            current = []
            depth = 0
            for ch in s:
                if ch in "([{":
                    depth += 1
                    current.append(ch)
                elif ch in ")]}":
                    depth -= 1
                    current.append(ch)
                elif ch == "," and depth == 0:
                    parts.append("".join(current).strip())
                    current = []
                else:
                    current.append(ch)
            if current:
                parts.append("".join(current).strip())

            if len(parts) < 2:
                return None

            # Last part is always axis specifier
            axis_str = parts[-1]
            flat_idx = _parse_axis_spec(axis_str, rows, cols)
            if flat_idx is None:
                return None

            # Parse x value (first part, supports expressions)
            try:
                x_val = _eval_expr_multiplot(parts[0])
            except Exception:
                return None

            # Parse optional y1, y2
            y1_val, y2_val = None, None
            if len(parts) == 4:  # x, y1, y2, axis_spec
                try:
                    y1_val = _eval_expr_multiplot(parts[1])
                    y2_val = _eval_expr_multiplot(parts[2])
                except Exception:
                    pass
            elif (
                len(parts) == 3
            ):  # x, y1, axis_spec (treat as x, axis_spec if y1 looks like axis spec)
                # Check if parts[1] could be axis spec
                test_idx = _parse_axis_spec(parts[1], rows, cols)
                if test_idx is not None:
                    # parts[1] is actually the axis spec, parts[2] is extra
                    return None
                # Otherwise parts[1] might be y1 - but we need y2 too for it to make sense
                # So treat as malformed for now
                pass

            # Use global ymin/ymax if y1, y2 not specified
            if y1_val is None:
                y1_val = ymin_global
            if y2_val is None:
                y2_val = ymax_global

            return (x_val, y1_val, y2_val, flat_idx)

        # Convert vline_vals from list of lists to dict for easy axis-specific updates
        vline_dict: Dict[int, List[Tuple[float, float | None, float | None]]] = {}
        for idx in range(len(vline_vals)):
            if vline_vals[idx] is not None:
                # Legacy vlines are just x values - convert to (x, None, None)
                vline_dict[idx] = [(x, None, None) for x in vline_vals[idx]]
            else:
                vline_dict[idx] = []

        # Process vline entries
        for vl_entry in vline_entries_raw:
            parsed = _parse_vline_with_axis(vl_entry, rows, cols, ymin, ymax)
            if parsed:
                x_val, y1_val, y2_val, flat_idx = parsed
                if flat_idx not in vline_dict:
                    vline_dict[flat_idx] = []
                vline_dict[flat_idx].append((x_val, y1_val, y2_val))

        # Convert back to list format for plotting code
        for idx in range(len(vline_vals)):
            if idx in vline_dict and vline_dict[idx]:
                vline_vals[idx] = vline_dict[idx]
            elif idx in vline_dict:
                vline_vals[idx] = None

        # Parse new-style line keyword with axis targeting
        # Gather all line: entries from content
        line_entries_raw = []
        if "line" in merged:
            line_entries_raw.append(merged["line"])
        for line_idx, line in enumerate(self.content):
            m = re.match(r"^line\s*:\s*(.+)$", line.strip())
            if m:
                line_entries_raw.append(m.group(1))

        # Parse line entries: a, b, axis_spec or a, (x0, y0), axis_spec
        # Format: a, b, axis_spec -> y = a*x + b
        #         a, (x0, y0), axis_spec -> y = y0 + a*(x - x0)
        def _parse_line_with_axis(s: str, rows: int, cols: int):
            """Parse 'a, b, axis_spec' or 'a, (x0, y0), axis_spec' and return (a, b, flat_idx) or None."""
            if not isinstance(s, str):
                return None
            s = s.strip()
            if not s:
                return None

            # Split at top-level commas
            parts = []
            current = []
            depth = 0
            for ch in s:
                if ch in "([{":
                    depth += 1
                    current.append(ch)
                elif ch in ")]}":
                    depth -= 1
                    current.append(ch)
                elif ch == "," and depth == 0:
                    parts.append("".join(current).strip())
                    current = []
                else:
                    current.append(ch)
            if current:
                parts.append("".join(current).strip())

            if len(parts) < 3:
                return None

            # Last part is always axis specifier
            axis_str = parts[-1]
            flat_idx = _parse_axis_spec(axis_str, rows, cols)
            if flat_idx is None:
                return None

            # Parse slope a (first part, supports expressions)
            try:
                a_val = _eval_expr_multiplot(parts[0])
            except Exception:
                return None

            # Parse second part: either b or (x0, y0)
            second_part = parts[1].strip()
            b_val = None

            # Check if it's a tuple (x0, y0)
            if second_part.startswith("(") and second_part.endswith(")"):
                # Extract x0, y0 from tuple
                inner = second_part[1:-1].strip()
                # Split on top-level comma
                coord_parts = []
                coord_current = []
                coord_depth = 0
                for ch in inner:
                    if ch in "([{":
                        coord_depth += 1
                        coord_current.append(ch)
                    elif ch in ")]}":
                        coord_depth -= 1
                        coord_current.append(ch)
                    elif ch == "," and coord_depth == 0:
                        coord_parts.append("".join(coord_current).strip())
                        coord_current = []
                    else:
                        coord_current.append(ch)
                if coord_current:
                    coord_parts.append("".join(coord_current).strip())

                if len(coord_parts) == 2:
                    try:
                        x0_val = _eval_expr_multiplot(coord_parts[0])
                        y0_val = _eval_expr_multiplot(coord_parts[1])
                        # Convert to y = a*x + b form: y = y0 + a*(x - x0) => y = a*x + (y0 - a*x0)
                        b_val = y0_val - a_val * x0_val
                    except Exception:
                        return None
                else:
                    return None
            else:
                # It's just b
                try:
                    b_val = _eval_expr_multiplot(second_part)
                except Exception:
                    return None

            if b_val is not None:
                return (a_val, b_val, flat_idx)
            return None

        # Convert line_specs from list to dict for easy axis-specific updates
        # Now each axis can have multiple lines, so we store lists of tuples
        line_dict: Dict[int, List[Tuple[float, float]]] = {}
        for idx in range(len(line_specs)):
            if line_specs[idx] is not None:
                # Legacy single-line format: convert to list
                line_dict[idx] = [line_specs[idx]]
            else:
                line_dict[idx] = []

        # Process line entries
        for ln_entry in line_entries_raw:
            parsed = _parse_line_with_axis(ln_entry, rows, cols)
            if parsed:
                a_val, b_val, flat_idx = parsed
                if flat_idx not in line_dict:
                    line_dict[flat_idx] = []
                line_dict[flat_idx].append((a_val, b_val))

        # Convert back to list format for plotting code
        for idx in range(len(line_specs)):
            if idx in line_dict and line_dict[idx]:
                # Store list of lines
                line_specs[idx] = line_dict[idx]
            else:
                # No lines for this axis
                line_specs[idx] = None

        # Process tangent keyword: tangent: x0, function_label, axis_spec
        tangent_entries_raw = []
        if "tangent" in merged:
            tangent_entries_raw.append(merged["tangent"])
        for line in self.content:
            m = re.match(r"^tangent\s*:\s*(.+)$", line.strip())
            if m:
                tangent_entries_raw.append(m.group(1))

        def _parse_tangent_with_axis(s: str, rows: int, cols: int):
            """
            Parse: x0, function_label, axis_spec
            Returns (x0_val, func_label, flat_idx) or None
            """
            import sympy

            # Split by commas at top level
            parts = _split_top_level(s)
            if len(parts) < 3:
                return None

            # Last part is axis_spec
            axis_part = parts[-1].strip()
            flat_idx = _parse_axis_spec(axis_part, rows, cols)
            if flat_idx is None:
                return None

            # Second-to-last is function label
            func_label = parts[-2].strip()

            # Everything before second-to-last is x0 expression
            x0_str = ",".join(parts[:-2]).strip()

            # Evaluate x0 using expression evaluator
            try:
                x0_val = _eval_expr_multiplot(x0_str)
            except Exception:
                return None

            return (x0_val, func_label, flat_idx)

        # Process tangent entries and add to line_specs
        for tg_entry in tangent_entries_raw:
            parsed = _parse_tangent_with_axis(tg_entry, rows, cols)
            if parsed:
                x0_val, func_label, flat_idx = parsed

                # Find the function index matching the label
                func_idx = None
                if labels_list:
                    for i, lbl in enumerate(labels_list):
                        if lbl.strip() == func_label:
                            func_idx = i
                            break

                if func_idx is not None and func_idx < len(functions):
                    # Compute tangent line: y = f'(x0) * (x - x0) + f(x0)
                    # Which is: y = f'(x0) * x + (f(x0) - x0 * f'(x0))
                    import sympy

                    x = sympy.symbols("x")
                    try:
                        expr_str = exprs[func_idx]  # Use expression string, not compiled function
                        sym = sympy.sympify(expr_str)
                        sym_deriv = sympy.diff(sym, x)

                        # Evaluate f(x0) and f'(x0)
                        f_x0 = float(sym.subs(x, x0_val))
                        fp_x0 = float(sym_deriv.subs(x, x0_val))

                        # Tangent line: y = fp_x0 * x + (f_x0 - x0_val * fp_x0)
                        a_tangent = fp_x0
                        b_tangent = f_x0 - x0_val * fp_x0

                        # Add to line_specs (append to existing list)
                        if line_specs[flat_idx] is None:
                            line_specs[flat_idx] = []
                        if isinstance(line_specs[flat_idx], tuple):
                            # Convert legacy single-line format to list
                            line_specs[flat_idx] = [line_specs[flat_idx]]
                        line_specs[flat_idx].append((a_tangent, b_tangent))
                    except Exception:
                        pass

        # Process per-axis xmin/xmax/ymin/ymax keywords
        # These can be specified with or without axis targeting
        # Format: xmin: value, axis_spec OR xmin: value (applies to all)

        def _parse_limit_with_axis(s: str, rows: int, cols: int):
            """
            Parse: value, axis_spec OR just value (applies to all)
            Returns (value, flat_idx) or (value, None) for all axes
            """
            parts = _split_top_level(s)
            if len(parts) == 0:
                return None

            if len(parts) == 1:
                # Just a value, applies to all axes
                try:
                    val = _eval_expr_multiplot(parts[0])
                    return (val, None)  # None means apply to all
                except Exception:
                    return None

            # Two or more parts: value, axis_spec
            axis_part = parts[-1].strip()
            flat_idx = _parse_axis_spec(axis_part, rows, cols)
            if flat_idx is None:
                return None

            # Everything before last part is the value
            val_str = ",".join(parts[:-1]).strip()
            try:
                val = _eval_expr_multiplot(val_str)
                return (val, flat_idx)
            except Exception:
                return None

        # Gather xmin entries
        xmin_entries_raw = []
        if "xmin" in merged and merged["xmin"]:
            xmin_entries_raw.append(merged["xmin"])
        for line in self.content:
            m = re.match(r"^xmin\s*:\s*(.+)$", line.strip())
            if m:
                xmin_entries_raw.append(m.group(1))

        # Gather xmax entries
        xmax_entries_raw = []
        if "xmax" in merged and merged["xmax"]:
            xmax_entries_raw.append(merged["xmax"])
        for line in self.content:
            m = re.match(r"^xmax\s*:\s*(.+)$", line.strip())
            if m:
                xmax_entries_raw.append(m.group(1))

        # Gather ymin entries
        ymin_entries_raw = []
        if "ymin" in merged and merged["ymin"]:
            ymin_entries_raw.append(merged["ymin"])
        for line in self.content:
            m = re.match(r"^ymin\s*:\s*(.+)$", line.strip())
            if m:
                ymin_entries_raw.append(m.group(1))

        # Gather ymax entries
        ymax_entries_raw = []
        if "ymax" in merged and merged["ymax"]:
            ymax_entries_raw.append(merged["ymax"])
        for line in self.content:
            m = re.match(r"^ymax\s*:\s*(.+)$", line.strip())
            if m:
                ymax_entries_raw.append(m.group(1))

        # Process xmin entries
        for xmin_entry in xmin_entries_raw:
            parsed = _parse_limit_with_axis(xmin_entry, rows, cols)
            if parsed:
                val, flat_idx = parsed
                if flat_idx is None:
                    # Apply to all axes
                    for idx in range(len(xlim_vals)):
                        if xlim_vals[idx] is None:
                            xlim_vals[idx] = (val, xmax)
                        else:
                            xlim_vals[idx] = (val, xlim_vals[idx][1])
                else:
                    # Apply to specific axis
                    if xlim_vals[flat_idx] is None:
                        xlim_vals[flat_idx] = (val, xmax)
                    else:
                        xlim_vals[flat_idx] = (val, xlim_vals[flat_idx][1])

        # Process xmax entries
        for xmax_entry in xmax_entries_raw:
            parsed = _parse_limit_with_axis(xmax_entry, rows, cols)
            if parsed:
                val, flat_idx = parsed
                if flat_idx is None:
                    # Apply to all axes
                    for idx in range(len(xlim_vals)):
                        if xlim_vals[idx] is None:
                            xlim_vals[idx] = (xmin, val)
                        else:
                            xlim_vals[idx] = (xlim_vals[idx][0], val)
                else:
                    # Apply to specific axis
                    if xlim_vals[flat_idx] is None:
                        xlim_vals[flat_idx] = (xmin, val)
                    else:
                        xlim_vals[flat_idx] = (xlim_vals[flat_idx][0], val)

        # Process ymin entries
        for ymin_entry in ymin_entries_raw:
            parsed = _parse_limit_with_axis(ymin_entry, rows, cols)
            if parsed:
                val, flat_idx = parsed
                if flat_idx is None:
                    # Apply to all axes
                    for idx in range(len(ylim_vals)):
                        if ylim_vals[idx] is None:
                            ylim_vals[idx] = (val, ymax)
                        else:
                            ylim_vals[idx] = (val, ylim_vals[idx][1])
                else:
                    # Apply to specific axis
                    if ylim_vals[flat_idx] is None:
                        ylim_vals[flat_idx] = (val, ymax)
                    else:
                        ylim_vals[flat_idx] = (val, ylim_vals[flat_idx][1])

        # Process ymax entries
        for ymax_entry in ymax_entries_raw:
            parsed = _parse_limit_with_axis(ymax_entry, rows, cols)
            if parsed:
                val, flat_idx = parsed
                if flat_idx is None:
                    # Apply to all axes
                    for idx in range(len(ylim_vals)):
                        if ylim_vals[idx] is None:
                            ylim_vals[idx] = (ymin, val)
                        else:
                            ylim_vals[idx] = (ylim_vals[idx][0], val)
                else:
                    # Apply to specific axis
                    if ylim_vals[flat_idx] is None:
                        ylim_vals[flat_idx] = (ymin, val)
                    else:
                        ylim_vals[flat_idx] = (ylim_vals[flat_idx][0], val)

        # Include per-axis settings in the hash to prevent stale caches

        # ─────────────────────────────────────────────────────────────
        # Helper for parsing text positioning (copied from plot.py)
        # ─────────────────────────────────────────────────────────────
        def _parse_text_positioning(pos: str) -> Tuple[str, str]:
            """Map positioning string to (va, ha). Default is (top, left)."""
            if not isinstance(pos, str):
                return ("top", "left")
            key = pos.strip().lower().replace("_", "-")
            mapping = {
                "top-left": ("bottom", "right"),
                "top-right": ("bottom", "left"),
                "bottom-left": ("top", "right"),
                "bottom-right": ("top", "left"),
                "top-center": ("bottom", "center"),
                "bottom-center": ("top", "center"),
                "center-left": ("center", "right"),
                "center-right": ("center", "left"),
                "longtop-left": ("longbottom", "left"),
                "longtop-longleft": ("longbottom", "longright"),
                "longbottom-right": ("longtop", "right"),
                "longbottom-left": ("longtop", "left"),
                "longtop-center": ("longbottom", "center"),
                "longbottom-center": ("longtop", "center"),
                "longtop-longright": ("longbottom", "longleft"),
                "longbottom-longright": ("longtop", "longleft"),
                "longtop-longleft": ("longbottom", "longright"),
                "longbottom-longleft": ("longtop", "longright"),
                "top-longleft": ("bottom", "longright"),
                "top-longright": ("bottom", "longleft"),
                "bottom-longleft": ("top", "longright"),
                "bottom-longright": ("top", "longleft"),
                "center-longleft": ("center", "longright"),
                "center-longright": ("center", "longleft"),
                "center-center": ("center", "center"),
            }
            return mapping.get(key, ("top", "left"))

        # ─────────────────────────────────────────────────────────────
        # Helper for parsing text annotation with axis specifier
        # ─────────────────────────────────────────────────────────────
        def _parse_text_with_axis(
            entry: str, rows: int, cols: int
        ) -> Tuple[float, float, str, str, int | None] | None:
            """
            Parse: x, y, "text"[, placement], axis_spec
            Returns: (x_val, y_val, text_str, placement_str, flat_idx) or None
            If axis_spec is omitted, flat_idx is None (applies to all axes).
            """
            parts = _split_top_level(entry)
            if len(parts) < 3:
                return None

            # Parse x and y as expressions
            try:
                x_val = _eval_expr_multiplot(parts[0].strip())
                y_val = _eval_expr_multiplot(parts[1].strip())
            except Exception:
                return None

            # Parse text string (may be quoted)
            text_raw = parts[2].strip()
            text_str = text_raw.strip('"').strip("'")

            # Determine placement and axis_spec based on number of parts
            placement_str = "top-left"  # default
            axis_spec_raw = None

            if len(parts) == 3:
                # No placement or axis_spec
                flat_idx = None
            elif len(parts) == 4:
                # Either placement or axis_spec
                candidate = parts[3].strip()
                # Check if it's a valid placement token
                pos_keys = {
                    "top-left",
                    "top-right",
                    "bottom-left",
                    "bottom-right",
                    "top-center",
                    "bottom-center",
                    "center-left",
                    "center-right",
                    "center-center",
                    "longtop-left",
                    "longtop-longleft",
                    "longbottom-right",
                    "longbottom-left",
                    "longtop-center",
                    "longbottom-center",
                    "longtop-longright",
                    "longbottom-longright",
                    "top-longleft",
                    "top-longright",
                    "bottom-longleft",
                    "bottom-longright",
                    "center-longleft",
                    "center-longright",
                }
                if candidate.lower().replace("_", "-") in pos_keys:
                    placement_str = candidate
                    flat_idx = None
                else:
                    # Treat as axis_spec
                    axis_spec_raw = candidate
                    parsed_axis = _parse_axis_spec(axis_spec_raw, rows, cols)
                    flat_idx = parsed_axis if parsed_axis is not None else None
            elif len(parts) == 5:
                # Both placement and axis_spec
                placement_str = parts[3].strip()
                axis_spec_raw = parts[4].strip()
                parsed_axis = _parse_axis_spec(axis_spec_raw, rows, cols)
                flat_idx = parsed_axis if parsed_axis is not None else None
            else:
                return None

            return (x_val, y_val, text_str, placement_str, flat_idx)

        # ─────────────────────────────────────────────────────────────
        # Parse text annotations
        # ─────────────────────────────────────────────────────────────
        # Format: text: x, y, "text"[, placement], axis_spec
        # Storage: per-axis dictionary of lists of (x, y, text, placement) tuples
        text_dict: Dict[int, List[Tuple[float, float, str, str]]] = {}

        text_entries_raw = []
        # From option
        text_opt = self.options.get("text", "").strip()
        if text_opt:
            text_entries_raw.append(text_opt)
        # From content
        for line in self.content:
            m = re.match(r"^text\s*:\s*(.+)$", line.strip())
            if m:
                text_entries_raw.append(m.group(1))

        for text_entry in text_entries_raw:
            parsed = _parse_text_with_axis(text_entry, rows, cols)
            if parsed:
                x_val, y_val, text_str, placement_str, flat_idx = parsed
                if flat_idx is None:
                    # Apply to all axes
                    for idx in range(rows * cols):
                        if idx not in text_dict:
                            text_dict[idx] = []
                        text_dict[idx].append((x_val, y_val, text_str, placement_str))
                else:
                    # Apply to specific axis
                    if flat_idx not in text_dict:
                        text_dict[flat_idx] = []
                    text_dict[flat_idx].append((x_val, y_val, text_str, placement_str))

        # ─────────────────────────────────────────────────────────────
        # Helper for parsing annotate with axis specifier
        # ─────────────────────────────────────────────────────────────
        def _parse_annotate_with_axis(
            entry: str, rows: int, cols: int
        ) -> Tuple[Tuple[float, float], Tuple[float, float], str, float, int | None] | None:
            """
            Parse: (x_text, y_text), (x_target, y_target), "text"[, arc], axis_spec
            Returns: ((x_text, y_text), (x_target, y_target), text_str, arc_val, flat_idx) or None
            If axis_spec is omitted, flat_idx is None (applies to all axes).
            """
            s = entry.strip()

            # Find first two balanced tuples
            def _grab_tuple(start_index: int) -> Tuple[int, int, str] | None:
                if start_index >= len(s) or s[start_index] != "(":
                    return None
                depth = 0
                for j in range(start_index, len(s)):
                    if s[j] == "(":
                        depth += 1
                    elif s[j] == ")":
                        depth -= 1
                        if depth == 0:
                            inner = s[start_index + 1 : j]
                            return (start_index, j, inner)
                return None

            # Locate first '('
            i1 = s.find("(")
            if i1 == -1:
                return None
            t1 = _grab_tuple(i1)
            if not t1:
                return None
            i2_search = t1[1] + 1
            # Skip commas/space
            while i2_search < len(s) and s[i2_search] in " ,":
                i2_search += 1
            if i2_search >= len(s) or s[i2_search] != "(":
                return None
            t2 = _grab_tuple(i2_search)
            if not t2:
                return None
            rest = s[t2[1] + 1 :].strip()

            # Split tuple inners on top-level comma
            def _split_pair(inner: str) -> Tuple[str, str] | None:
                depth = 0
                for k, ch in enumerate(inner):
                    if ch == "(":
                        depth += 1
                    elif ch == ")":
                        depth -= 1
                    elif ch == "," and depth == 0:
                        left = inner[:k].strip()
                        right = inner[k + 1 :].strip()
                        if left and right:
                            return (left, right)
                return None

            p1 = _split_pair(t1[2])
            p2 = _split_pair(t2[2])
            if not (p1 and p2):
                return None

            # Extract quoted text
            import re

            m_txt = re.search(
                r"\"([^\"\\]*(?:\\.[^\"\\]*)*)\"|\'([^\'\\]*(?:\\.[^\'\\]*)*)\'",
                rest,
            )
            if not m_txt:
                return None
            text_str = m_txt.group(1) if m_txt.group(1) is not None else m_txt.group(2)
            after = rest[m_txt.end() :].strip().lstrip(",").strip()

            # Parse remaining parts: [arc,] axis_spec
            remaining_parts = _split_top_level(after) if after else []
            arc_val = 0.3  # default
            flat_idx = None

            if len(remaining_parts) == 0:
                # No arc or axis_spec
                pass
            elif len(remaining_parts) == 1:
                # Could be arc or axis_spec
                candidate = remaining_parts[0]
                # Try to parse as axis_spec first
                parsed_axis = _parse_axis_spec(candidate, rows, cols)
                if parsed_axis is not None:
                    flat_idx = parsed_axis
                else:
                    # Try as arc value
                    try:
                        arc_val = _eval_expr_multiplot(candidate)
                    except Exception:
                        pass
            elif len(remaining_parts) >= 2:
                # First is arc, second is axis_spec
                try:
                    arc_val = _eval_expr_multiplot(remaining_parts[0])
                except Exception:
                    pass
                parsed_axis = _parse_axis_spec(remaining_parts[1], rows, cols)
                if parsed_axis is not None:
                    flat_idx = parsed_axis

            # Evaluate coordinates
            try:
                x_text = _eval_expr_multiplot(p1[0])
                y_text = _eval_expr_multiplot(p1[1])
                x_target = _eval_expr_multiplot(p2[0])
                y_target = _eval_expr_multiplot(p2[1])
            except Exception:
                return None

            return ((x_text, y_text), (x_target, y_target), text_str, arc_val, flat_idx)

        # ─────────────────────────────────────────────────────────────
        # Parse annotate annotations
        # ─────────────────────────────────────────────────────────────
        # Format: annotate: (x_text, y_text), (x_target, y_target), "text"[, arc], axis_spec
        # Storage: per-axis dictionary of lists of ((xytext), (xy), text, arc) tuples
        annotate_dict: Dict[
            int, List[Tuple[Tuple[float, float], Tuple[float, float], str, float]]
        ] = {}

        annotate_entries_raw = []
        # From option
        annotate_opt = self.options.get("annotate", "").strip()
        if annotate_opt:
            annotate_entries_raw.append(annotate_opt)
        # From content
        for line in self.content:
            m = re.match(r"^annotate\s*:\s*(.+)$", line.strip())
            if m:
                annotate_entries_raw.append(m.group(1))

        for annotate_entry in annotate_entries_raw:
            parsed = _parse_annotate_with_axis(annotate_entry, rows, cols)
            if parsed:
                xytext, xy, text_str, arc_val, flat_idx = parsed
                if flat_idx is None:
                    # Apply to all axes
                    for idx in range(rows * cols):
                        if idx not in annotate_dict:
                            annotate_dict[idx] = []
                        annotate_dict[idx].append((xytext, xy, text_str, arc_val))
                else:
                    # Apply to specific axis
                    if flat_idx not in annotate_dict:
                        annotate_dict[flat_idx] = []
                    annotate_dict[flat_idx].append((xytext, xy, text_str, arc_val))

        # Include per-axis settings in the hash to prevent stale caches
        content_hash = _hash_key(
            "|".join(exprs),
            "|".join(labels_list),
            xmin,
            xmax,
            ymin,
            ymax,
            xstep,
            ystep,
            fontsize,
            lw,
            alpha,
            rows,
            cols,
            int(grid_flag),
            int(ticks_flag),
            "|".join(["" if d is None else f"{d[0]},{d[1]}" for d in dom_list]),
            "|".join(["|".join(map(str, exs)) if exs else "" for exs in excl_list]),
            "|".join(["|".join(map(str, vs)) if vs else "" for vs in vline_vals]),
            "|".join(["|".join(map(str, hs)) if hs else "" for hs in hline_vals]),
            "|".join(["" if xl is None else f"{xl[0]},{xl[1]}" for xl in xlim_vals]),
            "|".join(["" if yl is None else f"{yl[0]},{yl[1]}" for yl in ylim_vals]),
            "|".join(
                [
                    (
                        ""
                        if ls is None
                        else (
                            ";".join([f"{a},{b}" for a, b in ls])
                            if isinstance(ls, list)
                            else f"{ls[0]},{ls[1]}"
                        )
                    )
                    for ls in line_specs
                ]
            ),
            "|".join(
                [
                    "" if pv is None else ";".join([f"{p[0]},{p[1]}" for p in pv])
                    for pv in points_vals
                ]
            ),
            "|".join(
                [
                    (
                        ""
                        if idx not in text_dict
                        else ";".join([f"{x},{y},{t},{p}" for x, y, t, p in text_dict[idx]])
                    )
                    for idx in range(rows * cols)
                ]
            ),
            "|".join(
                [
                    (
                        ""
                        if idx not in annotate_dict
                        else ";".join(
                            [
                                f"{xt[0]},{xt[1]},{xy[0]},{xy[1]},{t},{a}"
                                for xt, xy, t, a in annotate_dict[idx]
                            ]
                        )
                    )
                    for idx in range(rows * cols)
                ]
            ),
        )
        base_name = explicit_name or f"multi_plot_{content_hash}"

        rel_dir = os.path.join("_static", "multi_plot")
        abs_dir = os.path.join(app.srcdir, rel_dir)
        os.makedirs(abs_dir, exist_ok=True)
        svg_name = f"{base_name}.svg"
        abs_svg = os.path.join(abs_dir, svg_name)

        regenerate = ("nocache" in merged) or not os.path.exists(abs_svg)
        if regenerate:
            try:
                letters = [chr(i) for i in range(65, 65 + len(functions))]
                # Create axes grid without auto-plotting functions
                fig, axes = plotmath.multiplot(
                    functions=[],
                    fn_labels=False,
                    xmin=xmin,
                    xmax=xmax,
                    ymin=ymin,
                    ymax=ymax,
                    xstep=xstep,
                    ystep=ystep,
                    ticks=ticks_flag,
                    grid=grid_flag,
                    rows=rows,
                    cols=cols,
                    lw=lw,
                    alpha=alpha,
                    fontsize=fontsize,
                    figsize=(4.5 * cols, 3.5 * rows),
                )
                # Normalize axes to flat list
                try:
                    import numpy as _np

                    axes_list = (
                        list(axes.flatten())
                        if hasattr(axes, "flatten")
                        else list(_np.array(axes).flatten())
                    )
                except Exception:
                    axes_list = axes if isinstance(axes, (list, tuple)) else [axes]

                # Ensure tick label font size matches provided fontsize (legend handled later)
                try:
                    for _ax in axes_list:
                        try:
                            _ax.tick_params(labelsize=int(fontsize))
                        except Exception:
                            pass
                except Exception:
                    pass

                # Manual plotting per-axis
                import numpy as np

                for idx, (expr, fn) in enumerate(zip(exprs, functions)):
                    if idx >= len(axes_list):
                        break
                    ax = axes_list[idx]
                    # Per-axis domain
                    dom = dom_list[idx]
                    x0, x1 = dom if dom is not None else (xmin, xmax)
                    N = int(2**12)
                    x = np.linspace(x0, x1, N)
                    y = fn(x)
                    # Ensure float array and blank out non-finite values
                    y = np.asarray(y, dtype=float)
                    y[~np.isfinite(y)] = np.nan
                    # Robust exclusions: widen window and clear neighbors
                    exs = [e for e in excl_list[idx] if x0 < e < x1]
                    if exs and N > 1:
                        dx = (x1 - x0) / (N - 1)
                        w = max(4 * dx, 1e-6 * (1.0 + max(abs(e) for e in exs)))
                        for e in exs:
                            try:
                                mask = np.abs(x - e) <= w
                                if mask.any():
                                    y[mask] = np.nan
                                j = int(np.argmin(np.abs(x - e)))
                                for k in (j - 2, j - 1, j, j + 1, j + 2):
                                    if 0 <= k < y.size:
                                        y[k] = np.nan
                            except Exception:
                                try:
                                    j = int(np.argmin(np.abs(x - e)))
                                    if 0 <= j < y.size:
                                        y[j] = np.nan
                                except Exception:
                                    pass
                    # Also break across steep jumps or extreme magnitudes
                    # Determine per-axis y-span preference: use provided ylim for this axis if any
                    if ylim_vals[idx] is not None:
                        y0_lim, y1_lim = ylim_vals[idx]
                    else:
                        y0_lim, y1_lim = ymin, ymax
                    try:
                        y_span = abs(float(y1_lim) - float(y0_lim))
                    except Exception:
                        y_span = np.nan
                    if not (isinstance(y_span, (int, float)) and y_span > 0):
                        finite_y = y[np.isfinite(y)]
                        if finite_y.size > 0:
                            y_span = float(np.nanmax(finite_y) - np.nanmin(finite_y))
                    if not (isinstance(y_span, (int, float)) and y_span > 0):
                        y_span = 1.0
                    finite_pair = np.isfinite(y[:-1]) & np.isfinite(y[1:])
                    jump_factor = 0.5
                    big_jump = finite_pair & (np.abs(y[1:] - y[:-1]) > (jump_factor * y_span))
                    if big_jump.any():
                        idx_break = np.where(big_jump)[0]
                        for i_b in idx_break:
                            if 0 <= i_b + 1 < y.size:
                                y[i_b + 1] = np.nan
                    mag_factor = 50.0
                    too_big = np.isfinite(y) & (np.abs(y) > (mag_factor * y_span))
                    if too_big.any():
                        y[too_big] = np.nan
                    lbl = labels_list[idx] if (labels_list and idx < len(labels_list)) else None
                    if lbl:
                        ax.plot(x, y, lw=lw, alpha=alpha, label=f"${lbl}$")
                        ax.legend(fontsize=int(fontsize))
                    else:
                        ax.plot(x, y, lw=lw, alpha=alpha)
                    # Plot per-axis points if provided
                    try:
                        pv = points_vals[idx]
                        if pv:
                            xs = [p[0] for p in pv]
                            ys = [p[1] for p in pv]
                            ax.plot(
                                xs,
                                ys,
                                linestyle="none",
                                marker="o",
                                markersize=max(4, min(12, int(fontsize) // 2)),
                                color="black",
                                alpha=0.8,
                            )
                    except Exception:
                        pass
                    # Optional line(s) y = a*x + b per axis
                    if line_specs[idx] is not None:
                        # Handle both legacy format (single tuple) and new format (list of tuples)
                        lines_to_plot = []
                        if isinstance(line_specs[idx], tuple):
                            lines_to_plot = [line_specs[idx]]
                        elif isinstance(line_specs[idx], list):
                            lines_to_plot = line_specs[idx]

                        for line_spec in lines_to_plot:
                            try:
                                a_l, b_l = line_spec  # type: ignore[misc]
                                # Use provided xlim for this axis if any; else global
                                if xlim_vals[idx] is not None:
                                    x_min_line, x_max_line = xlim_vals[idx]
                                else:
                                    x_min_line, x_max_line = xmin, xmax
                                x_line = np.array(
                                    [float(x_min_line), float(x_max_line)], dtype=float
                                )
                                y_line = a_l * x_line + b_l
                                ax.plot(
                                    x_line,
                                    y_line,
                                    linestyle="--",
                                    color=plotmath.COLORS.get("red"),
                                    lw=lw,
                                    alpha=alpha,
                                )
                            except Exception:
                                pass
                    # vlines / hlines (support multiple values per axis)
                    for xv in vline_vals[idx] or []:
                        try:
                            # Support both old format (float) and new format (tuple)
                            if isinstance(xv, tuple) and len(xv) == 3:
                                x_val, y1_val, y2_val = xv
                                # If y1, y2 specified, use plot line segment
                                if y1_val is not None and y2_val is not None:
                                    import numpy as np

                                    x_line = np.array([float(x_val), float(x_val)])
                                    y_line = np.array([float(y1_val), float(y2_val)])
                                    ax.plot(
                                        x_line,
                                        y_line,
                                        color=plotmath.COLORS.get("red"),
                                        linestyle="--",
                                        lw=lw,
                                    )
                                else:
                                    # Full vertical line
                                    ax.axvline(
                                        x=float(x_val),
                                        color=plotmath.COLORS.get("red"),
                                        linestyle="--",
                                        lw=lw,
                                    )
                            else:
                                # Old format: just x value
                                ax.axvline(
                                    x=float(xv),
                                    color=plotmath.COLORS.get("red"),
                                    linestyle="--",
                                    lw=lw,
                                )
                        except Exception:
                            pass
                    for yh in hline_vals[idx] or []:
                        try:
                            # Support both old format (float) and new format (tuple)
                            if isinstance(yh, tuple) and len(yh) == 3:
                                y_val, x1_val, x2_val = yh
                                # If x1, x2 specified, use axhspan or plot line segment
                                if x1_val is not None and x2_val is not None:
                                    import numpy as np

                                    x_line = np.array([float(x1_val), float(x2_val)])
                                    y_line = np.array([float(y_val), float(y_val)])
                                    ax.plot(
                                        x_line,
                                        y_line,
                                        color=plotmath.COLORS.get("red"),
                                        linestyle="--",
                                        lw=lw,
                                    )
                                else:
                                    # Full horizontal line
                                    ax.axhline(
                                        y=float(y_val),
                                        color=plotmath.COLORS.get("red"),
                                        linestyle="--",
                                        lw=lw,
                                    )
                            else:
                                # Old format: just y value
                                ax.axhline(
                                    y=float(yh),
                                    color=plotmath.COLORS.get("red"),
                                    linestyle="--",
                                    lw=lw,
                                )
                        except Exception:
                            pass

                    # Draw text annotations
                    if idx in text_dict:
                        # Get axes dimensions for offset calculation
                        try:
                            fig.canvas.draw()  # ensure layout is realized
                            _bbox_px = ax.get_window_extent()
                            _ax_w_px, _ax_h_px = _bbox_px.width, _bbox_px.height
                            if _ax_w_px <= 0 or _ax_h_px <= 0:
                                _ax_w_px = _ax_h_px = None
                        except Exception:
                            _ax_w_px = _ax_h_px = None

                        # Get current axis limits for fallback offset calculation
                        try:
                            ax_xlim = ax.get_xlim()
                            ax_ylim = ax.get_ylim()
                            ax_dx = abs(ax_xlim[1] - ax_xlim[0])
                            ax_dy = abs(ax_ylim[1] - ax_ylim[0])
                        except Exception:
                            ax_dx = ax_dy = 1.0

                        for x0, y0, text_str, pos_str in text_dict[idx]:
                            va, ha = _parse_text_positioning(pos_str)

                            # Offset factors (matching plot.py)
                            _fx_short = 0.015
                            _fy_short = 0.015
                            _fx_long = 0.03
                            _fy_long = 0.03

                            # Resolve long* variants
                            _use_fx = _fx_short
                            _use_fy = _fy_short
                            if va == "longbottom":
                                va = "bottom"
                                _use_fy = _fy_long
                            elif va == "longtop":
                                va = "top"
                                _use_fy = _fy_long
                            if ha == "longright":
                                ha = "right"
                                _use_fx = _fx_long
                            elif ha == "longleft":
                                ha = "left"
                                _use_fx = _fx_long

                            # Calculate offset
                            if _ax_w_px and _ax_h_px:
                                # Pixel-based offsets
                                dx_px = 0.0
                                dy_px = 0.0
                                if ha == "right":
                                    dx_px = -_ax_w_px * _use_fx
                                elif ha == "left":
                                    dx_px = _ax_w_px * _use_fx
                                if va == "bottom":
                                    dy_px = _ax_h_px * _use_fy
                                elif va == "top":
                                    dy_px = -_ax_h_px * _use_fy
                                x_disp, y_disp = ax.transData.transform((x0, y0))
                                x1, y1 = ax.transData.inverted().transform(
                                    (x_disp + dx_px, y_disp + dy_px)
                                )
                                dx = x1 - x0
                                dy = y1 - y0
                            else:
                                # Fallback: data-space offsets
                                if va == "bottom":
                                    dy = (_fy_short if _use_fy == _fy_short else _fy_long) * ax_dy
                                elif va == "top":
                                    dy = -(_fy_short if _use_fy == _fy_short else _fy_long) * ax_dy
                                else:
                                    dy = 0.0
                                if ha == "right":
                                    dx = -(_fx_short if _use_fx == _fx_short else _fx_long) * ax_dx
                                elif ha == "left":
                                    dx = (_fx_short if _use_fx == _fx_short else _fx_long) * ax_dx
                                else:
                                    dx = 0.0

                            # Draw text
                            ax.text(
                                x0 + dx,
                                y0 + dy,
                                text_str,
                                fontsize=int(fontsize),
                                ha=ha,
                                va=va,
                            )

                    # Draw arrow annotations
                    if idx in annotate_dict:
                        import matplotlib.pyplot as plt

                        plt.sca(ax)  # Set current axes
                        for xytext, xy, text_str, arc_val in annotate_dict[idx]:
                            plotmath.annotate(
                                xy=xy,
                                xytext=xytext,
                                s=text_str,
                                arc=arc_val,
                                fontsize=int(fontsize),
                            )

                    # x/ylims
                    if xlim_vals[idx] is not None:
                        ax.set_xlim(*xlim_vals[idx])
                    if ylim_vals[idx] is not None:
                        ax.set_ylim(*ylim_vals[idx])
                # Save via the single Figure object
                fig.savefig(abs_svg, format="svg", bbox_inches="tight", transparent=True)
                # Also save a PDF sidecar for debugging comparisons (optional)
                # try:
                #     fig.savefig(
                #         os.path.join(abs_dir, f"{base_name}.pdf"),
                #         format="pdf",
                #         bbox_inches="tight",
                #         transparent=True,
                #     )
                # except Exception:
                #     pass
                import matplotlib

                matplotlib.pyplot.close(fig)
            except Exception as e:
                return [
                    self.state_machine.reporter.error(
                        f"Feil under generering av graf: {e}", line=self.lineno
                    )
                ]

        if not os.path.exists(abs_svg):
            return [self.state_machine.reporter.error("multi-plot: SVG mangler.", line=self.lineno)]

        env.note_dependency(abs_svg)
        try:  # copy to output _static
            out_static = os.path.join(app.outdir, "_static", "multi_plot")
            os.makedirs(out_static, exist_ok=True)
            shutil.copy2(abs_svg, os.path.join(out_static, svg_name))
        except Exception:
            pass

        try:
            raw_svg = open(abs_svg, "r", encoding="utf-8").read()
        except Exception as e:
            return [
                self.state_machine.reporter.error(
                    f"graph inline: kunne ikke lese SVG: {e}", line=self.lineno
                )
            ]

        if not debug_mode and "viewBox" in raw_svg:
            raw_svg = _strip_root_svg_size(raw_svg)

        def _rewrite_ids(txt: str, prefix: str) -> str:
            # Collect ids
            ids = re.findall(r'\bid="([^"]+)"', txt)
            if not ids:
                return txt
            # Skip font glyphs to avoid disrupting text rendering
            skip_prefixes = (
                "DejaVu",
                "CM",
                "STIX",
                "Nimbus",
                "Bitstream",
                "Arial",
                "Times",
                "Helvetica",
            )
            mapping = {}
            for i in ids:
                if i.startswith(skip_prefixes):
                    continue
                mapping[i] = f"{prefix}{i}"
            if not mapping:
                return txt

            # Replace id definitions
            def repl_id(m: re.Match) -> str:
                old = m.group(1)
                new = mapping.get(old, old)
                return f'id="{new}"'

            txt = re.sub(r'\bid="([^"]+)"', repl_id, txt)

            # Replace url(#id) everywhere (attributes and styles)
            def repl_url(m: re.Match) -> str:
                old = m.group(1).strip()
                new = mapping.get(old, old)
                return f"url(#{new})"

            txt = re.sub(r"url\(#\s*([^\)\s]+)\s*\)", repl_url, txt)

            # Replace href/xlink:href references supporting both quote styles
            def repl_href(m: re.Match) -> str:
                attr = m.group(1)
                quote = m.group(2)
                old = m.group(3).strip()
                new = mapping.get(old, old)
                return f"{attr}={quote}#{new}{quote}"

            txt = re.sub(
                r'(xlink:href|href)\s*=\s*(["\"])#\s*([^"\"]+)\s*\2',
                repl_href,
                txt,
            )
            return txt

        if not debug_mode:
            raw_svg = _rewrite_ids(raw_svg, f"mgr_{content_hash}_{uuid.uuid4().hex[:6]}_")

        alt_default = f"Multiplot av {len(exprs)} funksjoner"
        alt = merged.get("alt", alt_default)

        width_opt = merged.get("width")
        percent = isinstance(width_opt, str) and width_opt.strip().endswith("%")

        def _augment(m):
            tag = m.group(0)
            if "class=" not in tag:
                tag = tag[:-1] + ' class="graph-inline-svg"' + ">"
            else:
                tag = tag.replace('class="', 'class="graph-inline-svg ')
            if alt and "aria-label=" not in tag:
                tag = tag[:-1] + f' role="img" aria-label="{alt}"' + ">"
            if width_opt:
                if percent:
                    wval = width_opt.strip()
                else:
                    wval = width_opt.strip()
                    if wval.isdigit():
                        wval += "px"
                style_frag = f"width:{wval}; height:auto; display:block; margin:0 auto;"
                if "style=" in tag:
                    tag = re.sub(
                        r'style="([^"]*)"',
                        lambda mm: f'style="{mm.group(1)}; {style_frag}"',
                        tag,
                        count=1,
                    )
                else:
                    tag = tag[:-1] + f' style="{style_frag}"' + ">"
            return tag

        raw_svg = re.sub(r"<svg\b[^>]*>", _augment, raw_svg, count=1)
        # Intentionally do not inject a <title> element to avoid hover tooltips; accessibility
        # remains via role="img" and aria-label attributes. Add manually later if truly needed.

        figure = nodes.figure()
        figure.setdefault("classes", []).extend(
            ["adaptive-figure", "multi-plot-figure", "no-click"]
        )
        raw_node = nodes.raw("", raw_svg, format="html")
        raw_node.setdefault("classes", []).extend(["graph-image", "no-click", "no-scaled-link"])
        figure += raw_node

        extra_classes = merged.get("class")
        if extra_classes:
            figure["classes"].extend(extra_classes)
        figure["align"] = merged.get("align", "center")

        caption_lines = list(self.content)[caption_idx:]
        while caption_lines and not caption_lines[0].strip():
            caption_lines.pop(0)
        if caption_lines:
            caption = nodes.caption()
            caption += nodes.Text("\n".join(caption_lines))
            figure += caption

        if explicit_name:
            self.add_name(figure)
        return [figure]


def setup(app):  # pragma: no cover
    app.add_directive("multi-plot", MultiPlotDirective)
    app.add_directive("multiplot", MultiPlotDirective)  # Also register without hyphen
    return {"version": "0.1", "parallel_read_safe": True, "parallel_write_safe": True}
