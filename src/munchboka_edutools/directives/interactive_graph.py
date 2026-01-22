"""
Interactive Graph Directive for Jupyter Book
============================================

Creates an interactive graph with a slider that allows users to explore
mathematical functions by changing a variable value in real-time.

Uses pre-rendered frames (similar to animate directive) for perfect
visual consistency and feature parity.

Example:
    ```
    :::{interactive-graph}
    interactive-var: a, -5, 5, 50

    function: x**2 + a*x, f
    point: (a, f(a))
    tangent: a, f, solid, blue
    text: 2, 10, "a = {a:.2f}", center-center
    xmin: -10
    xmax: 10
    ymin: -20
    ymax: 20
    :::
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

# Import frame generation from animate directive
from .animate import (
    _eval_expr,
    _hash_key,
    _parse_bool,
    _substitute_variable,
)


class InteractiveGraphDirective(SphinxDirective):
    """Sphinx directive for creating interactive graphs with sliders."""

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True

    # Import plot directive's option spec for consistency
    from munchboka_edutools.directives.plot import PlotDirective

    option_spec = {
        # Interactive-specific options
        "interactive-var": directives.unchanged,
        "width": directives.unchanged,
        "height": directives.unchanged,
        "align": directives.unchanged,
        "class": directives.unchanged,
        "alt": directives.unchanged,
        "name": directives.unchanged,
        "caption": directives.unchanged,
        # Include all plot directive options for compatibility
        **PlotDirective.option_spec,
    }

    def run(self) -> List[nodes.Node]:
        """Process the interactive-graph directive."""
        app = self.env.app
        env = self.env

        # Parse content like plot/animate directives
        scalars_dict, lists_dict, caption_idx = self._parse_kv_block()

        # Merge directive options and content scalars
        merged = {**scalars_dict, **self.options}

        # Get interactive variable specification
        var_spec = merged.get("interactive-var")
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

        # Determine output directory
        srcdir = env.srcdir
        static_dir = os.path.join(srcdir, "_static", "interactive")
        os.makedirs(static_dir, exist_ok=True)

        # Prepare content for frame generation
        content_lines = list(self.content)
        caption_lines = content_lines[caption_idx:] if caption_idx < len(content_lines) else []

        # Filter interactive-specific keys from plot content
        interactive_keys = {"interactive-var"}
        plot_content_lines = []
        for i, line in enumerate(content_lines):
            if i >= caption_idx:
                break
            line_stripped = line.strip()
            if not line_stripped:
                continue
            m = re.match(r"^([A-Za-z_][\w-]*)\s*:", line)
            if m and m.group(1) in interactive_keys:
                continue
            plot_content_lines.append(line)

        # Generate hash for caching
        content_for_hash = "\n".join(plot_content_lines)
        hash_key = _hash_key(
            var_spec,
            content_for_hash,
            str(merged),
            "interactive",
        )
        base_name = f"interactive_{hash_key}"

        # Create output paths for frames
        frame_dir = os.path.join(static_dir, base_name)
        frames_exist = os.path.isdir(frame_dir) and len(os.listdir(frame_dir)) == len(var_values)

        # Check if regeneration needed
        nocache = "nocache" in merged
        regenerate = nocache or not frames_exist

        if regenerate:
            try:
                # Generate all frames
                self._generate_frames(
                    app,
                    var_name,
                    var_values,
                    plot_content_lines,
                    frame_dir,
                    merged,
                )
            except Exception as e:
                return [
                    self.state_machine.reporter.error(
                        f"Error generating interactive graph: {e}",
                        line=self.lineno,
                    )
                ]

        # Register dependency
        env.note_dependency(frame_dir)

        # Copy frames to build output
        try:
            build_static_dir = os.path.join(app.outdir, "_static", "interactive", base_name)
            os.makedirs(os.path.dirname(build_static_dir), exist_ok=True)
            if os.path.exists(build_static_dir):
                shutil.rmtree(build_static_dir)
            shutil.copytree(frame_dir, build_static_dir)
        except Exception:
            pass  # Non-fatal if copy fails during build

        # Generate HTML output with slider
        html_content = self._generate_html(
            base_name,
            var_name,
            var_values,
            merged,
        )

        # Create output node
        raw_node = nodes.raw("", html_content, format="html")
        raw_node.setdefault("classes", []).extend(
            ["interactive-graph", "no-click", "no-scaled-link"]
        )

        align = merged.get("align", "center")
        
        # For left/right alignment, use a simple container to avoid figure width issues
        # For center, use figure for consistency with other directives
        if align in ("left", "right"):
            container = nodes.container()
            container.setdefault("classes", []).extend(
                ["interactive-figure", "no-click", "no-scaled-link"]
            )
            container += raw_node
            
            # Add caption if present
            if caption_lines:
                caption_para = nodes.paragraph()
                caption_text = "\n".join(caption_lines)
                parsed_nodes, messages = self.state.inline_text(caption_text, self.lineno)
                caption_para.extend(parsed_nodes)
                caption_para["classes"].append("caption")
                container += caption_para
            
            # Handle explicit name
            explicit_name = self.options.get("name")
            if explicit_name:
                self.add_name(container)
            
            return [container]
        else:
            # Use figure for center alignment
            figure = nodes.figure()
            figure.setdefault("classes", []).extend(
                ["adaptive-figure", "interactive-figure", "no-click", "no-scaled-link"]
            )
            figure["align"] = align
            figure += raw_node
            
            # Add caption if present
            if caption_lines:
                caption = nodes.caption()
                caption_text = "\n".join(caption_lines)
                parsed_nodes, messages = self.state.inline_text(caption_text, self.lineno)
                caption.extend(parsed_nodes)
                figure += caption
            
            # Handle explicit name
            explicit_name = self.options.get("name")
            if explicit_name:
                self.add_name(figure)
            
            return [figure]

    def _parse_kv_block(self) -> Tuple[Dict[str, Any], Dict[str, List[str]], int]:
        """Parse content block into scalars, lists, and caption index.

        Returns:
            Tuple of (scalars_dict, lists_dict, caption_index)
        """
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

        caption_idx = len(self.content)

        for i, line in enumerate(self.content):
            line_stripped = line.strip()
            if not line_stripped:
                continue

            # Check for caption marker
            if line_stripped.startswith("---"):
                caption_idx = i + 1
                break

            # Parse key: value
            m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line_stripped)
            if m:
                key, value = m.group(1), m.group(2).strip()
                if key in lists_dict:
                    lists_dict[key].append(value)
                else:
                    scalars_dict[key] = value

        return scalars_dict, lists_dict, caption_idx

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

    def _generate_frames(
        self,
        app: Sphinx,
        var_name: str,
        var_values: List[float],
        plot_content_lines: List[str],
        output_dir: str,
        merged_options: Dict[str, Any],
    ) -> None:
        """Generate all frames as SVG images.

        Args:
            app: Sphinx application
            var_name: Variable name
            var_values: List of values
            plot_content_lines: Content for plot
            output_dir: Directory to save frames
            merged_options: Merged options
        """
        os.makedirs(output_dir, exist_ok=True)

        # Import frame generation from animate
        from .animate import AnimateDirective
        import re

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

        # Generate each frame as SVG
        for i, value in enumerate(var_values):
            # Substitute variable in content
            frame_content = "\n".join(plot_content_lines)
            frame_content = _substitute_variable(frame_content, var_name, value)

            # Generate SVG directly to output directory
            svg_path = os.path.join(output_dir, f"frame_{i:04d}.svg")
            temp_directive._generate_frame_svg(
                app,
                frame_content,
                svg_path,
                merged_options,
                var_name,
                value,
            )

            # Make SVG IDs unique by adding frame index prefix
            with open(svg_path, "r", encoding="utf-8") as f:
                svg_content = f.read()

            # Add unique prefix to all IDs to avoid conflicts
            import uuid

            unique_prefix = f"frame{i:04d}_{uuid.uuid4().hex[:6]}_"
            svg_content = re.sub(
                r'id="([^"]+)"', lambda m: f'id="{unique_prefix}{m.group(1)}"', svg_content
            )
            svg_content = re.sub(
                r"url\(#([^)]+)\)", lambda m: f"url(#{unique_prefix}{m.group(1)})", svg_content
            )
            svg_content = re.sub(
                r'href="#([^"]+)"', lambda m: f'href="#{unique_prefix}{m.group(1)}"', svg_content
            )

            with open(svg_path, "w", encoding="utf-8") as f:
                f.write(svg_content)

    def _generate_html(
        self,
        base_name: str,
        var_name: str,
        var_values: List[float],
        options: Dict[str, Any],
    ) -> str:
        """Generate HTML with slider and frame-swapping JavaScript.

        Args:
            base_name: Base name for frame directory
            var_name: Variable name
            var_values: List of values
            options: Directive options

        Returns:
            HTML string
        """
        import uuid

        unique_id = uuid.uuid4().hex[:8]
        width = options.get("width", "80%")
        height = options.get("height", "auto")
        align = options.get("align", "center")

        # Determine wrapper styling based on alignment
        if align == "left":
            wrapper_style = f"display: inline-block; max-width: {width}; float: left; clear: left;"
        elif align == "right":
            wrapper_style = f"display: inline-block; max-width: {width}; float: right; clear: right;"
        else:  # center or default
            wrapper_style = f"max-width: {width}; margin: 0 auto; display: block;"

        # Calculate relative path based on document depth
        # self.env.docname gives us the path like "book/omvendte_funksjoner/derivasjon/oppgaver"
        # The HTML output mirrors this structure, so we count slashes to determine depth
        docname = self.env.docname
        depth = docname.count("/")  # Number of directory levels from root
        rel_prefix = "../" * depth  # Each level needs one "../" to reach root

        # Generate frame paths using relative paths that work from any page depth
        frame_paths = [
            f"{rel_prefix}_static/interactive/{base_name}/frame_{i:04d}.svg"
            for i in range(len(var_values))
        ]

        # JavaScript array of frame paths
        frame_paths_js = "[" + ",".join(f'"{p}"' for p in frame_paths) + "]"

        # JavaScript array of values
        values_js = "[" + ",".join(f"{v:.10f}" for v in var_values) + "]"

        var_min = var_values[0]
        var_max = var_values[-1]
        initial_idx = self._get_initial_frame_index(var_values, options)
        initial_value = var_values[initial_idx]

        # Add preload hints for initial frame and nearby frames for faster loading
        preload_links = []
        for i in range(max(0, initial_idx - 3), min(len(frame_paths), initial_idx + 4)):
            preload_links.append(f'<link rel="preload" as="image" href="{frame_paths[i]}">')
        preload_html = "\n".join(preload_links)

        html = f"""
{preload_html}
<div class="interactive-graph-wrapper" style="{wrapper_style}">
<div class="interactive-graph-container" style="display: inline-block; width: 100%;">
    <div class="interactive-graph-display" style="text-align: center;">
        <img id="interactive-img-{unique_id}" 
             class="adaptive-figure"
             src="{frame_paths[initial_idx]}" 
             alt="Interactive graph"
             style="width: 100%; height: {height}; display: block;"
             loading="eager">
    </div>
    <div class="interactive-graph-controls" style="padding: 8px 0; text-align: center;">
        <div style="display: flex; align-items: center; gap: 10px; max-width: 600px; margin: 0 auto;">
            <span style="font-family: monospace; min-width: 40px; text-align: right; font-size: 14px;">{var_min:.2f}</span>
            <input type="range" 
                   id="interactive-slider-{unique_id}"
                   class="interactive-slider"
                   min="0" 
                   max="{len(var_values) - 1}" 
                   value="{initial_idx}"
                   step="1"
                   style="flex: 1; cursor: pointer; -webkit-appearance: none; appearance: none; height: 8px; border-radius: 5px; background: #ddd; outline: none; pointer-events: auto; z-index: 100; position: relative;">
            <span style="font-family: monospace; min-width: 40px; text-align: left; font-size: 14px;">{var_max:.2f}</span>
        </div>
        <div style="margin-top: 10px; font-family: monospace; font-size: 16px; font-weight: bold;">
            <span id="interactive-value-{unique_id}">{var_name} = {initial_value:.2f}</span>
        </div>
    </div>
