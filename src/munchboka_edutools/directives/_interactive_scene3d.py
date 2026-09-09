"""Sphinx output adapter for live 3D scenes (registered by interactive_plot3d)."""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
from pathlib import Path

from docutils import nodes
from sphinx.util import logging

from ._scene3d import build_scene


class Scene3DNode(nodes.General, nodes.Element):
    pass


def css_length(value, default):
    text = str(value or default).strip()
    if re.fullmatch(r"\d+(?:\.\d+)?", text):
        text += "px"
    if not re.fullmatch(r"\d+(?:\.\d+)?(?:px|%|em|rem|vh|vw)", text):
        raise ValueError(f"Invalid figure dimension: {text}")
    if float(re.match(r"[\d.]+", text).group()) <= 0:
        raise ValueError("Figure dimensions must be positive")
    return text


def visit_html(translator, node):
    data = (
        json.dumps(node["scene"], ensure_ascii=True, allow_nan=False)
        .replace("<", "\\u003c")
        .replace("&", "\\u0026")
    )
    identifier = html.escape(node["board_id"], quote=True)
    alt = html.escape(node["alt"], quote=True)
    margin = {"left": "0 auto 0 0", "right": "0 0 0 auto", "center": "0 auto"}[node["align"]]
    translator.body.append(
        f'<div class="munch-3d interactive-plot3d no-click" style="width:{node["width"]};margin:{margin}">'
        f'<script type="application/json">{data}</script>'
        f'<div class="munch-3d-board jxgbox" id="{identifier}" role="img" aria-label="{alt}" '
        f'style="height:{node["height"]}"></div>'
        '<div class="munch-3d-controls"></div>'
        '<p class="munch-3d-status" role="status">Static preview. Enable JavaScript for an interactive view.</p>'
        '<div class="munch-3d-fallback">'
    )


def depart_html(translator, node):
    translator.body.append("</div></div>")


def passthrough(translator, node):
    pass


def run_scene(directive):
    # Local import avoids a cycle with the backend dispatcher.
    from .interactive_plot3d import _substitute_plot3d_variables
    from .plot3d_2 import _render_plot3d2_svg_from_lines

    lines = list(directive.content)
    try:
        scene, settings, caption_idx = build_scene(lines, directive.options)
        width = css_length(settings.get("width"), "100%")
        height = css_length(settings.get("height"), "460px")
        align = str(settings.get("align", "center"))
        if align not in {"left", "center", "right"}:
            raise ValueError("align must be left, center, or right")
        for option in ("parallel", "interactive-workers", "interactive-max-frames"):
            if option in settings:
                logging.getLogger(__name__).warning(
                    "%s is ignored by backend: jsxgraph (no frames are generated)",
                    option,
                    location=(directive.env.docname, directive.lineno),
                )
        # Render just the initial state, shared by no-JS, printing, and non-HTML output.
        variables = {
            s["name"]: s["min"] + (s["max"] - s["min"]) * s["initial"] / (s["count"] - 1)
            for s in scene["sliders"]
        }
        initial = _substitute_plot3d_variables("\n".join(lines[:caption_idx]), variables)
        render_options = dict(settings)
        for key, value in render_options.items():
            if isinstance(value, str):
                render_options[key] = _substitute_plot3d_variables(value, variables)
        # A browser fallback should not depend on a local TeX installation.
        render_options["usetex"] = "false"
        signature = json.dumps([scene, initial, render_options], sort_keys=True, default=str)
        digest = hashlib.sha256(signature.encode()).hexdigest()[:24]
        cache = Path(directive.env.doctreedir) / "munch-scene3d"
        cache.mkdir(parents=True, exist_ok=True)
        path = cache / f"{digest}.png"
        if not path.exists() or "nocache" in settings:
            import cairosvg

            svg = _render_plot3d2_svg_from_lines(
                initial.splitlines(),
                render_options,
                default_usetex=False,
                rewrite_ids=False,
                width="",
            )
            # Atomic replacement also works with parallel Sphinx reads.
            import tempfile

            with tempfile.NamedTemporaryFile(dir=cache, suffix=".png", delete=False) as temp:
                temporary = Path(temp.name)
            try:
                cairosvg.svg2png(bytestring=svg.encode(), write_to=str(temporary), scale=2)
                os.replace(temporary, path)
            finally:
                temporary.unlink(missing_ok=True)
        alt = str(settings.get("alt", "3D-koordinatsystem"))
        scene_node = Scene3DNode(
            scene=scene,
            width=width,
            height=height,
            align=align,
            alt=alt,
            board_id=f"munch-3d-{directive.env.new_serialno('munch-scene3d')}-{digest}",
        )
        document_dir = Path(directive.env.doc2path(directive.env.docname)).parent
        scene_node += nodes.image(uri=os.path.relpath(path, document_dir), alt=alt, width="100%")
        figure = nodes.figure("", scene_node, align=align)
        classes = settings.get("class", [])
        figure["classes"] += ["interactive-figure", "no-click"] + (
            classes.split() if isinstance(classes, str) else classes
        )
        caption_text = str(settings.get("caption") or "\n".join(lines[caption_idx:])).strip()
        if caption_text:
            caption = nodes.caption()
            children, messages = directive.state.inline_text(caption_text, directive.lineno)
            caption.extend(children)
            figure += caption
            figure.extend(messages)
        if settings.get("name"):
            figure["names"].append(nodes.fully_normalize_name(str(settings["name"])))
            directive.state.document.note_explicit_target(figure)
        return [figure]
    except (ValueError, KeyError, TypeError, ArithmeticError) as exc:
        return [
            directive.state_machine.reporter.error(
                f"interactive-plot3d (jsxgraph): {exc}", line=directive.lineno
            )
        ]


def register_scene(app):
    app.add_node(
        Scene3DNode,
        html=(visit_html, depart_html),
        latex=(passthrough, passthrough),
        text=(passthrough, passthrough),
        man=(passthrough, passthrough),
        texinfo=(passthrough, passthrough),
    )
    app.connect("html-page-context", add_page_assets)


def add_page_assets(app, pagename, templatename, context, doctree):
    if doctree is None or not any(doctree.findall(Scene3DNode)):
        return
    app.add_js_file("munchboka/vendor/jsxgraph/jsxgraphcore.js", priority=400)
    app.add_js_file("munchboka/js/interactive3d/scene.js", priority=410)
    app.add_js_file("munchboka/js/interactive3d/runtime.js", priority=420)
    app.add_css_file("munchboka/vendor/jsxgraph/jsxgraph.css")
    app.add_css_file("munchboka/css/interactive3d.css")
