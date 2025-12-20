"""
Factor Tree Directive
=====================

A Sphinx directive that generates visual factor trees (prime factorization trees) for integers.
Uses matplotlib to create SVG visualizations showing the step-by-step breakdown of a number
into its prime factors.

Features:
- Automatic prime factorization
- Customizable tree appearance (angle, branch length, font size)
- Configurable figure sizing
- Content-based caching to avoid regeneration
- Accessibility support with ARIA labels
- Caption support

Dependencies:
- matplotlib (for plotting)
- numpy (for calculations)

Usage Examples:
--------------

Basic usage (factor tree for 68):
```
.. factor-tree::
   :n: 68
```

Custom styling:
```
.. factor-tree::
   :n: 120
   :angle: 40
   :branch_length: 2.0
   :fontsize: 20
   :width: 400px
```

With figure sizing:
```
.. factor-tree::
   :n: 84
   :figsize: 4,4
   :width: 80%
   :align: center

   Factor tree for 84
```

YAML-style configuration:
```
.. factor-tree::
   ---
   n: 96
   angle: 35
   fontsize: 22
   ---

   Prime factorization of 96
```

Author: Original implementation from matematikk_r1
"""

from __future__ import annotations

import os
import re
import shutil
import uuid
import html
from typing import Any, Dict, List, Tuple

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective


# --------------------
# Utilities
# --------------------
import hashlib


def _hash_key(*parts) -> str:
    """Generate a hash key from multiple parts for caching."""
    h = hashlib.sha1()
    for p in parts:
        if p is None:
            p = "__NONE__"
        h.update(str(p).encode("utf-8"))
        h.update(b"||")
    return h.hexdigest()[:12]


def _strip_root_svg_size(svg_text: str) -> str:
    """Remove width/height attributes from root <svg> tag to make it responsive."""

    def repl(m):
        tag = m.group(0)
        tag = re.sub(r'\swidth="[^"]+"', "", tag)
        tag = re.sub(r'\sheight="[^"]+"', "", tag)
        return tag

    return re.sub(r"<svg\b[^>]*>", repl, svg_text, count=1)


