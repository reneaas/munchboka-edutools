"""
Multi Interactive Graph Directive for Jupyter Book
==================================================

Creates multiple synchronized interactive graphs sharing a single slider.
Similar to multi-plot2 but for interactive graphs.

Example:
    ```
    ::::{multi-interactive-graph}
    ---
    rows: 1
    cols: 2
    interactive-var: a, -5, 5, 50
    ---

    :::{interactive-graph}
    function: x**2 + a*x
    xmin: -10
    xmax: 10
    :::

    :::{interactive-graph}
    function: sin(a*x)
    xmin: -10
    xmax: 10
    :::
    ::::
    ```

Author: Generated for munchboka-edutools
License: MIT
"""

import hashlib
import os
import re
import shutil
import tempfile
from typing import Any, Dict, List, Tuple

from tqdm import tqdm

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective

# Import utilities
from .animate import (
    _eval_expr,
    _hash_key,
    _parse_bool,
    _substitute_variable,
)
from .svg_delta import compute_svg_deltas, save_delta_format


class MultiInteractiveGraphDirective(SphinxDirective):
    """Sphinx directive for creating multiple synchronized interactive graphs."""

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True

    option_spec = {
        "interactive-var": directives.unchanged,
        "interactive-var-start": directives.unchanged,
        "rows": directives.unchanged,
        "cols": directives.unchanged,
        "width": directives.unchanged,
        "height": directives.unchanged,
        "align": directives.unchanged,
        "class": directives.unchanged,
        "name": directives.unchanged,
    }

    def run(self) -> List[nodes.Node]:
        """Process the multi-interactive-graph directive."""
        app = self.env.app
        env = self.env

        # Parse YAML frontmatter if present
        frontmatter, content_start = self._parse_frontmatter()

        # Merge frontmatter with options
        merged_options = {**frontmatter, **self.options}

        # Get interactive variable specification
        var_spec = merged_options.get("interactive-var")
        if not var_spec:
            return [
                self.state_machine.reporter.error(
                    "interactive-var option is required (format: name, min, max, frames)",
                    line=self.lineno,
                )
            ]

        # Parse interactive variable
        try:
            var_name, var_values = self._parse_interactive_var(var_spec)
        except ValueError as e:
            return [
                self.state_machine.reporter.error(
                    f"Invalid interactive-var: {e}",
                    line=self.lineno,
                )
            ]

        # Parse nested interactive-graph directives
        graph_blocks = self._parse_graph_blocks(content_start)

        if not graph_blocks:
            return [
                self.state_machine.reporter.error(
                    "multi-interactive-graph must contain at least one interactive-graph directive",
                    line=self.lineno,
                )
            ]

        # Get layout options
        rows = int(merged_options.get("rows", 1))
        cols = int(merged_options.get("cols", len(graph_blocks)))

        # Determine output directory
        srcdir = env.srcdir
        static_dir = os.path.join(srcdir, "_static", "multi_interactive")
        os.makedirs(static_dir, exist_ok=True)

        # Generate hash for caching
        all_content = "\n".join(["\n".join(block) for block in graph_blocks])
        hash_key = _hash_key(
            var_spec,
            all_content,
            str(merged_options),
            "multi_interactive",
        )
        base_name = f"multi_interactive_{hash_key}"

        # Create delta asset directories for each graph panel
        frame_dirs = []
        for i in range(len(graph_blocks)):
            frame_dir = os.path.join(static_dir, base_name, f"graph_{i}")
            frame_dirs.append(frame_dir)

        def _delta_assets_exist(d: str) -> bool:
            return os.path.isfile(os.path.join(d, "base.svg")) and os.path.isfile(
                os.path.join(d, "deltas.json")
            )

        # Check if regeneration needed
        nocache = "nocache" in merged_options
        all_frames_exist = all(_delta_assets_exist(d) for d in frame_dirs)
        regenerate = nocache or not all_frames_exist

        if regenerate:
            try:
                # Generate delta assets for all graph panels
                self._generate_all_frames_delta(
                    var_name,
                    var_values,
                    graph_blocks,
                    frame_dirs,
                )
            except Exception as e:
                return [
                    self.state_machine.reporter.error(
                        f"Error generating multi-interactive graphs: {e}",
                        line=self.lineno,
                    )
                ]

        # Register dependencies
        for frame_dir in frame_dirs:
            env.note_dependency(frame_dir)

        # Copy delta assets to build output
        try:
            build_base_dir = os.path.join(app.outdir, "_static", "multi_interactive", base_name)
            os.makedirs(os.path.dirname(build_base_dir), exist_ok=True)
            if os.path.exists(build_base_dir):
                shutil.rmtree(build_base_dir)

            for i, frame_dir in enumerate(frame_dirs):
                build_dir = os.path.join(build_base_dir, f"graph_{i}")
                shutil.copytree(frame_dir, build_dir)
        except Exception:
            pass  # Non-fatal if copy fails during build

        # Generate HTML output with synchronized slider using delta engine
        html_content = self._generate_html_delta(
            base_name,
            var_name,
            var_values,
            len(graph_blocks),
            rows,
            cols,
            merged_options,
        )

        # Create output node
        raw_node = nodes.raw("", html_content, format="html")
        raw_node.setdefault("classes", []).extend(["multi-interactive-graph", "no-click"])

        # Build container
        container = nodes.container()
        container.setdefault("classes", []).extend(["multi-interactive-container", "no-click"])

        align = merged_options.get("align", "center")
        container["align"] = align

        container += raw_node

        # Handle explicit name
        explicit_name = self.options.get("name")
        if explicit_name:
            self.add_name(container)

        return [container]

    def _parse_frontmatter(self) -> Tuple[Dict[str, Any], int]:
        """Parse YAML frontmatter from content.

        Returns:
            Tuple of (frontmatter_dict, content_start_line)
        """
        frontmatter = {}
        content_start = 0

        # Check if first line is ---
        if self.content and self.content[0].strip() == "---":
            # Find closing ---
            for i in range(1, len(self.content)):
                if self.content[i].strip() == "---":
                    # Parse YAML-like content
                    for line in self.content[1:i]:
                        if ":" in line:
                            key, value = line.split(":", 1)
                            frontmatter[key.strip()] = value.strip()
                    content_start = i + 1
                    break

        return frontmatter, content_start

    def _parse_graph_blocks(self, start_line: int) -> List[List[str]]:
        """Parse nested interactive-graph directive blocks.

        Returns:
            List of content blocks (each is a list of lines)
        """
        blocks = []
        current_block = []
        in_block = False
        indent_level = 0

        for i in range(start_line, len(self.content)):
            line = self.content[i]
            stripped = line.strip()

            # Detect start of interactive-graph block
            if stripped.startswith(":::{interactive-graph}") or stripped.startswith(
                "```{interactive-graph}"
            ):
                if current_block:
                    blocks.append(current_block)
                current_block = []
                in_block = True
                indent_level = len(line) - len(line.lstrip())
                continue

            # Detect end of block
            if in_block and (stripped == ":::" or stripped == "```"):
                if current_block:
                    blocks.append(current_block)
                current_block = []
                in_block = False
                continue

            # Add content to current block
            if in_block:
                # Remove indent
                if line.startswith(" " * indent_level):
                    current_block.append(line[indent_level:])
                else:
                    current_block.append(line)

        # Add final block if exists
        if current_block:
            blocks.append(current_block)

        return blocks

    def _parse_interactive_var(self, var_spec: str) -> Tuple[str, List[float]]:
        """Parse interactive variable specification.

        Args:
            var_spec: String like "a, -5, 5, 50" (name, min, max, frames)

        Returns:
            Tuple of (variable_name, list_of_values)
        """
        parts = [p.strip() for p in var_spec.split(",")]
        if len(parts) != 4:
            raise ValueError(
                f"interactive-var must have 4 parts: name, min, max, frames. Got: {var_spec}"
            )

        var_name = parts[0]
        if not var_name.isidentifier():
            raise ValueError(f"Invalid variable name: {var_name}")

        try:
            var_min = _eval_expr(parts[1])
            var_max = _eval_expr(parts[2])
            num_frames = int(parts[3])
            if num_frames < 2:
                raise ValueError("Frame count must be at least 2")
        except Exception as e:
            raise ValueError(f"Error parsing interactive-var '{var_spec}': {e}")

        # Generate linear interpolation
        import numpy as np

        values = np.linspace(var_min, var_max, num_frames).tolist()

        return var_name, values

    def _get_initial_frame_index(
        self, var_values: List[float], merged_options: Dict[str, Any]
    ) -> int:
        """Get the initial frame index based on interactive-var-start option.

        Args:
            var_values: List of variable values
            merged_options: Merged options dictionary

        Returns:
            Index of the initial frame (0-based)
        """
        start_value_str = merged_options.get("interactive-var-start")
        if start_value_str is None:
            # Default to middle frame
            return len(var_values) // 2

        try:
            start_value = _eval_expr(start_value_str)
            # Find closest value in var_values
            import numpy as np

            idx = int(np.argmin(np.abs(np.array(var_values) - start_value)))
            return idx
        except:
            # Fall back to middle if parsing fails
            return len(var_values) // 2

    def _generate_all_frames_delta(
        self,
        var_name: str,
        var_values: List[float],
        graph_blocks: List[List[str]],
        frame_dirs: List[str],
    ) -> None:
        """Generate delta assets (base.svg + deltas.json) for each graph panel.

        For each panel we render all N frames, compute SVG deltas, and write
        ``base.svg`` + ``deltas.json`` using the same engine as
        ``interactive-graph``.  This typically reduces storage from
        O(N × frame_size) to O(frame_size + N × delta_size).
        """
        from docutils.statemachine import StringList
        from sphinx.util import logging

        from .plot import PlotDirective

        logger = logging.getLogger(__name__)

        for graph_idx, (content_lines, frame_dir) in enumerate(zip(graph_blocks, frame_dirs)):
            os.makedirs(frame_dir, exist_ok=True)

            internal_plot_name = f"__{os.path.basename(frame_dir)}_plot_tmp"

            def _render_svg(frame_content: str, _name: str = internal_plot_name) -> str:
                plot_directive = PlotDirective(
                    name="plot",
                    arguments=[],
                    options={},
                    content=StringList(frame_content.splitlines()),
                    lineno=self.lineno,
                    content_offset=self.content_offset,
                    block_text=self.block_text,
                    state=self.state,
                    state_machine=self.state_machine,
                )
                plot_directive.options["nocache"] = None
                plot_directive.options["internal"] = None
                plot_directive.options["internal-name"] = _name

                rendered_nodes = plot_directive.run()
                svg_text: str | None = None
                for top in rendered_nodes:
                    for raw in top.findall(nodes.raw):
                        txt = raw.astext()
                        if "<svg" in txt:
                            svg_text = txt
                            break
                    if svg_text is not None:
                        break
                if svg_text is None:
                    raise ValueError("PlotDirective did not return inline SVG")
                return svg_text

            # Render all frames for this panel
            svg_frames: List[str] = []
            desc = f"multi-interactive-graph panel {graph_idx + 1}/{len(graph_blocks)}"
            for value in tqdm(var_values, desc=desc, unit="frame", leave=False):
                frame_content = "\n".join(content_lines)
                frame_content = _substitute_variable(frame_content, var_name, value)
                svg_frames.append(_render_svg(frame_content))

            # Compute and store deltas
            logger.info(f"  {desc}: computing SVG deltas")
            base_svg, deltas = compute_svg_deltas(svg_frames)
            save_delta_format(base_svg, deltas, frame_dir)
            logger.info(
                f"  ✓ {desc}: {len(var_values)} frames → base.svg + deltas.json "
                f"(saved to {frame_dir})"
            )

    def _parse_graph_content(self, content_lines: List[str]) -> Dict[str, Any]:
        """Parse graph content to extract options.

        Returns:
            Dictionary of options
        """
        options = {}

        for line in content_lines:
            line = line.strip()
            if not line or ":" not in line:
                continue

            m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
            if m:
                key, value = m.group(1), m.group(2).strip()
                options[key] = value

        return options

    def _generate_html_delta(
        self,
        base_name: str,
        var_name: str,
        var_values: List[float],
        num_graphs: int,
        rows: int,
        cols: int,
        options: Dict[str, Any],
    ) -> str:
        """Generate HTML for multi-panel delta-based interactive graph.

        Each panel has its own inline SVG container driven by the shared delta
        engine; only one slider is rendered and controls all panels in sync.
        """
        import uuid

        unique_id = uuid.uuid4().hex[:8]
        width = options.get("width", "100%")
        height = options.get("height", "auto")

        var_min = var_values[0]
        var_max = var_values[-1]
        initial_idx = self._get_initial_frame_index(var_values, options)
        initial_value = var_values[initial_idx]

        docname = self.env.docname
        depth = docname.count("/")
        rel_prefix = "../" * depth

        # URLs for base SVG and deltas per panel
        base_svg_urls_js = (
            "["
            + ",".join(
                f'"{rel_prefix}_static/multi_interactive/{base_name}/graph_{i}/base.svg"'
                for i in range(num_graphs)
            )
            + "]"
        )
        deltas_urls_js = (
            "["
            + ",".join(
                f'"{rel_prefix}_static/multi_interactive/{base_name}/graph_{i}/deltas.json"'
                for i in range(num_graphs)
            )
            + "]"
        )

        values_js = "[" + ",".join(f"{v:.10f}" for v in var_values) + "]"

        # Build SVG container divs for each panel
        grid_items = "\n".join(f"""            <div class="multi-interactive-item">
                <div id="multi-svg-container-{unique_id}-{i}" class="adaptive-figure" style="width: 100%; display: block;"></div>
            </div>""" for i in range(num_graphs))

        svg_height_css = f"; height: {height}" if height and height != "auto" else ""

        return f"""
<div class="multi-interactive-container" style="width: {width}; margin: 0 auto;">
    <div class="multi-interactive-grid" style="display: grid; grid-template-columns: repeat({cols}, 1fr); grid-template-rows: repeat({rows}, auto); gap: 10px; margin-bottom: 15px;">
{grid_items}
    </div>
    <div class="multi-interactive-controls" style="padding: 15px 10px; text-align: center; border-top: 1px solid #ddd;">
        <div style="display: flex; align-items: center; gap: 10px; max-width: 600px; margin: 0 auto;">
            <span style="font-family: monospace; min-width: 40px; text-align: right; font-size: 14px;">{var_min:.2f}</span>
            <input type="range"
                   id="multi-interactive-slider-{unique_id}"
                   class="multi-interactive-slider"
                   min="0"
                   max="{len(var_values) - 1}"
                   value="{initial_idx}"
                   step="1"
                   style="flex: 1; cursor: pointer; -webkit-appearance: none; appearance: none; height: 8px; border-radius: 5px; background: #ddd; outline: none; pointer-events: auto; z-index: 100; position: relative;">
            <span style="font-family: monospace; min-width: 40px; text-align: left; font-size: 14px;">{var_max:.2f}</span>
        </div>
        <div style="margin-top: 10px; font-family: monospace; font-size: 16px; font-weight: bold;">
            <span id="multi-interactive-value-{unique_id}">{var_name} = {initial_value:.2f}</span>
        </div>
    </div>
</div>

<style>
.multi-interactive-slider::-webkit-slider-thumb {{
    -webkit-appearance: none;
    appearance: none;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: #2196F3;
    cursor: pointer;
    pointer-events: auto;
}}
.multi-interactive-slider::-moz-range-thumb {{
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: #2196F3;
    cursor: pointer;
    pointer-events: auto;
    border: none;
}}
.multi-interactive-slider:active::-webkit-slider-thumb {{ background: #1976D2; }}
.multi-interactive-slider:active::-moz-range-thumb  {{ background: #1976D2; }}
.multi-interactive-item {{
    border: 1px solid var(--pst-color-border, #e0e0e0);
    border-radius: 8px;
    padding: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    background: transparent;
}}
html[data-theme="dark"] .multi-interactive-item {{
    box-shadow: 0 2px 4px rgba(255,255,255,0.05);
}}
</style>

<script>
(function() {{
    const uid = '{unique_id}';
    const allBaseSvgUrls = {base_svg_urls_js};
    const allDeltasUrls  = {deltas_urls_js};
    const values   = {values_js};
    const varName  = '{var_name}';
    const numPanels = {num_graphs};

    const slider       = document.getElementById('multi-interactive-slider-' + uid);
    const valueDisplay = document.getElementById('multi-interactive-value-' + uid);

    if (!slider) return;

    // ── per-panel state objects ──────────────────────────────────────────────
    const panels = allBaseSvgUrls.map(function(_, i) {{
        return {{
            container:        document.getElementById('multi-svg-container-' + uid + '-' + i),
            svgDoc:           null,
            baseSvgTemplate:  null,
            svgElements:      {{}},
            baseElementsById: {{}},
            baseOuterHtmlById:{{}},
            deltas:           null,
            lastFrameIndex:   null,
        }};
    }});

    // ── helpers (applied per-panel) ──────────────────────────────────────────
    function styleSvg(svg) {{
        if (!svg) return;
        try {{ svg.removeAttribute('width');  }} catch(e) {{}}
        try {{ svg.removeAttribute('height'); }} catch(e) {{}}
        try {{ svg.setAttribute('preserveAspectRatio', 'xMidYMid meet'); }} catch(e) {{}}
        svg.style.width  = '100%';
        const h = '{height}';
        svg.style.height  = (h && h !== 'auto') ? h : 'auto';
        svg.style.display = 'block';
        svg.style.shapeRendering = 'geometricPrecision';
        svg.style.textRendering  = 'geometricPrecision';
        svg.classList.add('adaptive-figure');
    }}

    function buildElementCache(p) {{
        if (!p.svgDoc) return;
        p.svgElements = {{}};
        p.svgDoc.querySelectorAll('[id]').forEach(function(el) {{
            p.svgElements[el.id] = el;
        }});
    }}

    function buildBaseCache(p) {{
        if (!p.baseSvgTemplate) return;
        p.baseElementsById  = {{}};
        p.baseOuterHtmlById = {{}};
        p.baseSvgTemplate.querySelectorAll('[id]').forEach(function(el) {{
            p.baseElementsById[el.id] = el;
            try {{ p.baseOuterHtmlById[el.id] = el.outerHTML; }} catch(e) {{}}
        }});
    }}

    function mountFreshBase(p) {{
        if (!p.baseSvgTemplate || !p.container) return;
        const fresh = p.baseSvgTemplate.cloneNode(true);
        p.container.innerHTML = '';
        p.container.appendChild(fresh);
        p.svgDoc = fresh;
        styleSvg(p.svgDoc);
        buildElementCache(p);
    }}

    function parseNsAttr(attr) {{
        if (!attr || attr.length < 3) return null;
        const LB = 123, RB = 125;
        if (attr.charCodeAt(0) !== LB) return null;
        if (attr.length >= 4 && attr.charCodeAt(1) === LB) {{
            for (let i = 2; i < attr.length - 1; i++) {{
                if (attr.charCodeAt(i) === RB && attr.charCodeAt(i+1) === RB) {{
                    const ns = attr.slice(2, i), local = attr.slice(i+2);
                    return (ns && local) ? {{ns, local}} : null;
                }}
            }}
            return null;
        }}
        const close = attr.indexOf(String.fromCharCode(RB));
        if (close <= 1) return null;
        const ns = attr.slice(1, close), local = attr.slice(close+1);
        return (ns && local) ? {{ns, local}} : null;
    }}

    function replaceOuterHtml(existingElem, outerHtml) {{
        try {{
            const parser = new DOMParser();
            const doc = parser.parseFromString(
                '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">' + outerHtml + '</svg>',
                'image/svg+xml');
            const err = doc.querySelector('parsererror');
            if (err) return false;
            const repl = doc.documentElement.firstElementChild;
            if (!repl) return false;
            existingElem.replaceWith(document.importNode(repl, true));
            return true;
        }} catch(e) {{ return false; }}
    }}

    function revertToBase(p) {{
        if (p.lastFrameIndex === null || !p.deltas) return;
        const entry = p.deltas[p.lastFrameIndex] || {{}};
        if (Object.prototype.hasOwnProperty.call(entry, 'fullSvg')) {{
            mountFreshBase(p); p.lastFrameIndex = null; return;
        }}
        let needReset = false, didReplace = false;
        for (const [id, changes] of Object.entries(entry.changes || {{}})) {{
            const live = p.svgElements[id], base = p.baseElementsById[id];
            if (!live || !base) {{ needReset = true; break; }}
            if (Object.prototype.hasOwnProperty.call(changes, 'outerHTML')) {{
                const baseOuter = p.baseOuterHtmlById[id];
                if (!baseOuter || !replaceOuterHtml(live, baseOuter)) {{ needReset = true; break; }}
                didReplace = true; continue;
            }}
            for (const attr of Object.keys(changes)) {{
                if (attr === 'textContent') {{
                    live.textContent = base.textContent || '';
                }} else if (attr === 'tailContent') {{
                    // skip
                }} else {{
                    const ns = parseNsAttr(attr);
                    const bv = ns ? base.getAttributeNS(ns.ns, ns.local) : base.getAttribute(attr);
                    if (bv === null) {{ ns ? live.removeAttributeNS(ns.ns, ns.local) : live.removeAttribute(attr); }}
                    else            {{ ns ? live.setAttributeNS(ns.ns, ns.local, bv) : live.setAttribute(attr, bv); }}
                }}
            }}
        }}
        if (needReset) {{ mountFreshBase(p); }}
        else if (didReplace) {{ buildElementCache(p); }}
        p.lastFrameIndex = null;
    }}

    function applyDelta(p, frameIndex) {{
        if (!p.deltas || frameIndex < 0 || frameIndex >= p.deltas.length) return;
        const delta = p.deltas[frameIndex];
        if (Object.prototype.hasOwnProperty.call(delta, 'fullSvg')) {{
            try {{
                const parser = new DOMParser();
                const doc = parser.parseFromString(delta.fullSvg, 'image/svg+xml');
                const err = doc.querySelector('parsererror');
                if (err) throw new Error(err.textContent || 'SVG parse error');
                const svgEl = doc.documentElement;
                if (!svgEl || svgEl.localName !== 'svg') throw new Error('No SVG element');
                const imp = document.importNode(svgEl, true);
                p.container.innerHTML = '';
                p.container.appendChild(imp);
                p.svgDoc = imp;
                styleSvg(p.svgDoc);
                buildElementCache(p);
            }} catch(e) {{ mountFreshBase(p); }}
            return;
        }}
        let didReplace = false;
        for (const [id, changes] of Object.entries(delta.changes || {{}})) {{
            const elem = p.svgElements[id];
            if (!elem) continue;
            for (const [attr, value] of Object.entries(changes)) {{
                if (attr === 'outerHTML') {{
                    if (replaceOuterHtml(elem, value)) didReplace = true;
                }} else if (attr === 'textContent') {{
                    elem.textContent = value;
                }} else if (attr === 'tailContent') {{
                    // skip
                }} else if (value === null) {{
                    const ns = parseNsAttr(attr);
                    ns ? elem.removeAttributeNS(ns.ns, ns.local) : elem.removeAttribute(attr);
                }} else {{
                    const ns = parseNsAttr(attr);
                    ns ? elem.setAttributeNS(ns.ns, ns.local, value) : elem.setAttribute(attr, value);
                }}
            }}
        }}
        if (didReplace) buildElementCache(p);
    }}

    function renderFrame(p, frameIndex) {{
        if (!p.svgDoc || !p.deltas || !p.baseSvgTemplate) return;
        if (!p.svgElements || Object.keys(p.svgElements).length === 0) buildElementCache(p);
        if (!p.baseElementsById || Object.keys(p.baseElementsById).length === 0) buildBaseCache(p);
        if (p.lastFrameIndex !== null) revertToBase(p);
        applyDelta(p, frameIndex);
        p.lastFrameIndex = frameIndex;
    }}

    // ── value display ─────────────────────────────────────────────────────────
    function updateValueDisplay(index) {{
        const v    = values[index];
        const vStr = (typeof v === 'number') ? v.toFixed(2) : String(v);
        if (window.katex && valueDisplay) {{
            try {{
                valueDisplay.innerHTML = window.katex.renderToString(
                    varName + ' = ' + vStr, {{throwOnError: false, displayMode: false}});
                return;
            }} catch(e) {{}}
        }}
        if (valueDisplay) valueDisplay.textContent = varName + ' = ' + vStr;
    }}

    // ── slider logic ──────────────────────────────────────────────────────────
    let pendingFrame = null;
    function updateAllFrames() {{
        const index = parseInt(slider.value);
        if (pendingFrame !== null) cancelAnimationFrame(pendingFrame);
        pendingFrame = requestAnimationFrame(function() {{
            panels.forEach(function(p) {{ renderFrame(p, index); }});
            updateValueDisplay(index);
            pendingFrame = null;
        }});
    }}

    slider.addEventListener('input',     updateAllFrames);
    slider.addEventListener('change',    updateAllFrames);
    slider.addEventListener('touchmove', updateAllFrames);
    slider.addEventListener('keydown', function(e) {{
        if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') {{
            e.preventDefault();
            this.value = Math.max(0, parseInt(this.value) - 1);
            updateAllFrames();
        }} else if (e.key === 'ArrowRight' || e.key === 'ArrowUp') {{
            e.preventDefault();
            this.value = Math.min({len(var_values) - 1}, parseInt(this.value) + 1);
            updateAllFrames();
        }}
    }});

    // ── load all panels then render initial frame ─────────────────────────────
    function initPanel(p, baseUrl, deltasUrl) {{
        return Promise.all([
            fetch(baseUrl).then(function(r) {{
                if (!r.ok) throw new Error('Failed to load base SVG: ' + r.status);
                return r.text();
            }}),
            fetch(deltasUrl).then(function(r) {{
                if (!r.ok) throw new Error('Failed to load deltas JSON: ' + r.status);
                return r.json();
            }})
        ]).then(function(results) {{
            let svgText   = results[0];
            const deltasData = results[1];
            svgText = svgText.replace(/<\?xml[^?]*\?>/g, '');
            svgText = svgText.replace(/<!DOCTYPE[^>]*>/g, '');
            svgText = svgText.replace(/<metadata>[\s\S]*?<\/metadata>/g, '');
            const parser = new DOMParser();
            const doc = parser.parseFromString(svgText, 'image/svg+xml');
            const parserError = doc.querySelector('parsererror');
            if (parserError) throw new Error('Failed to parse base.svg as SVG XML');
            const svgElement = doc.documentElement;
            if (!svgElement || svgElement.localName !== 'svg')
                throw new Error('No SVG element found in base.svg');
            const imported = document.importNode(svgElement, true);
            p.container.innerHTML = '';
            p.container.appendChild(imported);
            p.svgDoc = imported;
            p.deltas = deltasData;
            styleSvg(p.svgDoc);
            p.baseSvgTemplate = imported.cloneNode(true);
            buildElementCache(p);
            buildBaseCache(p);
        }}).catch(function(err) {{
            if (p.container)
                p.container.innerHTML = '<p style="color:red;padding:10px;">Failed to load panel: ' + err.message + '</p>';
        }});
    }}

    Promise.all(panels.map(function(p, i) {{
        return initPanel(p, allBaseSvgUrls[i], allDeltasUrls[i]);
    }})).then(function() {{
        const index = parseInt(slider.value);
        panels.forEach(function(p) {{ renderFrame(p, index); }});
        updateValueDisplay(index);
    }});
}})();
</script>
"""


def setup(app: Sphinx) -> Dict[str, Any]:
    """Setup the multi-interactive-graph directive."""
    app.add_directive("multi-interactive-graph", MultiInteractiveGraphDirective)

    return {
        "version": "0.1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
