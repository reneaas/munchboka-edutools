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

    def test_circuit_build_inline_svg(tmp_path):
        src = tmp_path / "src"
        src.mkdir()

        (src / "conf.py").write_text(
            """
    extensions = [
        'munchboka_edutools',
    ]

    master_doc = 'index'
    """.lstrip(),
            encoding="utf-8",
        )

        (src / "index.rst").write_text(
            """
    Circuit
    =======

    .. circuit::
       :width: 70%

       component: V1, battery, 12 V
       component: R1, resistor, 1 kΩ
       component: L1, lamp

       circuit: series(V1, parallel(R1, L1))
    """.lstrip(),
            encoding="utf-8",
        )

        build = tmp_path / "_build"

        from sphinx.application import Sphinx

        app = Sphinx(
            srcdir=str(src),
            confdir=str(src),
            outdir=str(build / "html"),
            doctreedir=str(build / "doctree"),
            buildername="html",
            warningiserror=True,
        )
        app.build()

        html = (build / "html" / "index.html").read_text(encoding="utf-8")
        assert '<svg class="graph-inline-svg' in html
        assert "circuit-inline-svg" in html

    # Smoke test plot directive: create a tiny additional page using plot
    (src / "plotpage.rst").write_text(
        """
Plot test
=========

.. plot::

    function: sin(x), f(x), (-3, 3) \\ {0}
   point: (pi/2, f(pi/2))
   xlabel: $x$, 6
   ylabel: $y$, 10
   width: 60%

   Enkel figur.

.. plot::

    function: sin(x), f, (0, 4)
    fill-between: f(x), 0, (0, 4), blue, 0.2, where=above
    width: 40%

    Fill-between test (function label).

.. plot::

    let: L = 3
    let: r = 1/2
    def: s(x) = L*(1 - r**x)
    repeat: n=1..3; point: (s(n), 0)
    function: s(x), s(x), (0, 4)
    fill-between: s(x), 0, (0, 4), blue, 0.2, where=above
    width: 40%

    Makrotest (let/def/repeat).

.. plot::

    circle: (0, 0), 1, fill, #123456
    xmin: -2
    xmax: 2
    ymin: -2
    ymax: 2
    width: 30%

    Filled circle test.

.. plot::

    let: a = 4
    let: b = 2
    let: r = b / 2
    curve: a + r * cos(t), b / 2 + r * sin(t), (-pi / 2, pi / 2), solid, #13579b
    xmin: -1
    xmax: 6
    ymin: -1
    ymax: 3
    axis: off
    axis: equal
    width: 30%

    Curve with let-macros test.

.. plot::

    let: d = 0.35
    def: px(i, j) = i + d * j
    def: py(i, j) = j / 3
    repeat: i=0..1; repeat: j=0..1; line-segment: (px(i, j), py(i, j)), (px(i, j) + 0.12, py(i, j)), solid, #2468ac
    xmin: -0.1
    xmax: 1.6
    ymin: -0.1
    ymax: 0.8
    axis: off
    width: 30%

    Nested repeat and multi-arg def test.

.. plot::

        let: d = 0.4
        macro: shortseg(i, j, color)
            line-segment: (i + d * j, j / 4), (i + d * j + 0.15, j / 4), solid, color
            point: (i + d * j, j / 4)
        endmacro
        repeat: i=0..1; repeat: j=0..1; use: shortseg(i, j, #b7410e)
        xmin: -0.1
        xmax: 1.7
        ymin: -0.1
        ymax: 0.8
        axis: off
        width: 30%

        Macro block and use test.

.. plot::

    let: d = 0
    macro: scopedseg(i, color)
        let: d = i / 10
        def: px(x) = x + d
        line-segment: (px(0), i / 5), (px(1/5), i / 5), solid, color
    endmacro
    use: scopedseg(1, #aa0000)
    use: scopedseg(2, #00aa00)
    line-segment: (d, 0), (d + 0.08, 0), solid, #000000
    xmin: -0.1
    xmax: 0.5
    ymin: -0.1
    ymax: 0.6
    axis: off
    width: 30%

    Scoped local let and def test.
"""
    )

    # Smoke test interactive-graph directive with plot-style macros.
    (src / "interactivegraph.rst").write_text(
        """
Interactive graph test
======================

.. interactive-graph::
   :width: 60%

    interactive-var: a, 0, 2, 5
    parallel: true
    interactive-workers: 2
   let: L = 3
   def: s(x) = L*(1 + a*x)
   repeat: n=1..2; point: (n, s(n))
   function: s(x), s
   xmin: 0
   xmax: L
   ymin: 0
   ymax: 10

   Makrotest i interactive-graph.
""".lstrip(),
        encoding="utf8",
    )

    (src / "interactivegraph_multi.rst").write_text(
        """
Interactive graph multi test
============================

.. interactive-graph::
   :width: 60%

   interactive-var: a, 0, 1, 2
   interactive-var: b, 0, 1, 2
   interactive-workers: 2
   function: a*x + b
   xmin: 0
   xmax: 2
   ymin: 0
   ymax: 3

   Multi-variabel test.
""".lstrip(),
        encoding="utf8",
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
    assert "Ugyldig funksjon 's(x)'" not in plot_html

    # Ensure circle fill uses the requested alpha (0.2) and color.
    # Matplotlib may insert newlines into long attributes (even inside words),
    # so normalize whitespace before checking.
    style_attrs = re.findall(r'style="([^"]*)"', plot_html)
    normalized = [re.sub(r"\s+", "", s) for s in style_attrs]
    assert any(
        ("fill:#123456" in s)
        and ("stroke:#123456" in s)
        and (("fill-opacity:0.2" in s) or ("opacity:0.2" in s))
        for s in normalized
    ), "Filled circle not found in SVG output"
    assert any("#13579b" in s for s in normalized), "Curve using let-macros not found in SVG output"
    assert (
        sum(1 for s in normalized if "stroke:#2468ac" in s) >= 4
    ), "Nested repeat with multi-arg defs did not render expected line segments"
    assert (
        sum(1 for s in normalized if "stroke:#b7410e" in s) >= 4
    ), "Macro block expansion did not render expected line segments"
    assert any("stroke:#aa0000" in s for s in normalized), "First scoped macro invocation missing"
    assert any("stroke:#00aa00" in s for s in normalized), "Second scoped macro invocation missing"
    assert any("stroke:#000000" in s for s in normalized), "Outer-scope line segment missing"

    ig_html = (build / "interactivegraph.html").read_text(encoding="utf8")
    assert "interactive-graph-wrapper" in ig_html
    assert 'type="range"' in ig_html

    ig_multi_html = (build / "interactivegraph_multi.html").read_text(encoding="utf8")
    assert "interactive-graph-wrapper" in ig_multi_html
    assert "interactive-controls-" in ig_multi_html
    assert "meta.json" in ig_multi_html

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
   A: 90$^\\circ$
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
