"""Direct test: call _generate_frame_svg and check if triangle is drawn."""

import tempfile, os, re
from pathlib import Path

# Test: call _generate_frame_svg directly and check the SVG output
from munchboka_edutools.directives.animate import AnimateDirective

content = """triangle: points=((0, 0), (cos(30 * pi/180), sin(30 * pi/180)), (cos(30 * pi/180), 0)), angles=(A, B), angle-radius=20, side-labels=(AB=exact, BC=exact, CA=exact), angle-labels=(A=numeric, C=numeric)
xmin: -1.5
xmax: 1.5
ymin: -1.5
ymax: 1.5"""

options = {"width": "60%"}

with tempfile.TemporaryDirectory() as tmpdir:
    svg_path = os.path.join(tmpdir, "test.svg")
    AnimateDirective._generate_frame_svg(
        None, None, content, svg_path, options, "__interactive_var__", 0.0
    )
    svg = open(svg_path).read()
    paths = len(re.findall(r"<path", svg))
    texts = len(re.findall(r"<text", svg))
    text_groups = re.findall(r'<g[^>]+id="text_[^"]*"', svg)
    print(
        f"Direct _generate_frame_svg: {paths} paths, {texts} texts, {len(text_groups)} text groups, size={len(svg)}"
    )

    # Save for inspection
    import shutil

    shutil.copy(svg_path, "/Users/reneaas/codes/vgs_books/munchboka-edutools/tests/_tri_direct.svg")
    print("Saved to tests/_tri_direct.svg")

# Also test WITHOUT triangle
content_notri = """xmin: -1.5
xmax: 1.5
ymin: -1.5
ymax: 1.5"""

with tempfile.TemporaryDirectory() as tmpdir:
    svg_path = os.path.join(tmpdir, "test.svg")
    AnimateDirective._generate_frame_svg(
        None, None, content_notri, svg_path, options, "__interactive_var__", 0.0
    )
    svg = open(svg_path).read()
    paths = len(re.findall(r"<path", svg))
    print(f"Direct NO triangle: {paths} paths, size={len(svg)}")
