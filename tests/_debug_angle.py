"""Test: build user's exact directive and check angle arc size."""

import tempfile, os, re
from pathlib import Path
from sphinx.application import Sphinx


def build_and_check(title, content_lines):
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
        content = "Test\n====\n\n.. plot::\n   :width: 70%\n\n"
        for line in content_lines:
            content += f"   {line}\n"
        content += "\n   Caption.\n"
        (src / "index.rst").write_text(content)

        app = Sphinx(
            str(src),
            str(src),
            str(build),
            str(doctree),
            "html",
            warningiserror=False,
            freshenv=True,
        )
        app.build()

        for root, dirs, files in os.walk(str(build)):
            for f in sorted(files):
                if f.endswith(".svg"):
                    svg = open(os.path.join(root, f)).read()
                    paths = len(re.findall(r"<path", svg))

                    # Extract all 'd' attributes from paths to analyze arc sizes
                    d_attrs = re.findall(r'd="([^"]+)"', svg)
                    # Find paths that look like arcs (many short line segments)
                    arc_paths = [d for d in d_attrs if d.count("L") > 10]

                    print(f"{title}: {paths} paths, size={len(svg)}")

                    # Check SVG viewBox
                    vb = re.search(r'viewBox="([^"]+)"', svg)
                    if vb:
                        print(f"  viewBox: {vb.group(1)}")
                    wh = re.search(r'width="([^"]+)".*?height="([^"]+)"', svg)
                    if wh:
                        print(f"  width={wh.group(1)} height={wh.group(2)}")

                    if arc_paths:
                        for i, ap in enumerate(arc_paths):
                            # Extract coordinates from the arc path
                            coords = re.findall(r"[ML]\s*([\d.]+)\s+([\d.]+)", ap)
                            if coords:
                                xs = [float(c[0]) for c in coords]
                                ys = [float(c[1]) for c in coords]
                                width = max(xs) - min(xs)
                                height = max(ys) - min(ys)
                                print(
                                    f"  Arc path {i}: {len(coords)} points, bbox {width:.1f}x{height:.1f}"
                                )
                    return svg
    return None


# User's exact directive
print("=== User's directive (no angle-radius specified, default=25) ===")
svg = build_and_check(
    "user-default",
    [
        "let: v = 30",
        "triangle: points=((0, 0), (cos(v * pi/180), sin(v * pi/180)), (cos(v * pi/180), 0)), angles=(A, B), color=blue",
        "axis: equal",
    ],
)

# With angle-radius=25 explicitly
print("\n=== angle-radius=25 (explicit) ===")
svg2 = build_and_check(
    "radius-25",
    [
        "let: v = 30",
        "triangle: points=((0, 0), (cos(v * pi/180), sin(v * pi/180)), (cos(v * pi/180), 0)), angles=(A, B), color=blue, angle-radius=25",
        "axis: equal",
    ],
)

# With angle-radius=500 (what user needed to make it visible)
print("\n=== angle-radius=500 ===")
svg2 = build_and_check(
    "radius-500",
    [
        "let: v = 30",
        "triangle: points=((0, 0), (cos(v * pi/180), sin(v * pi/180)), (cos(v * pi/180), 0)), angles=(A, B), color=blue, angle-radius=500",
        "axis: equal",
    ],
)
