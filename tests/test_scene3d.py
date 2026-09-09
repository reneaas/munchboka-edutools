"""The live scene preserves mathematics independently of either renderer."""
import io
import json
import math
from pathlib import Path

import pytest
from sphinx.application import Sphinx

from munchboka_edutools.directives._scene3d import Expressions, build_scene, evaluate
from munchboka_edutools.directives._interactive_scene3d import Scene3DNode, visit_html


@pytest.mark.parametrize(
    "source",
    [
        "__import__('os')",
        "a.real",
        "a[0]",
        "[x for x in a]",
        "lambda: 1",
        "open('file')",
        "sin(1,2)",
    ],
)
def test_rejects_non_math_expressions(source):
    with pytest.raises(ValueError):
        Expressions(["a"]).compile(source)


def test_expressions_keep_variables_and_nested_parentheses():
    ex = Expressions(["a"])
    triple = ex.vector("(a**2, 1/3, sqrt(2))")
    assert [evaluate(v, {"a": 3}) for v in triple] == pytest.approx([9, 1 / 3, math.sqrt(2)])


def test_embedded_scene_cannot_terminate_json_script():
    from types import SimpleNamespace

    translator = SimpleNamespace(body=[])
    value = '</script><script>alert("x")</script>'
    node = Scene3DNode(
        scene={"text": value},
        board_id="test",
        alt=value,
        width="100%",
        height="460px",
        align="center",
    )
    visit_html(translator, node)
    markup = "".join(translator.body)
    assert value not in markup
    assert markup.count("</script>") == 1
    payload = markup.split('type="application/json">')[1].split("</script>")[0]
    assert json.loads(payload)["text"] == value


def test_scene_sliders_bindings_plane_and_captions():
    scene, _, caption = build_scene(
        [
            "backend: jsxgraph",
            "interactive-var: a, 0, 2, 5",
            "interactive-var: b, -1, 1, 3",
            "interactive-var-start: a=1.4, b=-1",
            "let: c = a**2",
            "def: f(u) = c + sin(u)",
            "point: (f(pi/2), b, sqrt(2)), red",
            "plane: equation=x + a*y = 2",
            "xticks: off",
            "",
            "A caption.",
        ]
    )
    assert caption == 10
    assert [s["initial"] for s in scene["sliders"]] == [3, 0]
    assert scene["ticks"] == [False, True, True]
    point = next(p for p in scene["primitives"] if p["type"] == "point")
    assert [evaluate(t, {"a": 2, "b": -1}) for t in point["coords"]] == pytest.approx(
        [5, -1, math.sqrt(2)]
    )
    plane = next(p for p in scene["primitives"] if p["type"] == "plane")
    assert [evaluate(t, {"a": 3}) for t in plane["coefficients"]] == [1, 3, 0, -2]
    json.dumps(scene, allow_nan=False)


@pytest.mark.parametrize(
    "line",
    [
        "normal-segment: point=(0,0,1), plane=z=0",
        "xstep: 0",
        "xrange: (1,1)",
        "plane: equation=z=x**2",
        "repeat: i=1..5; point: (i,0,0)",
        "interactive-var: a, 1, 1, 3",
    ],
)
def test_unsupported_or_invalid_scene_is_reported(line):
    with pytest.raises((ValueError, KeyError)):
        build_scene([line])


DEMO = """Live 3D
=======

.. interactive-plot3d::

   backend: jsxgraph
   name: live-vector
   interactive-var: a, 0, 2, 5
   interactive-var-start: 1
   xrange: (-2, 3)
   yrange: (-2, 3)
   zrange: (-2, 3)
   grid: true
   vector: (0, 0, 0), (a, 1, 2), blue
   point: (a, 1, 2), red
   plane: equation=z = 0, color=orange, alpha=0.25
   sphere: center=(-1, -1, 1), radius=0.6, color=teal
   right-angle: at=(0,0,0), dir1=(1,0,0), dir2=(0,1,0)
   angle: dir1=(1,0,0), dir2=(0,1,1), radius=0.6
   line: point=(0,0,0), direction=(1,-1,1), color=gray
   text: at=(a,1,2), value="$P$", offset=(0.1,0.1,0.1)

   A live vector and a plane.

.. interactive-plot3d::

   backend: jsxgraph
   ticks: off
   point: (1, 2, 3), red

   Rotation without sliders.

.. toctree::
   :hidden:

   plain
"""


def build_demo(tmp_path, builder="html"):
    src = tmp_path / "src"
    src.mkdir(parents=True, exist_ok=True)
    (src / "conf.py").write_text(
        "project='scene3d'\nextensions=['munchboka_edutools']\nhtml_theme='basic'\nplot_default_usetex=False\n"
    )
    (src / "index.rst").write_text(DEMO)
    (src / "plain.rst").write_text("Plain page\n==========\n\nNo interactive figure.\n")
    warnings = io.StringIO()
    app = Sphinx(
        str(src),
        str(src),
        str(tmp_path / builder),
        str(tmp_path / "doctrees"),
        builder,
        status=io.StringIO(),
        warning=warnings,
        freshenv=True,
    )
    app.build()
    return app, warnings.getvalue()


def test_sphinx_live_output_and_static_fallback(tmp_path):
    app, warnings = build_demo(tmp_path)
    assert "ERROR" not in warnings
    page = (Path(app.outdir) / "index.html").read_text()
    assert page.count('class="munch-3d interactive-plot3d') == 2
    assert 'id="live-vector"' in page
    assert "A live vector and a plane." in page
    assert "munch-3d-fallback" in page
    assert "deltas.json" not in page
    assert page.count("vendor/jsxgraph/jsxgraphcore.js") == 1
    assert "jsxgraphcore.js" not in (Path(app.outdir) / "plain.html").read_text()
    assert len(list((Path(app.outdir) / "_images").glob("*.png"))) == 2
    assert (Path(app.outdir) / "_static/munchboka/vendor/jsxgraph/jsxgraphcore.js").exists()


def test_non_html_builder_uses_initial_image(tmp_path):
    app, warnings = build_demo(tmp_path, "latex")
    assert "ERROR" not in warnings
    tex = next(Path(app.outdir).glob("*.tex")).read_text()
    assert "includegraphics" in tex
    assert "application/json" not in tex


def test_documented_myst_example_builds(tmp_path):
    source = tmp_path / "src"
    source.mkdir()
    (source / "conf.py").write_text(
        "project='myst-scene3d'\nextensions=['munchboka_edutools','myst_parser']\n"
        "myst_enable_extensions=['colon_fence']\nhtml_theme='basic'\n"
    )
    documentation = (Path(__file__).parents[1] / "docs/interactive-plot3d-jsxgraph.md").read_text()
    example = documentation.split("````markdown\n", 1)[1].split("\n````", 1)[0]
    (source / "index.md").write_text("# Live figure\n\n" + example)
    warnings = io.StringIO()
    app = Sphinx(
        str(source),
        str(source),
        str(tmp_path / "html"),
        str(tmp_path / "doctrees"),
        "html",
        status=io.StringIO(),
        warning=warnings,
        freshenv=True,
    )
    app.build()
    assert "ERROR" not in warnings.getvalue()
    assert 'class="munch-3d interactive-plot3d' in (tmp_path / "html/index.html").read_text()
