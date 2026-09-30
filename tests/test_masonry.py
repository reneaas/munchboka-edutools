"""Exercise parsing, assets and source-order fallbacks through real Sphinx builds."""

from io import StringIO

import pytest
from bs4 import BeautifulSoup
from sphinx.application import Sphinx
from sphinx.util.docutils import docutils_namespace

from munchboka_edutools.directives.masonry import columns_option, gap_option


@pytest.mark.parametrize("value", ["0", "13", "1 2", "1 2 3 4", "1 -2 3", "auto"])
def test_invalid_columns(value):
    with pytest.raises(ValueError):
        columns_option(value)


@pytest.mark.parametrize("value", ["-1rem", "1%", "1", "1rem; color:red", "calc(1px)"])
def test_invalid_gap(value):
    with pytest.raises(ValueError):
        gap_option(value)


def build(tmp_path, source, builder="html", umbrella=False):
    src = tmp_path / "src"
    src.mkdir()
    extension = "munchboka_edutools" if umbrella else "munchboka_edutools.directives.masonry"
    (src / "conf.py").write_text(
        f"extensions = ['myst_parser', '{extension}']\n"
        "myst_enable_extensions = ['colon_fence', 'dollarmath']\n"
        "html_theme = 'basic'\nmaster_doc = 'index'\nproject = 'Masonry'\n"
    )
    (src / "index.md").write_text(source)
    warnings = StringIO()
    with docutils_namespace():
        app = Sphinx(
            str(src),
            str(src),
            str(tmp_path / "out"),
            str(tmp_path / "tree"),
            builder,
            status=StringIO(),
            warning=warnings,
            freshenv=True,
        )
        app.build()
    return tmp_path / "out", warnings.getvalue()


SOURCE = """# Cards

::::{masonry}
:columns: 1 2 3
:gap: .5em
:placement: alternating
:class: custom-layout
:name: collection

:::{masonry-card} First *title*
:name: first-card
:class: custom-card

Paragraph with **strong text** and $x^2$.

```{note}
Nested note.
```
:::

:::{masonry-card}
Second body.
:::
::::

See {ref}`the first card <first-card>`.
"""


@pytest.mark.parametrize("umbrella", [False, True])
def test_html_content_and_assets(tmp_path, umbrella):
    out, warnings = build(tmp_path, SOURCE, umbrella=umbrella)
    # The umbrella extension overrides docutils' built-in hint directive.
    unexpected = [
        line
        for line in warnings.splitlines()
        if "directive 'hint' is already registered" not in line
    ]
    assert not unexpected
    soup = BeautifulSoup((out / "index.html").read_text(), "html.parser")
    grid = soup.select_one(".mb-masonry")
    assert grid["data-columns"] == "1 2 3"
    assert grid["data-placement"] == "alternating"
    assert grid["style"] == "--mb-masonry-gap: .5em"
    assert "custom-layout" in grid["class"]
    cards = grid.select(":scope > .mb-masonry-card")
    assert len(cards) == 2
    assert cards[0]["id"] == "first-card"
    assert cards[0].select_one(".mb-masonry-title em").text == "title"
    assert cards[0].select_one(".note").get_text().strip().endswith("Nested note.")
    assert cards[0].select_one(".math")
    assert cards[1].select_one(".mb-masonry-title") is None
    assert soup.select_one('a[href="#first-card"]')
    assert soup.select_one('script[src*="js/masonry.js"]').has_attr("defer")
    for relative in ["css/masonry.css", "js/masonry.js"]:
        assert (out / "_static" / "munchboka" / relative).is_file()
        assert relative in str(soup)


@pytest.mark.parametrize("builder,filename", [("text", "index.txt"), ("latex", "masonry.tex")])
def test_non_html_retains_content(tmp_path, builder, filename):
    out, warnings = build(tmp_path, SOURCE, builder)
    assert not warnings
    content = (out / filename).read_text()
    assert content.index("First") < content.index("Nested note.") < content.index("Second body.")


@pytest.mark.parametrize(
    "source,expected",
    [
        (":::{masonry}\n:columns: 0\n:::", "columns must contain"),
        (":::{masonry}\n:gap: -1px\n:::", "gap must be"),
        (":::{masonry}\n:placement: random\n:::", "placement"),
        (":::{masonry}\nUnexpected paragraph.\n:::", "only masonry-card"),
    ],
)
def test_invalid_directives_report_errors(tmp_path, source, expected):
    _, warnings = build(tmp_path, "# Invalid\n\n" + source)
    assert expected in warnings