</div>

<style>
.interactive-slider::-webkit-slider-thumb {{
    -webkit-appearance: none;
    appearance: none;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: #2196F3;
    cursor: pointer;
    pointer-events: auto;
}}

.interactive-slider::-moz-range-thumb {{
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: #2196F3;
    cursor: pointer;
    pointer-events: auto;
    border: none;
}}

.interactive-slider:hover {{
    opacity: 1;
}}

.interactive-slider:active::-webkit-slider-thumb {{
    background: #1976D2;
}}

.interactive-slider:active::-moz-range-thumb {{
    background: #1976D2;
}}
</style>

<script>
(function() {{
    console.log('Interactive graph script starting for {unique_id}');
    
    const frames = {frame_paths_js};
    const values = {values_js};
    const img = document.getElementById('interactive-img-{unique_id}');
    const slider = document.getElementById('interactive-slider-{unique_id}');
    const valueDisplay = document.getElementById('interactive-value-{unique_id}');
    
    console.log('Elements found:', {{
        img: !!img,
        slider: !!slider,
        valueDisplay: !!valueDisplay,
        framesCount: frames.length
    }});
    
    if (!img || !slider || !valueDisplay) {{
        console.error('Missing elements for {unique_id}!');
        return;
    }}
    
    // Create image cache for instant switching
    const imageCache = {{}};
    let pendingFrame = null;
    
    function updateFrame() {{
        const index = parseInt(slider.value);
        
        // Cancel any pending frame update
        if (pendingFrame !== null) {{
            cancelAnimationFrame(pendingFrame);
        }}
        
        // Use requestAnimationFrame for smoother updates
        pendingFrame = requestAnimationFrame(() => {{
            // Use cached image if available for instant display
            if (imageCache[index]) {{
                img.src = imageCache[index].src;
            }} else {{
                img.src = frames[index];
            }}
            valueDisplay.textContent = '{var_name} = ' + values[index].toFixed(2);
            pendingFrame = null;
        }});
    }}
    
    // Aggressive preloading strategy
    const preloadedFrames = new Set();
    
    function preloadFrame(index) {{
        if (preloadedFrames.has(index) || index < 0 || index >= frames.length) return;
        preloadedFrames.add(index);
        
        const imgObj = new Image();
        imgObj.src = frames[index];
        imageCache[index] = imgObj;
    }}
    
    function preloadNearbyFrames(currentIdx, radius) {{
        // Preload frames in order of importance: current, then alternating left/right
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
        // Aggressively preload ALL frames immediately in batches
        const currentIdx = parseInt(slider.value);
        const total = frames.length;
        const batchSize = 10; // Larger batches for faster loading
        let loaded = 0;
        
        function loadBatch() {{
            const start = loaded;
            const end = Math.min(loaded + batchSize, total);
            
            // Load batch starting from current position and spiraling out
            for (let i = start; i < end; i++) {{
                const offset = Math.floor(i / 2) + 1;
                const idx = i % 2 === 0 
                    ? (currentIdx + offset) % total
                    : (currentIdx - offset + total) % total;
                preloadFrame(idx);
            }}
            
            loaded = end;
            
            if (loaded < total) {{
                // Continue loading immediately - no delays
                requestAnimationFrame(loadBatch);
            }} else {{
                console.log('All {len(var_values)} frames preloaded for {unique_id}');
            }}
        }}
        
        loadBatch();
    }}
    
    // Function to initialize the graph
    function initializeGraph() {{
        console.log('Initializing graph {unique_id}');
        // Force reload the current frame
        updateFrame();
        
        // Immediately start aggressive preloading
        const currentIdx = parseInt(slider.value);
        preloadNearbyFrames(currentIdx, 20); // Preload 40 frames around current
        
        // Start loading all frames immediately (no delay)
        preloadAllFrames();
    }}
    
    // Optimize slider interaction with debouncing for preloading
    let preloadTimer = null;
    function onSliderInput() {{
        updateFrame(); // Update immediately
        
        // Debounce nearby preloading to avoid excessive preload calls
        if (preloadTimer) clearTimeout(preloadTimer);
        preloadTimer = setTimeout(() => {{
            const currentIdx = parseInt(slider.value);
            preloadNearbyFrames(currentIdx, 10);
        }}, 50);
    }}
    
    slider.addEventListener('input', onSliderInput);
    slider.addEventListener('change', updateFrame);
    
    // Touch events for mobile
    slider.addEventListener('touchmove', onSliderInput);
    
    // Keyboard navigation
    slider.addEventListener('keydown', function(e) {{
        if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') {{
            e.preventDefault();
            this.value = Math.max(0, parseInt(this.value) - 1);
            updateFrame();
        }} else if (e.key === 'ArrowRight' || e.key === 'ArrowUp') {{
            e.preventDefault();
            this.value = Math.min({len(var_values) - 1}, parseInt(this.value) + 1);
            updateFrame();
        }}
    }});
    
    // Check if inside a dropdown admonition
    let dropdownParent = img.closest('.admonition.dropdown');
    
    if (dropdownParent) {{
        console.log('Graph {unique_id} is inside a dropdown');
        
        // Find the toggle button (summary element or button)
        const toggleButton = dropdownParent.querySelector('summary, .admonition-title');
        
        if (toggleButton) {{
            // Check if already open
            const isOpen = !dropdownParent.classList.contains('toggle');
            
            if (isOpen) {{
                // Already open, initialize immediately
                initializeGraph();
            }} else {{
                // Wait for dropdown to be opened
                let initialized = false;
                
                // Listen for click on toggle
                toggleButton.addEventListener('click', function() {{
                    if (!initialized) {{
                        // Small delay to ensure dropdown is fully opened
                        setTimeout(function() {{
                            initializeGraph();
                            initialized = true;
                        }}, 50);
                    }}
                }}, {{ once: false }});
                
                // Also use MutationObserver as backup
                const observer = new MutationObserver(function(mutations) {{
                    mutations.forEach(function(mutation) {{
                        if (mutation.type === 'attributes' && mutation.attributeName === 'class') {{
                            const isNowOpen = !dropdownParent.classList.contains('toggle');
                            if (isNowOpen && !initialized) {{
                                setTimeout(function() {{
                                    initializeGraph();
                                    initialized = true;
                                    observer.disconnect();
                                }}, 50);
                            }}
                        }}
                    }});
                }});
                
                observer.observe(dropdownParent, {{ 
                    attributes: true,
                    attributeFilter: ['class']
                }});
            }}
        }} else {{
            // No toggle found, initialize anyway
            initializeGraph();
        }}
    }} else {{
        // Not in dropdown, initialize immediately
        initializeGraph();
    }}
    
    console.log('Event listeners attached successfully');
}})();
</script>
</div>
"""
        return html


def setup(app: Sphinx) -> Dict[str, Any]:
    """Setup the interactive-graph directive."""
    app.add_directive("interactive-graph", InteractiveGraphDirective)

    return {
        "version": "0.1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
