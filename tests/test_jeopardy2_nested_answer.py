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


def test_jeopardy2_allows_nested_answer_in_question(tmp_path: Path):
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

# Needed for MyST fenced directive syntax like ::::{jeopardy-2}
myst_enable_extensions = [
    'colon_fence',
]
""".lstrip(),
        encoding="utf8",
    )

    (src / "index.md").write_text(
        """
# Jeopardy 2 nested answer

:::::{jeopardy-2}

::::{jeopardy-question}
---
category: Regneregler
points: 100
---
Bestem lengden av $\\vec{a} = [-1, 2]$.

:::{jeopardy-answer}
$$
|\\vec{a}| = \\sqrt{5}
$$
:::

::::

::::{jeopardy-question}
---
category: Geometri
points: 200
---
Hvor mange grader er en rett vinkel?
::::

::::{jeopardy-answer}
---
category: Geometri
points: 200
---
90$^\\circ$
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

    assert data["values"] == [100, 200]

    categories = {c["name"]: c for c in data["categories"]}
    assert "Regneregler" in categories
    assert "Geometri" in categories

    reg_tile = categories["Regneregler"]["tiles"][0]
    assert reg_tile["value"] == 100
    assert "Bestem lengden" in reg_tile["question"]
    assert "<h3>Fasit</h3>" in reg_tile["answer"]
    assert "\\sqrt{5}" in reg_tile["answer"]

    geo_tile = categories["Geometri"]["tiles"][0]
    assert geo_tile["value"] == 200
    assert "rett vinkel" in geo_tile["question"]
    assert "<h3>Fasit</h3>" in geo_tile["answer"]
    assert "90" in geo_tile["answer"]
