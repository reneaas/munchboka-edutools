from __future__ import annotations

import html as _html
import json
import os
import re
import uuid
from typing import Any, Dict, List

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective


class FlashcardsDirective(SphinxDirective):
    has_content = True
    required_arguments = 0
    option_spec = {
        "shuffle": directives.flag,
        "show_progress": directives.flag,
        "start_index": directives.nonnegative_int,
    }

    def run(self):
        deck_id = uuid.uuid4().hex
        container_id = f"flashcards-{deck_id}"

        data = self._parse_deck()

        source_file = self.state.document["source"]
        source_dir = os.path.dirname(source_file)
        app_src_dir = self.env.srcdir
        depth = os.path.relpath(source_dir, app_src_dir).count(os.sep)
        rel_prefix = "../" * (depth + 1)

        cfg: Dict[str, Any] = {
            "cards": data["cards"],
            "options": {
                "shuffle": "shuffle" in self.options,
                "show_progress": "show_progress" in self.options,
                "start_index": int(self.options.get("start_index", 0) or 0),
                "staticPrefix": rel_prefix,
            },
        }

        cfg_str_attr = _html.escape(json.dumps(cfg, ensure_ascii=False), quote=True)
        json_str = json.dumps(cfg, ensure_ascii=False)

        html = f"""
        <div id="{container_id}" class=\"flashcards-container\" data-config=\"{cfg_str_attr}\">
          <script type=\"application/json\" class=\"flashcards-data\">{json_str}</script>
        </div>
        <link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/katex/dist/katex.min.css\">
        <script defer src=\"https://cdn.jsdelivr.net/npm/katex/dist/katex.min.js\"></script>
        <script defer src=\"https://cdn.jsdelivr.net/npm/katex/dist/contrib/auto-render.min.js\"></script>
        """
        return [nodes.raw("", html, format="html")]

    def _parse_deck(self) -> Dict[str, Any]:
        cards: List[Dict[str, Any]] = []
        current: Dict[str, Any] | None = None
        section: str | None = None

        def flush():
            nonlocal current
            if current is not None:
                for k in ("front", "back"):
                    if current.get(k) is None:
                        current[k] = ""
                cards.append(current)
            current = None

        for raw in self.content:
            line = self._process_figures(raw)
            if line is None:
                line = raw
            s = line.rstrip("\n")

            m = re.match(r"^\s*Q\s*:\s*(.*)$", s, flags=re.IGNORECASE)
            if m:
                flush()
                current = {"front": m.group(1), "back": ""}
                section = "front"
                continue

            m = re.match(r"^\s*A\s*:\s*(.*)$", s, flags=re.IGNORECASE)
            if m and current is not None:
                current["back"] = (current.get("back") or "") + m.group(1)
                section = "back"
                continue

            if section == "front" and current is not None:
                current["front"] = (current.get("front") or "") + "\n" + s
                continue
            if section == "back" and current is not None:
                current["back"] = (current.get("back") or "") + "\n" + s
                continue

        flush()

        for c in cards:
            for key in ("front", "back"):
                val = c.get(key) or ""
                c[key] = self._process_code_blocks(val)

        return {"cards": cards}

    def _process_code_blocks(self, text: str) -> str:
        def repl(match):
            code = match.group(2).replace("\\n", "\n")
            lang = match.group(1)
            return f'<pre><code class="{lang}">{code}</code></pre>'

        pattern = r'<pre><code class="([\\w-]+)">(.*?)</code></pre>'
        return re.sub(pattern, repl, text, flags=re.DOTALL)

    def _process_figures(self, text: str):
        import shutil
        import json as _json

        if not hasattr(self, "_image_counter"):
            self._image_counter = 0

        def _parse_figure_options(alt_text: str) -> Dict[str, Any]:
            opts: Dict[str, Any] = {}
            s = (alt_text or "").strip()

            def parse_pairs(content: str):
                for m in re.finditer(
                    r'(\\w+)\\s*=\\s*(?:"([^"]*)"|\'([^\']*)\'|([^\\s}]+))', content
                ):
                    val = m.group(2) or m.group(3) or m.group(4) or ""
                    opts[m.group(1)] = val

            if s.startswith("{") and s.endswith("}"):
                inner = s[1:-1].strip()
                ok = False
                try:
                    js = s
                    js = re.sub(r"(\\w+)\\s*:", r'"\\1":', js)
                    js = re.sub(r':\\s*([^",}]+)', r': "\\1"', js)
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

        def _build_figure_html(html_img_path: str, options: Dict[str, Any]) -> str:
            user_opts = dict(options or {})
            user_class = user_opts.pop("class", "").strip()
            classes = "flashcard-image adaptive-figure" + (f" {user_class}" if user_class else "")

            alt_text = user_opts.pop("alt", "Figure")
            title = user_opts.pop("title", None)
            width = user_opts.pop("width", None)
            height = user_opts.pop("height", None)
            extra_style = user_opts.pop("style", None)

            def _normalize_wh(val: Any) -> str:
                s = str(val).strip()
                if re.fullmatch(r"\\d+(?:\\.\\d+)?", s):
                    return f"{s}px"
                s = re.sub(r"\\s+(?=(px|%|em|rem|vh|vw)$)", "", s)
                return s

            styles: List[str] = []
            if width is not None:
                styles.append(f"width: {_normalize_wh(width)};")
            if height is not None:
                styles.append(f"height: {_normalize_wh(height)};")
            if extra_style:
                styles.append(str(extra_style))

            attrs = [f'src="{html_img_path}"', f'class="{classes}"', f'alt="{alt_text}"']
            if title:
                attrs.append(f'title="{title}"')
            if styles:
                style_str = " ".join(styles)
                attrs.append(f'style="{style_str}"')
            for k, v in user_opts.items():
                if k not in {"src", "class", "alt", "title", "width", "height", "style"}:
                    attrs.append(f'{k}="{v}"')
            img = f"<img {' '.join(attrs)} >"
            return f'<div class="flashcard-image-container">{img}</div>'

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
                return f'<img src="{raw_src}" class="flashcard-image adaptive-figure" alt="Figure (missing)">'

            relative_doc_path = os.path.relpath(source_dir, app_src_dir)
            figure_dest_dir = os.path.join(app_src_dir, "_static", "figurer", relative_doc_path)
            os.makedirs(figure_dest_dir, exist_ok=True)

            rel_path_from_source = os.path.relpath(abs_fig_src, source_dir)
            safe_path = rel_path_from_source.replace(os.sep, "_").replace("/", "_")
            base, ext = os.path.splitext(safe_path)
            fig_filename = f"flash_{self._image_counter}_{base}{ext}"
            fig_dest_path = os.path.join(figure_dest_dir, fig_filename)
            shutil.copy2(abs_fig_src, fig_dest_path)

            depth = os.path.relpath(source_dir, app_src_dir).count(os.sep)
            rel_prefix = "../" * (depth + 1)
            html_img_path = f"{rel_prefix}_static/figurer/{relative_doc_path}/{fig_filename}"
            return _build_figure_html(html_img_path, options)

        return re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", replace, text)


def setup(app):
    app.add_directive("flashcards", FlashcardsDirective)
    try:
        app.add_css_file("munchboka/css/flashcards.css")
        app.add_js_file("munchboka/js/flashcards.js")
        app.add_css_file("munchboka/css/general_style.css")
    except Exception:
        pass
    return {"version": "0.1", "parallel_read_safe": True, "parallel_write_safe": True}
