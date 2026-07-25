from collections import Counter
import re

from sphinx.application import Sphinx


def _build_plot_page(tmp_path, index_rst: str) -> str:
    src = tmp_path / "src"
    build = tmp_path / "build"
    doctree = tmp_path / "doctree"
    src.mkdir()
    build.mkdir()
    doctree.mkdir()

    (src / "conf.py").write_text(
        """
project = 'plot-svg-id-test'
extensions = ['munchboka_edutools']
html_theme = 'basic'
exclude_patterns = []
""".lstrip(),
        encoding="utf-8",
    )
    (src / "index.rst").write_text(index_rst, encoding="utf-8")

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
    return (build / "index.html").read_text(encoding="utf-8")


def _inline_plot_svgs(html: str) -> str:
    svgs = re.findall(r"<svg\b(?=[^>]*graph-inline-svg)[\s\S]*?</svg>", html)
    assert svgs
    return "\n".join(svgs)


def test_plot_inline_svg_font_glyph_ids_are_namespaced_across_plots(tmp_path):
    html = _build_plot_page(
        tmp_path,
        r"""
Plot SVG ids
============

.. plot::

   axis: off
   text: 0, 0, "$a$", center

.. plot::

   axis: off
   text: 0, 0, "$a$", center

.. plot::

   axis: off
   text: 0, 0, "$\ell$", center
""".lstrip(),
    )

    svg_html = _inline_plot_svgs(html)
    ids = re.findall(r'\bid="([^"]+)"', svg_html)
    duplicates = {value: count for value, count in Counter(ids).items() if count > 1}

    assert not duplicates
    assert not re.search(r'\bid="CMMI12-61"', svg_html)
    assert not re.search(r'xlink:href="#CMMI12-61"', svg_html)
    assert re.search(r'\bid="cpl_[^"]+CMMI12-61"', svg_html)
    assert re.search(r'xlink:href="#cpl_[^"]+CMMI12-61"', svg_html)


def test_plot_text_labels_are_preserved_with_math_variables(tmp_path):
    html = _build_plot_page(
        tmp_path,
        r"""
Plot labels
===========

.. plot::

   width: 70%
   ticks: off
   let: x = 2.4
   point: (0, 4)
   point: (8, 0)
   point: (0, x)
   point: (x, 0)
   point: (4, 2)
   let: dx = 0.15
   let: dy = 0.15
   line-segment: (0, 4), (8, 0), solid, black
   polygon: (x, 0), (0, x), (4, 2), blue, 0.2
   text: 0 - dx, x, "$P(0, a)$", center-left
   text: x, -dy, "$Q(a, 0)$", bottom-center
   text: -dx, -dy, "$O$", bottom-left
   text: 8, dy, "$B(8, 0)$", top-right
   text: 0 - dx, 4, "$A(0, 4)$", center-left
   text: 4 + dx, 2 + dy, "$M(4, 2)$", top-right
   xmin: -1.5
   xmax: 9
   ymin: -1
   ymax: 5
   axis: equal
""".lstrip(),
    )

    svg_html = _inline_plot_svgs(html)

    assert "<!-- $P(0, a)$ -->" in svg_html
    assert "<!-- $Q(a, 0)$ -->" in svg_html
    assert "<!-- $P(0, \\ell)$ -->" not in svg_html
    assert "<!-- $Q(\\ell, 0)$ -->" not in svg_html


def test_plot_triangle_edges_are_rendered_as_one_joined_path(tmp_path):
    html = _build_plot_page(
        tmp_path,
        r"""
Triangle edges
==============

.. plot::

   axis: off
   axis: equal
   let: s = 6
   let: Ax = 0
   let: Ay = 0
   let: v = 30 * pi / 180
   let: Bx = s * cos(v)
   let: By = 0
   let: Cx = s * cos(v)
   let: Cy = s * sin(v)
   triangle: points=((Ax, Ay), (Bx, By), (Cx, Cy)), angles=(A, B), angle-radius=60
""".lstrip(),
    )

    svg_html = _inline_plot_svgs(html)
    blue_paths = [
        match.group(0)
        for match in re.finditer(r"<path[^>]+>", svg_html)
        if "#0072b2" in match.group(0)
    ]

    assert len(blue_paths) == 1
    assert blue_paths[0].count("\nL ") == 3
    assert "stroke-linecap: round" in blue_paths[0]
