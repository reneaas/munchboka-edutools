"""Build-level tests for the client-side plot-builder directive."""
import io

import pytest
from bs4 import BeautifulSoup
from sphinx.application import Sphinx


def _build(tmp_path, content):
    src = tmp_path / "src"
    src.mkdir()
    (src / "conf.py").write_text(
        "extensions=['munchboka_edutools.directives.plot_builder']\n"
        "master_doc='index'\nproject='Plot builder test'\n",
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
        "Test\n====\n\n.. plot-builder::\n   :height: 500\n",
    )
    assert "ERROR" not in warnings
    html = (out / "index.html").read_text()
    assert html.count("js/plot_builder.js") == 1
    assert html.count("vendor/jsxgraph/jsxgraphcore.js") == 1
    assert html.count("css/plot_builder.css") == 1
    soup = BeautifulSoup(html, "html.parser")
    mount = soup.select_one(".munch-plot-builder")
    assert mount is not None
    assert mount["data-board-height"] == "500"
    assert (out / "_static/munchboka/js/plot_builder.js").is_file()
    assert (out / "_static/munchboka/css/plot_builder.css").is_file()
    assert (out / "_static/munchboka/vendor/jsxgraph/jsxgraphcore.js").is_file()
    assert (out / "_static/munchboka/vendor/mathjax-fbd/tex-svg.min.js").is_file()


def test_two_instances_on_one_page_share_assets_but_have_distinct_ids(tmp_path):
    app, out, warnings = _build(
        tmp_path,
        "Test\n====\n\n.. plot-builder::\n   :name: first\n\n.. plot-builder::\n   :name: second\n",
    )
    assert "ERROR" not in warnings
    html = (out / "index.html").read_text()
    # Vendored/own assets should only be injected once per page, not per instance.
    assert html.count("js/plot_builder.js") == 1
    assert html.count("vendor/jsxgraph/jsxgraphcore.js") == 1
    soup = BeautifulSoup(html, "html.parser")
    mounts = soup.select(".munch-plot-builder")
    assert len(mounts) == 2
    assert mounts[0]["id"] != mounts[1]["id"]


def test_text_builder_has_no_assets(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "conf.py").write_text(
        "extensions=['munchboka_edutools.directives.plot_builder']\nmaster_doc='index'\n",
        encoding="utf8",
    )
    (src / "index.rst").write_text("Test\n====\n\n.. plot-builder::\n", encoding="utf8")
    warnings = io.StringIO()
    app = Sphinx(
        str(src), str(src), str(tmp_path / "out"), str(tmp_path / "doctrees"), "text",
        status=io.StringIO(), warning=warnings, freshenv=True,
    )
    app.build(force_all=True)
    assert "ERROR" not in warnings.getvalue()
    text = (tmp_path / "out" / "index.txt").read_text()
    assert "krever JavaScript" in text
