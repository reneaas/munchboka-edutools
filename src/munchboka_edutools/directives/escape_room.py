"""
Escape Room Directive
=====================

A Sphinx directive for creating interactive escape room puzzles where students must
solve problems sequentially by entering codes to unlock the next room.

Usage:
    .. escape-room::
        :case_insensitive:

        Puzzle: Step 1 title
        Code: ABC123
        Q: Question text can include markdown images and code
           ![{width="60%" class="adaptive-figure"}](path/to/img.png)

        Puzzle: Step 2 title
        Code: 42, forty-two, XLII
        Q: More content ...

Recognized headers (case-insensitive):
  - Puzzle: or Step:  - Starts a new puzzle/room
  - Code:             - Code(s) to unlock this room (comma-separated for multiple)
  - Q:                - Question/content for this room

MyST Syntax (colon-fence):
    :::{escaperoom}
    :case_insensitive:

    Puzzle: Step 1 title
    Code: ABC123
    Q: Question text
    :::

Note: Due to MyST limitations with hyphens in directive names when using colon-fence
syntax (:::), the directive is also registered as "escaperoom" (no hyphen).
"""

from __future__ import annotations

import json
import html as _html
import os
import re
import uuid
from typing import Any, Dict, List

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective


class EscapeRoomDirective(SphinxDirective):
    """Directive that renders an Escape-Room style sequence of puzzles.

    Only one question is shown at a time; students must type a code to unlock
    the next. Supports figures and code blocks like quiz/jeopardy.
    """

    has_content = True
    required_arguments = 0
    option_spec = {
        # Placeholder for future options (e.g., case-insensitive codes)
        "case_insensitive": directives.flag,
    }

    def run(self):
        self.board_id = uuid.uuid4().hex
        container_id = f"escape-room-{self.board_id}"

        data = self._parse_content()

        # Compute relative prefix to _static (same approach as jeopardy)
        source_file = self.state.document["source"]
        source_dir = os.path.dirname(source_file)
        app_src_dir = self.env.srcdir
        depth = os.path.relpath(source_dir, app_src_dir).count(os.sep)
        rel_prefix = "../" * (depth + 1)

        json_str = json.dumps(data, ensure_ascii=False)
        # Escape JSON for safe embedding in a double-quoted attribute
        attr_json = _html.escape(json_str, quote=True)

        # Note: CSS and JS are registered in __init__.py with munchboka/ prefix
        # KaTeX is also loaded globally, no need to load it per-directive
        html = f"""
        <div id="{container_id}" class="escape-room-container" data-config="{attr_json}">
          <script type="application/json" class="escape-room-data">{json_str}</script>
        </div>
        """

        return [nodes.raw("", html, format="html")]

    # -------------------- parsing helpers --------------------
    def _parse_content(self) -> Dict[str, Any]:
        steps: List[Dict[str, Any]] = []
        current: Dict[str, Any] | None = None
        current_section: str | None = None  # 'Q'

        def flush():
            nonlocal current
            if current is not None:
                # normalize
                current.setdefault("title", "")
                codes = current.get("codes") or []
                current["codes"] = [str(c).strip() for c in codes if str(c).strip()]
                current.setdefault("question", "")
                # post-process code blocks
                current["question"] = self._process_code_blocks(current["question"])
                steps.append(current)
            current = None

        for raw in self.content:
            line = self._process_figures(raw) or raw
            s = line.rstrip("\n")

            # Puzzle/Step header
            m = re.match(r"^\s*(?:Puzzle|Step)\s*:\s*(.+?)\s*$", s, flags=re.IGNORECASE)
            if m:
                flush()
                current = {"title": m.group(1).strip(), "codes": [], "question": ""}
                current_section = None
                continue

            # Code line (allow comma-separated)
            m = re.match(r"^\s*Code\s*:\s*(.+?)\s*$", s, flags=re.IGNORECASE)
            if m and current is not None:
                codes_str = m.group(1).strip()
                codes = [c.strip() for c in re.split(r",|;", codes_str)] if codes_str else []
                current["codes"] = codes
                continue

            # Q: starts question block
            m = re.match(r"^\s*Q\s*:\s*(.*)$", s, flags=re.IGNORECASE)
            if m and current is not None:
                current_section = "Q"
                current["question"] = (current.get("question") or "") + m.group(1)
                continue

            # Continuation
            if current_section == "Q" and current is not None:
                current["question"] = (current.get("question") or "") + "\n" + s
                continue

        flush()

        case_insensitive = "case_insensitive" in self.options
        return {"steps": steps, "caseInsensitive": bool(case_insensitive)}

    def _process_figures(self, text):
        """Copy images to _static/figurer/... and rewrite to HTML, like quiz/jeopardy."""
        import shutil
        import json as _json

        if not hasattr(self, "_image_counter"):
            self._image_counter = 0

        def _parse_figure_options(alt_text):
            # Support JSON-like {width: 60%, class: adaptive-figure} and key=value forms
            opts = {}
            s = (alt_text or "").strip()

            def parse_pairs(text: str):
                for m in re.finditer(r'(\w+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s}]+))', text):
                    val = m.group(2) or m.group(3) or m.group(4) or ""
                    opts[m.group(1)] = val

            if s.startswith("{") and s.endswith("}"):
                inner = s[1:-1].strip()
                ok = False
                try:
                    js = s
                    js = re.sub(r"(\w+)\s*:", r'"\1":', js)
                    js = re.sub(r':\s*([^",}]+)', r': "\1"', js)
                    opts.update(_json.loads(js))
                    ok = True
                except Exception:
                    ok = False
                if not ok:
                    parse_pairs(inner)
            else:
                parse_pairs(s)
                if not opts and s:
                    opts["alt"] = s
            return opts

        def _normalize_wh(val: Any) -> str:
            s = str(val).strip()
            if re.fullmatch(r"\d+(?:\.\d+)?", s):
                return f"{s}px"
            s = re.sub(r"\s+(?=(px|%|em|rem|vh|vw)$)", "", s)
            return s

        def _build_figure_html(html_img_path, options):
            user_opts = dict(options or {})
            user_class = user_opts.pop("class", "").strip()
            classes = "escape-room-image adaptive-figure" + (f" {user_class}" if user_class else "")
            alt_text = user_opts.pop("alt", "Figure")
            title = user_opts.pop("title", None)
            width = user_opts.pop("width", None)
            height = user_opts.pop("height", None)
            extra_style = user_opts.pop("style", None)

            styles: List[str] = []
            if width is not None:
                styles.append(f"width: {_normalize_wh(width)};")
            if height is not None:
                styles.append(f"height: {_normalize_wh(height)};")
            if extra_style:
                styles.append(str(extra_style))

            attrs = [
                f'src="{html_img_path}"',
                f'class="{classes}"',
                f'alt="{alt_text}"',
            ]
            if title:
                attrs.append(f'title="{title}"')
            if styles:
                attrs.append(f'style="{' '.join(styles)}"')
            for k, v in user_opts.items():
                if k not in {
                    "src",
                    "class",
                    "alt",
                    "title",
                    "width",
                    "height",
                    "style",
                }:
                    attrs.append(f'{k}="{v}"')

            img = f"<img {' '.join(attrs)}>"
            return f'<div class="escape-room-image-container">{img}</div>'

        def replace(m):
            alt_or_opts = m.group(1).strip()
            raw_src = m.group(2)

            self._image_counter += 1

            options = _parse_figure_options(alt_or_opts)

            source_file = self.state.document["source"]
            source_dir = os.path.dirname(source_file)
            app_src_dir = self.env.srcdir

            abs_fig_src = os.path.normpath(os.path.join(source_dir, raw_src))
            if not os.path.exists(abs_fig_src):
                return f'<img src="{raw_src}" class="escape-room-image adaptive-figure" alt="Figure (missing)">'  # noqa: E501

            relative_doc_path = os.path.relpath(source_dir, app_src_dir)
            figure_dest_dir = os.path.join(app_src_dir, "_static", "figurer", relative_doc_path)
            os.makedirs(figure_dest_dir, exist_ok=True)

            rel_path_from_source = os.path.relpath(abs_fig_src, source_dir)
            safe_path = rel_path_from_source.replace(os.sep, "_").replace("/", "_")
            base, ext = os.path.splitext(safe_path)
            fig_filename = f"{self.board_id}_img{self._image_counter}_{base}{ext}"
            fig_dest_path = os.path.join(figure_dest_dir, fig_filename)
            shutil.copy2(abs_fig_src, fig_dest_path)

            depth = os.path.relpath(source_dir, app_src_dir).count(os.sep)
            rel_prefix = "../" * (depth + 1)
            html_img_path = f"{rel_prefix}_static/figurer/{relative_doc_path}/{fig_filename}"
            return _build_figure_html(html_img_path, options)

        return re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", replace, text)

    def _process_code_blocks(self, text: str) -> str:
        """Process HTML code blocks to handle escaped newlines (like quiz)."""

        def replace_newlines(match):
            lang = match.group(1)
            code = match.group(2)
            code = code.replace("\\n", "\n")
            return f'<pre><code class="{lang}">{code}</code></pre>'

        pattern = r'<pre><code class="([\w-]+)">(.*?)</code></pre>'
        return re.sub(pattern, replace_newlines, text, flags=re.DOTALL)


def setup(app):
    """
    Setup the escape-room directive.

    Registers the directive under two names:
    - "escape-room" for RST compatibility
    - "escaperoom" for MyST colon-fence compatibility (no hyphens allowed)

    Note: CSS and JS files are registered in __init__.py with the munchboka/ prefix
    """
    app.add_directive("escape-room", EscapeRoomDirective)
    app.add_directive("escaperoom", EscapeRoomDirective)  # MyST compatibility

    return {"version": "0.1", "parallel_read_safe": True, "parallel_write_safe": True}
