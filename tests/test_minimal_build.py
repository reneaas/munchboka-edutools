import os
import re
from pathlib import Path
from sphinx.application import Sphinx


def _make_source(src: Path) -> None:
    """Create a minimal Sphinx project source tree."""
    # Minimal conf.py enabling the extension under test.
    (src / "conf.py").write_text(
        """
project = 'test'
extensions = [
    'munchboka_edutools',
]

# Keep the build lean and deterministic
exclude_patterns = []
html_theme = 'basic'
""".lstrip(),
        encoding="utf8",
    )

    # Root document with a quiz block.
    (src / "index.rst").write_text(
        """
Quiz test
=========

.. quiz::

   Q: Hva er $2+2$?
   + 4
   - 5
""".lstrip(),
        encoding="utf8",
    )


def test_quiz_build(tmp_path):
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
        warningiserror=False,
        freshenv=True,
    )
    app.build()

    html = (build / "index.html").read_text(encoding="utf8")
    assert "quiz-main-container" in html
    # Asset folder created
    assert (build / "_static" / "munchboka" / "css" / "general_style.css").exists()
    # Quiz JS copied
    assert (build / "_static" / "munchboka" / "js" / "quiz.js").exists()
    # Quiz CSS copied
    assert (build / "_static" / "munchboka" / "css" / "quiz.css").exists()

    # Smoke test plot directive: create a tiny additional page using plot
    (src / "plotpage.rst").write_text(
        """
Plot test
=========

.. plot::

   function: sin(x), f(x), (-3, 3) \ {0}
   point: (pi/2, f(pi/2))
   xlabel: $x$, 6
   ylabel: $y$, 10
   width: 60%

   Enkel figur.
"""
    )

    app2 = Sphinx(
        srcdir=str(src),
        confdir=str(src),
        outdir=str(build),
        doctreedir=str(doctree),
        buildername="html",
        warningiserror=False,
        freshenv=True,
    )
    app2.build()
    plot_html = (build / "plotpage.html").read_text(encoding="utf8")
    assert re.search(
        r"<svg[^>]*class=\"[^\"]*graph-inline-svg", plot_html
    ), "Inline plot SVG missing"

    # Add Jeopardy page and ensure container and assets
    (src / "jeopardy.rst").write_text(
        """
Jeopardy test
=============

.. jeopardy::

   Category: Tall og Algebra
   100:
   Q: Hva er $2+3$?
   A: 5

   200:
   Q: Faktorer $x^2-1$.
   A: $(x-1)(x+1)$

   Category: Geometri
   100:
   Q: Hvor mange grader er en rett vinkel?
   A: 90$^\circ$
        """
    )

    app3 = Sphinx(
        srcdir=str(src),
        confdir=str(src),
        outdir=str(build),
        doctreedir=str(doctree),
        buildername="html",
        warningiserror=False,
        freshenv=True,
    )
    app3.build()
    jp_html = (build / "jeopardy.html").read_text(encoding="utf8")
    assert "jeopardy-container" in jp_html
    # Inline JSON config is embedded for faithful runtime behavior
    assert 'class="jeopardy-data"' in jp_html
    assert (build / "_static" / "munchboka" / "css" / "jeopardy.css").exists()
    assert (build / "_static" / "munchboka" / "js" / "jeopardy.js").exists()

    # Add interactive-code page and ensure container and assets
    (src / "interactive_code.rst").write_text(
        """
Interactive Code test
======================

.. interactive-code::

   print("Hello from interactive code!")
   x = 2 + 2
   print(f"Result: {x}")
        """
    )

    app4 = Sphinx(
        srcdir=str(src),
        confdir=str(src),
        outdir=str(build),
        doctreedir=str(doctree),
        buildername="html",
        warningiserror=False,
        freshenv=True,
    )
    app4.build()
    ic_html = (build / "interactive_code.html").read_text(encoding="utf8")
    assert "makeInteractiveCode" in ic_html
    assert (build / "_static" / "munchboka" / "css" / "interactive_code.css").exists()
    assert (
        build / "_static" / "munchboka" / "js" / "interactiveCode" / "interactiveCodeSetup.js"
    ).exists()
    assert (build / "_static" / "munchboka" / "js" / "interactiveCode" / "codeEditor.js").exists()
    assert (build / "_static" / "munchboka" / "js" / "interactiveCode" / "pythonRunner.js").exists()
    assert (
        build / "_static" / "munchboka" / "js" / "interactiveCode" / "workerManager.js"
    ).exists()
