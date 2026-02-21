from __future__ import annotations

import html
from typing import List, Sequence

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective


def _is_truthy_option(val) -> bool:
    """Interpret directive options from reST or MyST YAML front matter.

    MyST may pass YAML booleans (True/False), empty strings, or strings.
    """

    if val is None:
        return True
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    if s in ("", "1", "true", "yes", "y", "on", "t"):
        return True
    if s in ("0", "false", "no", "n", "off", "f"):
        return False
    return bool(s)


def _split_csv_line(line: str) -> List[str]:
    # Minimal CSV: split on commas, trim whitespace.
    # (Intentionally does not implement quoted commas.)
    return [p.strip() for p in line.split(",")]


_ELLIPSIS_TOKENS = {"...", "…"}


def _normalize_placement_token(token: str) -> str:
    t = str(token).strip().lower()
    if t in {"left", "l", "start"}:
        return "left"
    if t in {"center", "centre", "c", "middle"}:
        return "center"
    if t in {"right", "r", "end"}:
        return "right"
    raise ValueError(f"Invalid placement value: {token!r} (expected left/center/right)")


def _expand_ellipsis_list(values: Sequence[str], width: int) -> List[str]:
    """Expand a placement list to `width`, supporting a single ellipsis marker.

    Example (width=4):
      ["center", "right", "...", "left"] -> ["center", "right", "right", "left"]
    """

    vals = [str(v).strip() for v in values if str(v).strip()]
    if not vals:
        return []

    ellipsis_positions = [i for i, v in enumerate(vals) if v in _ELLIPSIS_TOKENS]
    if not ellipsis_positions:
        return list(vals)
    if len(ellipsis_positions) > 1:
        raise ValueError("placement: only one '...' token is supported")

    idx = ellipsis_positions[0]
    if idx == 0:
        raise ValueError("placement: '...' must follow a placement value")

    head = vals[:idx]
    tail = vals[idx + 1 :]

    fill_value = head[-1]
    fill_count = width - len(head) - len(tail)
    if fill_count < 0:
        raise ValueError("placement: too many values for the number of labels")

    return list(head) + ([fill_value] * fill_count) + list(tail)


def _is_ellipsis_row(line: str) -> bool:
    """True if a raw line represents an ellipsis-only row.

    Accepts:
    - "..."
    - "...," variants
    - "…"
    - a single dot row (".") as a common authoring shorthand
    """

    compact = "".join(ch for ch in line.strip() if ch not in {",", " ", "\t"})
    return compact in {"...", "…", "."}


def _pad_or_trim(row: Sequence[str], width: int) -> List[str]:
    row_list = list(row)
    if len(row_list) < width:
        row_list.extend([""] * (width - len(row_list)))
    return row_list[:width]


