"""Test that the triangle primitive renders in interactive-graph frames."""

import os
import re
import tempfile
from pathlib import Path

import pytest


def test_interactive_graph_triangle_renders():
    """Triangle primitives in interactive-graph should produce edges in SVG."""
    from sphinx.application import Sphinx

    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "source"
        build = Path(tmpdir) / "build"
        doctree = Path(tmpdir) / "doctrees"
        src.mkdir()
        build.mkdir()
        doctree.mkdir()

        (src / "conf.py").write_text(
            "extensions = ['munchboka_edutools']\n" "exclude_patterns = ['_build']\n",
            encoding="utf8",
        )
        # Use a triangle with expressions involving the interactive variable.
        # Avoid v=0 and v=180/360 which produce degenerate (collinear) triangles.
        (src / "index.rst").write_text(
            "Triangle in interactive-graph\n"
            "=============================\n\n"
            ".. interactive-graph::\n"
            "   :width: 60%\n\n"
            "   interactive-var: v, 30, 150, 3\n"
            "   interactive-var-start: 30\n"
            "   triangle: points=((0, 0), (cos(v * pi/180), sin(v * pi/180)), (cos(v * pi/180), 0)), angles=(A, B), angle-radius=20, side-labels=(AB=exact, BC=exact, CA=exact), angle-labels=(A=numeric, C=numeric)\n"
            "   xmin: -1.5\n"
            "   xmax: 1.5\n"
            "   ymin: -1.5\n"
            "   ymax: 1.5\n\n"
            "   Triangle test.\n",
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
        assert "interactive-graph-wrapper" in html, "Interactive graph wrapper missing"

        # The delta-based system produces base.svg + deltas.json.
        base_svg = None
        for root, dirs, files in os.walk(str(build)):
            for f in files:
                if f == "base.svg":
                    base_svg = open(os.path.join(root, f), encoding="utf8").read()
                    break
            if base_svg:
                break

        assert base_svg is not None, "No base.svg found in build output"

        # Triangle edges are rendered as <path> elements by matplotlib.
        # A bare axes plot has ~10-15 paths; with triangle edges + labels
        # we expect significantly more.
        path_count = len(re.findall(r"<path", base_svg))
        assert path_count > 15, (
            f"Expected many <path> elements from triangle edges + labels, " f"got only {path_count}"
        )

        # Check that deltas.json exists (confirming multi-frame generation)
        deltas_found = False
        for root, dirs, files in os.walk(str(build)):
            if "deltas.json" in files:
                deltas_found = True
                break
        assert deltas_found, "deltas.json not found — frames not generated"


def test_interactive_graph_triangle_static():
    """Triangle with fixed (non-interactive) coordinates should also work."""
    from sphinx.application import Sphinx

    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "source"
        build = Path(tmpdir) / "build"
        doctree = Path(tmpdir) / "doctrees"
        src.mkdir()
        build.mkdir()
        doctree.mkdir()

        (src / "conf.py").write_text(
            "extensions = ['munchboka_edutools']\n" "exclude_patterns = ['_build']\n",
            encoding="utf8",
        )
        (src / "index.rst").write_text(
            """
Static triangle
===============

.. interactive-graph::
   :width: 60%

   interactive-var: t, 0, 1, 2
   triangle: points=((0, 0), (3, 0), (0, 4)), angles=(A, B, C), side-labels=(AB=exact, BC=exact, CA=exact)
   xmin: -1
   xmax: 5
   ymin: -1
   ymax: 5

   Static triangle.
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

        svg_files = []
        for root, dirs, files in os.walk(str(build)):
            for f in files:
                if f.endswith(".svg"):
                    svg_files.append(os.path.join(root, f))

        assert len(svg_files) > 0, "No SVG frame files generated"

        # The 3-4-5 right triangle should have a right-angle marker
        # (vertex C at origin has a 90° angle).
        # Check that path elements exist in frames.
        has_paths = False
        for svg_path in svg_files:
            content = open(svg_path, encoding="utf8").read()
            if "<path" in content:
                has_paths = True
                break

        assert has_paths, "No triangle edges rendered in static triangle test"
