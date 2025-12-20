"""
Sign Chart Directive for Munchboka Edutools
==========================================

This directive generates sign charts (fortegnsskjema) for polynomial functions
using the external `signchart` package. Sign charts are visual representations
showing where a polynomial function is positive, negative, or zero.

Usage in MyST Markdown:
    ```{signchart}
    ---
    function: x**2 - 4, f(x)
    factors: true
    width: 100%
    ---
    Optional caption text
    ```

Dependencies:
    - signchart: External Python package for generating sign charts
    - matplotlib: Used internally by signchart

Features:
    - Automatic polynomial factorization display
    - Configurable width and alignment
    - SVG output with theme-aware styling
    - Caching for faster builds
    - Accessible with aria-label support

Author: René Aasen (ported from matematikk_r1)
Date: November 2025
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import uuid
from typing import Any, Dict, List, Tuple

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective


# ------------------------------------
# Utilities
# ------------------------------------


def _hash_key(*parts) -> str:
    """
    Generate a short hash key from multiple parts.

    Used for creating unique filenames based on function content.

    Args:
        *parts: Variable number of parts to hash

    Returns:
        str: 12-character hex hash
    """
    h = hashlib.sha1()
    for p in parts:
        if p is None:
            p = "__NONE__"
        h.update(str(p).encode("utf-8"))
        h.update(b"||")
    return h.hexdigest()[:12]


def _safe_literal(val: str):
    """
    Safely evaluate a string as a Python literal.

    Args:
        val: String to evaluate

    Returns:
        Evaluated value or None if evaluation fails
    """
    import ast

    try:
        return ast.literal_eval(val)
    except Exception:
        return None


def _parse_bool(val, default: bool | None = None) -> bool | None:
    """
    Parse a value as a boolean.

    Args:
        val: Value to parse (bool, str, or None)
        default: Default value if parsing fails

    Returns:
        bool | None: Parsed boolean value or default
    """
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


def _strip_root_svg_size(svg_text: str) -> str:
    """
    Remove width/height attributes from the root <svg> tag.

    This allows CSS to control the SVG size.

    Args:
        svg_text: Raw SVG content

    Returns:
        str: SVG with width/height removed from root tag
    """

    def repl(m):
        tag = m.group(0)
        tag = re.sub(r'\swidth="[^"]+"', "", tag)
        tag = re.sub(r'\sheight="[^"]+"', "", tag)
        return tag

    return re.sub(r"<svg\b[^>]*>", repl, svg_text, count=1)


def _rewrite_ids(txt: str, prefix: str) -> str:
    """
    Rewrite all id attributes in SVG to avoid conflicts.

    When multiple SVGs are on the same page, id conflicts can cause
    rendering issues. This function prefixes all ids with a unique prefix.

    Args:
        txt: SVG content
        prefix: Prefix to add to all ids

    Returns:
        str: SVG with rewritten ids
    """
    ids = re.findall(r'\bid="([^"]+)"', txt)
    if not ids:
        return txt
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

    def repl_id(m: re.Match) -> str:
        old = m.group(1)
        new = mapping.get(old, old)
        return f'id="{new}"'

    txt = re.sub(r'\bid="([^"]+)"', repl_id, txt)

    def repl_url(m: re.Match) -> str:
        old = m.group(1).strip()
        new = mapping.get(old, old)
        return f"url(#{new})"

    txt = re.sub(r"url\(#\s*([^\)\s]+)\s*\)", repl_url, txt)

    def repl_href(m: re.Match) -> str:
        attr = m.group(1)
        quote = m.group(2)
        old = m.group(3).strip()
        new = mapping.get(old, old)
        return f"{attr}={quote}#{new}{quote}"

    txt = re.sub(r'(xlink:href|href)\s*=\s*(["\"])#\s*([^"\"]+)\s*\2', repl_href, txt)
    return txt


class SignChartDirective(SphinxDirective):
    """
    Sphinx directive for generating sign charts of polynomial functions.

    This directive uses the `signchart` package to generate visual representations
    showing where a polynomial function is positive, negative, or zero.

    Options:
        function (required): The polynomial expression and optional label
                            Format: "expression, label" or ("expression", "label")
                            Example: "x**2 - 4, f(x)"
        factors (optional): Whether to show factored form (default: true)
        xmin (optional): Minimum x-value for the domain (custom domain)
        xmax (optional): Maximum x-value for the domain (custom domain)
        width (optional): Width of the chart (e.g., "100%", "500px", "500")
        align (optional): Alignment ("left", "center", "right")
        class (optional): Additional CSS classes
        name (optional): Reference name for the figure
        nocache (optional): Force regeneration of the chart
        debug (optional): Keep original SVG dimensions and ids
        alt (optional): Alt text for accessibility (default: "Fortegnsskjema")

    Example:
        ```{signchart}
        ---
        function: x**2 - 4, f(x)
        factors: true
        width: 80%
        ---
        Sign chart for f(x) = x² - 4
        ```

        With custom domain:
        ```{signchart}
        ---
        function: -3/2 * k**2 + 9/2, A'(k)
        xmin: 0
        xmax: 3
        width: 100%
        ---
        Sign chart restricted to domain [0, 3]
        ```
    """

    has_content = True
    required_arguments = 0
    option_spec = {
        # presentation / misc
        "width": directives.length_or_percentage_or_unitless,
        "align": lambda a: directives.choice(a, ["left", "center", "right"]),
        "class": directives.class_option,
        "name": directives.unchanged,
        "nocache": directives.flag,
        "debug": directives.flag,
        "alt": directives.unchanged,
        # specific options
        "function": directives.unchanged_required,  # e.g. "x**2 - 4, f(x)"
        "factors": directives.unchanged,  # default True
        "xmin": directives.unchanged,  # custom domain minimum
        "xmax": directives.unchanged,  # custom domain maximum
    }

    def _parse_kv_block(self) -> Tuple[Dict[str, Any], int]:
        """
        Parse YAML-style key-value block from directive content.

        Supports two formats:
        1. YAML front-matter style with --- delimiters
        2. Simple key: value pairs at the start

        Returns:
            tuple: (dict of parsed options, index where caption starts)
        """
        lines = list(self.content)
        scalars: Dict[str, Any] = {}
        idx = 0
        if lines and lines[0].strip() == "---":
            idx = 1
            while idx < len(lines) and lines[idx].strip() != "---":
                line = lines[idx].rstrip()
                if not line.strip():
                    idx += 1
                    continue
                m = re.match(r"^([A-Za-z_][\w]*)\s*:\s*(.*)$", line)
                if m:
                    scalars[m.group(1)] = m.group(2)
                idx += 1
            if idx < len(lines) and lines[idx].strip() == "---":
                idx += 1
            while idx < len(lines) and not lines[idx].strip():
                idx += 1
            return scalars, idx

        caption_start = 0
        for i, line in enumerate(lines):
            if not line.strip():
                caption_start = i + 1
                continue
            m = re.match(r"^([A-Za-z_][\w]*)\s*:\s*(.*)$", line)
            if m:
                scalars[m.group(1)] = m.group(2)
                caption_start = i + 1
            else:
                break
        return scalars, caption_start

    def run(self):  # noqa: C901
        """
        Generate the sign chart.

        Returns:
            list: List of docutils nodes (figure containing SVG)
        """
        env = self.state.document.settings.env
        app = env.app
        try:
            import signchart  # type: ignore
        except Exception as e:
            err = nodes.error()
            err += nodes.paragraph(text=f"Could not import signchart: {e}")
            return [err]

        scalars, caption_idx = self._parse_kv_block()
        merged: Dict[str, Any] = {**scalars, **self.options}

        func_raw = merged.get("function")
        if not func_raw:
            return [
                self.state_machine.reporter.error(
                    "Directive 'signchart' requires 'function:' option", line=self.lineno
                )
            ]

        # Parse function as either (expr, label) literal or "expr, label"
        f_expr = None
        f_name = None
        lit = _safe_literal(str(func_raw))
        if isinstance(lit, (list, tuple)) and len(lit) >= 1:
            f_expr = str(lit[0]).strip()
            if len(lit) > 1:
                f_name = str(lit[1]).strip() or None
        else:
            s = str(func_raw)
            if "," in s:
                expr, label = s.split(",", 1)
                f_expr = expr.strip()
                label = label.strip()
                f_name = label or None
            else:
                f_expr = s.strip()
                f_name = None

        include_factors = _parse_bool(merged.get("factors"), default=True)
        explicit_name = merged.get("name")
        debug_mode = "debug" in merged

        # Parse custom domain if provided
        xmin_val = merged.get("xmin")
        xmax_val = merged.get("xmax")
        custom_domain = None
        if xmin_val is not None and xmax_val is not None:
            try:
                xmin_float = float(xmin_val)
                xmax_float = float(xmax_val)
                custom_domain = (xmin_float, xmax_float)
            except (ValueError, TypeError):
                return [
                    self.state_machine.reporter.warning(
                        f"signchart: Could not parse xmin='{xmin_val}' and xmax='{xmax_val}' as floats. Ignoring domain.",
                        line=self.lineno,
                    )
                ]

        # Hash includes function, name, factors, and domain
        content_hash = _hash_key(
            f_expr,
            f_name or "",
            int(bool(include_factors)),
            str(custom_domain) if custom_domain else "",
        )
        base_name = explicit_name or f"signchart_{content_hash}"

        rel_dir = os.path.join("_static", "signchart")
        abs_dir = os.path.join(app.srcdir, rel_dir)
        os.makedirs(abs_dir, exist_ok=True)
        svg_name = f"{base_name}.svg"
        abs_svg = os.path.join(abs_dir, svg_name)

        regenerate = ("nocache" in merged) or not os.path.exists(abs_svg)
        if regenerate:
            try:
                # Render using signchart and save as SVG
                plot_kwargs = {
                    "f": f_expr,
                    "fn_name": f_name or None,
                    "include_factors": bool(include_factors),
                }
                # Add domain if custom domain is specified
                if custom_domain is not None:
                    plot_kwargs["domain"] = custom_domain

                signchart.plot(**plot_kwargs)
                signchart.savefig(dirname=abs_dir, fname=svg_name)
            except Exception as e:
                return [
                    self.state_machine.reporter.error(
                        f"Error generating sign chart: {e}",
                        line=self.lineno,
                    )
                ]

        if not os.path.exists(abs_svg):
            return [
                self.state_machine.reporter.error("signchart: SVG file missing.", line=self.lineno)
            ]

        env.note_dependency(abs_svg)
        # copy into build _static
        try:
            out_static = os.path.join(app.outdir, "_static", "signchart")
            os.makedirs(out_static, exist_ok=True)
            shutil.copy2(abs_svg, os.path.join(out_static, svg_name))
        except Exception:
            pass

        try:
            raw_svg = open(abs_svg, "r", encoding="utf-8").read()
        except Exception as e:
            return [
                self.state_machine.reporter.error(
                    f"signchart inline: could not read SVG: {e}", line=self.lineno
                )
            ]

        if not debug_mode and "viewBox" in raw_svg:
            raw_svg = _strip_root_svg_size(raw_svg)

        if not debug_mode:
            raw_svg = _rewrite_ids(raw_svg, f"sgc_{content_hash}_{uuid.uuid4().hex[:6]}_")

        alt_default = "Fortegnsskjema"
        alt = merged.get("alt", alt_default)

        width_opt = merged.get("width")
        percent = isinstance(width_opt, str) and width_opt.strip().endswith("%")

        def _augment(m):
            """Add classes, aria-label, and width styling to root SVG tag."""
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
        # Suppress automatic <title> insertion to avoid browser hover tooltips.
        # Accessibility is maintained via role="img" and aria-label set above.

        figure = nodes.figure()
        figure.setdefault("classes", []).extend(["adaptive-figure", "signchart-figure", "no-click"])
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
            caption_text = "\n".join(caption_lines)
            # Parse as inline text to support math while avoiding extra paragraph nodes
            parsed_nodes, messages = self.state.inline_text(caption_text, self.lineno)
            caption.extend(parsed_nodes)
            figure += caption

        if explicit_name := merged.get("name"):
            self.add_name(figure)
        return [figure]


def setup(app):
    """
    Setup function to register the directive with Sphinx.

    This function is called automatically by Sphinx when the extension is loaded.
    It registers both 'signchart' and 'sign-chart' directives for compatibility.

    Args:
        app: The Sphinx application instance

    Returns:
        dict: Extension metadata including version and parallel processing flags
    """
    app.add_directive("signchart", SignChartDirective)
    app.add_directive("sign-chart", SignChartDirective)
    return {"version": "0.1", "parallel_read_safe": True, "parallel_write_safe": True}
