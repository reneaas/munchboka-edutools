"""Check recovery hooks in generated HTML, including nested page URLs."""

from io import StringIO

from bs4 import BeautifulSoup
from sphinx.application import Sphinx
from sphinx.util.docutils import docutils_namespace


def test_core_asset_recovery(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "conf.py").write_text(
        "extensions=['munchboka_edutools']\nhtml_theme='basic'\nmaster_doc='index'\n"
    )
    (src / "index.rst").write_text(
        "Recovery\n========\n\n.. toctree::\n\n   chapter/exercises\n"
    )
    (src / "chapter").mkdir()
    (src / "chapter/exercises.rst").write_text(
        "Exercises\n=========\n\n.. part:: a\n\n   Problem\n\n"
        "   .. answer::\n\n      Answer text\n\n"
        "   .. solution::\n\n      Solution text\n\n"
        ".. solution:: Timed\n   :delay: 42\n\n   Timed text\n"
    )
    out = tmp_path / "out"
    with docutils_namespace():
        app = Sphinx(
            str(src), str(src), str(out), str(tmp_path / "doctrees"), "html",
            status=StringIO(), warning=StringIO(), freshenv=True,
        )
        app.build()
        assert app.statuscode == 0

    soup = BeautifulSoup((out / "chapter/exercises.html").read_text(), "html.parser")
    for asset in [
        "css/admonitions.css", "css/part.css", "js/part.js", "js/solution2.js",
        "js/solution_timer.js", "js/goals.js", "js/proof.js", "js/hint.js",
    ]:
        attribute = "href" if asset.endswith(".css") else "src"
        elements = soup.select(f'[{attribute}*="munchboka/{asset}"]')
        assert len(elements) == 1
        element = elements[0]
        assert element[attribute].startswith("../_static/")
        assert "?v=" in element[attribute]
        assert "attempt <= 2" in element["onerror"]
        assert (out / "_static/munchboka" / asset).is_file()

    # Ordered dependency chains must not be retried out of order.
    assert not soup.select_one('script[src*="pairPuzzle/game.js"]').has_attr("onerror")
