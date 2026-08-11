import json

from sphinx.application import Sphinx

from munchboka_edutools.directives.interactive_graph import _render_svg_frame_worker


def test_interactive_graph_parallel_worker_angle_arc_arrow_is_preserved():
    svg = _render_svg_frame_worker(
        (
            "\n".join(
                [
                    "angle-arc: (0, 0), 0.2, 0, 45, purple, arrow",
                    "axis: equal",
                    "grid: off",
                    "ticks: off",
                    "fontsize: 32",
                ]
            ),
            {},
        )
    )

    assert svg.lower().count("#6a3d9a") >= 2


def test_multi_interactive_graph_angle_arc_arrow_is_preserved(tmp_path):
    src = tmp_path / "source"
    build = tmp_path / "build"
    doctree = tmp_path / "doctrees"
    src.mkdir()
    build.mkdir()
    doctree.mkdir()

    (src / "conf.py").write_text(
        "extensions = ['munchboka_edutools']\nexclude_patterns = ['_build']\n",
        encoding="utf8",
    )
    (src / "index.rst").write_text(
        r"""
Angle arc arrow
===============

.. multi-interactive-graph::

   ---
   rows: 1
   cols: 1
   interactive-var: x, 0, pi, 4
   interactive-var-start: pi/3
   ---

   :::{interactive-graph}
   angle-arc: (0, 0), 0.2, 0, x * 180 / pi, purple, arrow
   axis: equal
   grid: off
   ticks: off
   fontsize: 32
   :::
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

    graph_dir = next((build / "_static" / "multi_interactive").glob("*/graph_0"))
    base_svg = (graph_dir / "base.svg").read_text(encoding="utf8")
    deltas = json.loads((graph_dir / "deltas.json").read_text(encoding="utf8"))

    assert base_svg.lower().count("#6a3d9a") >= 2
    assert any(
        isinstance(frame, dict)
        and (frame.get("fullSvg") or "").lower().count("#6a3d9a") >= 2
        for frame in deltas[1:]
    )
