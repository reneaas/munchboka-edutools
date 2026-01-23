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
    _substitute_variables,
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
        # Guard for cartesian-product frame grids (only relevant for multi-var)
        "interactive-max-frames": directives.nonnegative_int,
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

        # Collect interactive variable specs.
        # Preferred syntax: repeated `interactive-var:` lines in the content.
        var_specs: List[str] = []
        if lists_dict.get("interactive-var"):
            var_specs.extend(lists_dict["interactive-var"])
        elif merged.get("interactive-var"):
            # Back-compat: single interactive-var in options/scalars.
            var_specs.append(str(merged.get("interactive-var")))

        if not var_specs:
            return [
                self.state_machine.reporter.error(
                    "interactive-var option is required (format: name, min, max, frames). "
                    "For multiple variables, repeat `interactive-var:` lines.",
                    line=self.lineno,
                )
            ]

        # Parse interactive variables (order matters)
        try:
            var_axes: List[Tuple[str, List[float]]] = [
                self._parse_interactive_var(s) for s in var_specs
            ]
        except ValueError as e:
            return [
                self.state_machine.reporter.error(
                    f"Invalid interactive-var: {e}",
                    line=self.lineno,
                )
            ]

        # Validate uniqueness
        seen = set()
        for vn, _vv in var_axes:
            if vn in seen:
                return [
                    self.state_machine.reporter.error(
                        f"Duplicate interactive-var name: {vn}",
                        line=self.lineno,
                    )
                ]
            seen.add(vn)

        is_multi = len(var_axes) > 1

        # Guard against combinatorial explosion.
        if is_multi:
            total_frames = 1
            for _vn, vv in var_axes:
                total_frames *= max(1, len(vv))

            max_frames = merged.get("interactive-max-frames")
            if max_frames is None:
                max_frames = 10000
            if total_frames > int(max_frames):
                return [
                    self.state_machine.reporter.error(
                        f"interactive-graph would generate {total_frames} frames (product of steps). "
                        f"Reduce steps or set interactive-max-frames to a higher value.",
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
        interactive_keys = {"interactive-var", "interactive-max-frames"}
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
        var_specs_for_hash = "\n".join(var_specs)
        hash_key = _hash_key(
            var_specs_for_hash,
            content_for_hash,
            str(merged),
            "interactive",
        )
        base_name = f"interactive_{hash_key}"

        # Create output paths for frames
        frame_dir = os.path.join(static_dir, base_name)

        # Check for delta format (preferred) or frame files (fallback)
        delta_base_path = os.path.join(frame_dir, "base.svg")
        delta_json_path = os.path.join(frame_dir, "deltas.json")
        meta_json_path = os.path.join(frame_dir, "meta.json")
        has_delta_format = os.path.isfile(delta_base_path) and os.path.isfile(delta_json_path)
        # Frame-based fallback is only supported for single-variable graphs.
        var_name, var_values = var_axes[0]
        has_frame_files = (
            (not is_multi)
            and os.path.isdir(frame_dir)
            and len(os.listdir(frame_dir)) >= len(var_values)
        )
        frames_exist = has_delta_format or has_frame_files

        def _delta_assets_look_corrupt() -> bool:
            """Detect legacy/broken cached delta assets.

            We previously had a bug where adding IDs via regex could truncate
            start tags, producing lines like:
              " style="..."
            instead of:
              " style="..."/>
            In that case the SVG may parse into DOM but not render.
            """
            if not has_delta_format:
                return False
            try:
                with open(delta_base_path, "r", encoding="utf-8") as f:
                    svg_text = f.read()
            except Exception:
                return True

            # Matplotlib SVG emits many self-closing tags. If we see a line that
            # looks like the end of a <path ...> tag but lacks the closing '/>',
            # treat as corrupted.
            if re.search(r'^\s*"\s+style="[^"]*"\s*$', svg_text, flags=re.MULTILINE):
                return True

            # Also catch truncated <use ...> start tags (missing '/>' or '>').
            if re.search(r'^\s*<use\b[^>]*"\s*$', svg_text, flags=re.MULTILINE):
                return True

            return False

        def _delta_assets_look_stale() -> bool:
            """Detect cached delta assets that are effectively no-ops.

            A common failure mode is that deltas only include non-visual
            metadata changes (e.g., dc:date tail text), so the slider logs
            "Applying delta" but the rendered SVG never changes.
            """
            if not has_delta_format:
                return False
            try:
                import json

                with open(delta_json_path, "r", encoding="utf-8") as f:
                    deltas = json.load(f)
            except Exception:
                return True

            def _is_noise_only(elem_id: str, changes: Dict[str, Any]) -> bool:
                # Tail text changes are not applied in the JS runtime.
                if set(changes.keys()) <= {"tailContent"}:
                    return True

                # Ignore common Matplotlib metadata ids (dc/rdf/cc) if they only
                # change tail/text content.
                if elem_id.startswith(("dc_", "rdf_", "cc_")) and set(changes.keys()) <= {
                    "tailContent",
                    "textContent",
                }:
                    return True

                return False

            # Look for at least one meaningful change across frames.
            for frame in deltas:
                changes = frame.get("changes") or {}
                for elem_id, ch in changes.items():
                    if not isinstance(ch, dict):
                        continue

                    # Marker churn guard:
                    # Matplotlib regenerates marker <defs> ids per render, which yields
                    # deltas like xlink:href="#m..." on <use> elements. Those ids do NOT
                    # exist in base.svg (only base defs are stored), so applying them
                    # makes markers (including point primitives) disappear.
                    #
                    # If we see any such delta, treat cache as stale so we regenerate
                    # with the fixed delta engine.
                    for k, v in ch.items():
                        if (
                            k
                            in (
                                "{http://www.w3.org/1999/xlink}href",
                                "xlink:href",
                                "{{http://www.w3.org/1999/xlink}}href",
                            )
                            and isinstance(v, str)
                            and v.startswith("#m")
                        ):
                            return True

                    if _is_noise_only(elem_id, ch):
                        continue
                    return False

            return True

        # Check if regeneration needed
        nocache = "nocache" in merged
        regenerate = (
            nocache
            or not frames_exist
            or _delta_assets_look_corrupt()
            or _delta_assets_look_stale()
        )

        if is_multi and has_delta_format and not os.path.isfile(meta_json_path):
            regenerate = True

        if regenerate:
            from sphinx.util import logging

            logger = logging.getLogger(__name__)
            try:
                # Ensure we don't keep broken legacy assets around.
                if os.path.isdir(frame_dir):
                    shutil.rmtree(frame_dir)

                # Generate all frames (will create delta format)
                if is_multi:
                    self._generate_frames_multi(
                        app,
                        var_axes,
                        plot_content_lines,
                        frame_dir,
                        merged,
                    )
                else:
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

        # Generate HTML output with slider(s)
        if is_multi:
            html_content = self._generate_html_multi(
                base_name,
                var_axes,
                merged,
            )
        else:
            html_content = self._generate_html(
                base_name,
                var_name,
                var_values,
                merged,
            )

        # Create output node
        raw_node = nodes.raw("", html_content, format="html")
        raw_node.setdefault("classes", []).extend(["interactive-graph", "no-click"])

        align = merged.get("align", "center")

        # For left/right alignment, use a simple container to avoid figure width issues
        # For center, use figure for consistency with other directives
        if align in ("left", "right"):
            container = nodes.container()
            container.setdefault("classes", []).extend(["interactive-figure", "no-click"])
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
                ["adaptive-figure", "interactive-figure", "no-click"]
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
            "interactive-var": [],
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
        """Generate all frames as SVG images and compute deltas.

        Args:
            app: Sphinx application
            var_name: Variable name
            var_values: List of values
            plot_content_lines: Content for plot
            output_dir: Directory to save frames
            merged_options: Merged options
        """
        import tempfile

        os.makedirs(output_dir, exist_ok=True)

        # Import frame generation from animate
        from .animate import AnimateDirective
        from .svg_delta import compute_svg_deltas, save_delta_format
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

        # Generate all frames in memory first
        svg_frames = []

        # Use temporary directory for frame generation
        with tempfile.TemporaryDirectory() as temp_dir:
            for i, value in enumerate(var_values):
                # Substitute variable in content
                frame_content = "\n".join(plot_content_lines)
                frame_content = _substitute_variable(frame_content, var_name, value)

                # Generate SVG to temp location
                svg_path = os.path.join(temp_dir, f"frame_{i:04d}.svg")
                temp_directive._generate_frame_svg(
                    app,
                    frame_content,
                    svg_path,
                    merged_options,
                    var_name,
                    value,
                )

                # Read SVG content
                with open(svg_path, "r", encoding="utf-8") as f:
                    svg_content = f.read()

                # Add consistent IDs to elements (needed for delta system)
                # Use simple numeric IDs based on frame to keep deltas small
                svg_content = self._ensure_element_ids(svg_content, i)

                svg_frames.append(svg_content)

        # Compute deltas
        try:
            base_svg, deltas = compute_svg_deltas(svg_frames)

            # Save in delta format
            save_delta_format(base_svg, deltas, output_dir)

            from sphinx.util import logging

            logger = logging.getLogger(__name__)
            logger.info(
                f"✓ Generated delta-based interactive graph: "
                f"{len(svg_frames)} frames → base.svg + deltas.json"
            )
        except Exception as e:
            # Fallback: save individual frames if delta generation fails
            import traceback
            from sphinx.util import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"⚠ Delta generation failed, using frame-based fallback: {e}")
            logger.warning(f"   Traceback: {traceback.format_exc()}")
            for i, svg in enumerate(svg_frames):
                frame_path = os.path.join(output_dir, f"frame_{i:04d}.svg")
                with open(frame_path, "w", encoding="utf-8") as f:
                    f.write(svg)

    def _compute_strides(self, lengths: List[int]) -> List[int]:
        """Row-major strides for mapping N-D indices to a 1-D frame index."""
        strides: List[int] = [1] * len(lengths)
        acc = 1
        for i in range(len(lengths) - 1, -1, -1):
            strides[i] = acc
            acc *= max(1, int(lengths[i]))
        return strides

    def _get_initial_indices(
        self, var_axes: List[Tuple[str, List[float]]], merged_options: Dict[str, Any]
    ) -> List[int]:
        """Initial slider indices for each variable.

        Back-compat: for single-var, respects `interactive-var-start`.
        Multi-var: supports `interactive-var-start: a=0, t=pi` (optional).
        """
        if not var_axes:
            return []

        if len(var_axes) == 1:
            vn, vv = var_axes[0]
            return [self._get_initial_frame_index(vv, merged_options)]

        # Default: middle index for each axis.
        indices = [len(vv) // 2 for _vn, vv in var_axes]

        start_value_str = merged_options.get("interactive-var-start")
        if not start_value_str:
            return indices

        # Parse simple name=value pairs.
        if "=" not in str(start_value_str):
            return indices

        start_map: Dict[str, float] = {}
        for part in str(start_value_str).split(","):
            if "=" not in part:
                continue
            k, v = part.split("=", 1)
            k = k.strip()
            v = v.strip()
            if not k:
                continue
            try:
                start_map[k] = _eval_expr(v)
            except Exception:
                continue

        if not start_map:
            return indices

        import numpy as np

        for i, (vn, vv) in enumerate(var_axes):
            if vn not in start_map:
                continue
            try:
                idx = int(np.argmin(np.abs(np.array(vv) - float(start_map[vn]))))
                indices[i] = idx
            except Exception:
                pass
        return indices

    def _generate_frames_multi(
        self,
        app: Sphinx,
        var_axes: List[Tuple[str, List[float]]],
        plot_content_lines: List[str],
        output_dir: str,
        merged_options: Dict[str, Any],
    ) -> None:
        """Generate a cartesian-product frame grid for multiple variables.

        Output format is always delta-based: base.svg + deltas.json + meta.json.
        """
        import itertools
        import json

        os.makedirs(output_dir, exist_ok=True)

        from .animate import AnimateDirective
        from .svg_delta import compute_svg_deltas, save_delta_format

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

        var_names = [vn for vn, _vv in var_axes]
        var_values_list = [vv for _vn, vv in var_axes]
        lengths = [len(vv) for vv in var_values_list]
        strides = self._compute_strides(lengths)
        initial_indices = self._get_initial_indices(var_axes, merged_options)

        # Generate all frames in memory first
        svg_frames: List[str] = []

        with tempfile.TemporaryDirectory() as temp_dir:
            frame_idx = 0
            for idx_tuple in itertools.product(*[range(n) for n in lengths]):
                variables = {
                    var_names[i]: var_values_list[i][idx_tuple[i]] for i in range(len(var_names))
                }

                frame_content = "\n".join(plot_content_lines)
                frame_content = _substitute_variables(frame_content, variables)

                # Reuse animate frame rendering. It only accepts a single
                # (var_name, var_value) pair; we pass the first axis.
                primary_name = var_names[0]
                primary_value = variables[primary_name]

                svg_path = os.path.join(temp_dir, f"frame_{frame_idx:04d}.svg")
                temp_directive._generate_frame_svg(
                    app,
                    frame_content,
                    svg_path,
                    merged_options,
                    primary_name,
                    primary_value,
                )

                with open(svg_path, "r", encoding="utf-8") as f:
                    svg_content = f.read()

                svg_content = self._ensure_element_ids(svg_content, frame_idx)
                svg_frames.append(svg_content)
                frame_idx += 1

        # Compute deltas and write delta assets
        base_svg, deltas = compute_svg_deltas(svg_frames)
        save_delta_format(base_svg, deltas, output_dir)

        meta = {
            "format_version": "2.0",
            "frame_count": len(deltas),
            "variables": [
                {
                    "name": vn,
                    "values": vv,
                    "min": vv[0] if vv else None,
                    "max": vv[-1] if vv else None,
                    "steps": len(vv),
                }
                for vn, vv in var_axes
            ],
            "lengths": lengths,
            "strides": strides,
            "initial_indices": initial_indices,
        }
        meta_path = os.path.join(output_dir, "meta.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, separators=(",", ":"))

        from sphinx.util import logging

        logger = logging.getLogger(__name__)
        logger.info(
            f"✓ Generated multi-var delta-based interactive graph: "
            f"{len(deltas)} frames ({'×'.join(str(n) for n in lengths)}) → base.svg + deltas.json + meta.json"
        )

    def _generate_html_multi(
        self,
        base_name: str,
        var_axes: List[Tuple[str, List[float]]],
        options: Dict[str, Any],
    ) -> str:
        """Generate HTML for delta-based multi-variable interactive graph."""
        import uuid
        import os

        unique_id = uuid.uuid4().hex[:8]
        width = options.get("width", "80%")
        height = options.get("height", "auto")
        align = options.get("align", "center")

        if align == "left":
            wrapper_style = f"width: {width}; float: left; clear: left;"
        elif align == "right":
            wrapper_style = f"width: {width}; float: right; clear: right;"
        else:
            wrapper_style = f"max-width: {width}; margin: 0 auto; display: block;"

        docname = self.env.docname
        depth = docname.count("/")
        rel_prefix = "../" * depth

        srcdir = self.env.srcdir
        static_dir = os.path.join(srcdir, "_static", "interactive", base_name)
        delta_base_path = os.path.join(static_dir, "base.svg")
        delta_json_path = os.path.join(static_dir, "deltas.json")
        meta_json_path = os.path.join(static_dir, "meta.json")
        use_delta_format = (
            os.path.isfile(delta_base_path)
            and os.path.isfile(delta_json_path)
            and os.path.isfile(meta_json_path)
        )

        if not use_delta_format:
            return (
                f"<div class='interactive-graph-wrapper' style='{wrapper_style}'>"
                f"<p style='color: red; padding: 10px;'>Failed to load multi-variable interactive graph assets.</p>"
                f"</div>"
            )

        from .svg_delta import generate_multi_delta_html

        base_svg_url = f"{rel_prefix}_static/interactive/{base_name}/base.svg"
        deltas_json_url = f"{rel_prefix}_static/interactive/{base_name}/deltas.json"
        meta_json_url = f"{rel_prefix}_static/interactive/{base_name}/meta.json"

        return generate_multi_delta_html(
            base_svg_url,
            deltas_json_url,
            meta_json_url,
            unique_id,
            wrapper_style=wrapper_style,
            height=height,
        )

    def _ensure_element_ids(self, svg_content: str, frame_idx: int) -> str:
        """
        Ensure SVG elements have consistent IDs for delta tracking.

        Uses regex-based approach to avoid XML namespace issues.
        """
        import re

        # NOTE: this function must preserve SVG validity.

        # Counter for generating IDs
        id_counters = {}

        def add_id(match):
            """Add ID to an element that doesn't have one.

            Important: preserve the original tag text exactly (including '/>' and
            any line breaks), otherwise we risk producing invalid SVG.
            """
            tag = match.group("tag")
            full_tag = match.group(0)

            # Skip if already has an id
            if "id=" in full_tag or "id =" in full_tag:
                return full_tag

            # Skip certain tags
            if tag in ("svg", "defs", "clipPath", "style", "metadata", "title", "desc"):
                return full_tag

            id_counters[tag] = id_counters.get(tag, 0)
            elem_id = f"{tag}_{id_counters[tag]}"
            id_counters[tag] += 1

            # Insert id right after the tag name, preserving everything else.
            insert_at = len(tag) + 1  # after '<tag'
            return full_tag[:insert_at] + f' id="{elem_id}"' + full_tag[insert_at:]

        # Match opening tags in a forgiving way. Excludes declarations/comments
        # because tag must start with a letter/underscore.
        pattern = r"<(?P<tag>[A-Za-z_][\w.-]*)(?P<rest>[^<>]*?)>"

        return re.sub(pattern, add_id, svg_content)

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
        import os

        unique_id = uuid.uuid4().hex[:8]
        width = options.get("width", "80%")
        height = options.get("height", "auto")
        align = options.get("align", "center")

        # Determine wrapper styling based on alignment.
        # For floats, prefer an explicit width so responsive sizing works
        # consistently for inline SVG (delta mode) and <img> (frame mode).
        if align == "left":
            wrapper_style = f"width: {width}; float: left; clear: left;"
        elif align == "right":
            wrapper_style = f"width: {width}; float: right; clear: right;"
        else:  # center or default
            wrapper_style = f"max-width: {width}; margin: 0 auto; display: block;"

        # Calculate relative path based on document depth
        docname = self.env.docname
        depth = docname.count("/")
        rel_prefix = "../" * depth

        # Check if delta format exists (use env.srcdir, same as in run())
        srcdir = self.env.srcdir
        static_dir = os.path.join(srcdir, "_static", "interactive", base_name)
        delta_base_path = os.path.join(static_dir, "base.svg")
        delta_json_path = os.path.join(static_dir, "deltas.json")
        delta_base_exists = os.path.isfile(delta_base_path)
        delta_json_exists = os.path.isfile(delta_json_path)
        use_delta_format = delta_base_exists and delta_json_exists

        if use_delta_format:
            # Use delta-based HTML
            from .svg_delta import generate_delta_html

            base_svg_url = f"{rel_prefix}_static/interactive/{base_name}/base.svg"
            deltas_json_url = f"{rel_prefix}_static/interactive/{base_name}/deltas.json"
            initial_idx = self._get_initial_frame_index(var_values, options)

            return generate_delta_html(
                base_svg_url,
                deltas_json_url,
                unique_id,
                var_name,
                var_values,
                initial_idx,
                wrapper_style,
                height,
            )
        else:
            # Fallback: frame-based HTML (old method)
            return self._generate_frame_based_html(
                base_name,
                var_name,
                var_values,
                options,
                unique_id,
                wrapper_style,
                rel_prefix,
            )

    def _generate_frame_based_html(
        self,
        base_name: str,
        var_name: str,
        var_values: List[float],
        options: Dict[str, Any],
        unique_id: str,
        wrapper_style: str,
        rel_prefix: str,
    ) -> str:
        """Generate HTML for frame-based (non-delta) interactive graph.

        This is the fallback method when delta format is not available.
        """
        height = options.get("height", "auto")

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

    function latexForVarName(name) {{
        const greek = {{
            alpha: '\\\\alpha', beta: '\\\\beta', gamma: '\\\\gamma', delta: '\\\\delta',
            epsilon: '\\\\epsilon', zeta: '\\\\zeta', eta: '\\\\eta', theta: '\\\\theta',
            iota: '\\\\iota', kappa: '\\\\kappa', lambda: '\\\\lambda', mu: '\\\\mu',
            nu: '\\\\nu', xi: '\\\\xi', pi: '\\\\pi', rho: '\\\\rho', sigma: '\\\\sigma',
            tau: '\\\\tau', upsilon: '\\\\upsilon', phi: '\\\\phi', chi: '\\\\chi',
            psi: '\\\\psi', omega: '\\\\omega',
            // Common variants
            varphi: '\\\\varphi', vartheta: '\\\\vartheta'
        }};
        if (greek[name]) return greek[name];
        // Preserve subscripts like a_1
        if (name.includes('_') || /\\d/.test(name)) return name;
        // Single-letter names are fine in math mode
        if (/^[A-Za-z]$/.test(name)) return name;
        // Multi-letter identifiers: keep as-is (e.g. "speed")
        return name;
    }}

    const varLatex = latexForVarName('{var_name}');

    function updateValueDisplay(index) {{
        const v = values[index];
        const vStr = (typeof v === 'number' ? v.toFixed(2) : String(v));
        if (window.katex && valueDisplay) {{
            try {{
                valueDisplay.innerHTML = window.katex.renderToString(varLatex + ' = ' + vStr, {{
                    throwOnError: false,
                    displayMode: false,
                }});
                return;
            }} catch (e) {{
                // fall through
            }}
        }}
        valueDisplay.textContent = '{var_name} = ' + vStr;
    }}
    
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
            updateValueDisplay(index);
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
