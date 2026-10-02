"""Build-level tests for the client-side free-body-diagram-builder directive."""
import io
import json
from pathlib import Path
import shutil
import subprocess

import pytest
from bs4 import BeautifulSoup
from sphinx.application import Sphinx


def _build(tmp_path, content):
    src = tmp_path / "src"
    src.mkdir()
    (src / "conf.py").write_text(
        "extensions=['munchboka_edutools.directives.free_body_diagram_builder']\n"
        "master_doc='index'\nproject='FBD builder test'\n",
        encoding="utf8",
    )
    (src / "index.rst").write_text(content, encoding="utf8")
    out = tmp_path / "out"
    warnings = io.StringIO()
    app = Sphinx(
        str(src), str(src), str(out), str(tmp_path / "doctrees"), "html",
        status=io.StringIO(), warning=warnings, freshenv=True,
    )
    app.build(force_all=True)
    return app, out, warnings.getvalue()


def test_single_instance_loads_assets_once(tmp_path):
    app, out, warnings = _build(
        tmp_path,
        "Test\n====\n\n.. free-body-diagram-builder::\n   :height: 500\n",
    )
    assert "ERROR" not in warnings
    html = (out / "index.html").read_text()
    assert html.count("js/free_body_diagram_builder.js") == 1
    assert html.count("vendor/jsxgraph/jsxgraphcore.js") == 1
    assert html.count("vendor/katex/dist/katex.min.js") == 1
    assert html.count("css/free_body_diagram_builder.css") == 1
    soup = BeautifulSoup(html, "html.parser")
    mount = soup.select_one(".munch-fbd-builder")
    assert mount is not None
    assert mount["data-board-height"] == "500"
    assert (out / "_static/munchboka/js/free_body_diagram_builder.js").is_file()
    assert (out / "_static/munchboka/css/free_body_diagram_builder.css").is_file()
    assert (out / "_static/munchboka/vendor/jsxgraph/jsxgraphcore.js").is_file()
    assert (out / "_static/munchboka/vendor/katex/dist/katex.min.js").is_file()
    assert (out / "_static/munchboka/vendor/mathjax-fbd/tex-svg.min.js").is_file()


def test_two_instances_on_one_page_share_assets_but_have_distinct_ids(tmp_path):
    app, out, warnings = _build(
        tmp_path,
        "Test\n====\n\n.. free-body-diagram-builder::\n   :name: first\n\n"
        ".. free-body-diagram-builder::\n   :name: second\n",
    )
    assert "ERROR" not in warnings
    html = (out / "index.html").read_text()
    assert html.count("js/free_body_diagram_builder.js") == 1
    soup = BeautifulSoup(html, "html.parser")
    mounts = soup.select(".munch-fbd-builder")
    assert len(mounts) == 2
    assert mounts[0]["id"] != mounts[1]["id"]


def test_text_builder_has_no_assets(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "conf.py").write_text(
        "extensions=['munchboka_edutools.directives.free_body_diagram_builder']\nmaster_doc='index'\n",
        encoding="utf8",
    )
    (src / "index.rst").write_text("Test\n====\n\n.. free-body-diagram-builder::\n", encoding="utf8")
    warnings = io.StringIO()
    app = Sphinx(
        str(src), str(src), str(src.parent / "out"), str(src.parent / "doctrees"), "text",
        status=io.StringIO(), warning=warnings, freshenv=True,
    )
    app.build(force_all=True)
    assert "ERROR" not in warnings.getvalue()
    text = (src.parent / "out" / "index.txt").read_text()
    assert "krever JavaScript" in text


def test_export_math_is_self_contained_svg():
    """The vendored browser bundle must render without Node globals or web fonts."""
    node = shutil.which("node")
    if not node:
        pytest.skip("Node.js is needed to exercise the browser math renderer")
    bundle = Path(__file__).resolve().parents[1] / (
        "src/munchboka_edutools/static/vendor/mathjax-fbd/tex-svg.min.js"
    )
    script = r"""
        const fs = require('node:fs');
        const vm = require('node:vm');
        const context = vm.createContext({});
        vm.runInContext(fs.readFileSync(process.argv[1], 'utf8'), context);
        const sources = [String.raw`\vec G`, String.raw`\vec F_{\mathrm{net}}`,
                         String.raw`\frac{mv^2}{r}`, 'x', 'y'];
        console.log(JSON.stringify(sources.map(s => context.MunchFbdMathSvg.render(s))));
    """
    result = subprocess.run([node, "-e", script, str(bundle)], check=True,
                            text=True, capture_output=True)
    for markup in json.loads(result.stdout):
        svg = BeautifulSoup(markup, "xml")
        assert svg.svg is not None
        assert svg.svg.get("viewBox")
        assert svg.find("path") is not None
        assert not svg.find(["foreignObject", "text", "use", "style"])
        assert not svg.select('[data-mml-node="merror"]')
        assert "url(" not in markup
