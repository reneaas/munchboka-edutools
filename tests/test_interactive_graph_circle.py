"""Test that the circle primitive renders in interactive-graph frames."""

import os
import re
import tempfile
from pathlib import Path

import pytest


def test_interactive_graph_circle_renders():
    """Circle primitives in interactive-graph should produce <circle> SVG elements."""
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
Circle in interactive-graph
===========================

.. interactive-graph::
   :width: 60%

   interactive-var: a, 1, 3, 3
   circle: (0, 0), a
   circle: (1, 1), 0.5, fill, blue
   circle: (2, 0), 1, dashed, red
   xmin: -5
   xmax: 5
   ymin: -5
   ymax: 5

   Circle test.
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
        assert "interactive-graph-wrapper" in html, "Interactive graph wrapper missing"

        # The generated frames should contain circle elements.
        # Find the frame SVG files in the build output.
        frame_dir = None
        for root, dirs, files in os.walk(str(build)):
            for f in files:
                if f.endswith(".svg") and "frame" in f.lower():
                    frame_dir = root
                    break
            if frame_dir:
                break

        # If no individual frame files, the SVGs may be embedded in meta.json
        # or directly in the HTML. Check for circle elements in any SVG content.
        svg_files = []
        for root, dirs, files in os.walk(str(build)):
            for f in files:
                if f.endswith(".svg"):
                    svg_files.append(os.path.join(root, f))

        assert len(svg_files) > 0, "No SVG frame files generated"

        # At least one frame SVG should contain a <circle element
        circle_found = False
        for svg_path in svg_files:
            content = open(svg_path, encoding="utf8").read()
            if "<circle" in content:
                circle_found = True
                break

        assert circle_found, (
            "No <circle> element found in any generated SVG frame. "
            f"Checked {len(svg_files)} SVG files."
        )

        # Check that the filled circle (blue) has fill attributes
        fill_found = False
        for svg_path in svg_files:
            content = open(svg_path, encoding="utf8").read()
            style_attrs = re.findall(r'style="([^"]*)"', content)
            normalized = [re.sub(r"\s+", "", s) for s in style_attrs]
            if any("fill-opacity:0.2" in s or "opacity:0.2" in s for s in normalized):
                fill_found = True
                break

        assert fill_found, "Filled circle with alpha not found in SVG frames"
