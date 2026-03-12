from pathlib import Path

from sphinx.application import Sphinx


def _make_source(src: Path) -> None:
    (src / "conf.py").write_text(
        """
project = 'test'
extensions = [
    'munchboka_edutools',
]

html_theme = 'basic'
""".lstrip(),
        encoding="utf8",
    )

    (src / "index.rst").write_text(
        """
Solution timer
==============

.. answer::

   Kort fasit.

.. solution::

   Full løsning.

.. solution:: Tilpasset løsning
   :delay: 42

   Kortere forsinkelse.
""".lstrip(),
        encoding="utf8",
    )


def test_solution_timer_build(tmp_path):
    src = tmp_path / "src"
    build = tmp_path / "build"
    doctree = tmp_path / "doctree"
    src.mkdir()
    build.mkdir()
    doctree.mkdir()
    _make_source(src)

    app = Sphinx(
        srcdir=str(src),
        confdir=str(src),
        outdir=str(build),
        doctreedir=str(doctree),
        buildername="html",
        warningiserror=True,
        freshenv=True,
    )
    app.build()

    html = (build / "index.html").read_text(encoding="utf8")
    assert "class=\"admonition answer" in html
    assert "solution-timed" in html
    assert "solution-delay-300" in html
    assert "solution-delay-42" in html
    assert "solution-ref-index-" in html

    js = (build / "_static" / "munchboka" / "js" / "solution_timer.js").read_text(encoding="utf8")
    assert "IntersectionObserver" in js
    assert "Du har bare prøvd på oppgaven i" in js