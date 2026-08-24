"""Interactive ``plot3d-2`` directive.

The public directive name is ``interactive-plot3d``. Its authoring syntax is
the ``interactive-graph`` slider syntax combined with the drawing primitives
from ``plot3d-2``:

.. code-block:: rst

   .. interactive-plot3d::

      interactive-var: a, 0, 2, 5
      vector: (0, 0, 0), (a, 1, 1), blue

At build time the directive substitutes slider variables into the 3D plot
content, renders one SVG per frame with the ``plot3d-2`` renderer, and stores
the frames as ``base.svg`` plus ``deltas.json`` so the browser can update the
figure with the same runtime used by ``interactive-graph``.
"""

from __future__ import annotations

import itertools
import json
import os
import re
import shutil
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any, Dict, List, Tuple

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.application import Sphinx

from munchboka_edutools.directives._plot_common import parse_kv_block
from munchboka_edutools.directives.animate import (
    _hash_key,
    _parse_bool,
    _substitute_variable,
    _substitute_variables,
)
from munchboka_edutools.directives.interactive_graph import InteractiveGraphDirective
from munchboka_edutools.directives.plot3d_2 import (
    _MULTI_KEYS as _PLOT3D2_MULTI_KEYS,
    _render_plot3d2_svg_from_lines,
    Plot3d2Directive,
)


_INTERACTIVE_PLOT3D_RENDER_VERSION = 1
_INTERACTIVE_KEYS = {
    "interactive-var",
    "interactive-var-start",
    "interactive-max-frames",
    "interactive-workers",
    "parallel",
}
_CAMERA_KEYS = {"azim", "elev", "zoom"}
_MULTI_KEYS = set(_PLOT3D2_MULTI_KEYS) | {"interactive-var"}


def _substitute_plot3d_variable(content: str, var_name: str, var_value: float) -> str:
    """Substitute a 3D interactive variable without rewriting matching keys.

    The shared 2D substitution helper works on the whole line. That is fine for
    most plot content, but it breaks the natural 3D camera syntax
    ``interactive-var: azim, ...`` plus ``azim: azim`` by turning the key into
    ``-20: -20``. Preserve a matching key and substitute only its value side.
    """

    result_lines: list[str] = []
    for line in content.split("\n"):
        match = re.match(r"^(\s*)([A-Za-z_][\w-]*)(\s*:\s*)(.*)$", line)
        if match and match.group(2) == var_name:
            prefix = "".join(match.group(i) for i in range(1, 4))
            value = _substitute_variable(match.group(4), var_name, var_value)
            result_lines.append(prefix + value)
        else:
            result_lines.append(_substitute_variable(line, var_name, var_value))
    return "\n".join(result_lines)


def _substitute_plot3d_variables(content: str, variables: dict[str, float]) -> str:
    """Substitute multiple 3D interactive variables without rewriting keys."""

    if not variables:
        return content

    result_lines: list[str] = []
    for line in content.split("\n"):
        match = re.match(r"^(\s*)([A-Za-z_][\w-]*)(\s*:\s*)(.*)$", line)
        if match and match.group(2) in variables:
            prefix = "".join(match.group(i) for i in range(1, 4))
            value = _substitute_variables(match.group(4), variables)
            result_lines.append(prefix + value)
        else:
            result_lines.append(_substitute_variables(line, variables))
    return "\n".join(result_lines)


