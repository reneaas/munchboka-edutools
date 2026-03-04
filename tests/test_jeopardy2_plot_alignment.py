import json
import re
from pathlib import Path

from sphinx.application import Sphinx


def _extract_jeopardy_data(html: str) -> dict:
    m = re.search(
        r'<script type="application/json" class="jeopardy-data">(.*?)</script>',
        html,
        flags=re.DOTALL,
    )
    assert m, "Jeopardy JSON <script> tag not found"
    return json.loads(m.group(1))


def test_jeopardy2_preserves_plot_figure_alignment_classes(tmp_path: Path):
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

root_doc = 'index'
source_suffix = {
    '.md': 'markdown',
}

html_theme = 'basic'

myst_enable_extensions = [
    'colon_fence',
]
""".lstrip(),
        encoding="utf8",
    )

    # Use the real `plot` directive inside a jeopardy-question.
    # The regression we care about is that the serialized HTML contains
    # `align-right` on the <figure>, not `align="right"`.
    (src / "index.md").write_text(
        """
# Jeopardy 2 plot alignment

:::::{jeopardy-2}

::::{jeopardy-question}
---
category: Plots
points: 100
---

:::{plot}
width: 70%
align: right
function: x, f, (-2, 2)
:::

En test.

::::

:::::
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
    data = _extract_jeopardy_data(html)

    categories = {c["name"]: c for c in data["categories"]}
    tile = categories["Plots"]["tiles"][0]
    qhtml = tile["question"]

    assert "<figure" in qhtml
    assert "align-right" in qhtml
    assert 'align="right"' not in qhtml