def _rewrite_ids(txt: str, prefix: str) -> str:
    """
    Rewrite IDs in SVG to avoid collisions when multiple SVGs are on the same page.
    Skips font-related IDs.
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

    txt = re.sub(r'(xlink:href|href)\s*=\s*(["\'])#\s*([^"\']+)\s*\2', repl_href, txt)
    return txt


class FactorTreeDirective(SphinxDirective):
    """
    Directive to create a visual factor tree for an integer.

    Options:
        :n: The integer to factorize (default: 68)
        :angle: Angle between branches in degrees (default: 30)
        :branch_length: Length of branches (default: 1.8)
        :fontsize: Font size for numbers (default: 18)
        :figsize: Figure size as "w,h" or "[w,h]" (e.g., "4,4")
        :figwidth: Figure width in inches
        :figheight: Figure height in inches
        :width: Display width (e.g., "400px" or "80%")
        :align: Alignment - left, center, or right (default: center)
        :class: Additional CSS classes
        :name: Explicit name for cross-referencing
        :nocache: Force regeneration of the figure
        :debug: Keep original SVG size attributes
        :alt: Alternative text for accessibility
    """

    has_content = True
    required_arguments = 0
    option_spec = {
        # presentation
        "width": directives.length_or_percentage_or_unitless,
        "align": lambda a: directives.choice(a, ["left", "center", "right"]),
        "class": directives.class_option,
        "name": directives.unchanged,
        "nocache": directives.flag,
        "debug": directives.flag,
        "alt": directives.unchanged,
        # parameters
        "n": directives.unchanged,
        "angle": directives.unchanged,  # degrees
        "branch_length": directives.unchanged,
        "fontsize": directives.unchanged,
        # figure sizing
        "figsize": directives.unchanged,  # "w,h" or "[w,h]" or "(w,h)"
        "figwidth": directives.unchanged,
        "figheight": directives.unchanged,
    }

    def _parse_kv_block(self) -> Tuple[Dict[str, Any], int]:
        """Parse YAML-style key-value block or simple key: value lines."""
        lines = list(self.content)
        scalars: Dict[str, Any] = {}
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
                    scalars[key] = value
                idx += 1
            if idx < len(lines) and lines[idx].strip() == "---":
                idx += 1
            while idx < len(lines) and not lines[idx].strip():
                idx += 1
            return scalars, idx
        # fallback: simple key: value lines at top
        caption_start = 0
        for i, line in enumerate(lines):
            if not line.strip():
                caption_start = i + 1
                continue
            m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
            if m:
                key, value = m.group(1), m.group(2)
                scalars[key] = value
                caption_start = i + 1
            else:
                break
        return scalars, caption_start

    def run(self):
        env = self.state.document.settings.env
        app = env.app
        try:
            import matplotlib
            import matplotlib.pyplot as plt
            import numpy as np  # noqa: F401
        except Exception as e:
            err = nodes.error()
            err += nodes.paragraph(text=f"Kunne ikke importere nødvendige biblioteker: {e}")
            return [err]

        scalars, caption_idx = self._parse_kv_block()
        merged: Dict[str, Any] = {**scalars, **self.options}

        def _f_float(name: str, default: float) -> float:
            v = merged.get(name)
            if v in (None, ""):
                return default
            try:
                return float(v)
            except Exception:
                return default

        def _f_int(name: str, default: int) -> int:
            v = merged.get(name)
            if v in (None, ""):
                return default
            try:
                return int(float(v))
            except Exception:
                return default

        def _f_float_opt(name: str) -> float | None:
            v = merged.get(name)
            if v in (None, ""):
                return None
            try:
                return float(v)
            except Exception:
                return None

        def _parse_figsize(val: str | None) -> Tuple[float, float] | None:
            if not isinstance(val, str) or not val.strip():
                return None
            s = val.strip()
            if (s.startswith("[") and s.endswith("]")) or (s.startswith("(") and s.endswith(")")):
                s = s[1:-1].strip()
            parts = [p.strip() for p in s.split(",") if p.strip()]
            if len(parts) >= 2:
                try:
                    w = float(parts[0])
                    h = float(parts[1])
                    return (w, h)
                except Exception:
                    return None
            return None

        n = _f_int("n", 68)
        angle = _f_float("angle", 30.0)
        branch_len = _f_float("branch_length", 1.8)
        fontsize = _f_int("fontsize", 18)

        explicit_name = merged.get("name")
        debug_mode = "debug" in merged  # noqa: F841 (reserved for future use)

        content_hash = _hash_key(n, angle, branch_len, fontsize)
        base_name = explicit_name or f"factor_tree_{content_hash}"

        rel_dir = os.path.join("_static", "factor_tree")
        abs_dir = os.path.join(app.srcdir, rel_dir)
        os.makedirs(abs_dir, exist_ok=True)
        svg_name = f"{base_name}.svg"
        abs_svg = os.path.join(abs_dir, svg_name)

        regenerate = ("nocache" in merged) or not os.path.exists(abs_svg)
        if regenerate:
            matplotlib.use("Agg")
            try:
                # Build the tree and plot
                import matplotlib as mpl

                # Keep mathtext only (no LaTeX dependency); fontsize configurable
                mpl.rcParams["text.usetex"] = False
                mpl.rcParams["font.size"] = fontsize

                def prime_factors(x: int) -> List[int]:
                    """Get list of prime factors in order."""
                    for i in range(2, x + 1):
                        if x % i == 0:
                            if i == x:
                                return [x]
                            return [i] + prime_factors(x // i)

                def build_tree(x: int):
                    """Build tree structure as (value, [children])."""
                    facs = prime_factors(x)
                    if len(facs) == 1:
                        return (x, [])
                    left = facs[0]
                    right = x // left
                    return (x, [build_tree(left), build_tree(right)])

                def get_tree_depth(node) -> int:
                    """Get maximum depth of tree."""
                    if not node[1]:
                        return 1
                    return 1 + max(get_tree_depth(child) for child in node[1])

                def plot_tree(node, x=0.0, y=0.0, ax=None, level=0, max_depth=None):
                    """Recursively plot the factor tree."""
                    if ax is None:
                        fig, ax = plt.subplots()
                        ax.axis("off")
                        ax.set_aspect("equal")

                    import numpy as _np

                    angle_rad = _np.radians(angle)
                    dx = branch_len * _np.sin(angle_rad)
                    dy = -branch_len * _np.cos(angle_rad)

                    value, children = node
                    # Use a hardcoded blue color instead of plotmath.COLORS
                    blue_color = (0.0, 0.447, 0.698)  # matplotlib RGB tuple

                    ax.text(
                        x,
                        y,
                        f"${value}$",
                        ha="center",
                        va="center",
                        bbox=dict(
                            boxstyle="circle,pad=0.3",
                            facecolor="#e0f7fa",
                            edgecolor=blue_color,
                            linewidth=1.5,
                        ),
                    )

                    if children:
                        offsets = [-dx, dx]
                        for child, offset_x in zip(children, offsets):
                            child_x = x + offset_x
                            child_y = y + dy
                            ax.plot(
                                [x, child_x],
                                [y, child_y],
                                color="#455a64",
                                linewidth=1.2,
                            )
                            plot_tree(
                                child,
                                x=child_x,
                                y=child_y,
                                ax=ax,
                                level=level + 1,
                                max_depth=max_depth,
                            )

                tree = build_tree(n)
                depth = get_tree_depth(tree)
                plot_tree(tree, max_depth=depth)

                # Expand limits to include text bbox circles and add margins
                ax = plt.gca()
                try:
                    ax.relim()
                    ax.autoscale_view()
                    ax.margins(x=0.3, y=0.4)
                except Exception:
                    pass

                fig = plt.gcf()
                # Figure size: from figsize, or figwidth/figheight, else default 3x3 in
                fs = _parse_figsize(merged.get("figsize"))
                fw = _f_float_opt("figwidth")
                fh = _f_float_opt("figheight")
                if fs is not None:
                    fig.set_size_inches(fs[0], fs[1])
                elif fw is not None or fh is not None:
                    fig.set_size_inches(
                        fw if fw is not None else 3.0, fh if fh is not None else 3.0
                    )
                else:
                    fig.set_size_inches(3, 3)

                plt.tight_layout(pad=0.6)

                fig.savefig(
                    abs_svg,
                    format="svg",
                    bbox_inches="tight",
                    transparent=True,
                    pad_inches=0.1,
                )
                import matplotlib.pyplot as _plt

                _plt.close(fig)
            except Exception as e:
                return [
                    self.state_machine.reporter.error(
                        f"Feil under generering av faktor-tre: {e}", line=self.lineno
                    )
                ]

        if not os.path.exists(abs_svg):
            return [
                self.state_machine.reporter.error("factor-tree: SVG mangler.", line=self.lineno)
            ]

        env.note_dependency(abs_svg)
        # copy into build _static
        try:
            out_static = os.path.join(app.outdir, "_static", "factor_tree")
            os.makedirs(out_static, exist_ok=True)
            shutil.copy2(abs_svg, os.path.join(out_static, svg_name))
        except Exception:
            pass

        try:
            raw_svg = open(abs_svg, "r", encoding="utf-8").read()
        except Exception as e:
            return [
                self.state_machine.reporter.error(
                    f"factor-tree inline: kunne ikke lese SVG: {e}", line=self.lineno
                )
            ]

        if "debug" not in merged and "viewBox" in raw_svg:
            raw_svg = _strip_root_svg_size(raw_svg)

        if "debug" not in merged:
            raw_svg = _rewrite_ids(raw_svg, f"ft_{content_hash}_{uuid.uuid4().hex[:6]}_")

        alt = merged.get("alt", f"Faktor-tre for {n}")
        width_opt = merged.get("width")
        align_raw = merged.get("align", "center")
        align_opt = str(align_raw).strip().lower() if isinstance(align_raw, str) else "center"
        if align_opt not in {"left", "center", "right"}:
            align_opt = "center"
        percent = isinstance(width_opt, str) and width_opt.strip().endswith("%")

        alt_attr = html.escape(alt, quote=True) if isinstance(alt, str) else ""
        alt_title = html.escape(alt, quote=False) if isinstance(alt, str) else ""

        def _augment(m):
            tag = m.group(0)
            if "class=" not in tag:
                tag = tag[:-1] + ' class="graph-inline-svg"' + ">"
            else:
                tag = tag.replace('class="', 'class="graph-inline-svg ')
            if alt and "aria-label=" not in tag:
                tag = tag[:-1] + f' role="img" aria-label="{alt_attr}"' + ">"
            if width_opt:
                if percent:
                    wval = width_opt.strip()
                else:
                    wval = width_opt.strip()
                    if wval.isdigit():
                        wval += "px"
                # Align-aware margins to avoid overriding figure alignment
                if align_opt == "left":
                    margin = "margin-left:0; margin-right:auto;"
                elif align_opt == "right":
                    margin = "margin-left:auto; margin-right:0;"
                else:
                    margin = "margin-left:auto; margin-right:auto;"
                style_frag = f"width:{wval}; height:auto; display:block; {margin}"
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

        # Correct pattern ensures augmentation executes
        raw_svg = re.sub(r"<svg\b[^>]*>", _augment, raw_svg, count=1)

        figure = nodes.figure()
        figure.setdefault("classes", []).extend(["adaptive-figure", "plot-figure", "no-click"])
        raw_node = nodes.raw("", raw_svg, format="html")
        raw_node.setdefault("classes", []).extend(["graph-image", "no-click", "no-scaled-link"])
        figure += raw_node

        extra_classes = merged.get("class")
        if extra_classes:
            figure["classes"].extend(extra_classes)
        figure["align"] = align_opt

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

        if explicit_name:
            self.add_name(figure)
        return [figure]


def setup(app):
    """Register the directive with Sphinx."""
    app.add_directive("factor-tree", FactorTreeDirective)
    return {"version": "0.1", "parallel_read_safe": True, "parallel_write_safe": True}
