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


def _path_points(path_tag: str) -> list[tuple[float, float]]:
    return [
        (float(x), float(y))
        for x, y in re.findall(r"[ML]\s+([+-]?\d+(?:\.\d+)?)\s+([+-]?\d+(?:\.\d+)?)", path_tag)
    ]


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


def test_plot_axis_equal_does_not_clip_triangle_edges(tmp_path):
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
        match
        for match in re.finditer(r"<path[^>]+>", svg_html)
        if "#0072b2" in match.group(0)
    ]

    assert blue_paths

    clip_match = re.search(
        r"<clipPath[^>]*>\s*<rect x=\"([^\"]+)\" y=\"([^\"]+)\" "
        r"width=\"([^\"]+)\" height=\"([^\"]+)\"",
        svg_html,
    )
    assert clip_match is not None
    clip_x, clip_y, clip_w, clip_h = (float(value) for value in clip_match.groups())
    clip_x2 = clip_x + clip_w
    clip_y2 = clip_y + clip_h

    for blue_path in blue_paths:
        for x_coord, y_coord in _path_points(blue_path.group(0)):
            assert clip_x <= x_coord <= clip_x2
            assert clip_y <= y_coord <= clip_y2


def test_plot_axis_equal_includes_vector_endpoints_and_labels(tmp_path):
    html = _build_plot_page(
        tmp_path,
        r"""
Vector bounds
=============

.. plot::

   nocache:
   usetex: false
   axis: off
   axis: equal
   let: Gx = 0
   let: Gy = 1
   let: hx = 0.6
   let: hy = 0.8
   vector: (0, 0), (Gx, Gy), blue
   vector: (0, 0), (hx, hy), red
   text: Gx, Gy + 0.1, "$\vec{G}$", center-center
   text: hx, hy + 0.1, "$\vec{c}$", center-center
   let: theta = atan(hy / hx)
   let: phi = acos((Gx * hx + Gy * hy) / (sqrt(Gx^2 + Gy^2) * sqrt(hx^2 + hy^2)))
   angle-arc: (0, 0), 0.2, theta * 180 / pi, (theta + phi) * 180/pi, black
   lw: 1.5
   text: 0.3 * cos((2*theta + phi)/2), 0.3 * sin((2*theta + phi)/2), "$\varphi$", center-center
   line-segment: (hx, hy), (0, hy), dashdot, gray
   let: ds = 0.1
   line-segment: (0, hy - ds), (ds, hy - ds), solid, gray
   line-segment: (ds, hy - ds), (ds, hy), solid, gray
   bar: (-ds, 0), hy, vertical
   text: -1.5*ds, 0.5 * hy, "$h$", center-center
""".lstrip(),
    )

    svg_html = _inline_plot_svgs(html)
    assert "<!-- $\\vec{{G}}$ -->" in svg_html
    assert "<!-- $\\vec{{c}}$ -->" in svg_html

    clip_match = re.search(
        r"<clipPath[^>]*>\s*<rect x=\"([^\"]+)\" y=\"([^\"]+)\" "
        r"width=\"([^\"]+)\" height=\"([^\"]+)\"",
        svg_html,
    )
    assert clip_match is not None
    clip_x, clip_y, clip_w, clip_h = (float(value) for value in clip_match.groups())
    clip_x2 = clip_x + clip_w
    clip_y2 = clip_y + clip_h

    vector_paths = [
        match
        for match in re.finditer(r"<path[^>]+>", svg_html)
        if "#0072b2" in match.group(0) or "#dc5e8b" in match.group(0)
    ]

    assert len(vector_paths) >= 2
    checked_points = 0
    for vector_path in vector_paths:
        for x_coord, y_coord in _path_points(vector_path.group(0)):
            checked_points += 1
            assert clip_x <= x_coord <= clip_x2
            assert clip_y <= y_coord <= clip_y2
    assert checked_points > 0
