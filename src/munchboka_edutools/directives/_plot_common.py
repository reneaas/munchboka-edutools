"""Shared helpers for plot-like directives.

The original ``plot`` directive still owns its legacy implementation.  New and
experimental directives can import from here while we extract stable behaviour
in small, testable pieces.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import Any

from docutils import nodes


SVG_FONT_ID_SKIP_PREFIXES = (
    "DejaVu",
    "CM",
    "STIX",
    "Nimbus",
    "Bitstream",
    "Arial",
    "Times",
    "Helvetica",
)


@dataclass(frozen=True)
class InlineSvgOptions:
    """Presentation options for inline SVG figures."""

    alt: str
    width: str | None = None
    align: str = "center"
    classes: list[str] | None = None
    explicit_name: bool = False


def parse_kv_block(
    lines: list[str],
    multi_keys: set[str],
) -> tuple[dict[str, Any], dict[str, list[str]], int]:
    """Parse directive front matter into scalar and repeatable keys.

    Supports the two formats used by the legacy plot directive:

    - YAML-like fenced front matter delimited by ``---``.
    - Plain ``key: value`` lines until the first non-key/value content line.

    Returns ``(scalars, lists, caption_idx)`` where ``caption_idx`` is the first
    content line that should be interpreted as caption text.
    """

    scalars: dict[str, Any] = {}
    lists: dict[str, list[str]] = {key: [] for key in multi_keys}

    if lines and lines[0].strip() == "---":
        idx = 1
        while idx < len(lines) and lines[idx].strip() != "---":
            line = lines[idx].rstrip()
            if not line.strip():
                idx += 1
                continue
            match = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
            if match:
                key, value = match.group(1), match.group(2)
                if key in lists:
                    lists[key].append(value)
                else:
                    scalars[key] = value
            idx += 1

        if idx < len(lines) and lines[idx].strip() == "---":
            idx += 1
        while idx < len(lines) and not lines[idx].strip():
            idx += 1
        return scalars, lists, idx

    caption_start = 0
    for idx, line in enumerate(lines):
        if not line.strip():
            caption_start = idx + 1
            continue
        match = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
        if not match:
            break
        key, value = match.group(1), match.group(2)
        if key in lists:
            lists[key].append(value)
        else:
            scalars[key] = value
        caption_start = idx + 1

    return scalars, lists, caption_start


def parse_bool(value: Any, default: bool | None = None) -> bool | None:
    """Parse the bool syntax accepted by plot-style directives."""

    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text == "":
        return True
    if text in {"true", "yes", "on", "1"}:
        return True
    if text in {"false", "no", "off", "0"}:
        return False
    return default


def strip_root_svg_size(svg_text: str) -> str:
    """Remove fixed root SVG width/height attributes."""

    def repl(match: re.Match) -> str:
        tag = match.group(0)
        tag = re.sub(r'\swidth="[^"]+"', "", tag)
        tag = re.sub(r'\sheight="[^"]+"', "", tag)
        return tag

    return re.sub(r"<svg\b[^>]*>", repl, svg_text, count=1)


def rewrite_svg_ids(svg_text: str, prefix: str) -> str:
    """Prefix SVG ids and matching url()/href references.

    Matplotlib SVGs commonly use global ids for paths, markers, clip paths, and
    gradients.  Prefixing avoids collisions when multiple figures appear on the
    same HTML page.
    """

    ids = re.findall(r'\bid="([^"]+)"', svg_text)
    if not ids:
        return svg_text

    mapping = {
        old_id: f"{prefix}{old_id}"
        for old_id in ids
        if not old_id.startswith(SVG_FONT_ID_SKIP_PREFIXES)
    }
    if not mapping:
        return svg_text

    def repl_id(match: re.Match) -> str:
        old = match.group(1)
        return f'id="{mapping.get(old, old)}"'

    svg_text = re.sub(r'\bid="([^"]+)"', repl_id, svg_text)

    def repl_url(match: re.Match) -> str:
        old = match.group(1).strip()
        return f"url(#{mapping.get(old, old)})"

    svg_text = re.sub(r"url\(#\s*([^\)\s]+)\s*\)", repl_url, svg_text)

    def repl_href(match: re.Match) -> str:
        attr = match.group(1)
        quote = match.group(2)
        old = match.group(3).strip()
        return f"{attr}={quote}#{mapping.get(old, old)}{quote}"

    return re.sub(
        r'(xlink:href|href)\s*=\s*(["\"])#\s*([^"\"]+)\s*\2',
        repl_href,
        svg_text,
    )


def augment_svg_root(
    svg_text: str,
    *,
    alt: str,
    width: str | None = None,
    css_class: str = "graph-inline-svg",
) -> str:
    """Add common accessibility, class, and width attributes to root SVG."""

    percent = isinstance(width, str) and width.strip().endswith("%")

    def repl(match: re.Match) -> str:
        tag = match.group(0)
        if "class=" not in tag:
            tag = tag[:-1] + f' class="{css_class}">'
        else:
            tag = tag.replace('class="', f'class="{css_class} ', 1)

        if alt and "aria-label=" not in tag:
            tag = tag[:-1] + f' role="img" aria-label="{alt}">'

        if width:
            width_value = width.strip()
            if not percent and width_value.isdigit():
                width_value += "px"
            style_frag = f"width:{width_value}; height:auto; display:block; margin:0 auto;"
            if "style=" in tag:
                tag = re.sub(
                    r'style="([^"]*)"',
                    lambda style_match: f'style="{style_match.group(1)}; {style_frag}"',
                    tag,
                    count=1,
                )
            else:
                tag = tag[:-1] + f' style="{style_frag}">'
        return tag

    return re.sub(r"<svg\b[^>]*>", repl, svg_text, count=1)


def prepare_inline_svg(
    svg_text: str,
    *,
    content_hash: str,
    alt: str,
    width: str | None = None,
    id_prefix_base: str = "cpl",
    strip_size: bool = True,
    rewrite_ids: bool = True,
) -> str:
    """Apply the standard inline-plot SVG post-processing pipeline."""

    if strip_size and "viewBox" in svg_text:
        svg_text = strip_root_svg_size(svg_text)
    if rewrite_ids:
        svg_text = rewrite_svg_ids(
            svg_text,
            f"{id_prefix_base}_{content_hash}_{uuid.uuid4().hex[:6]}_",
        )
    return augment_svg_root(svg_text, alt=alt, width=width)


def build_inline_svg_figure(
    directive: Any,
    raw_svg: str,
    *,
    caption_lines: list[str],
    options: InlineSvgOptions,
) -> nodes.figure:
    """Create the docutils figure node used by plot-like directives."""

    figure = nodes.figure()
    figure.setdefault("classes", []).extend(["adaptive-figure", "plot-figure", "no-click"])

    raw_node = nodes.raw("", raw_svg, format="html")
    raw_node.setdefault("classes", []).extend(["graph-image", "no-click", "no-scaled-link"])
    figure += raw_node

    if options.classes:
        figure["classes"].extend(options.classes)
    figure["align"] = options.align

    caption = list(caption_lines)
    while caption and not caption[0].strip():
        caption.pop(0)
    if caption:
        caption_node = nodes.caption()
        parsed_nodes, _ = directive.state.inline_text("\n".join(caption), directive.lineno)
        caption_node.extend(parsed_nodes)
        figure += caption_node

    if options.explicit_name:
        directive.add_name(figure)

    return figure
