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

      Full løsning (default delay from config = 300 s).

.. solution:: Tilpasset løsning
   :delay: 42

   Kortere forsinkelse.

.. solution:: Ingen forsinkelse
   :delay: 0

   Skal ikke tidslåses.

.. solution:: Allerede åpen
   :open:

   Vises med det samme — ingen lås.
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

    # Parent answer block is present (answer-2-toggle button from Answer2Directive)
    assert 'class="answer-2-toggle"' in html

    # Solution inside answer gets default 300 s delay on its toggle button
    assert 'data-delay-seconds="300"' in html

    # Custom per-directive delay
    assert 'data-delay-seconds="42"' in html

    # :delay: 0 — no data attribute emitted
    assert 'data-delay-seconds="0"' not in html

    # :open: — solution is expanded from the start, no lock
    assert "Allerede åpen" in html

    # Toggle button class is present
    assert 'class="solution-2-toggle"' in html

    js = (build / "_static" / "munchboka" / "js" / "solution_timer.js").read_text(encoding="utf8")
    assert "IntersectionObserver" in js
    assert "rootMargin" in js
    assert "START_MARGIN_PX" in js
    assert "isNearViewport" in js
    assert "Du har bare prøvd på oppgaven i" in js
