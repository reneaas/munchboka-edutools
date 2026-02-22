import re

import pytest


def test_table_directive_transpose_and_css(tmp_path):
    myst = pytest.importorskip("myst_parser")
    _ = myst  # silence unused

    from sphinx.application import Sphinx

    src = tmp_path / "src"
    build = tmp_path / "build"
    doctree = tmp_path / "doctree"
    src.mkdir()
    build.mkdir()
    doctree.mkdir()

    (src / "conf.py").write_text(
        """
project = 'test'
extensions = [
    'myst_parser',
    'munchboka_edutools',
]

myst_enable_extensions = ['colon_fence']
html_theme = 'basic'
master_doc = 'index'
""".lstrip(),
        encoding="utf8",
    )

    (src / "index.md").write_text(
        """
# Table directive test

:::{table}
labels: x1, ..., x3
1, $x^2$, 3
..., 5, ...
...
4, 5, 6
:::

:::{table}
labels: $t$, Areal av rektangel
0, 0
0.5,
1, 4096
...
3,
:::

:::{table}
---
transpose:
---
labels: x1, ..., x3
1, $x^2$, 3
..., 5, ...
...
4, 5, 6
:::

:::{table}
labels: a, b, c
placement: right
1, 2, 3
:::

:::{table}
labels: x1, x2, x3, x4
placement: center, right, ..., left
1, 2, 3, 4
:::

:::{table}
width: 60%
align: right
labels: u, v
1, 2
:::
""".lstrip(),
        encoding="utf8",
    )

    app = Sphinx(
        srcdir=str(src),
        confdir=str(src),
        outdir=str(build),
        doctreedir=str(doctree),
        buildername="html",
        warningiserror=False,
        freshenv=True,
    )
    app.build()

    html = (build / "index.html").read_text(encoding="utf8")
    assert "munchboka-table" in html
    assert html.count("munchboka-table--transpose") == 1
    assert "munchboka-table-label" in html
    assert "x1" in html and "x3" in html
    # LaTeX content should be preserved in the HTML so KaTeX auto-render can process it.
    assert "$x^2$" in html
    # Transposed tables must NOT create numeric column headers.
    assert 'scope="col">1<' not in html

    # Verify transpose swaps like a matrix transpose:
    # Original data (rows):
    #   [1, $x^2$, 3]
    #   [4, 5, 6]
    # Transposed should include a row for x1 with values 1 and 4.
    compact = "".join(html.split())
    assert "munchboka-table--transpose" in compact
    assert re.search(
        r"<tr><thscope=\"row\"class=\"munchboka-table-label[^\"]*\">x1</th><td[^>]*>1</td>.*<td[^>]*>4</td></tr>",
        compact,
    )

    # Ellipsis rules:
    # - Non-transposed: cell ... => $\ldots$, ellipsis-only row => $\vdots$ in first column only
    assert "$\\ldots$" in html
    assert "$\\vdots$" in html

    # In the non-transposed table, ellipsis-only row should NOT fill every column.
    # (Expect at least one empty cell adjacent to a $\vdots$ cell.)
    compact = "".join(html.split())
    assert re.search(r"<td[^>]*>\$\\vdots\$</td><td[^>]*></td>", compact)

    # In transpose mode, ellipsis tokens should be vertical ellipsis only.
    m_transposed = re.search(
        r"<table[^>]*munchboka-table--transpose[^>]*>[\s\S]*?</table>",
        html,
    )
    assert m_transposed, "Transposed table HTML not found"
    transposed_html = m_transposed.group(0)
    assert "$\\vdots$" in transposed_html
    assert "$\\ldots$" not in transposed_html

    # Labels must also obey the same rules.
    # - In the first (non-transposed) table, labels are columns, so `...` -> $\ldots$ in a <th scope="col">.
    assert re.search(r"<th[^>]*scope=\"col\"[^>]*>\$\\ldots\$</th>", html)
    # - In the transposed table, labels are rows, so `...` -> $\vdots$ in a <th scope="row">.
    assert re.search(r"<th[^>]*scope=\"row\"[^>]*>\$\\vdots\$</th>", html)

    css_path = build / "_static" / "munchboka" / "css" / "table.css"
    assert css_path.exists()
    css = css_path.read_text(encoding="utf8")
    assert re.search(r"rgba\(0,\s*114,\s*178,\s*0\.(1|2)\)", css)
    assert "text-align: center" in css

    # Placement rules
    compact = "".join(html.split())
    # Global placement: placement: right applies to all body cells
    assert re.search(
        r"<tdclass=\"munchboka-table-align-right\">1</td><tdclass=\"munchboka-table-align-right\">2</td><tdclass=\"munchboka-table-align-right\">3</td>",
        compact,
    )

    # Per-label placement with ellipsis expansion:
    # center, right, ..., left for 4 labels => center, right, right, left
    assert re.search(
        r"<thscope=\"col\"class=\"munchboka-table-labelmunchboka-table-align-center\">x1</th>",
        compact,
    )
    assert re.search(
        r"<thscope=\"col\"class=\"munchboka-table-labelmunchboka-table-align-right\">x2</th>",
        compact,
    )
    assert re.search(
        r"<thscope=\"col\"class=\"munchboka-table-labelmunchboka-table-align-right\">x3</th>",
        compact,
    )
    assert re.search(
        r"<thscope=\"col\"class=\"munchboka-table-labelmunchboka-table-align-left\">x4</th>",
        compact,
    )

    # Empty cells must be allowed (trailing comma yields an empty <td>).
    assert re.search(r"<td[^>]*>0\.5</td><td[^>]*></td>", compact)

    # Width option should apply to the frame wrapper.
    assert re.search(
        r'<div[^>]*class="[^"]*munchboka-table-frame[^"]*"[^>]*style="width:60%;"[^>]*>',
        compact,
    )

    # Align defaults to center, but this table explicitly sets align: right.
    assert "munchboka-table-frame--align-center" in compact
    assert re.search(
        r'<div[^>]*class="[^"]*munchboka-table-frame--align-right[^"]*"[^>]*style="width:60%;"',
        compact,
    )
