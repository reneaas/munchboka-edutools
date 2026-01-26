r"""Animate directive — create animated plots with transparent backgrounds

This directive extends the plot directive to generate animations by varying
one or more animation variables across frames. The result is an animated
WebP or GIF file with transparent background that can be embedded in web pages.

Usage
-----
:::{animate}
animate-var: a, 0, 10, 20          # Variable name, start, end, frames
fps: 10                             # Frames per second (default: 10)
format: webp                        # webp or gif (default: webp)
loop: true                          # Loop animation (default: true)

# All standard plot directive options work here
function: sin(a*x)
xmin: -10
xmax: 10
ymin: -2
ymax: 2
grid: true
width: 80%
:::
Animasjon av sinusfunksjon med varierende frekvens.

Animation Variable Syntax
--------------------------
animate-var: name, start, end, count
  * name: Variable name to use (e.g., a, t, n)
  * start: Starting value (supports SymPy expressions like 0, pi, sqrt(2))
  * end: Ending value (supports SymPy expressions)
  * count: Number of frames (positive integer)

The variable will be linearly interpolated from start to end across count frames.

Examples:
  animate-var: t, 0, 2*pi, 30       # 30 frames from 0 to 2π
  animate-var: a, -5, 5, 20         # 20 frames from -5 to 5
  animate-var: n, 1, 10, 10         # 10 frames from 1 to 10

Output Formats
--------------
* webp (default): Better compression, native transparency, good browser support
* gif: Wider compatibility, larger file size

Technical Details
-----------------
* Each frame is generated using the plot directive logic
* SVG frames are converted to PNG with transparency using cairosvg
* PNGs are assembled into animation using Pillow (GIF) or imageio (WebP)
* Animations are cached based on content hash
* Output directory: _static/animate/
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import tempfile
import uuid
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Tuple

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective


def _parse_bool(val, default: bool | None = None) -> bool | None:
    """Parse boolean value from string."""
    if val is None:
        return default
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    if s == "":
        return True
    if s in {"true", "yes", "on", "1"}:
        return True
    if s in {"false", "no", "off", "0"}:
        return False
    return default


def _eval_expr(expr_str: str) -> float:
    """Evaluate a SymPy expression to a float."""
    import sympy as sp

    # Define safe namespace
    safe_dict = {
        "pi": sp.pi,
        "E": sp.E,
        "sqrt": sp.sqrt,
        "exp": sp.exp,
        "log": sp.log,
        "sin": sp.sin,
        "cos": sp.cos,
        "tan": sp.tan,
        "asin": sp.asin,
        "acos": sp.acos,
        "atan": sp.atan,
        "Abs": sp.Abs,
        "abs": sp.Abs,
    }

    expr_str = expr_str.strip()
    try:
        sym = sp.sympify(expr_str, locals=safe_dict)
        return float(sym.evalf())
    except Exception as e:
        raise ValueError(f"Could not evaluate expression '{expr_str}': {e}")


def _get_safe_namespace(**extra_vars) -> dict:
    """Get a safe namespace for eval with SymPy functions and numpy fallbacks.

    This provides comprehensive support for mathematical functions, matching
    the plot directive's capabilities.

    Args:
        **extra_vars: Additional variables to include in namespace (e.g., animation variable)

    Returns:
        Dictionary suitable for use with eval()
    """
    import math
    import numpy as np
    import sympy as sp

    # Create namespace with SymPy symbolic functions
    namespace = {
        "__builtins__": {},
        # Constants
        "pi": np.pi,
        "e": np.e,
        "E": np.e,
        # Trigonometric
        "sin": np.sin,
        "cos": np.cos,
        "tan": np.tan,
        "asin": np.arcsin,
        "acos": np.arccos,
        "atan": np.arctan,
        "atan2": np.arctan2,
        "sinh": np.sinh,
        "cosh": np.cosh,
        "tanh": np.tanh,
        "asinh": np.arcsinh,
        "acosh": np.arccosh,
        "atanh": np.arctanh,
        # Exponential and logarithmic
        "exp": np.exp,
        "log": np.log,
        "log10": np.log10,
        "log2": np.log2,
        "ln": np.log,
        # Power and roots
        "sqrt": np.sqrt,
        "cbrt": np.cbrt,
        "pow": np.power,
        # Rounding and absolute
        "abs": np.abs,
        "Abs": np.abs,
        "ceil": np.ceil,
        "floor": np.floor,
        "round": np.round,
        # Sign and comparison
        "sign": np.sign,
        "max": np.maximum,
        "min": np.minimum,
        # Special functions
        "factorial": math.factorial,
    }

    # Add any extra variables (like animation variable, parameter for curves, etc.)
    namespace.update(extra_vars)

    return namespace


def _parse_function_item(s: str, default_xmin: float, default_xmax: float) -> Tuple[
    str,  # expression
    str | None,  # label
    Tuple[float, float] | None,  # domain
    List[float],  # exclusions
    str | None,  # color
    Tuple[str, str],  # (left_endpoint_type, right_endpoint_type)
]:
    """Parse function specification with domain, exclusions, and endpoint markers.

    Supports formats like:
    - "x**2"  # simple expression
    - "x**2, f"  # with label
    - "x**2, [-2, 2]"  # with domain (closed endpoints)
    - "x**2, (-2, 2)"  # with domain (open endpoints)
    - "x**2, [-2, 2), blue"  # mixed endpoints and color
    - "1/x, \\{0}"  # with exclusion

    Args:
        s: Function specification string
        default_xmin: Default minimum x value if no domain specified
        default_xmax: Default maximum x value if no domain specified

    Returns:
        Tuple of (expression, label, domain, exclusions, color, (left_type, right_type))
    """
    import re
    from ast import literal_eval

    s = str(s).strip()

    # Helper to check if a string looks like a color
    def _looks_like_color(tok: str) -> bool:
        if not isinstance(tok, str):
            return False
        t = tok.strip()
        if not t:
            return False
        # hex colors
        if re.match(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$", t):
            return True
        if t.lower().startswith("tab:"):
            return True
        if re.match(r"^C\d+$", t):
            return True
        # plotmath named colors
        try:
            import plotmath as _pm

            if _pm.COLORS.get(t) is not None:
                return True
        except Exception:
            pass
        return False

    # Helper to evaluate symbolic expressions like pi, sqrt(2)
    def _sym_eval_num(txt: str) -> float:
        import sympy

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
            ]
            if hasattr(sympy, k)
        }
        expr = sympy.sympify(txt, locals=allowed)
        return float(expr.evalf())

    # Helper to extract domain and exclusions from text
    def _extract_domain_and_exclusions(text: str):
        """Return (domain_tuple|None, exclusions_list, text_without_domain, left_bracket, right_bracket)."""
        n = len(text)
        i = 0
        while i < n:
            left_bracket = None
            right_bracket = None
            if text[i] in "([⟨":
                left_bracket = text[i]
                # Find matching closing bracket
                depth = 1
                j = i + 1
                while j < n and depth > 0:
                    ch = text[j]
                    if ch in "([⟨":
                        depth += 1
                    elif ch in ")]⟩":
                        depth -= 1
                        if depth == 0:
                            right_bracket = ch
                    j += 1
                if depth != 0:
                    # unbalanced, give up
                    break
                content = text[i + 1 : j - 1].strip()
                # Find a single top-level comma in content
                depth2 = 0
                comma_index: int | None = None
                for k, ch in enumerate(content):
                    if ch == "(":
                        depth2 += 1
                    elif ch == ")":
                        depth2 -= 1
                    elif ch == "," and depth2 == 0:
                        if comma_index is None:
                            comma_index = k
                        else:
                            # more than one top-level comma => not domain
                            comma_index = None
                            break
                if comma_index is not None:
                    left = content[:comma_index].strip()
                    right = content[comma_index + 1 :].strip()
                    if left and right:
                        # Optional exclusions right after ) like \{a,b}
                        k2 = j
                        excl_list: List[float] = []
                        # skip whitespace
                        while k2 < n and text[k2].isspace():
                            k2 += 1
                        if k2 < n and text[k2] == "\\":
                            k2 += 1
                            while k2 < n and text[k2].isspace():
                                k2 += 1
                            if k2 < n and text[k2] == "{":
                                k2 += 1
                                excl_start = k2
                                # read until matching '}'
                                while k2 < n and text[k2] != "}":
                                    k2 += 1
                                excl_content = text[excl_start:k2]
                                if k2 < n and text[k2] == "}":
                                    k2 += 1  # consume '}'
                                for tok in [
                                    t.strip() for t in excl_content.split(",") if t.strip()
                                ]:
                                    try:
                                        excl_list.append(_sym_eval_num(tok))
                                    except Exception:
                                        pass
                        # Attempt numeric evaluation of endpoints
                        dom_tuple: Tuple[float, float] | None = None
                        try:
                            d0 = _sym_eval_num(left)
                            d1 = _sym_eval_num(right)
                            dom_tuple = (d0, d1)
                        except Exception:
                            dom_tuple = None
                        # Remove the consumed substring from original text
                        new_text = (text[:i] + text[k2:]).strip()
                        # Determine endpoint types from bracket types
                        left_type = "closed" if left_bracket == "[" else "open"
                        right_type = "closed" if right_bracket == "]" else "open"
                        return dom_tuple, excl_list, new_text, left_type, right_type
                # Move past this bracket group and continue scanning
                i = j
                continue
            i += 1
        return None, [], text, "none", "none"

    domain, excludes, s_wo_dom, left_endpoint, right_endpoint = _extract_domain_and_exclusions(s)

    # Tokenize on commas to find expression, label, color
    parts = [p.strip() for p in s_wo_dom.split(",") if p.strip()]

    expr = parts[0] if parts else s_wo_dom.strip()
    label = None
    color = None

    # Scan remaining tokens for label/color
    for tok in parts[1:]:
        t = tok.strip()
        if t.lower().startswith("label="):
            if label is None:
                label = t.split("=", 1)[1].strip()
            continue
        if t.lower().startswith("color="):
            if color is None:
                color = t.split("=", 1)[1].strip()
            continue
        if color is None and _looks_like_color(t):
            color = t
        elif label is None:
            label = t

    return expr, label, domain, excludes, color, (left_endpoint, right_endpoint)


def _draw_endpoint_marker(ax, x_arr, y_arr, idx, marker_type, direction, color_use, lw_use):
    """Draw endpoint marker orthogonal to curve at endpoint.

    Parameters:
    - ax: matplotlib axes
    - x_arr, y_arr: full arrays of x and y data for the curve
    - idx: index of the endpoint (0 for left, -1 for right)
    - marker_type: "closed" (bracket) or "open" (angle bracket)
    - direction: "left" or "right" indicating which endpoint
    - color_use: line color
    - lw_use: line width
    """
    import numpy as np

    if marker_type not in ["closed", "open"]:
        return

    x_pt = x_arr[idx]
    y_pt = y_arr[idx]

    # If the endpoint y-value is NaN, find the nearest finite point
    if not np.isfinite(y_pt):
        if direction == "left":
            # Search forward for first finite point
            for i in range(1, min(10, len(y_arr))):
                if np.isfinite(y_arr[i]):
                    y_pt = y_arr[i]
                    break
        else:  # right endpoint
            # Search backward for first finite point
            for i in range(len(y_arr) - 2, max(-1, len(y_arr) - 11), -1):
                if np.isfinite(y_arr[i]):
                    y_pt = y_arr[i]
                    break

        # If still no finite point found, give up
        if not np.isfinite(y_pt):
            return

    # Calculate tangent vector at endpoint using nearby points
    if direction == "left":
        # Use forward difference for left endpoint
        tangent_idx = None
        for i in range(1, min(10, len(x_arr))):
            if np.isfinite(y_arr[i]):
                tangent_idx = i
                break
        if tangent_idx is None:
            return  # No valid points to compute tangent
        dx = x_arr[tangent_idx] - x_pt
        dy = y_arr[tangent_idx] - y_pt
    else:  # right endpoint
        # Use backward difference for right endpoint
        tangent_idx = None
        for i in range(len(x_arr) - 2, max(-1, len(x_arr) - 11), -1):
            if np.isfinite(y_arr[i]):
                tangent_idx = i
                break
        if tangent_idx is None:
            return  # No valid points to compute tangent
        dx = x_pt - x_arr[tangent_idx]
        dy = y_pt - y_arr[tangent_idx]

    # Get axes limits and figure dimensions
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    x_range = xlim[1] - xlim[0]
    y_range = ylim[1] - ylim[0]

    # Get pixel dimensions of axes
    try:
        bbox = ax.get_window_extent()
        ax_width_px = bbox.width
        ax_height_px = bbox.height
    except Exception:
        # Fallback if we can't get pixel dimensions
        ax_width_px = 600
        ax_height_px = 600

    # Convert tangent vector from data coordinates to display (pixel) coordinates
    data_to_px_x = ax_width_px / x_range if x_range > 0 else 1.0
    data_to_px_y = ax_height_px / y_range if y_range > 0 else 1.0

    dx_px = dx * data_to_px_x
    dy_px = dy * data_to_px_y

    # Normalize tangent vector in pixel space
    tangent_length_px = np.sqrt(dx_px**2 + dy_px**2)
    if tangent_length_px < 1e-10:
        # Fallback to horizontal tangent in pixel space
        tx_px, ty_px = 1.0, 0.0
    else:
        tx_px = dx_px / tangent_length_px
        ty_px = dy_px / tangent_length_px

    # Compute orthogonal vector in pixel space (rotate tangent 90° CCW)
    ortho_x_px = -ty_px
    ortho_y_px = tx_px

    # Base marker size in pixels
    marker_size_px = 25.0

    # Scale orthogonal vector to desired pixel length
    ortho_x_px_scaled = ortho_x_px * marker_size_px
    ortho_y_px_scaled = ortho_y_px * marker_size_px

    # Convert back to data coordinates for plotting
    px_to_data_x = x_range / ax_width_px if ax_width_px > 0 else 0.01
    px_to_data_y = y_range / ax_height_px if ax_height_px > 0 else 0.01

    ortho_x_scaled = ortho_x_px_scaled * px_to_data_x
    ortho_y_scaled = ortho_y_px_scaled * px_to_data_y

    # Convert tangent vector for caps
    tx = tx_px * px_to_data_x
    ty = ty_px * px_to_data_y
    # Normalize in data space for unit tangent
    t_norm = np.sqrt(tx**2 + ty**2)
    if t_norm > 1e-10:
        tx = tx / t_norm
        ty = ty / t_norm

    if marker_type == "closed":
        # Draw bracket: main line perpendicular to curve with short caps along tangent
        # Main perpendicular line
        x_main = [x_pt - ortho_x_scaled / 2, x_pt + ortho_x_scaled / 2]
        y_main = [y_pt - ortho_y_scaled / 2, y_pt + ortho_y_scaled / 2]
        plot_kwargs = {
            "lw": lw_use * 0.8,
            "solid_capstyle": "butt",
            "zorder": 10,
        }
        if color_use is not None:
            plot_kwargs["color"] = color_use
        ax.plot(x_main, y_main, **plot_kwargs)

        # Cap length along the tangent direction
        cap_length_px = 8.0
        cap_tx_px = tx_px * cap_length_px
        cap_ty_px = ty_px * cap_length_px
        cap_tx = cap_tx_px * px_to_data_x
        cap_ty = cap_ty_px * px_to_data_y

        # Determine cap direction based on endpoint
        if direction == "left":
            # Caps point inward (to the right/into the curve)
            cap_sign = 1.0
        else:
            # Caps point inward (to the left/into the curve)
            cap_sign = -1.0

        # Top cap (at +ortho end)
        x_top_end = x_pt + ortho_x_scaled / 2
        y_top_end = y_pt + ortho_y_scaled / 2
        cap_kwargs = {
            "lw": lw_use * 0.8,
            "solid_capstyle": "butt",
            "zorder": 10,
        }
        if color_use is not None:
            cap_kwargs["color"] = color_use
        ax.plot(
            [x_top_end, x_top_end + cap_sign * cap_tx],
            [y_top_end, y_top_end + cap_sign * cap_ty],
            **cap_kwargs,
        )

        # Bottom cap (at -ortho end)
        x_bot_end = x_pt - ortho_x_scaled / 2
        y_bot_end = y_pt - ortho_y_scaled / 2
        ax.plot(
            [x_bot_end, x_bot_end + cap_sign * cap_tx],
            [y_bot_end, y_bot_end + cap_sign * cap_ty],
            **cap_kwargs,
        )

    elif marker_type == "open":
        # Draw angle bracket: two lines forming < or >
        # Angle opening along tangent direction
        angle_length_px = 8.0
        angle_tx_px = tx_px * angle_length_px
        angle_ty_px = ty_px * angle_length_px
        angle_tx = angle_tx_px * px_to_data_x
        angle_ty = angle_ty_px * px_to_data_y

        # Determine angle direction based on endpoint
        if direction == "left":
            # Angle opens to the right (inward toward curve)
            angle_sign = 1.0
        else:
            # Angle opens to the left (inward toward curve)
            angle_sign = -1.0

        # Upper arm: from the curve point to upper outer position
        x_upper_outer = x_pt + angle_sign * angle_tx + ortho_x_scaled / 2
        y_upper_outer = y_pt + angle_sign * angle_ty + ortho_y_scaled / 2
        angle_kwargs = {
            "lw": lw_use * 0.8,
            "solid_capstyle": "butt",
            "zorder": 10,
        }
        if color_use is not None:
            angle_kwargs["color"] = color_use
        ax.plot(
            [x_pt, x_upper_outer],
            [y_pt, y_upper_outer],
            **angle_kwargs,
        )

        # Lower arm: from the curve point to lower outer position
        x_lower_outer = x_pt + angle_sign * angle_tx - ortho_x_scaled / 2
        y_lower_outer = y_pt + angle_sign * angle_ty - ortho_y_scaled / 2
        ax.plot(
            [x_pt, x_lower_outer],
            [y_pt, y_lower_outer],
            **angle_kwargs,
        )


def _parse_animate_var(var_spec: str) -> Tuple[str, List[float]]:
    """Parse animation variable specification.

    Args:
        var_spec: String like "a, 0, 10, 20" (name, start, end, count)

    Returns:
        Tuple of (variable_name, list_of_values)
    """
    parts = [p.strip() for p in var_spec.split(",")]
    if len(parts) != 4:
        raise ValueError(f"animate-var must have 4 parts: name, start, end, count. Got: {var_spec}")

    var_name = parts[0]
    if not var_name.isidentifier():
        raise ValueError(f"Invalid variable name: {var_name}")

    try:
        start = _eval_expr(parts[1])
        end = _eval_expr(parts[2])
        count = int(parts[3])
        if count < 1:
            raise ValueError("Frame count must be positive")
    except Exception as e:
        raise ValueError(f"Error parsing animate-var '{var_spec}': {e}")

    # Generate linear interpolation
    import numpy as np

    values = np.linspace(start, end, count).tolist()

    return var_name, values


def _substitute_variable(content: str, var_name: str, var_value: float) -> str:
    """Substitute animation variable with its value in content.

    Args:
        content: Content string with variable references
        var_name: Name of variable to replace
        var_value: Numeric value to substitute

    Returns:
        Content with variable substituted (skips quoted strings)
    """
    # Format value: use decimal if small enough, otherwise scientific notation
    if abs(var_value) < 1e10 and (abs(var_value) > 1e-4 or var_value == 0):
        # Remove unnecessary trailing zeros after decimal point
        value_str = f"{var_value:.10f}".rstrip("0").rstrip(".")
    else:
        value_str = f"{var_value:.6e}"

    def _format_text_placeholders(text: str) -> str:
        """Evaluate `{...}` placeholders inside quoted text.

        Supports:
        - `{phi}` / `{phi:.2f}`
        - `{2 * 1.5 * cos(phi*pi/180):.2f}` (expression + optional format)

        Safety/robustness goals:
        - Preserve escaped braces `{{` / `}}`
        - Avoid rewriting normal LaTeX braces used as command arguments
          like `\\frac{1}{2}` or `\\vec{a}`.
        """
        if "{" not in text or "}" not in text:
            return text

        # Preserve escaped braces.
        lbrace_token = "\u0000LBRACE\u0000"
        rbrace_token = "\u0000RBRACE\u0000"
        tmp = text.replace("{{", lbrace_token).replace("}}", rbrace_token)

        ns = _get_safe_namespace(**{var_name: var_value})

        def _is_latex_command_argument(s: str, lbrace_index: int) -> bool:
            # If the brace is immediately an argument to a LaTeX command, skip.
            # Example: "\\frac{1}{2}" or "\\vec{a}".
            j = lbrace_index - 1
            while j >= 0 and s[j].isspace():
                j -= 1
            if j < 0:
                return False
            k = j
            while k >= 0 and s[k].isalpha():
                k -= 1
            return k >= 0 and s[k] == "\\" and k < j

        def _split_expr_and_format(inner: str) -> tuple[str, str | None]:
            # Split `expr:format` at a top-level ':' (not inside parentheses).
            depth = 0
            for idx, ch in enumerate(inner):
                if ch in "([":
                    depth += 1
                elif ch in ")]":
                    depth = max(0, depth - 1)
                elif ch == ":" and depth == 0:
                    return inner[:idx].strip(), inner[idx + 1 :].strip()
            return inner.strip(), None

        out: list[str] = []
        i = 0
        while i < len(tmp):
            ch = tmp[i]
            if ch != "{":
                out.append(ch)
                i += 1
                continue

            # Find matching '}' (no nesting expected in placeholders).
            j = tmp.find("}", i + 1)
            if j == -1:
                out.append(ch)
                i += 1
                continue

            latex_arg = _is_latex_command_argument(tmp, i)

            inner = tmp[i + 1 : j].strip()
            if not inner:
                out.append(tmp[i : j + 1])
                i = j + 1
                continue

            # If the placeholder contains LaTeX commands, treat it as literal.
            if "\\" in inner:
                out.append(tmp[i : j + 1])
                i = j + 1
                continue

            expr_str, fmt_spec = _split_expr_and_format(inner)

            # Only attempt evaluation if it mentions the animation variable
            # or looks like a numeric expression.
            # Avoid eating common LaTeX argument braces like `\frac{1}{2}`.
            # Only treat `{...}` as a placeholder if it references the animation
            # variable, or if it looks like a real expression (operators, parens,
            # or function/identifier names). Plain numeric literals are left as-is.
            has_var = bool(re.search(r"\b" + re.escape(var_name) + r"\b", expr_str))
            has_ops_or_parens = bool(re.search(r"[+\-*/^()]", expr_str))
            has_ident = bool(re.search(r"[A-Za-z_]", expr_str))
            # If this is a LaTeX command argument (e.g. \sqrt{...}), only
            # substitute when the placeholder actually references the animation
            # variable. This preserves common constructs like \frac{1}{2}.
            looks_expr = has_var or (not latex_arg and (has_ops_or_parens or has_ident))

            if not looks_expr:
                out.append(tmp[i : j + 1])
                i = j + 1
                continue

            try:
                val = eval(expr_str, ns)
                # Normalize numpy scalars etc.
                try:
                    val_num = float(val)
                except Exception:
                    val_num = val

                if fmt_spec:
                    rendered = format(val_num, fmt_spec)
                else:
                    # Match the main substitution formatting.
                    rendered = value_str if expr_str == var_name else str(val_num)
                out.append("{" + rendered + "}" if latex_arg else rendered)
            except Exception:
                # As a conservative fallback: only replace `{var}` / `{var:fmt}`.
                if expr_str == var_name:
                    if fmt_spec:
                        try:
                            rendered = format(var_value, fmt_spec)
                        except Exception:
                            rendered = value_str
                    else:
                        rendered = value_str
                    out.append("{" + rendered + "}" if latex_arg else rendered)
                else:
                    out.append(tmp[i : j + 1])

            i = j + 1

        return "".join(out).replace(lbrace_token, "{").replace(rbrace_token, "}")

    # Process line by line to handle text: lines specially
    lines = content.split("\n")
    result_lines = []

    for line in lines:
        # Check if this is a text: line with quotes
        if line.strip().startswith("text:"):
            # Don't substitute inside quoted strings on text: lines
            # Parse to find quoted sections
            parts = []
            current = ""
            in_quotes = False
            quote_char = None

            for char in line:
                if char in ('"', "'") and (not in_quotes or char == quote_char):
                    if in_quotes:
                        # End of quoted section - don't substitute inside
                        parts.append(("quoted", current))
                        current = ""
                        in_quotes = False
                        quote_char = None
                    else:
                        # Start of quoted section - substitute what we have so far
                        if current:
                            parts.append(("normal", current))
                            current = ""
                        in_quotes = True
                        quote_char = char
                    parts.append(("quote_char", char))
                else:
                    current += char

            if current:
                if in_quotes:
                    parts.append(("quoted", current))
                else:
                    parts.append(("normal", current))

            # Reconstruct line:
            # - substitute bare variable names in non-quoted parts
            # - apply `{var}` / `{var:...}` placeholders inside quoted parts
            pattern = r"\b" + re.escape(var_name) + r"\b"
            reconstructed = ""
            for part_type, part_content in parts:
                if part_type == "normal":
                    reconstructed += re.sub(pattern, value_str, part_content)
                elif part_type == "quoted":
                    reconstructed += _format_text_placeholders(part_content)
                else:
                    reconstructed += part_content

            result_lines.append(reconstructed)
        elif line.strip().startswith("curve:") and var_name == "t":
            # Special case: when the interactive variable is named `t`, it
            # collides with the curve parameter `t`. We must NOT substitute
            # inside the x/y expressions of a `curve:` line, otherwise the
            # curve degenerates into a moving single point per frame.
            #
            # We still want bounds like `(0, t)` to use the interactive value.
            range_pattern = r",\s*\(([^,]+),\s*([^)]+)\)"
            range_match = re.search(range_pattern, line)
            if not range_match:
                pattern = r"\b" + re.escape(var_name) + r"\b"
                result_lines.append(re.sub(pattern, value_str, line))
                continue

            before_range = line[: range_match.start()]
            after_range = line[range_match.end() :]
            t_min_expr = range_match.group(1)
            t_max_expr = range_match.group(2)

            pattern = r"\b" + re.escape(var_name) + r"\b"
            t_min_expr_sub = re.sub(pattern, value_str, t_min_expr)
            t_max_expr_sub = re.sub(pattern, value_str, t_max_expr)
            after_range_sub = re.sub(pattern, value_str, after_range)

            result_lines.append(
                f"{before_range}, ({t_min_expr_sub.strip()}, {t_max_expr_sub.strip()}){after_range_sub}"
            )
        else:
            # For non-text lines, do normal substitution
            pattern = r"\b" + re.escape(var_name) + r"\b"
            result_lines.append(re.sub(pattern, value_str, line))

    return "\n".join(result_lines)


def _substitute_variables(content: str, variables: dict[str, float]) -> str:
    """Substitute multiple interactive variables with their numeric values.

    This is used by the interactive-graph directive when multiple
    ``interactive-var:`` lines are present.

    Notes:
    - For ``text:`` lines, quoted segments support `{expr}` / `{expr:fmt}`
      placeholders evaluated in a namespace containing *all* variables.
    - For ``curve:`` lines, if the variable set includes `t`, we avoid
      substituting `t` inside the x/y expressions (where `t` is the curve
      parameter). We still substitute variables inside the range bounds.
    """

    if not variables:
        return content

    # Precompute formatted strings for bare variable substitution.
    value_strs: dict[str, str] = {}
    for name, val in variables.items():
        if abs(val) < 1e10 and (abs(val) > 1e-4 or val == 0):
            value_strs[name] = f"{val:.10f}".rstrip("0").rstrip(".")
        else:
            value_strs[name] = f"{val:.6e}"

    def _apply_word_subs(text: str, *, skip: set[str] | None = None) -> str:
        out = text
        for name, val_str in value_strs.items():
            if skip and name in skip:
                continue
            pattern = r"\b" + re.escape(name) + r"\b"
            out = re.sub(pattern, val_str, out)
        return out

    def _format_text_placeholders(text: str) -> str:
        if "{" not in text or "}" not in text:
            return text

        # Preserve escaped braces.
        lbrace_token = "\u0000LBRACE\u0000"
        rbrace_token = "\u0000RBRACE\u0000"
        tmp = text.replace("{{", lbrace_token).replace("}}", rbrace_token)

        ns = _get_safe_namespace(**variables)

        def _is_latex_command_argument(s: str, lbrace_index: int) -> bool:
            j = lbrace_index - 1
            while j >= 0 and s[j].isspace():
                j -= 1
            if j < 0:
                return False
            k = j
            while k >= 0 and s[k].isalpha():
                k -= 1
            return k >= 0 and s[k] == "\\" and k < j

        def _split_expr_and_format(inner: str) -> tuple[str, str | None]:
            depth = 0
            for idx, ch in enumerate(inner):
                if ch in "([":
                    depth += 1
                elif ch in ")]":
                    depth = max(0, depth - 1)
                elif ch == ":" and depth == 0:
                    return inner[:idx].strip(), inner[idx + 1 :].strip()
            return inner.strip(), None

        out_chars: list[str] = []
        i = 0
        while i < len(tmp):
            ch = tmp[i]
            if ch != "{":
                out_chars.append(ch)
                i += 1
                continue

            j = tmp.find("}", i + 1)
            if j == -1:
                out_chars.append(ch)
                i += 1
                continue

            latex_arg = _is_latex_command_argument(tmp, i)
            inner = tmp[i + 1 : j].strip()
            if not inner:
                out_chars.append(tmp[i : j + 1])
                i = j + 1
                continue

            # If the placeholder contains LaTeX commands, treat it as literal.
            if "\\" in inner:
                out_chars.append(tmp[i : j + 1])
                i = j + 1
                continue

            expr_str, fmt_spec = _split_expr_and_format(inner)

            has_any_var = any(
                re.search(r"\b" + re.escape(vn) + r"\b", expr_str) for vn in variables
            )
            has_ops_or_parens = bool(re.search(r"[+\-*/^()]", expr_str))
            has_ident = bool(re.search(r"[A-Za-z_]", expr_str))
            looks_expr = has_any_var or (not latex_arg and (has_ops_or_parens or has_ident))
            if not looks_expr:
                out_chars.append(tmp[i : j + 1])
                i = j + 1
                continue

            try:
                val = eval(expr_str, ns)
                try:
                    val_num = float(val)
                except Exception:
                    val_num = val

                if fmt_spec:
                    rendered = format(val_num, fmt_spec)
                else:
                    # If this is exactly a bare variable, match bare substitution formatting.
                    rendered = value_strs.get(expr_str, str(val_num))
                out_chars.append("{" + rendered + "}" if latex_arg else rendered)
            except Exception:
                # Conservative fallback: only replace `{var}` / `{var:fmt}`.
                if expr_str in variables:
                    if fmt_spec:
                        try:
                            rendered = format(variables[expr_str], fmt_spec)
                        except Exception:
                            rendered = value_strs[expr_str]
                    else:
                        rendered = value_strs[expr_str]
                    out_chars.append("{" + rendered + "}" if latex_arg else rendered)
                else:
                    out_chars.append(tmp[i : j + 1])

            i = j + 1

        return "".join(out_chars).replace(lbrace_token, "{").replace(rbrace_token, "}")

    def _substitute_curve_line(line: str) -> str:
        # Keep this in sync with the `curve:` parsing strategy in AnimateDirective.
        range_pattern = r",\s*\(([^,]+),\s*([^)]+)\)"
        m = re.search(range_pattern, line)
        if not m:
            return _apply_word_subs(line)

        before_range = line[: m.start()].rstrip()
        after_range = line[m.end() :]

        # Split before_range into prefix + x,y parts.
        # Example: "curve: cos(t), sin(a*t)"
        if ":" not in before_range:
            return _apply_word_subs(line)
        prefix, rest = before_range.split(":", 1)
        before_parts = [p.strip() for p in rest.split(",")]
        if len(before_parts) < 2:
            return _apply_word_subs(line)

        x_expr = before_parts[0]
        y_expr = before_parts[1]

        # Substitute all vars except `t` inside x/y.
        x_expr_sub = _apply_word_subs(x_expr, skip={"t"})
        y_expr_sub = _apply_word_subs(y_expr, skip={"t"})

        # Bounds get full substitution (including interactive `t`).
        t_min_expr = _apply_word_subs(m.group(1).strip())
        t_max_expr = _apply_word_subs(m.group(2).strip())

        after_sub = _apply_word_subs(after_range)

        # Preserve the original prefix exactly.
        return f"{prefix}:{x_expr_sub}, {y_expr_sub}, ({t_min_expr}, {t_max_expr}){after_sub}"

    lines = content.split("\n")
    result_lines: list[str] = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("text:"):
            # Match the single-var behavior: do not substitute inside quoted
            # strings except for `{...}` placeholders.
            parts: list[tuple[str, str]] = []
            current = ""
            in_quotes = False
            quote_char: str | None = None

            for ch in line:
                if ch in ('"', "'") and (not in_quotes or ch == quote_char):
                    if in_quotes:
                        parts.append(("quoted", current))
                        current = ""
                        in_quotes = False
                        quote_char = None
                    else:
                        if current:
                            parts.append(("normal", current))
                            current = ""
                        in_quotes = True
                        quote_char = ch
                    parts.append(("quote_char", ch))
                else:
                    current += ch

            if current:
                parts.append(("quoted" if in_quotes else "normal", current))

            reconstructed = ""
            for kind, txt in parts:
                if kind == "normal":
                    reconstructed += _apply_word_subs(txt)
                elif kind == "quoted":
                    reconstructed += _format_text_placeholders(txt)
                else:
                    reconstructed += txt

            result_lines.append(reconstructed)
            continue

        if stripped.startswith("curve:") and "t" in variables:
            result_lines.append(_substitute_curve_line(line))
            continue

        result_lines.append(_apply_word_subs(line))

    return "\n".join(result_lines)


def _hash_key(*parts) -> str:
    """Generate hash key from parts."""
    h = hashlib.sha1()
    for p in parts:
        if p is None:
            p = "__NONE__"
        h.update(str(p).encode("utf-8"))
        h.update(b"||")
    return h.hexdigest()[:12]


class AnimateDirective(SphinxDirective):
    """Sphinx directive for creating animated plots with transparent backgrounds."""

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True

    # Import plot directive's option spec
    from munchboka_edutools.directives.plot import PlotDirective

    option_spec = {
        # Animation-specific options (can be in directive options OR content)
        "animate-var": directives.unchanged,
        "fps": directives.positive_int,
        "duration": directives.positive_int,
        "loop": lambda x: _parse_bool(x, default=True),
        "format": lambda x: directives.choice(x.lower(), ["webp", "gif"]),
        # Back-compat: some users/tests expect plot primitives as directive options.
        # The directive still primarily parses primitives from the content block.
        "function": directives.unchanged,
        "functions": directives.unchanged,
        # Inherit all plot options
        **PlotDirective.option_spec,
    }

    def _parse_kv_block(self) -> Tuple[Dict[str, Any], Dict[str, List[str]], int]:
        """Parse content block similar to plot directive.

        Returns: (scalars, lists, caption_idx)
        """
        lines = list(self.content)
        scalars: Dict[str, Any] = {}
        lists: Dict[str, List[str]] = {
            "function": [],
            "point": [],
            "annotate": [],
            "text": [],
            "vline": [],
            "hline": [],
            "line": [],
            "tangent": [],
            "polygon": [],
            "axis": [],
            "fill-polygon": [],
            "bar": [],
            "vector": [],
            "line-segment": [],
            "angle-arc": [],
            "circle": [],
            "ellipse": [],
            "curve": [],
        }

        # YAML-like fenced front matter
        if lines and lines[0].strip() == "---":
            idx = 1
            while idx < len(lines) and lines[idx].strip() != "---":
                line = lines[idx].rstrip()
                if not line.strip():
                    idx += 1
                    continue
                m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
                if m:
                    key, value = m.group(1), m.group(2)
                    if key in lists:
                        lists[key].append(value)
                    else:
                        scalars[key] = value
                idx += 1
            # Skip closing fence if present
            if idx < len(lines) and lines[idx].strip() == "---":
                idx += 1
            # Skip trailing blanks before caption
            while idx < len(lines) and not lines[idx].strip():
                idx += 1
            return scalars, lists, idx

        # Fallback: non-fenced lines until first non "key: value" or a blank separator
        caption_start = 0
        for i, line in enumerate(lines):
            if not line.strip():
                caption_start = i + 1
                continue
            m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
            if m:
                key, value = m.group(1), m.group(2)
                if key in lists:
                    lists[key].append(value)
                else:
                    scalars[key] = value
                caption_start = i + 1
            else:
                break
        return scalars, lists, caption_start

    def run(self) -> List[nodes.Node]:
        """Generate animated plot."""

        env = self.state.document.settings.env
        app = env.app

        # Parse content block (like plot directive)
        scalars, lists, caption_idx = self._parse_kv_block()

        # Merge with directive options (directive options take precedence)
        merged: Dict[str, Any] = {**scalars, **self.options}

        # Parse animation variable from merged options
        animate_var_spec = merged.get("animate-var")
        if not animate_var_spec:
            return [
                self.state_machine.reporter.error(
                    "animate directive requires 'animate-var' option",
                    line=self.lineno,
                )
            ]

        try:
            var_name, var_values = _parse_animate_var(str(animate_var_spec))
        except ValueError as e:
            return [
                self.state_machine.reporter.error(
                    f"Error parsing animate-var: {e}",
                    line=self.lineno,
                )
            ]

        # Get animation options from merged dict
        output_format = str(merged.get("format", "webp")).lower()
        fps = int(merged.get("fps", 10))
        duration_ms = merged.get("duration")
        if duration_ms:
            duration_ms = int(duration_ms)
        loop = _parse_bool(merged.get("loop"), default=True)

        # Calculate frame duration
        if duration_ms is not None:
            frame_duration = duration_ms
        else:
            frame_duration = int(1000 / fps)

        # Animation-specific keys to exclude from plot content
        animation_keys = {"animate-var", "fps", "duration", "loop", "format"}

        # Prepare content for plot directive - only non-animation keys
        content_lines = list(self.content)

        # Get caption lines
        caption_lines = content_lines[caption_idx:] if caption_idx < len(content_lines) else []

        # Filter plot content to exclude animation-specific keys
        plot_content_lines = []
        for i, line in enumerate(content_lines):
            if i >= caption_idx:
                break  # Stop at caption
            line_stripped = line.strip()
            if not line_stripped:
                continue
            # Check if this is an animation-specific key
            m = re.match(r"^([A-Za-z_][\w-]*)\s*:", line)
            if m:
                key = m.group(1)
                if key in animation_keys:
                    continue  # Skip animation keys
            plot_content_lines.append(line)

        # Generate hash for caching
        content_for_hash = "\n".join(plot_content_lines)
        hash_key = _hash_key(
            animate_var_spec,
            output_format,
            frame_duration,
            loop,
            content_for_hash,
            str(merged),
        )

        # Check for explicit name
        explicit_name = merged.get("name")
        base_name = explicit_name or f"animate_{hash_key}"

        # Setup output paths
        rel_dir = os.path.join("_static", "animate")
        abs_dir = os.path.join(app.srcdir, rel_dir)
        os.makedirs(abs_dir, exist_ok=True)

        output_filename = f"{base_name}.{output_format}"
        abs_output = os.path.join(abs_dir, output_filename)

        # Check if regeneration needed
        nocache = "nocache" in merged
        regenerate = nocache or not os.path.exists(abs_output)

        if regenerate:
            try:
                # Generate animation
                self._generate_animation(
                    app,
                    var_name,
                    var_values,
                    plot_content_lines,
                    abs_output,
                    output_format,
                    frame_duration,
                    loop,
                    merged,  # Pass merged options
                )
            except Exception as e:
                return [
                    self.state_machine.reporter.error(
                        f"Error generating animation: {e}",
                        line=self.lineno,
                    )
                ]

        # Register dependency
        env.note_dependency(abs_output)

        # Copy to build output
        try:
            build_static_dir = os.path.join(app.outdir, "_static", "animate")
            os.makedirs(build_static_dir, exist_ok=True)
            build_output = os.path.join(build_static_dir, output_filename)
            shutil.copy2(abs_output, build_output)
        except Exception:
            pass  # Non-fatal if copy fails during build

        # Create output node
        rel_path = os.path.join("_static", "animate", output_filename)
        uri = "/" + rel_path.replace(os.sep, "/")

        # Build figure node
        figure = nodes.figure()
        figure.setdefault("classes", []).extend(
            ["adaptive-figure", "animate-figure", "no-click", "no-scaled-link"]
        )

        # Get width and align options from merged dict
        width = merged.get("width", "80%")
        align = merged.get("align", "center")
        figure["align"] = align

        # Create image node
        img_node = nodes.image()
        img_node["uri"] = uri
        img_node["alt"] = merged.get("alt", "Animated plot")

        # Add no-click classes to prevent clickable links
        img_node.setdefault("classes", []).extend(["no-click", "no-scaled-link"])

        # Set width
        if isinstance(width, str) and width.strip().endswith("%"):
            img_node["width"] = width
        elif width:
            img_node["width"] = str(width) if not str(width).endswith("px") else width

        # Add CSS classes
        extra_classes = merged.get("class", [])
        if extra_classes:
            if isinstance(extra_classes, str):
                extra_classes = [extra_classes]
            figure["classes"].extend(extra_classes)

        figure += img_node

        # Add caption if present
        while caption_lines and not caption_lines[0].strip():
            caption_lines.pop(0)
        if caption_lines:
            caption = nodes.caption()
            caption_text = "\n".join(caption_lines)
            parsed_nodes, messages = self.state.inline_text(caption_text, self.lineno)
            caption.extend(parsed_nodes)
            figure += caption

        if explicit_name:
            self.add_name(figure)

        return [figure]

    def _generate_animation(
        self,
        app,
        var_name: str,
        var_values: List[float],
        plot_content_lines: List[str],
        output_path: str,
        output_format: str,
        frame_duration: int,
        loop: bool,
        merged_options: Dict[str, Any],
    ) -> None:
        """Generate animation by creating frames and assembling them.

        Args:
            app: Sphinx application
            var_name: Animation variable name
            var_values: List of values for animation variable
            plot_content_lines: Content lines for plot directive
            output_path: Path to save animation
            output_format: 'webp' or 'gif'
            frame_duration: Duration per frame in milliseconds
            loop: Whether to loop animation
            merged_options: Merged directive options and content scalars
        """
        import matplotlib

        matplotlib.use("Agg")

        # Create temporary directory for frames
        with tempfile.TemporaryDirectory() as tmpdir:
            frame_paths = []

            # Generate each frame
            for i, value in enumerate(var_values):
                # Substitute variable in content
                frame_content = "\n".join(plot_content_lines)
                frame_content = _substitute_variable(frame_content, var_name, value)

                # Generate SVG for this frame
                svg_path = os.path.join(tmpdir, f"frame_{i:04d}.svg")
                self._generate_frame_svg(
                    app,
                    frame_content,
                    svg_path,
                    merged_options,
                    var_name,
                    value,
                )

                # Convert SVG to PNG with transparency
                png_path = os.path.join(tmpdir, f"frame_{i:04d}.png")
                self._svg_to_png(svg_path, png_path)

                frame_paths.append(png_path)

            # Assemble frames into animation
            if output_format == "gif":
                self._create_gif(frame_paths, output_path, frame_duration, loop)
            else:  # webp
                self._create_webp(frame_paths, output_path, frame_duration, loop)

    def _generate_frame_svg(
        self,
        app,
        content: str,
        output_path: str,
        options: Dict[str, Any],
        var_name: str,
        var_value: float,
    ) -> None:
        """Generate SVG for a single frame by calling plot directive code directly.

        Args:
            app: Sphinx application
            content: Frame content (with variable substituted)
            output_path: Path to save SVG
            options: Directive options
            var_name: Animation variable name
            var_value: Current value of animation variable
        """
        # Import the full plot directive to use its complete generation logic
        import sys
        import importlib

        # Import plot module
        try:
            plot_module = importlib.import_module("munchboka_edutools.directives.plot")
        except ImportError:
            # Fallback to local _ext if in matematikk_r1/r2
            plot_module = importlib.import_module("_ext.plot")

        # Create a mock directive instance to parse content and generate SVG
        # We'll use the PlotDirective's internal content parsing and SVG generation
        from docutils.parsers.rst import directives as rst_directives
        from docutils.statemachine import StringList

        # Create content list from our frame content
        content_lines = content.strip().split("\n")

        # Parse the content using the same logic as plot directive
        scalars_dict = {}
        lists_dict = {
            "function": [],
            "point": [],
            "annotate": [],
            "text": [],
            "vline": [],
            "hline": [],
            "line": [],
            "tangent": [],
            "polygon": [],
            "axis": [],
            "fill-polygon": [],
            "bar": [],
            "vector": [],
            "line-segment": [],
            "angle-arc": [],
            "circle": [],
            "ellipse": [],
            "curve": [],
        }

        for line in content_lines:
            line = line.strip()
            if not line or ":" not in line:
                continue
            m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
            if m:
                key, value = m.group(1), m.group(2)
                if key in lists_dict:
                    lists_dict[key].append(value)
                else:
                    scalars_dict[key] = value

        # Merge with options
        merged = {**scalars_dict, **options}

        # Now call the plot generation code directly
        # This is essentially what the plot directive does internally
        import matplotlib

        matplotlib.use("Agg")

        try:
            import plotmath
        except ImportError:
            from munchboka_edutools import _plotmath_shim as plotmath

        # Import the actual plot generation logic from plot.py
        # The plot directive has a massive run() method that does all the work
        # We need to essentially replicate its SVG generation part

        # Actually, let's take a different approach: write content to a temp file
        # and use matplotlib + plotmath directly with the full plot directive's logic

        # Import necessary plot directive functions
        import numpy as np

        # We'll need to import the _compile_function and other helpers from plot.py
        # and then run through all the rendering logic

        # Since this is getting complex, let's use a simpler approach:
        # Write the content as a temporary markdown file and have Sphinx process it
        # NO - that's even more complex

        # Best approach: Copy the core logic from PlotDirective.run() that generates the SVG
        # This is a significant amount of code, but it's the only way to get full compatibility

        # For now, let's at least handle tangent lines which is what the user needs
        # We can import the plot directive's code generation

        # Actually, the simplest solution: generate a Python script that uses plotmath
        # directly to create the figure, then save it

        # Let me try a hybrid approach: use plotmath for the figure, but parse
        # all the directives properly

        # Now generate the SVG using the parsed content
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        # Enable LaTeX rendering for consistent math formatting
        plt.rcParams["text.usetex"] = True
        plt.rcParams["text.latex.preamble"] = r"\usepackage{amsmath}"

        try:
            import plotmath
        except ImportError:
            from munchboka_edutools import _plotmath_shim as plotmath
        import numpy as np

        # Import plot directive helpers
        from munchboka_edutools.directives import plot as plot_module

        # Extract plot parameters
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
        fontsize = int(_f("fontsize", 20))
        lw = _f("lw", 2.5)
        figsize_raw = merged.get("figsize")

        def _parse_figsize(val):
            if val in (None, ""):
                return None
            # Already a 2-tuple/list
            if isinstance(val, (list, tuple)) and len(val) == 2:
                try:
                    return (float(val[0]), float(val[1]))
                except Exception:
                    return None
            if not isinstance(val, str):
                return None
            s = val.strip()
            if not s:
                return None
            # Allow "6,4" shorthand
            if re.match(r"^[-+]?\d+(?:\.\d+)?\s*,\s*[-+]?\d+(?:\.\d+)?$", s):
                try:
                    a, b = s.split(",", 1)
                    return (float(a.strip()), float(b.strip()))
                except Exception:
                    return None
            # Allow literal tuple/list like "(6, 4)" or "[6,4]"
            try:
                import ast

                lit = ast.literal_eval(s)
                if isinstance(lit, (list, tuple)) and len(lit) == 2:
                    return (float(lit[0]), float(lit[1]))
            except Exception:
                return None
            return None

        parsed_figsize = _parse_figsize(figsize_raw)
        alpha_val = merged.get("alpha", 1.0)
        if alpha_val:
            alpha_val = float(alpha_val)

        grid_flag = str(merged.get("grid", "true")).lower() in ("true", "yes", "on", "1")
        ticks_flag = str(merged.get("ticks", "true")).lower() in ("true", "yes", "on", "1")

        # Parse axis commands (similar to plot directive)
        axis_cmds = lists_dict.get("axis", [])
        axis_off = any(str(c).lower() == "off" for c in axis_cmds)
        axis_equal = any(str(c).lower() == "equal" for c in axis_cmds)

        # Create figure based on axis flags
        if axis_off:
            # Create a plain figure with axes hidden (no ticks/grid)
            import matplotlib.pyplot as _plt

            fig, ax = _plt.subplots()
            fig.set_size_inches(6.0, 6.0)
            ax.set_xlim(xmin, xmax)
            ax.set_ylim(ymin, ymax)
            try:
                ax.axis("off")
            except Exception:
                pass
            # Apply equal aspect if requested
            if axis_equal:
                try:
                    ax.axis("equal")
                except Exception:
                    pass
        else:
            # Standard path: use plotmath for ticks, grid, labels
            fig, ax = plotmath.plot(
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
                lw=lw,
                alpha=alpha_val if alpha_val else 1.0,
                fontsize=fontsize,
            )
            # If equal requested (without off), apply after plot creation
            if axis_equal:
                try:
                    ax.axis("equal")
                except Exception:
                    pass

        # Process functions with robust domain/endpoint support
        function_dict = {}
        endpoint_markers_flag = merged.get("function-endpoints", False)
        if isinstance(endpoint_markers_flag, str):
            endpoint_markers_flag = endpoint_markers_flag.lower() in ("true", "yes", "1")

        for fn_spec in lists_dict.get("function", []):
            # Parse function with domain, exclusions, and endpoint markers
            expr, func_label, domain, excludes, color, endpoints = _parse_function_item(
                fn_spec, xmin, xmax
            )

            try:
                func = plot_module._compile_function(expr)

                # Determine x range: use domain if specified, otherwise use plot bounds
                if domain is not None:
                    x_domain_min, x_domain_max = domain
                else:
                    x_domain_min, x_domain_max = xmin, xmax

                # Generate x values within domain
                x = np.linspace(x_domain_min, x_domain_max, 1024)
                y = func(x)

                # Apply exclusions: mask out values near excluded points
                if excludes:
                    for excl_val in excludes:
                        # Mask out points within a small tolerance of excluded values
                        tolerance = (x_domain_max - x_domain_min) / 1000.0
                        mask = np.abs(x - excl_val) < tolerance
                        y = np.where(mask, np.nan, y)

                # Store function for later reference (e.g., in points or tangents)
                if func_label:
                    function_dict[func_label] = func

                # Resolve color using plotmath.COLORS if available
                resolved_color = None
                if color:
                    try:
                        resolved_color = plotmath.COLORS.get(color)
                        if resolved_color is None:
                            # If not in plotmath.COLORS, use the color string as-is
                            # (matplotlib will handle it)
                            resolved_color = color
                    except Exception:
                        resolved_color = color

                # Plot function with label and color
                plot_kwargs = {
                    "lw": lw,
                    "alpha": alpha_val if alpha_val else 0.8,
                }
                if func_label:
                    plot_kwargs["label"] = "${}$".format(func_label)
                if resolved_color:
                    plot_kwargs["color"] = resolved_color

                ax.plot(x, y, **plot_kwargs)

                # Draw endpoint markers if enabled
                if endpoint_markers_flag and endpoints:
                    left_type, right_type = endpoints
                    # Use the same resolved color for markers, or let matplotlib use its default
                    color_for_marker = resolved_color if resolved_color else None

                    # Draw left endpoint marker
                    if left_type in ["closed", "open"]:
                        # Check if there's at least one finite point near the left endpoint
                        has_nearby_finite = any(np.isfinite(y[i]) for i in range(min(10, len(y))))
                        if has_nearby_finite:
                            _draw_endpoint_marker(
                                ax, x, y, 0, left_type, "left", color_for_marker, lw
                            )

                    # Draw right endpoint marker
                    if right_type in ["closed", "open"]:
                        # Check if there's at least one finite point near the right endpoint
                        has_nearby_finite = any(
                            np.isfinite(y[i]) for i in range(max(0, len(y) - 10), len(y))
                        )
                        if has_nearby_finite:
                            _draw_endpoint_marker(
                                ax, x, y, -1, right_type, "right", color_for_marker, lw
                            )
            except Exception as e:
                pass

        # Process points (including f(a) notation)
        for pt_spec in lists_dict.get("point", []):
            try:
                # Parse point like "(a, f(a))" or "a, f(a)"
                pt_spec = pt_spec.strip()
                if pt_spec.startswith("(") and pt_spec.endswith(")"):
                    pt_spec = pt_spec[1:-1]

                parts = pt_spec.split(",")
                if len(parts) == 2:
                    x_expr = parts[0].strip()
                    y_expr = parts[1].strip()

                    # Evaluate x
                    namespace = _get_safe_namespace(**{var_name: var_value})
                    x_val = eval(x_expr, namespace)

                    # Evaluate y - might reference a user-defined function
                    if "(" in y_expr:
                        # Check if it's a reference to a user-defined function like f(a)
                        func_name = y_expr.split("(")[0].strip()
                        if func_name in function_dict:
                            # Use the compiled function
                            y_val = function_dict[func_name](x_val)
                        else:
                            # It's a math expression like sin(a), cos(a), etc.
                            y_val = eval(y_expr, namespace)
                    else:
                        y_val = eval(y_expr, namespace)

                    ax.plot(x_val, y_val, "o", markersize=10, alpha=0.8, color="black")
            except Exception as e:
                pass

        # Process tangent lines
        for tang_spec in lists_dict.get("tangent", []):
            try:
                # Parse tangent: x, func_label, style, color
                parts = [p.strip() for p in tang_spec.split(",")]
                if len(parts) < 2:
                    continue

                x_expr = parts[0]
                func_label = parts[1]
                style = parts[2] if len(parts) > 2 else "solid"
                color = parts[3] if len(parts) > 3 else None

                # Evaluate x position
                namespace = _get_safe_namespace(**{var_name: var_value})
                x_val = eval(x_expr, namespace)

                # Get function
                if func_label in function_dict:
                    func = function_dict[func_label]

                    # Calculate derivative numerically
                    h = 0.0001
                    y_val = func(x_val)
                    slope = (func(x_val + h) - func(x_val - h)) / (2 * h)

                    # Draw tangent line
                    x_line = np.array([xmin, xmax])
                    y_line = slope * (x_line - x_val) + y_val

                    style_map = {"solid": "-", "dashed": "--", "dotted": ":", "dashdot": "-."}
                    ls = style_map.get(style.lower(), "-")

                    plot_kwargs = {"linestyle": ls, "lw": lw}
                    if color:
                        # Try to resolve color through plotmath
                        try:
                            resolved_color = plotmath.COLORS.get(color, color)
                            plot_kwargs["color"] = resolved_color
                        except:
                            plot_kwargs["color"] = color

                    ax.plot(x_line, y_line, **plot_kwargs)
            except Exception as e:
                pass

        # Process general lines (same semantics as plot directive)
        # line: a, b[, linestyle][, color]               -> y = a*x + b
        # line: a, (x0, y0)[, linestyle][, color]        -> y = a*(x - x0) + y0
        # line: (x1, y1), (x2, y2)[, linestyle][, color] -> line through two points
        try:
            _allowed_styles_line = {"solid", "dotted", "dashed", "dashdot"}
            style_map_line = {
                "solid": "-",
                "dotted": ":",
                "dashed": "--",
                "dashdot": "-.",
            }

            def _build_eval_namespace_lines():
                ns = _get_safe_namespace(**{var_name: var_value})

                # Provide scalar-friendly wrappers for user-defined functions (from function labels)
                for _fname, _f in function_dict.items():

                    def make_scalar_func(f):
                        def scalar_func(x):
                            if np.isscalar(x):
                                return float(f(np.array([x]))[0])
                            return f(x)

                        return scalar_func

                    ns[_fname] = make_scalar_func(_f)
                return ns

            eval_namespace_lines = _build_eval_namespace_lines()

            def _split_top_level_commas(s: str) -> List[str]:
                s = str(s or "").strip()
                if not s:
                    return []
                # Only strip outer brackets/parens if they enclose the entire expression
                depth = 0
                has_top_level_comma = False
                for ch in s:
                    if ch in "([{":
                        depth += 1
                    elif ch in ")]}":
                        depth = max(0, depth - 1)
                    elif ch == "," and depth == 0:
                        has_top_level_comma = True
                        break
                if not has_top_level_comma:
                    if (s.startswith("[") and s.endswith("]")) or (
                        s.startswith("(") and s.endswith(")")
                    ):
                        s = s[1:-1].strip()

                out: List[str] = []
                cur: List[str] = []
                depth = 0
                for ch in s:
                    if ch in "([{":
                        depth += 1
                        cur.append(ch)
                    elif ch in ")]}":
                        depth = max(0, depth - 1)
                        cur.append(ch)
                    elif ch == "," and depth == 0:
                        part = "".join(cur).strip()
                        if part:
                            out.append(part)
                        cur = []
                    else:
                        cur.append(ch)
                tail = "".join(cur).strip()
                if tail:
                    out.append(tail)
                return out

            def _extract_coord_pairs_from_line(s: str) -> List[Tuple[str, str]]:
                """Extract up to 2 coordinate pairs (x_expr, y_expr) from a line spec."""
                s = str(s or "")
                pairs: List[Tuple[str, str]] = []
                i = 0
                n = len(s)
                while i < n and len(pairs) < 2:
                    if s[i] != "(":
                        i += 1
                        continue
                    depth = 1
                    j = i + 1
                    while j < n and depth > 0:
                        if s[j] == "(":
                            depth += 1
                        elif s[j] == ")":
                            depth -= 1
                        j += 1
                    if depth != 0:
                        break
                    inner = s[i + 1 : j - 1]
                    # Split inner by top-level comma
                    d2 = 0
                    cur = []
                    parts_inner: List[str] = []
                    for ch in inner:
                        if ch in "([":
                            d2 += 1
                            cur.append(ch)
                        elif ch in ")]":
                            d2 = max(0, d2 - 1)
                            cur.append(ch)
                        elif ch == "," and d2 == 0:
                            parts_inner.append("".join(cur).strip())
                            cur = []
                        else:
                            cur.append(ch)
                    if cur:
                        parts_inner.append("".join(cur).strip())
                    if len(parts_inner) == 2 and all(p.strip() for p in parts_inner):
                        pairs.append((parts_inner[0], parts_inner[1]))
                    i = j
                return pairs

            default_line_color = plotmath.COLORS.get("red") or "red"
            x_line = np.array([xmin, xmax], dtype=float)

            for l in lists_dict.get("line", []):
                try:
                    raw = str(l).strip()
                    if not raw:
                        continue

                    a_val: float | None = None
                    b_val: float | None = None
                    style_line: str | None = None
                    color_line: str | None = None

                    # Detect new syntax: two coordinate pairs
                    pairs = _extract_coord_pairs_from_line(raw)
                    if len(pairs) >= 2:
                        x1 = float(eval(pairs[0][0], eval_namespace_lines))
                        y1 = float(eval(pairs[0][1], eval_namespace_lines))
                        x2 = float(eval(pairs[1][0], eval_namespace_lines))
                        y2 = float(eval(pairs[1][1], eval_namespace_lines))
                        if abs(x2 - x1) <= 1e-12:
                            # Vertical line is handled by vline; skip here.
                            continue
                        a_val = (y2 - y1) / (x2 - x1)
                        b_val = y1 - a_val * x1

                        # Remove the two coordinate tuples and parse remaining extras
                        rest = raw
                        for _ in range(2):
                            rest = re.sub(r"\([^()]*?,[^()]*?\)", "", rest, count=1)
                        rest = re.sub(r",{2,}", ",", rest).strip().strip(",")
                        tokens = [t.strip().strip("\"'") for t in rest.split(",") if t.strip()]
                        for tok in tokens:
                            low = tok.lower()
                            if low in _allowed_styles_line and style_line is None:
                                style_line = low
                            elif color_line is None:
                                color_line = tok
                    else:
                        # Old syntax: a, b OR a, (x0, y0)
                        parts = _split_top_level_commas(raw)
                        if len(parts) < 2:
                            continue

                        a_val = float(eval(parts[0], eval_namespace_lines))
                        second = parts[1].strip()
                        if second.startswith("(") and second.endswith(")"):
                            inner = second[1:-1]
                            inner_parts = _split_top_level_commas(inner)
                            if len(inner_parts) != 2:
                                continue
                            x0 = float(eval(inner_parts[0], eval_namespace_lines))
                            y0 = float(eval(inner_parts[1], eval_namespace_lines))
                            b_val = y0 - a_val * x0
                        else:
                            b_val = float(eval(second, eval_namespace_lines))

                        for extra in parts[2:]:
                            tok = str(extra).strip().strip("\"'")
                            if not tok:
                                continue
                            low = tok.lower()
                            if low in _allowed_styles_line and style_line is None:
                                style_line = low
                            elif color_line is None:
                                color_line = tok

                    if a_val is None or b_val is None:
                        continue

                    ls = style_map_line.get((style_line or "dashed").lower(), "--")
                    mapped = plotmath.COLORS.get(color_line) if color_line else None
                    col_use = (mapped if mapped else color_line) or default_line_color
                    y_line = a_val * x_line + b_val
                    ax.plot(x_line, y_line, linestyle=ls, color=col_use, lw=lw, alpha=alpha_val)
                except Exception:
                    pass

            if lists_dict.get("line"):
                try:
                    ax.set_xlim(xmin, xmax)
                    ax.set_ylim(ymin, ymax)
                except Exception:
                    pass
        except Exception:
            pass

        # Process parametric curves
        for curve_spec in lists_dict.get("curve", []):
            try:
                # Parse curve: x_expr, y_expr, (t_min, t_max), style, color
                # Example: cos(t), sin(t), (0, a), solid, blue
                # This means x(t) = cos(t), y(t) = sin(t), for t in (0, a)

                # Strategy: Find the range by looking for ",\s*\(" pattern (comma followed by opening paren)
                # This ensures we don't match function calls like sin(t)
                range_pattern = r",\s*\(([^,]+),\s*([^)]+)\)"
                range_match = re.search(range_pattern, curve_spec)
                if not range_match:
                    continue

                # Extract everything before the range (excluding the comma)
                before_range = curve_spec[: range_match.start()].strip()
                after_range = curve_spec[range_match.end() :].strip()

                # Parse before range: x_expr, y_expr
                before_parts = [p.strip() for p in before_range.split(",")]
                if len(before_parts) < 2:
                    continue

                x_expr = before_parts[0]
                y_expr = before_parts[1]
                param_var = "t"  # Default parameter name

                # If the interactive variable is also named "t", it collides with
                # the curve parameter and turns the curve into a single point.
                # In that case, interpret "t" inside x/y expressions as the curve
                # parameter, while allowing bounds like (0, t) to still refer to
                # the interactive variable.
                x_expr_eval = x_expr
                y_expr_eval = y_expr
                if var_name == param_var:
                    param_var = "__curve_t"
                    x_expr_eval = re.sub(r"\bt\b", param_var, x_expr)
                    y_expr_eval = re.sub(r"\bt\b", param_var, y_expr)

                # Parse range
                t_min_expr = range_match.group(1).strip()
                t_max_expr = range_match.group(2).strip()

                # Parse after range: style, color (optional)
                after_parts = [p.strip() for p in after_range.split(",") if p.strip()]
                style = after_parts[0] if len(after_parts) > 0 else "solid"
                color = after_parts[1] if len(after_parts) > 1 else None

                # Evaluate range limits
                eval_namespace = _get_safe_namespace(**{var_name: var_value})
                t_min = eval(t_min_expr, eval_namespace)
                t_max = eval(t_max_expr, eval_namespace)

                # Generate parameter values and evaluate vectorized.
                # Vectorized eval avoids per-point eval failures and produces
                # a proper polyline in the SVG (instead of a degenerate single point).
                t_vals = np.linspace(t_min, t_max, 1024)
                param_namespace = _get_safe_namespace(
                    **{
                        param_var: t_vals,
                        var_name: var_value,
                    }
                )
                x_vals = eval(x_expr_eval, param_namespace)
                y_vals = eval(y_expr_eval, param_namespace)

                # Normalize to 1D numpy arrays.
                x_vals = np.asarray(x_vals)
                y_vals = np.asarray(y_vals)
                if x_vals.shape == ():
                    x_vals = np.full_like(t_vals, float(x_vals))
                if y_vals.shape == ():
                    y_vals = np.full_like(t_vals, float(y_vals))

                if x_vals.shape != y_vals.shape or x_vals.size < 2:
                    continue

                # Drop non-finite points.
                mask = np.isfinite(x_vals) & np.isfinite(y_vals)
                if mask.sum() < 2:
                    continue
                x_vals = x_vals[mask]
                y_vals = y_vals[mask]

                # Plot the curve
                style_map = {"solid": "-", "dashed": "--", "dotted": ":", "dashdot": "-."}
                ls = style_map.get(style.lower(), "-")

                plot_kwargs = {"linestyle": ls, "lw": lw}
                if color:
                    try:
                        resolved_color = plotmath.COLORS.get(color, color)
                        plot_kwargs["color"] = resolved_color
                    except:
                        plot_kwargs["color"] = color

                ax.plot(x_vals, y_vals, **plot_kwargs)
            except Exception as e:
                pass

        # Process vlines/hlines (same semantics as plot directive)
        # vline: x[, ymin, ymax][, linestyle][, color] (style/color any order)
        # hline: y[, xmin, xmax][, linestyle][, color] (style/color any order)
        try:
            import ast

            def _safe_literal(val: str):
                try:
                    return ast.literal_eval(val)
                except Exception:
                    return None

            def _build_eval_namespace():
                ns = _get_safe_namespace(**{var_name: var_value})

                # Provide scalar-friendly wrappers for user-defined functions (from function labels)
                # so expressions like f(a) can be used in vline/hline specs.
                for _fname, _f in function_dict.items():

                    def make_scalar_func(f):
                        def scalar_func(x):
                            if np.isscalar(x):
                                return float(f(np.array([x]))[0])
                            return f(x)

                        return scalar_func

                    ns[_fname] = make_scalar_func(_f)
                return ns

            _allowed_styles = {"solid", "dotted", "dashed", "dashdot"}
            style_map = {
                "solid": "-",
                "dotted": ":",
                "dashed": "--",
                "dashdot": "-.",
            }
            default_line_color = plotmath.COLORS.get("red") or "red"
            eval_namespace_lines = _build_eval_namespace()

            # vlines
            for v in lists_dict.get("vline", []):
                try:
                    lit = _safe_literal(str(v).strip())
                    if isinstance(lit, (list, tuple)):
                        tokens = [str(x).strip().strip("\"'") for x in lit]
                    else:
                        tokens = [p.strip().strip("\"'") for p in str(v).split(",") if p.strip()]

                    nums: List[float] = []
                    extras: List[str] = []
                    for t in tokens:
                        try:
                            nums.append(float(eval(t, eval_namespace_lines)))
                        except Exception:
                            extras.append(t)

                    if not nums:
                        continue
                    x_v = nums[0]
                    y0 = nums[1] if len(nums) >= 3 else None
                    y1 = nums[2] if len(nums) >= 3 else None

                    st = None
                    col = None
                    for e in extras:
                        el = e.lower()
                        if el in _allowed_styles and st is None:
                            st = e
                        elif col is None:
                            col = e

                    y_min = ymin if y0 is None else y0
                    y_max = ymax if y1 is None else y1
                    ls_val = style_map.get((st or "dashed").lower(), ":")
                    mapped = plotmath.COLORS.get(col) if col else None
                    color_to_try = (mapped if mapped else col) or default_line_color
                    try:
                        ax.vlines(
                            x=x_v,
                            ymin=y_min,
                            ymax=y_max,
                            colors=color_to_try,
                            lw=lw,
                            alpha=1,
                            ls=ls_val,
                        )
                    except Exception:
                        ax.vlines(
                            x=x_v,
                            ymin=y_min,
                            ymax=y_max,
                            colors=default_line_color,
                            lw=lw,
                            alpha=1,
                            ls=ls_val,
                        )
                except Exception:
                    pass

            # hlines
            for h in lists_dict.get("hline", []):
                try:
                    lit = _safe_literal(str(h).strip())
                    if isinstance(lit, (list, tuple)):
                        tokens = [str(x).strip().strip("\"'") for x in lit]
                    else:
                        tokens = [p.strip().strip("\"'") for p in str(h).split(",") if p.strip()]

                    nums_h: List[float] = []
                    extras_h: List[str] = []
                    for t in tokens:
                        try:
                            nums_h.append(float(eval(t, eval_namespace_lines)))
                        except Exception:
                            extras_h.append(t)

                    if not nums_h:
                        continue
                    y_h = nums_h[0]
                    x0 = nums_h[1] if len(nums_h) >= 3 else None
                    x1 = nums_h[2] if len(nums_h) >= 3 else None

                    st_h = None
                    col_h = None
                    for e in extras_h:
                        el = e.lower()
                        if el in _allowed_styles and st_h is None:
                            st_h = e
                        elif col_h is None:
                            col_h = e

                    x_min = xmin if x0 is None else x0
                    x_max = xmax if x1 is None else x1
                    ls_val_h = style_map.get((st_h or "dashed").lower(), ":")
                    mapped_h = plotmath.COLORS.get(col_h) if col_h else None
                    color_to_try_h = (mapped_h if mapped_h else col_h) or default_line_color
                    try:
                        ax.hlines(
                            y=y_h,
                            xmin=x_min,
                            xmax=x_max,
                            colors=color_to_try_h,
                            lw=lw,
                            alpha=1,
                            ls=ls_val_h,
                        )
                    except Exception:
                        ax.hlines(
                            y=y_h,
                            xmin=x_min,
                            xmax=x_max,
                            colors=default_line_color,
                            lw=lw,
                            alpha=1,
                            ls=ls_val_h,
                        )
                except Exception:
                    pass
        except Exception:
            pass

        # Process angle-arcs (circle arcs)
        # angle-arc: (x, y), radius, start_angle_deg, end_angle_deg[, linestyle][, color]
        _allowed_arc_styles = {"solid", "dotted", "dashed", "dashdot"}
        for arc in lists_dict.get("angle-arc", []):
            try:
                raw_arc = str(arc).strip()
                # Find first balanced parenthesis group for center
                idx_arc = raw_arc.find("(")
                if idx_arc == -1:
                    continue
                depth_arc = 0
                end_center = -1
                for j in range(idx_arc, len(raw_arc)):
                    ch = raw_arc[j]
                    if ch == "(":
                        depth_arc += 1
                    elif ch == ")":
                        depth_arc -= 1
                        if depth_arc == 0:
                            end_center = j
                            break
                if end_center == -1:
                    continue
                center_inner = raw_arc[idx_arc + 1 : end_center]
                # Split center_inner by top-level comma
                depth_c = 0
                cur_bits = []
                center_parts = []
                for ch in center_inner:
                    if ch == "(":
                        depth_c += 1
                        cur_bits.append(ch)
                    elif ch == ")":
                        depth_c -= 1
                        cur_bits.append(ch)
                    elif ch == "," and depth_c == 0:
                        token = "".join(cur_bits).strip()
                        if token:
                            center_parts.append(token)
                        cur_bits = []
                    else:
                        cur_bits.append(ch)
                tail_cp = "".join(cur_bits).strip()
                if tail_cp:
                    center_parts.append(tail_cp)
                if len(center_parts) != 2:
                    continue
                rest_arc = raw_arc[end_center + 1 :].lstrip(",").strip()
                if not rest_arc:
                    continue
                # Split rest by top-level commas
                depth_r = 0
                cur_r = []
                tokens_r = []
                for ch in rest_arc:
                    if ch == "(":
                        depth_r += 1
                        cur_r.append(ch)
                    elif ch == ")":
                        depth_r -= 1
                        cur_r.append(ch)
                    elif ch == "," and depth_r == 0:
                        tk = "".join(cur_r).strip()
                        if tk:
                            tokens_r.append(tk)
                        cur_r = []
                    else:
                        cur_r.append(ch)
                tail_r = "".join(cur_r).strip()
                if tail_r:
                    tokens_r.append(tail_r)
                if len(tokens_r) < 3:
                    continue
                radius_expr = tokens_r[0]
                start_expr = tokens_r[1]
                end_expr = tokens_r[2]
                style_arc = None
                color_arc = None
                for extra_tok in tokens_r[3:]:
                    low = extra_tok.lower()
                    if low in _allowed_arc_styles and style_arc is None:
                        style_arc = low
                    elif color_arc is None:
                        color_arc = extra_tok

                # Evaluate expressions with current variable value
                eval_namespace = _get_safe_namespace(**{var_name: var_value})
                cx_val = float(eval(center_parts[0], eval_namespace))
                cy_val = float(eval(center_parts[1], eval_namespace))
                r_val = float(eval(radius_expr, eval_namespace))
                if r_val <= 0:
                    continue
                start_deg_val = float(eval(start_expr, eval_namespace))
                end_deg_val = float(eval(end_expr, eval_namespace))

                # Render the arc
                sa = np.deg2rad(start_deg_val)
                ea = np.deg2rad(end_deg_val)
                theta = np.linspace(sa, ea, 1024)
                xs = cx_val + r_val * np.cos(theta)
                ys = cy_val + r_val * np.sin(theta)

                # Style and color
                style_map_arc = {
                    "solid": "-",
                    "dotted": ":",
                    "dashed": "--",
                    "dashdot": "-.",
                }
                ls_use = style_map_arc.get((style_arc or "solid").lower(), "-")

                # Resolve color via plotmath palette
                default_arc_color = plotmath.COLORS.get("black") or "black"
                if color_arc:
                    mapped_color = plotmath.COLORS.get(color_arc)
                    col_use = mapped_color if mapped_color else color_arc
                else:
                    col_use = default_arc_color

                ax.plot(xs, ys, lw=1, color=col_use, linestyle=ls_use)
            except Exception:
                pass

        # Process line-segments: (x1,y1), (x2,y2)[, linestyle][, color]
        _allowed_seg_styles = {"solid", "dotted", "dashed", "dashdot"}
        for ls in lists_dict.get("line-segment", []):
            try:
                s = str(ls).strip()
                # Extract coordinate pairs using balanced parentheses
                pairs = []
                i = 0
                n = len(s)
                while i < n and len(pairs) < 2:
                    if s[i] == "(":
                        depth = 1
                        j = i + 1
                        while j < n and depth > 0:
                            if s[j] == "(":
                                depth += 1
                            elif s[j] == ")":
                                depth -= 1
                            j += 1
                        if depth == 0:
                            inner = s[i + 1 : j - 1]
                            # Split inner by top-level comma
                            d2 = 0
                            has_comma = False
                            parts_inner = []
                            cur = []
                            for ch in inner:
                                if ch == "(":
                                    d2 += 1
                                    cur.append(ch)
                                elif ch == ")":
                                    d2 -= 1
                                    cur.append(ch)
                                elif ch == "," and d2 == 0:
                                    has_comma = True
                                    parts_inner.append("".join(cur).strip())
                                    cur = []
                                else:
                                    cur.append(ch)
                            if cur:
                                parts_inner.append("".join(cur).strip())

                            if has_comma and len(parts_inner) == 2:
                                pairs.append((parts_inner[0], parts_inner[1]))
                        i = j
                    else:
                        i += 1

                if len(pairs) < 2:
                    continue

                # Evaluate the two points
                eval_namespace = _get_safe_namespace(**{var_name: var_value})
                pcoords = []
                for x_expr, y_expr in pairs[:2]:
                    try:
                        xv = float(eval(x_expr, eval_namespace))
                        yv = float(eval(y_expr, eval_namespace))
                        pcoords.append((xv, yv))
                    except Exception:
                        pcoords = []
                        break

                if len(pcoords) != 2:
                    continue

                # Extract style and color from the rest
                # Find where the second point ends
                spans = []
                depth = 0
                idx = 0
                while idx < n and len(spans) < 2:
                    if s[idx] == "(":
                        depth = 1
                        j_start = idx
                        j = idx + 1
                        while j < n and depth > 0:
                            if s[j] == "(":
                                depth += 1
                            elif s[j] == ")":
                                depth -= 1
                            j += 1
                        if depth == 0:
                            inner = s[j_start + 1 : j - 1]
                            d2 = 0
                            has_comma = False
                            for ch in inner:
                                if ch == "(":
                                    d2 += 1
                                elif ch == ")":
                                    d2 -= 1
                                elif ch == "," and d2 == 0:
                                    has_comma = True
                                    break
                            if has_comma:
                                spans.append((j_start, j))
                        idx = j
                    else:
                        idx += 1

                # Build rest excluding coordinate tuples
                if spans:
                    parts_rest = []
                    last = 0
                    for a, b in spans:
                        if a > last:
                            parts_rest.append(s[last:a])
                        last = b
                    if last < len(s):
                        parts_rest.append(s[last:])
                    rest = "".join(parts_rest)
                else:
                    rest = s

                # Clean and parse tokens
                rest = re.sub(r",{2,}", ",", rest)
                tokens = [tok.strip().strip("'\"") for tok in rest.split(",") if tok.strip()]
                style_seg = None
                color_seg = None
                for tok in tokens:
                    low = tok.lower()
                    if low in _allowed_seg_styles and style_seg is None:
                        style_seg = low
                    elif color_seg is None:
                        color_seg = tok

                # Render the line segment
                (x1s, y1s), (x2s, y2s) = pcoords[0], pcoords[1]
                style_map_seg = {
                    "solid": "-",
                    "dotted": ":",
                    "dashed": "--",
                    "dashdot": "-.",
                }
                ls_use = style_map_seg.get((style_seg or "solid").lower(), "-")

                default_seg_color = plotmath.COLORS.get("black") or "black"
                if color_seg:
                    mapped_seg = plotmath.COLORS.get(color_seg)
                    col_use = mapped_seg if mapped_seg else color_seg
                else:
                    col_use = default_seg_color

                ax.plot([x1s, x2s], [y1s, y2s], linestyle=ls_use, color=col_use, lw=lw)
            except Exception:
                pass

        # Process vectors: support multiple syntaxes
        # 1. Legacy: x, y, dx, dy[, color]
        # 2. Point + components: (x, y), dx, dy[, color]
        # 3. Two points: (x1, y1), (x2, y2)[, color]
        for vline in lists_dict.get("vector", []):
            try:
                s = str(vline).strip()
                # Remove surrounding brackets if present
                if (s.startswith("[") and s.endswith("]")) or (
                    s.startswith("(") and s.endswith(")")
                ):
                    s = s[1:-1].strip()

                # Parse by splitting on top-level commas
                depth_vec = 0
                cur_tok = []
                parts = []
                for ch in s:
                    if ch in "([":
                        depth_vec += 1
                        cur_tok.append(ch)
                    elif ch in ")]":
                        depth_vec -= 1
                        cur_tok.append(ch)
                    elif ch == "," and depth_vec == 0:
                        tok = "".join(cur_tok).strip()
                        if tok:
                            parts.append(tok)
                        cur_tok = []
                    else:
                        cur_tok.append(ch)
                tail_tok = "".join(cur_tok).strip()
                if tail_tok:
                    parts.append(tail_tok)

                if len(parts) < 2:
                    continue

                eval_namespace = _get_safe_namespace(**{var_name: var_value})

                # Check if first part is a coordinate pair
                first_part = parts[0].strip()
                if first_part.startswith("(") and first_part.endswith(")"):
                    # Extract coordinates from first tuple
                    coord_str = first_part[1:-1]
                    coord_parts = coord_str.split(",")
                    if len(coord_parts) != 2:
                        continue
                    x_v = float(eval(coord_parts[0].strip(), eval_namespace))
                    y_v = float(eval(coord_parts[1].strip(), eval_namespace))

                    # Check second part
                    if len(parts) >= 2:
                        second_part = parts[1].strip()
                        if second_part.startswith("(") and second_part.endswith(")"):
                            # Format: (x1, y1), (x2, y2)[, color]
                            coord2_str = second_part[1:-1]
                            coord2_parts = coord2_str.split(",")
                            if len(coord2_parts) != 2:
                                continue
                            x2 = float(eval(coord2_parts[0].strip(), eval_namespace))
                            y2 = float(eval(coord2_parts[1].strip(), eval_namespace))
                            dx_v = x2 - x_v
                            dy_v = y2 - y_v
                            color_v = (
                                parts[2].strip()
                                if len(parts) >= 3 and parts[2].strip()
                                else "black"
                            )
                        elif len(parts) >= 3:
                            # Format: (x, y), dx, dy[, color]
                            dx_v = float(eval(parts[1], eval_namespace))
                            dy_v = float(eval(parts[2], eval_namespace))
                            color_v = (
                                parts[3].strip()
                                if len(parts) >= 4 and parts[3].strip()
                                else "black"
                            )
                        else:
                            continue
                    else:
                        continue
                elif len(parts) >= 4:
                    # Legacy format: x, y, dx, dy[, color]
                    x_v = float(eval(parts[0], eval_namespace))
                    y_v = float(eval(parts[1], eval_namespace))
                    dx_v = float(eval(parts[2], eval_namespace))
                    dy_v = float(eval(parts[3], eval_namespace))
                    color_v = parts[4].strip() if len(parts) >= 5 and parts[4].strip() else "black"
                else:
                    continue

                # Resolve color through palette
                default_vector_color = plotmath.COLORS.get("black") or "black"
                if color_v:
                    mapped_vec = plotmath.COLORS.get(color_v)
                    color_use = mapped_vec if mapped_vec else color_v
                else:
                    color_use = default_vector_color

                # Get axis limits for pixel-to-data conversion
                xlim = ax.get_xlim()
                ylim = ax.get_ylim()
                x_range_vec = xlim[1] - xlim[0]
                y_range_vec = ylim[1] - ylim[0]

                # Get figure size in pixels
                fig_width_inches = fig.get_figwidth()
                fig_height_inches = fig.get_figheight()
                ax_width_px_vec = fig_width_inches * fig.dpi
                ax_height_px_vec = fig_height_inches * fig.dpi

                # Data to pixel conversion factors
                data_to_px_x_vec = ax_width_px_vec / x_range_vec if x_range_vec > 0 else 1
                data_to_px_y_vec = ax_height_px_vec / y_range_vec if y_range_vec > 0 else 1
                px_to_data_x_vec = x_range_vec / ax_width_px_vec if ax_width_px_vec > 0 else 0.01
                px_to_data_y_vec = y_range_vec / ax_height_px_vec if ax_height_px_vec > 0 else 0.01

                # Convert vector components to pixel space
                dx_px = dx_v * data_to_px_x_vec
                dy_px = dy_v * data_to_px_y_vec

                # Get vector length in pixel space
                vec_length_px = np.sqrt(dx_px**2 + dy_px**2)

                if vec_length_px > 1e-10:
                    # Normalize in pixel space
                    dx_px_norm = dx_px / vec_length_px
                    dy_px_norm = dy_px / vec_length_px

                    # Use the original pixel length
                    dx_px_scaled = dx_px_norm * vec_length_px
                    dy_px_scaled = dy_px_norm * vec_length_px

                    # Convert back to data coordinates
                    dx_data = dx_px_scaled * px_to_data_x_vec
                    dy_data = dy_px_scaled * px_to_data_y_vec
                else:
                    # Zero or near-zero vector
                    dx_data = 0
                    dy_data = 0

                # Draw arrow
                ax.quiver(
                    x_v,
                    y_v,
                    dx_data,
                    dy_data,
                    angles="xy",
                    scale_units="xy",
                    scale=1,
                    width=0.006,
                    headwidth=5,
                    headlength=5,
                    color=color_use,
                    zorder=100,
                )
            except Exception:
                pass

        # Process text annotations with f-string support
        for text_spec in lists_dict.get("text", []):
            try:
                # Parse text: x, y, "text string"[, alignment][, bbox]
                # Handle quoted strings that may contain commas and format specs like {a:.2f}
                # bbox can be: "bbox", True, False, or omitted (default False)

                # Find the quoted text section using regex
                # Match: number/expr, number/expr, "quoted text"[, optional tokens...]
                match = re.match(
                    r'^\s*([^,]+)\s*,\s*([^,]+)\s*,\s*(["\'])(.+?)\3\s*(?:,\s*(.+))?\s*$', text_spec
                )

                if not match:
                    continue

                x_expr = match.group(1).strip()
                y_expr = match.group(2).strip()
                text_str = match.group(4)  # Text without quotes
                remaining = match.group(5)  # Everything after the text

                # Parse remaining tokens: can be alignment and/or bbox
                alignment = "center-center"
                bbox_flag = False

                if remaining:
                    # Split by commas to get individual tokens
                    tokens = [t.strip() for t in remaining.split(",")]

                    # Check each token
                    for token in tokens:
                        if not token:
                            continue
                        # Check if it's a bbox indicator
                        if token.lower() == "bbox":
                            bbox_flag = True
                        elif token.lower() in ("true", "yes", "1"):
                            bbox_flag = True
                        elif token.lower() in ("false", "no", "0"):
                            bbox_flag = False
                        else:
                            # Assume it's an alignment specification
                            alignment = token

                # Evaluate x and y positions - include function_dict for function references
                eval_namespace = _get_safe_namespace(**{var_name: var_value})
                # Add scalar-compatible versions of functions
                for func_name, func in function_dict.items():
                    # Wrap function to handle scalar inputs
                    def make_scalar_func(f):
                        def scalar_func(x):
                            if np.isscalar(x):
                                return float(f(np.array([x]))[0])
                            return f(x)

                        return scalar_func

                    eval_namespace[func_name] = make_scalar_func(func)

                try:
                    x_pos = eval(x_expr, eval_namespace)
                    y_pos = eval(y_expr, eval_namespace)
                except:
                    continue

                # Format text with variable value - handle both f-string-like formatting and LaTeX
                formatted_text = text_str

                # Only attempt formatting if there are format placeholders
                if "{" in text_str and "}" in text_str:
                    # Find all LaTeX expressions (anything between $ signs)
                    latex_pattern = r"\$[^$]+\$"
                    latex_matches = []
                    latex_placeholders = []
                    for i, latex_match in enumerate(re.finditer(latex_pattern, text_str)):
                        latex_matches.append(latex_match.group(0))
                        placeholder = f"__LATEX_{i}__"
                        latex_placeholders.append(placeholder)

                    # Replace LaTeX with placeholders
                    temp_text = text_str
                    for i, latex_expr in enumerate(latex_matches):
                        temp_text = temp_text.replace(latex_expr, latex_placeholders[i], 1)

                    # Create namespace for formatting
                    text_namespace = {var_name: var_value, "pi": np.pi, "e": np.e}

                    # Find and evaluate all function calls like g(a) in the temp text
                    func_call_pattern = r"(\w+)\(([^)]+)\)"
                    for func_match in re.finditer(func_call_pattern, temp_text):
                        func_name = func_match.group(1)
                        arg_expr = func_match.group(2)
                        if func_name in eval_namespace:
                            try:
                                arg_val = eval(arg_expr, eval_namespace)
                                result = eval_namespace[func_name](arg_val)
                                text_namespace[func_match.group(0)] = result
                            except:
                                pass

                    # Format the text (with placeholders instead of LaTeX)
                    try:
                        formatted_text = temp_text.format(**text_namespace)
                    except (KeyError, ValueError):
                        # If formatting fails, use original text
                        formatted_text = text_str

                    # Restore LaTeX expressions
                    try:
                        for i, placeholder in enumerate(latex_placeholders):
                            if i < len(latex_matches):
                                formatted_text = formatted_text.replace(
                                    placeholder, latex_matches[i]
                                )
                    except:
                        pass

                    # If the text contains LaTeX and non-LaTeX content mixed, wrap everything in math mode
                    try:
                        if latex_matches and not (
                            formatted_text.startswith("$") and formatted_text.endswith("$")
                        ):
                            # Check if there's text outside of LaTeX expressions
                            temp_check = formatted_text
                            for latex_expr in latex_matches:
                                temp_check = temp_check.replace(latex_expr, "", 1)
                            # If there's remaining text (not just whitespace), we have mixed content
                            if temp_check.strip():
                                # Remove the $ signs from LaTeX parts and wrap the whole thing
                                temp_formatted = formatted_text
                                for latex_expr in latex_matches:
                                    if latex_expr in temp_formatted:
                                        # Remove outer $ signs from the LaTeX expression
                                        inner_latex = latex_expr[1:-1]  # Remove first and last $
                                        temp_formatted = temp_formatted.replace(
                                            latex_expr, inner_latex, 1
                                        )
                                # Wrap entire text in math mode
                                formatted_text = f"${temp_formatted}$"
                    except:
                        # If LaTeX wrapping fails, keep the formatted text as-is
                        pass

                # Parse alignment (e.g., "center-center", "left-bottom", "right-top")
                # Map positioning to matplotlib alignment, inverting for intuitive sense
                # Matplotlib expects the position to refer to where the object is relative to the text
                # We invert it so "top-left" means "place text at top-left of the point"
                alignment_key = alignment.strip().lower().replace("_", "-")

                # Mapping with inverted logic (same as plot directive)
                alignment_map = {
                    "top-left": ("bottom", "right"),
                    "top-right": ("bottom", "left"),
                    "bottom-left": ("top", "right"),
                    "bottom-right": ("top", "left"),
                    "top-center": ("bottom", "center"),
                    "bottom-center": ("top", "center"),
                    "center-left": ("center", "right"),
                    "center-right": ("center", "left"),
                    "center-center": ("center", "center"),
                }

                va, ha = alignment_map.get(alignment_key, ("top", "left"))

                # Prepare bbox kwargs if bbox is requested
                bbox_kwargs = None
                if bbox_flag:
                    bbox_kwargs = dict(
                        boxstyle="round,pad=0.3", facecolor="white", alpha=0.8, edgecolor="none"
                    )

                # Add text to plot
                ax.text(
                    x_pos,
                    y_pos,
                    formatted_text,
                    horizontalalignment=ha,
                    verticalalignment=va,
                    fontsize=fontsize,
                    bbox=bbox_kwargs,
                )
            except Exception:
                # Silently skip text annotations that fail
                pass

        # Handle individual tick control (xticks/yticks off)
        xticks_raw = merged.get("xticks")
        yticks_raw = merged.get("yticks")

        if isinstance(xticks_raw, str) and xticks_raw.strip().lower() == "off":
            try:
                ax.set_xticks([])
            except Exception:
                pass

        if isinstance(yticks_raw, str) and yticks_raw.strip().lower() == "off":
            try:
                ax.set_yticks([])
            except Exception:
                pass

        # Save to SVG
        fig.patch.set_alpha(0)
        ax.patch.set_alpha(0)

        # Apply user figsize at the very end if provided
        if parsed_figsize is not None:
            try:
                fig.set_size_inches(*parsed_figsize)
            except Exception:
                pass

        fig.savefig(
            output_path,
            format="svg",
            bbox_inches="tight",
            transparent=True,
            facecolor="none",
        )
        plt.close(fig)

    def _svg_to_png(self, svg_path: str, png_path: str) -> None:
        """Convert SVG to PNG with transparency using cairosvg.

        Args:
            svg_path: Path to input SVG file
            png_path: Path to output PNG file
        """
        try:
            import cairosvg

            cairosvg.svg2png(
                url=svg_path,
                write_to=png_path,
                background_color=None,  # Transparent background
                dpi=150,  # High DPI for quality
            )
        except ImportError:
            raise ImportError(
                "cairosvg is required for animate directive. "
                "Install it with: pip install cairosvg"
            )

    def _create_gif(
        self,
        frame_paths: List[str],
        output_path: str,
        duration: int,
        loop: bool,
    ) -> None:
        """Create animated GIF from PNG frames.

        Args:
            frame_paths: List of PNG frame paths
            output_path: Path to save GIF
            duration: Frame duration in milliseconds
            loop: Whether to loop (True = infinite loop)
        """
        try:
            from PIL import Image

            images = [Image.open(fp).convert("RGBA") for fp in frame_paths]

            # Save as GIF with transparency
            images[0].save(
                output_path,
                format="GIF",
                save_all=True,
                append_images=images[1:],
                duration=duration,
                loop=0 if loop else 1,  # 0 = infinite, 1 = play once
                disposal=2,  # Clear previous frame
                transparency=0,
                optimize=False,  # Preserve transparency
            )
        except ImportError:
            raise ImportError(
                "Pillow is required for GIF creation. " "Install it with: pip install Pillow"
            )

    def _create_webp(
        self,
        frame_paths: List[str],
        output_path: str,
        duration: int,
        loop: bool,
    ) -> None:
        """Create animated WebP from PNG frames.

        Args:
            frame_paths: List of PNG frame paths
            output_path: Path to save WebP
            duration: Frame duration in milliseconds
            loop: Whether to loop (True = infinite loop)
        """
        try:
            from PIL import Image

            images = [Image.open(fp).convert("RGBA") for fp in frame_paths]

            # Save as WebP with transparency
            images[0].save(
                output_path,
                format="WEBP",
                save_all=True,
                append_images=images[1:],
                duration=duration,
                loop=0 if loop else 1,  # 0 = infinite
                lossless=False,  # Use lossy compression for smaller files
                quality=85,  # Good quality with reasonable file size
                method=4,  # Balance between speed and compression
            )
        except Exception as e:
            # Fallback: try using imageio if Pillow WebP support fails
            try:
                import imageio
                import numpy as np
                from PIL import Image

                # Load frames
                frames = [np.array(Image.open(fp).convert("RGBA")) for fp in frame_paths]

                # Save with imageio
                imageio.mimsave(
                    output_path,
                    frames,
                    format="WEBP",
                    duration=duration / 1000.0,  # imageio uses seconds
                    loop=0 if loop else 1,
                )
            except ImportError:
                raise ImportError(
                    "Pillow with WebP support or imageio is required for WebP creation. "
                    "Install with: pip install Pillow imageio or pip install pillow-webp"
                ) from e


def setup(app):  # pragma: no cover
    app.add_directive("animate", AnimateDirective)
    # Ensure CSS is loaded (reuse plot figure styles)
    try:
        app.add_css_file("munchboka/css/general_style.css")
    except Exception:
        pass
    return {"version": "0.1", "parallel_read_safe": True, "parallel_write_safe": True}
