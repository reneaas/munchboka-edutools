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


class MultiInteractiveGraphDirective(SphinxDirective):
    """Sphinx directive for creating multiple synchronized interactive graphs."""

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True

    option_spec = {
        "interactive-var": directives.unchanged,
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

        # Create frame directories for each graph
        frame_dirs = []
        for i in range(len(graph_blocks)):
            frame_dir = os.path.join(static_dir, base_name, f"graph_{i}")
            frame_dirs.append(frame_dir)

        # Check if regeneration needed
        nocache = "nocache" in merged_options
        all_frames_exist = all(
            os.path.isdir(d) and len(os.listdir(d)) == len(var_values) for d in frame_dirs
        )
        regenerate = nocache or not all_frames_exist

        if regenerate:
            try:
                # Generate frames for all graphs
                self._generate_all_frames(
                    app,
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

        # Copy frames to build output
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

        # Generate HTML output with synchronized slider
        html_content = self._generate_html(
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

    def _generate_all_frames(
        self,
        app: Sphinx,
        var_name: str,
        var_values: List[float],
        graph_blocks: List[List[str]],
        frame_dirs: List[str],
    ) -> None:
        """Generate frames for all graphs.

        Args:
            app: Sphinx application
            var_name: Variable name
            var_values: List of values
            graph_blocks: List of content blocks
            frame_dirs: List of output directories
        """
        from .animate import AnimateDirective

        # Create a temporary animate directive instance to reuse its methods
        temp_directive = AnimateDirective(
            name=self.name,
            arguments=self.arguments,
            options=self.options,
            content=self.content,
            lineno=self.lineno,
            content_offset=self.content_offset,
            block_text=self.block_text,
            state=self.state,
            state_machine=self.state_machine,
        )

        # Generate frames for each graph
        for graph_idx, (content_lines, frame_dir) in enumerate(zip(graph_blocks, frame_dirs)):
            os.makedirs(frame_dir, exist_ok=True)

            # Parse content to get options
            merged_options = self._parse_graph_content(content_lines)

            # Generate each frame as SVG
            for i, value in enumerate(var_values):
                # Substitute variable in content
                frame_content = "\n".join(content_lines)
                frame_content = _substitute_variable(frame_content, var_name, value)

                # Generate SVG directly to output directory
                svg_path = os.path.join(frame_dir, f"frame_{i:04d}.svg")
                temp_directive._generate_frame_svg(
                    app,
                    frame_content,
                    svg_path,
                    merged_options,
                    var_name,
                    value,
                )

                # Make SVG IDs unique by adding frame and graph index prefix
                with open(svg_path, "r", encoding="utf-8") as f:
                    svg_content = f.read()

                # Add unique prefix to all IDs to avoid conflicts
                import uuid

                unique_prefix = f"g{graph_idx}f{i:04d}_{uuid.uuid4().hex[:6]}_"
                svg_content = re.sub(
                    r'id="([^"]+)"', lambda m: f'id="{unique_prefix}{m.group(1)}"', svg_content
                )
                svg_content = re.sub(
                    r"url\(#([^)]+)\)", lambda m: f"url(#{unique_prefix}{m.group(1)})", svg_content
                )
                svg_content = re.sub(
                    r'href="#([^"]+)"',
                    lambda m: f'href="#{unique_prefix}{m.group(1)}"',
                    svg_content,
                )

                with open(svg_path, "w", encoding="utf-8") as f:
                    f.write(svg_content)

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

    def _generate_html(
        self,
        base_name: str,
        var_name: str,
        var_values: List[float],
        num_graphs: int,
        rows: int,
        cols: int,
        options: Dict[str, Any],
    ) -> str:
        """Generate HTML with synchronized slider.

        Args:
            base_name: Base name for frame directories
            var_name: Variable name
            var_values: List of values
            num_graphs: Number of graphs
            rows: Number of rows
            cols: Number of columns
            options: Directive options

        Returns:
            HTML string
        """
        import uuid

        unique_id = uuid.uuid4().hex[:8]
        width = options.get("width", "100%")
        height = options.get("height", "auto")

        var_min = var_values[0]
        var_max = var_values[-1]
        initial_idx = self._get_initial_frame_index(var_values, options)
        initial_value = var_values[initial_idx]

        # Calculate relative path based on document depth (same as interactive_graph)
        docname = self.env.docname
        depth = docname.count("/")
        rel_prefix = "../" * depth

        # Generate frame paths for all graphs
        all_frame_paths = []
        for graph_idx in range(num_graphs):
            frame_paths = [
                f"{rel_prefix}_static/multi_interactive/{base_name}/graph_{graph_idx}/frame_{i:04d}.svg"
                for i in range(len(var_values))
            ]
            all_frame_paths.append(frame_paths)

        # JavaScript arrays for all graphs
        frames_arrays_js = (
            "["
            + ",".join("[" + ",".join(f'"{p}"' for p in paths) + "]" for paths in all_frame_paths)
            + "]"
        )

        values_js = "[" + ",".join(f"{v:.10f}" for v in var_values) + "]"

        # Add preload hints for initial frames and nearby frames for faster loading
        preload_links = []
        for frame_idx in range(max(0, initial_idx - 3), min(len(var_values), initial_idx + 4)):
            for graph_idx in range(num_graphs):
                preload_links.append(
                    f'<link rel="preload" as="image" href="{all_frame_paths[graph_idx][frame_idx]}">'
                )
        preload_html = "\n".join(preload_links)

        # Generate grid of images
        grid_items = []
        for graph_idx in range(num_graphs):
            grid_items.append(
                f"""
            <div class="multi-interactive-item">
                <img id="multi-interactive-img-{unique_id}-{graph_idx}" 
                     class="adaptive-figure"
                     src="{all_frame_paths[graph_idx][initial_idx]}" 
                     alt="Interactive graph {graph_idx + 1}"
                     style="width: 100%; height: {height}; display: block;"
                     loading="eager">
            </div>
            """
            )

        grid_html = "\n".join(grid_items)

        html = f"""
{preload_html}
<div class="multi-interactive-container" style="width: {width}; margin: 0 auto;">
    <div class="multi-interactive-grid" style="display: grid; grid-template-columns: repeat({cols}, 1fr); grid-template-rows: repeat({rows}, auto); gap: 10px; margin-bottom: 15px;">
        {grid_html}
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

.multi-interactive-slider:hover {{
    opacity: 1;
}}

.multi-interactive-slider:active::-webkit-slider-thumb {{
    background: #1976D2;
}}

.multi-interactive-slider:active::-moz-range-thumb {{
    background: #1976D2;
}}

.multi-interactive-item {{
    border: 1px solid var(--pst-color-border, #e0e0e0);
    border-radius: 8px;
    padding: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    background: transparent;
}}

/* Dark mode adjustments */
html[data-theme="dark"] .multi-interactive-item {{
    box-shadow: 0 2px 4px rgba(255,255,255,0.05);
}}
</style>

<script>
(function() {{
    console.log('Multi-interactive graph script starting for {unique_id}');
    
    const allFrames = {frames_arrays_js};
    const values = {values_js};
    const slider = document.getElementById('multi-interactive-slider-{unique_id}');
    const valueDisplay = document.getElementById('multi-interactive-value-{unique_id}');
    
    // Get all image elements
    const images = [];
    for (let i = 0; i < {num_graphs}; i++) {{
        const img = document.getElementById('multi-interactive-img-{unique_id}-' + i);
        if (img) {{
            images.push(img);
        }}
    }}
    
    console.log('Elements found:', {{
        slider: !!slider,
        valueDisplay: !!valueDisplay,
        imagesCount: images.length,
        framesArrays: allFrames.length
    }});
    
    if (!slider || !valueDisplay || images.length === 0) {{
        console.error('Missing elements!');
        return;
    }}
    
    function updateFrames() {{
        const index = parseInt(slider.value);
        console.log('Updating to frame', index);
        
        // Update all images
        for (let i = 0; i < images.length; i++) {{
            images[i].src = allFrames[i][index];
        }}
        
        valueDisplay.textContent = '{var_name} = ' + values[index].toFixed(2);
    }}
    
    // Preload images with priority
    const preloadedFrames = new Set();
    
    function preloadFrame(index) {{
        if (preloadedFrames.has(index) || index < 0 || index >= allFrames[0].length) return;
        preloadedFrames.add(index);
        // Preload all graph frames for this index
        for (let graphIdx = 0; graphIdx < allFrames.length; graphIdx++) {{
            const img = new Image();
            img.src = allFrames[graphIdx][index];
        }}
    }}
    
    function preloadNearbyFrames(currentIdx, radius) {{
        for (let offset = 0; offset <= radius; offset++) {{
            if (offset === 0) {{
                preloadFrame(currentIdx);
            }} else {{
                preloadFrame(currentIdx + offset);
                preloadFrame(currentIdx - offset);
            }}
        }}
    }}
    
    function preloadAllFrames() {{
        const currentIdx = parseInt(slider.value);
        const total = allFrames[0].length;
        let loaded = 0;
        const batchSize = 5;
        
        function loadBatch() {{
            for (let i = 0; i < batchSize && loaded < total; i++) {{
                const offset = Math.floor(loaded / 2) + 1;
                const idx = loaded % 2 === 0 
                    ? (currentIdx + offset) % total
                    : (currentIdx - offset + total) % total;
                preloadFrame(idx);
                loaded++;
            }}
            
            if (loaded < total) {{
                if (window.requestIdleCallback) {{
                    requestIdleCallback(loadBatch, {{ timeout: 1000 }});
                }} else {{
                    setTimeout(loadBatch, 50);
                }}
            }}
        }}
        
        loadBatch();
    }}
    
    // Initialize preloading
    function initializeGraphs() {{
        updateFrames();
        const currentIdx = parseInt(slider.value);
        preloadNearbyFrames(currentIdx, 10);
        setTimeout(preloadAllFrames, 100);
    }}
    
    function onSliderChange() {{
        updateFrames();
        const currentIdx = parseInt(slider.value);
        preloadNearbyFrames(currentIdx, 5);
    }}
    
    slider.addEventListener('input', updateFrames);
    slider.addEventListener('change', onSliderChange);
    slider.addEventListener('touchmove', updateFrames);
    
    // Keyboard navigation
    slider.addEventListener('keydown', function(e) {{
        if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') {{
            e.preventDefault();
            this.value = Math.max(0, parseInt(this.value) - 1);
            updateFrames();
        }} else if (e.key === 'ArrowRight' || e.key === 'ArrowUp') {{
            e.preventDefault();
            this.value = Math.min({len(var_values) - 1}, parseInt(this.value) + 1);
            updateFrames();
        }}
    }});
    
    // Start initialization
    initializeGraphs();
    
    console.log('Event listeners attached successfully');
}})();
</script>
"""
        return html


def setup(app: Sphinx) -> Dict[str, Any]:
    """Setup the multi-interactive-graph directive."""
    app.add_directive("multi-interactive-graph", MultiInteractiveGraphDirective)

    return {
        "version": "0.1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