class TableDirective(SphinxDirective):
    """A simple labels+values table directive with optional transposition.

    MyST syntax:

    :::{table}
    ---
    transpose:
    ---
    labels: x1, x2, x3
    1, 2, 3
    4, 5, 6
    :::
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = True

    option_spec = {
        # MyST YAML front matter may supply this as a boolean/None/string.
        "transpose": directives.unchanged,
        "class": directives.class_option,
        "name": directives.unchanged,
    }

    def run(self) -> List[nodes.Node]:
        transpose = False
        if "transpose" in self.options:
            transpose = _is_truthy_option(self.options.get("transpose"))
        extra_classes = self.options.get("class", [])

        labels, rows, placement = self._parse_content()

        classes = ["munchboka-table"]
        if transpose:
            classes.append("munchboka-table--transpose")
        classes.extend(extra_classes)

        html_table = self._render_html(
            labels=labels,
            rows=rows,
            transpose=transpose,
            classes=classes,
            placement=placement,
        )
        raw = nodes.raw("", html_table, format="html")

        container = nodes.container()
        container.setdefault("classes", []).extend(["munchboka-table-container"])
        container += raw

        explicit_name = self.options.get("name")
        if explicit_name:
            container["ids"].append(explicit_name)

        return [container]

    def _parse_content(self) -> tuple[List[str], List[List[str]], List[str] | None]:
        transpose = False
        if "transpose" in self.options:
            transpose = _is_truthy_option(self.options.get("transpose"))

        cell_ellipsis = "$\\vdots$" if transpose else "$\\ldots$"
        # Ellipsis-only rows:
        # - Non-transposed tables: show vertical ellipsis in the first column only.
        # - Transposed tables: fill the whole row with vertical ellipsis so that after
        #   transposition it becomes a full column of \vdots.
        row_ellipsis = "$\\vdots$"

        labels: List[str] | None = None
        rows: List[List[str]] = []
        raw_placement: List[str] | None = None

        for raw in self.content:
            line = str(raw).strip()
            if not line:
                continue

            if line.lower().startswith("placement:"):
                after = line.split(":", 1)[1].strip()
                raw_placement = [p for p in _split_csv_line(after) if p]
                continue

            if labels is None:
                if not line.lower().startswith("labels:"):
                    continue
                after = line.split(":", 1)[1].strip()
                raw_labels = [p for p in _split_csv_line(after) if p]
                labels = [cell_ellipsis if p.strip() in _ELLIPSIS_TOKENS else p for p in raw_labels]
                continue

            # Data row
            if _is_ellipsis_row(line):
                rows.append(["..."])
            else:
                parts = _split_csv_line(line)
                # Keep empty cells if author writes consecutive commas.
                rows.append(parts)

        if labels is None:
            labels = []

        width = len(labels)
        placement: List[str] | None = None
        if width > 0 and raw_placement is not None:
            try:
                expanded = _expand_ellipsis_list(raw_placement, width)
                if len(expanded) == 1:
                    placement = [_normalize_placement_token(expanded[0])] * width
                elif len(expanded) == width:
                    placement = [_normalize_placement_token(v) for v in expanded]
                else:
                    raise ValueError(
                        f"placement: expected 1 value or {width} values (got {len(expanded)})"
                    )
            except ValueError as e:
                raise self.error(str(e))

        if width > 0:
            # Apply ellipsis transformations after width is known.
            # - transpose off (labels are columns): cell ... -> \ldots, ellipsis-only row -> \vdots
            # - transpose on  (labels are rows):    cell ... -> \vdots, ellipsis-only row -> \vdots
            normalized_rows: List[List[str]] = []
            for r in rows:
                # Ellipsis-only row expands based on transpose mode.
                if len(r) == 1 and str(r[0]).strip() in _ELLIPSIS_TOKENS:
                    if transpose:
                        normalized_rows.append([row_ellipsis] * width)
                    else:
                        normalized_rows.append([row_ellipsis] + ([""] * (width - 1)))
                    continue

                padded = _pad_or_trim(r, width)
                out_row: List[str] = []
                for cell in padded:
                    if str(cell).strip() in _ELLIPSIS_TOKENS:
                        out_row.append(cell_ellipsis)
                    else:
                        out_row.append(cell)
                normalized_rows.append(out_row)

            rows = normalized_rows

        return labels, rows, placement

    def _render_html(
        self,
        *,
        labels: List[str],
        rows: List[List[str]],
        transpose: bool,
        classes: List[str],
        placement: List[str] | None,
    ) -> str:
        cls_attr = " ".join(html.escape(c) for c in classes if c)

        def _align_class(p: str) -> str:
            v = _normalize_placement_token(p)
            return f"munchboka-table-align-{v}"

        effective_placement: List[str] | None = None
        if placement is not None:
            effective_placement = placement
        elif labels:
            effective_placement = ["center"] * len(labels)

        def _wrap(table_html: str) -> str:
            return (
                '<div class="munchboka-table-frame">'
                '<div class="munchboka-table-scroll">'
                f"{table_html}"
                "</div>"
                "</div>"
            )

        if not labels:
            return _wrap(f'<table class="{cls_attr}"></table>')

        if not transpose:
            thead_cells = "".join(
                f'<th scope="col" class="munchboka-table-label {_align_class(effective_placement[i])}">{html.escape(lbl)}</th>'
                for i, lbl in enumerate(labels)
            )
            thead = f"<thead><tr>{thead_cells}</tr></thead>"

            body_rows = []
            for row in rows:
                tds = "".join(
                    f'<td class="{_align_class(effective_placement[i])}">{html.escape(val)}</td>'
                    for i, val in enumerate(row)
                )
                body_rows.append(f"<tr>{tds}</tr>")
            tbody = "<tbody>" + "".join(body_rows) + "</tbody>"

            return _wrap(f'<table class="{cls_attr}" data-katex="true">{thead}{tbody}</table>')

        # Transpose: labels become row headers; columns are the input row index.
        # Important: do NOT label columns by number; only label by provided labels.
        rcount = len(rows)

        body_rows = []
        for i, lbl in enumerate(labels):
            vals = []
            for r in range(rcount):
                v = rows[r][i] if i < len(rows[r]) else ""
                vals.append(
                    f'<td class="{_align_class(effective_placement[i])}">{html.escape(v)}</td>'
                )
            row_html = (
                f'<tr><th scope="row" class="munchboka-table-label {_align_class(effective_placement[i])}">{html.escape(lbl)}</th>'
                + "".join(vals)
                + "</tr>"
            )
            body_rows.append(row_html)

        tbody = "<tbody>" + "".join(body_rows) + "</tbody>"
        return _wrap(f'<table class="{cls_attr}" data-katex="true">{tbody}</table>')


def setup(app: Sphinx):
    # Note: this intentionally registers under the name "table" to match
    # the requested MyST syntax ::{table}.
    app.add_directive("table", TableDirective)
    return {
        "version": "0.1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
