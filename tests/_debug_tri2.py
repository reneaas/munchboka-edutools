"""Diagnose triangle rendering failure in interactive-graph."""

import tempfile, os, re, sys
from pathlib import Path
from sphinx.application import Sphinx

with tempfile.TemporaryDirectory() as tmpdir:
    src = Path(tmpdir) / "source"
    build = Path(tmpdir) / "build"
    doctree = Path(tmpdir) / "doctrees"
    src.mkdir()
    build.mkdir()
    doctree.mkdir()

    (src / "conf.py").write_text(
        "extensions = ['munchboka_edutools']\nexclude_patterns = ['_build']\n"
    )
    (src / "index.rst").write_text(
        "Triangle test\n"
        "=============\n\n"
        ".. interactive-graph::\n"
        "   :width: 60%\n\n"
        "   interactive-var: v, 30, 150, 3\n"
        "   interactive-var-start: 30\n"
        "   triangle: points=((0, 0), (cos(v * pi/180), sin(v * pi/180)), (cos(v * pi/180), 0)), angles=(A, B), angle-radius=20, side-labels=(AB=exact, BC=exact, CA=exact), angle-labels=(A=numeric, C=numeric)\n"
        "   xmin: -1.5\n"
        "   xmax: 1.5\n"
        "   ymin: -1.5\n"
        "   ymax: 1.5\n\n"
        "   Triangle test.\n"
    )

    app = Sphinx(
        str(src), str(src), str(build), str(doctree), "html", warningiserror=False, freshenv=True
    )
    app.build()

    # Count elements in base.svg
    for root, dirs, files in os.walk(str(build)):
        for f in sorted(files):
            if f == "base.svg":
                content = open(os.path.join(root, f)).read()
                paths = len(re.findall(r"<path", content))
                texts = len(re.findall(r"<text", content))
                lines = len(re.findall(r"<line", content))
                print(
                    f"\nbase.svg: {paths} paths, {texts} texts, {lines} lines, size={len(content)}"
                )