def _plot3d_content_uses_interactive_camera(
    plot_content_lines: List[str],
    var_names: set[str],
) -> bool:
    """Return True when an interactive variable drives a camera option."""

    if not var_names:
        return False

    for line in plot_content_lines:
        match = re.match(r"^\s*([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
        if not match or match.group(1) not in _CAMERA_KEYS:
            continue
        value = match.group(2)
        if any(re.search(r"\b" + re.escape(var_name) + r"\b", value) for var_name in var_names):
            return True
    return False


def _save_full_svg_delta_format(svg_frames: List[str], output_dir: str) -> None:
    """Save frames as full-SVG entries in the delta format."""

    from munchboka_edutools.directives.svg_delta import (
        _prepare_svg_for_deltas,
        save_delta_format,
    )

    if not svg_frames:
        raise ValueError("Need at least one frame")

    prepared_frames = [_prepare_svg_for_deltas(svg) for svg in svg_frames]
    deltas: list[dict[str, Any]] = [{"frame": 0, "changes": {}}]
    deltas.extend(
        {"frame": frame_index, "fullSvg": prepared_frames[frame_index]}
        for frame_index in range(1, len(prepared_frames))
    )
    save_delta_format(prepared_frames[0], deltas, output_dir)


def _render_plot3d2_svg_frame_worker(task: Tuple[str, Dict[str, Any], bool]) -> str:
    """Render one already-substituted ``plot3d-2`` frame in a worker process."""

    frame_content, render_options, default_usetex = task
    return _render_plot3d2_svg_from_lines(
        frame_content.splitlines(),
        render_options,
        default_usetex=default_usetex,
        alt=str(render_options.get("alt", "3D-koordinatsystem")),
        width="",
        rewrite_ids=False,
    )


class InteractivePlot3dDirective(InteractiveGraphDirective):
    """Create an interactive ``plot3d-2`` figure with one or more sliders."""

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True

    option_spec = {
        "interactive-var": directives.unchanged,
        "interactive-var-start": directives.unchanged,
        "interactive-max-frames": directives.nonnegative_int,
        "interactive-workers": directives.unchanged,
        "parallel": directives.unchanged,
        "height": directives.unchanged,
        "caption": directives.unchanged,
        **Plot3d2Directive.option_spec,
    }

    def run(self) -> List[nodes.Node]:
        """Parse the directive, render cached frame assets, and return HTML.

        The implementation intentionally mirrors ``InteractiveGraphDirective``
        where possible, but routes frame rendering through ``plot3d-2`` instead
        of the 2D ``plot`` directive.
        """

        app = self.env.app
        env = self.env

        content_lines = [str(line).rstrip("\n") for line in self.content]
        scalars, lists, caption_idx = parse_kv_block(content_lines, _MULTI_KEYS)
        merged = {**scalars, **self.options}

        var_specs: List[str] = []
        if lists.get("interactive-var"):
            var_specs.extend(lists["interactive-var"])
        elif merged.get("interactive-var"):
            var_specs.append(str(merged.get("interactive-var")))

        if not var_specs:
            return [
                self.state_machine.reporter.error(
                    "interactive-var option is required (format: name, min, max, frames). "
                    "For multiple variables, repeat `interactive-var:` lines.",
                    line=self.lineno,
                )
            ]

        try:
            var_axes: List[Tuple[str, List[float]]] = [
                self._parse_interactive_var(spec) for spec in var_specs
            ]
        except ValueError as exc:
            return [
                self.state_machine.reporter.error(
                    f"Invalid interactive-var: {exc}",
                    line=self.lineno,
                )
            ]

        seen: set[str] = set()
        for var_name, _var_values in var_axes:
            if var_name in seen:
                return [
                    self.state_machine.reporter.error(
                        f"Duplicate interactive-var name: {var_name}",
                        line=self.lineno,
                    )
                ]
            seen.add(var_name)

        is_multi = len(var_axes) > 1
        if is_multi:
            total_frames = 1
            for _var_name, var_values in var_axes:
                total_frames *= max(1, len(var_values))
            max_frames = int(merged.get("interactive-max-frames") or 10000)
            if total_frames > max_frames:
                return [
                    self.state_machine.reporter.error(
                        f"interactive-plot3d would generate {total_frames} frames "
                        f"(product of steps). Reduce steps or set interactive-max-frames "
                        f"to a higher value.",
                        line=self.lineno,
                    )
                ]

        plot_content_lines: List[str] = []
        for index, line in enumerate(content_lines):
            if index >= caption_idx:
                break
            match = re.match(r"^([A-Za-z_][\w-]*)\s*:", line.strip())
            if match and match.group(1) in _INTERACTIVE_KEYS:
                continue
            plot_content_lines.append(line)

        hash_key = _hash_key(
            _INTERACTIVE_PLOT3D_RENDER_VERSION,
            "\n".join(var_specs),
            "\n".join(plot_content_lines),
            str(merged),
            "interactive-plot3d",
        )
        base_name = f"interactive_plot3d_{hash_key}"
        frame_dir = os.path.join(env.srcdir, "_static", "interactive", base_name)

        delta_base_path = os.path.join(frame_dir, "base.svg")
        delta_json_path = os.path.join(frame_dir, "deltas.json")
        meta_json_path = os.path.join(frame_dir, "meta.json")
        has_delta_format = os.path.isfile(delta_base_path) and os.path.isfile(delta_json_path)
        first_var_name, first_var_values = var_axes[0]
        has_frame_files = (
            (not is_multi)
            and os.path.isdir(frame_dir)
            and len(os.listdir(frame_dir)) >= len(first_var_values)
        )

        regenerate = "nocache" in merged or not (has_delta_format or has_frame_files)
        if is_multi and has_delta_format and not os.path.isfile(meta_json_path):
            regenerate = True

        if regenerate:
            try:
                if os.path.isdir(frame_dir):
                    shutil.rmtree(frame_dir)
                if is_multi:
                    self._generate_plot3d_frames_multi(
                        app,
                        var_axes,
                        plot_content_lines,
                        frame_dir,
                        merged,
                    )
                else:
                    self._generate_plot3d_frames(
                        app,
                        first_var_name,
                        first_var_values,
                        plot_content_lines,
                        frame_dir,
                        merged,
                    )
            except Exception as exc:
                return [
                    self.state_machine.reporter.error(
                        f"Error generating interactive 3D plot: {exc}",
                        line=self.lineno,
                    )
                ]

        env.note_dependency(frame_dir)
        try:
            build_static_dir = os.path.join(app.outdir, "_static", "interactive", base_name)
            os.makedirs(os.path.dirname(build_static_dir), exist_ok=True)
            if os.path.exists(build_static_dir):
                shutil.rmtree(build_static_dir)
            shutil.copytree(frame_dir, build_static_dir)
        except Exception:
            pass

        if is_multi:
            html_content = self._generate_html_multi(base_name, var_axes, merged)
        else:
            html_content = self._generate_html(
                base_name,
                first_var_name,
                first_var_values,
                merged,
            )

        raw_node = nodes.raw("", html_content, format="html")
        raw_node.setdefault("classes", []).extend(["interactive-plot3d", "no-click"])
        caption_lines = content_lines[caption_idx:]
        align = str(merged.get("align", "center"))

        if align in ("left", "right"):
            container = nodes.container()
            container.setdefault("classes", []).extend(["interactive-figure", "no-click"])
            container += raw_node
            if caption_lines:
                caption_para = nodes.paragraph()
                parsed_nodes, _messages = self.state.inline_text(
                    "\n".join(caption_lines),
                    self.lineno,
                )
                caption_para.extend(parsed_nodes)
                caption_para["classes"].append("caption")
                container += caption_para
            if self.options.get("name"):
                self.add_name(container)
            return [container]

        figure = nodes.figure()
        figure.setdefault("classes", []).extend(
            ["adaptive-figure", "interactive-figure", "no-click"]
        )
        figure["align"] = align
        figure += raw_node
        if caption_lines:
            caption = nodes.caption()
            parsed_nodes, _messages = self.state.inline_text(
                "\n".join(caption_lines),
                self.lineno,
            )
            caption.extend(parsed_nodes)
            figure += caption
        if self.options.get("name"):
            self.add_name(figure)
        return [figure]

    def _render_svg(self, app: Sphinx, frame_content: str, options: Dict[str, Any]) -> str:
        """Render a substituted ``plot3d-2`` content block to inline SVG."""

        default_usetex = bool(getattr(app.config, "plot_default_usetex", True))
        return _render_plot3d2_svg_from_lines(
            frame_content.splitlines(),
            options,
            default_usetex=default_usetex,
            alt=str(options.get("alt", "3D-koordinatsystem")),
            width="",
            rewrite_ids=False,
        )

    def _render_options(self, merged_options: Dict[str, Any]) -> Dict[str, Any]:
        """Remove interactive-only keys before passing options to ``plot3d-2``."""

        render_options = dict(merged_options)
        for key in _INTERACTIVE_KEYS:
            render_options.pop(key, None)
        return render_options

    def _iter_with_progress(self, items, *, total: int, desc: str):
        """Yield items while reporting coarse Sphinx build progress."""

        from sphinx.util import logging

        logger = logging.getLogger(__name__)
        log_every = max(1, total // 20)
        for n, item in enumerate(items, 1):
            if n == 1 or n == total or (n % log_every) == 0:
                logger.info(f"{desc}: {n}/{total}")
            yield item

    def _generate_plot3d_frames(
        self,
        app: Sphinx,
        var_name: str,
        var_values: List[float],
        plot_content_lines: List[str],
        output_dir: str,
        merged_options: Dict[str, Any],
    ) -> None:
        """Generate frame assets for a single slider variable."""

        from sphinx.util import logging

        from munchboka_edutools.directives.svg_delta import compute_svg_deltas, save_delta_format

        logger = logging.getLogger(__name__)
        os.makedirs(output_dir, exist_ok=True)
        render_options = self._render_options(merged_options)
        use_full_svg_deltas = _plot3d_content_uses_interactive_camera(
            plot_content_lines,
            {var_name},
        )
        total_frames = len(var_values)
        desc = f"interactive-plot3d({var_name})"
        parallel_enabled = _parse_bool(merged_options.get("parallel"), default=False)
        worker_count = (
            self._get_interactive_worker_count(total_frames, merged_options)
            if parallel_enabled
            else 1
        )

        svg_frames: List[str] = []
        if worker_count > 1:
            default_usetex = bool(getattr(app.config, "plot_default_usetex", True))
            tasks = []
            for value in var_values:
                frame_content = _substitute_plot3d_variable(
                    "\n".join(plot_content_lines),
                    var_name,
                    value,
                )
                tasks.append((frame_content, render_options, default_usetex))
            try:
                import multiprocessing

                completed_svgs: List[str | None] = [None] * total_frames
                mp_context = multiprocessing.get_context("spawn")
                with ProcessPoolExecutor(
                    max_workers=worker_count,
                    mp_context=mp_context,
                ) as executor:
                    future_to_index = {
                        executor.submit(_render_plot3d2_svg_frame_worker, task): index
                        for index, task in enumerate(tasks)
                    }
                    for future in self._iter_with_progress(
                        as_completed(future_to_index),
                        total=total_frames,
                        desc=desc,
                    ):
                        completed_svgs[future_to_index[future]] = future.result()
                svg_frames = [svg for svg in completed_svgs if svg is not None]
            except Exception as exc:
                logger.warning(
                    f"{desc}: parallel rendering failed, falling back to serial mode: {exc}"
                )
                worker_count = 1

        if worker_count <= 1:
            value_iter = self._iter_with_progress(
                var_values,
                total=total_frames,
                desc=desc,
            )
            for value in value_iter:
                frame_content = _substitute_plot3d_variable(
                    "\n".join(plot_content_lines),
                    var_name,
                    value,
                )
                svg_frames.append(self._render_svg(app, frame_content, render_options))

        try:
            if use_full_svg_deltas:
                _save_full_svg_delta_format(svg_frames, output_dir)
            else:
                base_svg, deltas = compute_svg_deltas(svg_frames)
                save_delta_format(base_svg, deltas, output_dir)
        except Exception as exc:
            logger.warning(
                f"{desc}: delta generation failed, using frame-based fallback: {exc}"
            )
            for index, svg in enumerate(svg_frames):
                with open(
                    os.path.join(output_dir, f"frame_{index:04d}.svg"),
                    "w",
                    encoding="utf-8",
                ) as frame_file:
                    frame_file.write(svg)

    def _generate_plot3d_frames_multi(
        self,
        app: Sphinx,
        var_axes: List[Tuple[str, List[float]]],
        plot_content_lines: List[str],
        output_dir: str,
        merged_options: Dict[str, Any],
    ) -> None:
        """Generate delta assets and metadata for multiple slider variables."""

        from sphinx.util import logging

        from munchboka_edutools.directives.svg_delta import compute_svg_deltas, save_delta_format

        logger = logging.getLogger(__name__)
        os.makedirs(output_dir, exist_ok=True)
        render_options = self._render_options(merged_options)
        var_names = [var_name for var_name, _var_values in var_axes]
        use_full_svg_deltas = _plot3d_content_uses_interactive_camera(
            plot_content_lines,
            set(var_names),
        )
        var_values_list = [var_values for _var_name, var_values in var_axes]
        lengths = [len(var_values) for var_values in var_values_list]
        strides = self._compute_strides(lengths)
        initial_indices = self._get_initial_indices(var_axes, merged_options)
        frame_indices = list(itertools.product(*[range(length) for length in lengths]))
        total_frames = len(frame_indices)
        desc = "interactive-plot3d(" + "x".join(var_names) + ")"
        worker_count = self._get_interactive_worker_count(total_frames, merged_options)

        svg_frames: List[str] = []
        if worker_count > 1:
            default_usetex = bool(getattr(app.config, "plot_default_usetex", True))
            tasks = []
            for idx_tuple in frame_indices:
                variables = {
                    var_names[i]: var_values_list[i][idx_tuple[i]]
                    for i in range(len(var_names))
                }
                frame_content = _substitute_plot3d_variables(
                    "\n".join(plot_content_lines),
                    variables,
                )
                tasks.append((frame_content, render_options, default_usetex))
            try:
                import multiprocessing

                completed_svgs: List[str | None] = [None] * total_frames
                mp_context = multiprocessing.get_context("spawn")
                with ProcessPoolExecutor(
                    max_workers=worker_count,
                    mp_context=mp_context,
                ) as executor:
                    future_to_index = {
                        executor.submit(_render_plot3d2_svg_frame_worker, task): index
                        for index, task in enumerate(tasks)
                    }
                    for future in self._iter_with_progress(
                        as_completed(future_to_index),
                        total=total_frames,
                        desc=desc,
                    ):
                        completed_svgs[future_to_index[future]] = future.result()
                svg_frames = [svg for svg in completed_svgs if svg is not None]
            except Exception as exc:
                logger.warning(
                    f"{desc}: parallel rendering failed, falling back to serial mode: {exc}"
                )
                worker_count = 1

        if worker_count <= 1:
            for idx_tuple in self._iter_with_progress(
                frame_indices,
                total=total_frames,
                desc=desc,
            ):
                variables = {
                    var_names[i]: var_values_list[i][idx_tuple[i]]
                    for i in range(len(var_names))
                }
                frame_content = _substitute_plot3d_variables(
                    "\n".join(plot_content_lines),
                    variables,
                )
                svg_frames.append(self._render_svg(app, frame_content, render_options))

        if use_full_svg_deltas:
            _save_full_svg_delta_format(svg_frames, output_dir)
            deltas = [{"frame": frame_index} for frame_index in range(len(svg_frames))]
        else:
            base_svg, deltas = compute_svg_deltas(svg_frames)
            save_delta_format(base_svg, deltas, output_dir)

        meta = {
            "format_version": "2.0",
            "frame_count": len(deltas),
            "variables": [
                {
                    "name": var_name,
                    "values": var_values,
                    "min": var_values[0] if var_values else None,
                    "max": var_values[-1] if var_values else None,
                    "steps": len(var_values),
                }
                for var_name, var_values in var_axes
            ],
            "lengths": lengths,
            "strides": strides,
            "initial_indices": initial_indices,
        }
        with open(os.path.join(output_dir, "meta.json"), "w", encoding="utf-8") as meta_file:
            json.dump(meta, meta_file, separators=(",", ":"))


def setup(app: Sphinx) -> Dict[str, Any]:
    app.add_directive("interactive-plot3d", InteractivePlot3dDirective)
    return {
        "version": "0.1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
