import re
from pathlib import Path

from sphinx.application import Sphinx


def test_plot2_directive_renders_inline_svg(tmp_path: Path):
    src = tmp_path / "src"
    build = tmp_path / "build"
    doctree = tmp_path / "doctree"
    src.mkdir()
    build.mkdir()
    doctree.mkdir()

    (src / "conf.py").write_text(
        """
project = 'plot2-test'
extensions = ['munchboka_edutools']
html_theme = 'basic'
""".lstrip(),
        encoding="utf8",
    )
    (src / "index.rst").write_text(
        """
Plot 2 test
===========

.. plot-2::
   :width: 45%

   function: x**2, f(x), (-2, 2)
   point: (1, f(1))
   xmin: -3
   xmax: 3
   ymin: -1
   ymax: 5

   Eksperimentell plot-2 figur.
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
    assert re.search(r"<svg[^>]*class=\"[^\"]*graph-inline-svg", html)
    assert "Eksperimentell plot-2 figur" in html
