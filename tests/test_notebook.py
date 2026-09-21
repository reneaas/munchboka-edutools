"""Notebook builds, Sphinx paths, dependency tracking and export invariants."""

import io
import json
import shutil
from urllib.parse import parse_qs, urlsplit

import pytest
from bs4 import BeautifulSoup
from click.testing import CliRunner
from sphinx.application import Sphinx

from munchboka_edutools.directives import notebook as directive
from munchboka_edutools.notebook import site


@pytest.fixture
def content(tmp_path):
    root = tmp_path / "content"
    root.mkdir()
    shutil.copyfile(site.EXAMPLES / "01_python.ipynb", root / "øvelse.ipynb")
    (root / "data.csv").write_text("x,y\n1,2\n", encoding="utf-8")
    return root


def test_invalid_notebooks_and_symlinks(content):
    pytest.importorskip("nbformat")
    path = content / "øvelse.ipynb"
    original = json.loads(path.read_text())
    original["metadata"]["kernelspec"]["language"] = "julia"
    path.write_text(json.dumps(original))
    with pytest.raises(ValueError, match="Python"):
        site.validate_notebook(path)
    path.write_text('{"nbformat": 4, "cells": "broken"}')
    with pytest.raises(ValueError, match="Ugyldig notebook"):
        site.validate_notebook(path)
    (content / "link").symlink_to(content / "data.csv")
    with pytest.raises(ValueError, match="Symbolske"):
        site.content_files(content)


def test_missing_extra_has_actionable_message(monkeypatch):
    def missing(name):
        raise site.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(site.metadata, "version", missing)
    with pytest.raises(ValueError, match=r"munchboka-edutools\[notebook\]"):
        site.dependencies()


def test_real_build_and_incremental_cache(content, tmp_path, monkeypatch):
    pytest.importorskip("jupyterlite_core")
    pytest.importorskip("jupyterlite_pyodide_kernel")
    output = tmp_path / "site"
    site.build_site(output, content, "Testbok")
    catalog = json.loads((output / "catalog.json").read_text())
    entry = catalog["notebooks"][0]
    assert catalog["title"] == "Testbok"
    assert entry["id"] == "øvelse.ipynb"
    supplied = output / "lite/files" / entry["path"]
    assert supplied.read_bytes() == (content / "øvelse.ipynb").read_bytes()
    assert (supplied.parent / "data.csv").read_text() == "x,y\n1,2\n"
    settings = json.loads((output / "lite/jupyter-lite.json").read_text())["jupyter-config-data"]
    assert (
        settings["settingsOverrides"]["@jupyterlab/translation-extension:plugin"]["locale"]
        == "nb_NO"
    )
    assert any(
        x["name"] == "@jupyterlite/pyodide-kernel-extension"
        for x in settings["federated_extensions"]
    )
    assert (output / "lite/api/translations/nb_NO.json").is_file()
    assert (output / "lite/lab/index.html").is_file()
    assert (output / "theme.js").is_file()
    before = (output / site.MARKER).read_bytes()

    def fail(*args, **kwargs):
        raise RuntimeError("simulated build failure")

    monkeypatch.setattr(site.subprocess, "run", fail)
    site.build_site(output, content, "Testbok")  # Cache must skip the subprocess.
    (content / "data.csv").write_text("changed")
    with pytest.raises(RuntimeError, match="simulated"):
        site.build_site(output, content, "Testbok")
    assert (output / site.MARKER).read_bytes() == before
    assert supplied.is_file()  # Failed rebuild did not damage the previous site.


def test_do_not_replace_unowned_output(content, tmp_path, monkeypatch):
    monkeypatch.setattr(site, "dependencies", dict)
    output = tmp_path / "important"
    output.mkdir()
    (output / "keep.txt").write_text("keep")
    with pytest.raises(ValueError, match="ikke en Munchboka"):
        site.build_site(output, content)
    assert (output / "keep.txt").read_text() == "keep"
    with pytest.raises(ValueError, match="adskilt"):
        site.build_site(content / "output", content)


@pytest.mark.parametrize("builder", ["html", "dirhtml", "text", "latex"])
def test_sphinx_nested_paths_and_dependencies(tmp_path, monkeypatch, builder):
    src = tmp_path / "src"
    chapter = src / "kapittel"
    chapter.mkdir(parents=True)
    shutil.copyfile(site.EXAMPLES / "01_python.ipynb", chapter / "øvelse.ipynb")
    (chapter / "data.csv").write_text("a,b\n1,2\n")
    (src / "conf.py").write_text(
        "extensions=['munchboka_edutools.directives.notebook']\nmaster_doc='index'\n"
        "project='Notebook test'\n",
        encoding="utf-8",
    )
    (src / "index.rst").write_text("Notebook\n========\n\n.. toctree::\n\n   kapittel/side\n")
    (chapter / "side.rst").write_text(
        "Oppgave\n=======\n\n.. notebook:: øvelse.ipynb\n"
        '   :title: Test "notebook"\n   :embed:\n   :height: 640px\n'
        "   :button-text: Åpne <oppgaven>\n   :files: data.csv\n",
        encoding="utf-8",
    )
    calls = []

    def fake_build(output, contents, title):
        calls.append(
            sorted(p.relative_to(contents).as_posix() for p in contents.rglob("*") if p.is_file())
        )
        output.mkdir(parents=True, exist_ok=True)
        (output / "index.html").write_text("notebook app")

    monkeypatch.setattr(directive, "build_site", fake_build)
    warnings = io.StringIO()
    out = tmp_path / "out"
    app = Sphinx(
        str(src),
        str(src),
        str(out),
        str(tmp_path / "cache"),
        builder,
        status=io.StringIO(),
        warning=warnings,
        freshenv=True,
    )
    app.build(force_all=True)
    assert not app.statuscode, warnings.getvalue()
    assert "ERROR" not in warnings.getvalue()
    dependencies = {str(p) for p in app.env.dependencies["kapittel/side"]}
    assert any(p.endswith("øvelse.ipynb") for p in dependencies)
    assert any(p.endswith("data.csv") for p in dependencies)
    if builder in {"text", "latex"}:
        assert calls == []
        assert "øvelse.ipynb" in "".join(
            p.read_text() for p in out.glob("**/*") if p.suffix in {".txt", ".tex"}
        )
        return
    assert calls == [["kapittel/data.csv", "kapittel/øvelse.ipynb"]]
    html = out / ("kapittel/side.html" if builder == "html" else "kapittel/side/index.html")
    soup = BeautifulSoup(html.read_text(), "html.parser")
    frame = soup.select_one(".munchboka-notebook-frame")
    url = urlsplit(frame["src"])
    assert (html.parent / url.path).resolve().is_file()
    assert parse_qs(url.query) == {"notebook": ["kapittel/øvelse.ipynb"]}
    assert frame["title"] == 'Test "notebook"'
    # Embedded notebooks rely on the iframe's own "Åpne i ny fane" button, not
    # a page-level link (button-text is only used in the non-embed link mode).
    assert soup.select_one(".munchboka-notebook-link") is None
    assert (out / "_static/munchboka/css/notebook.css").is_file()
    # Removing the directive must remove it from the incremental build inventory.
    (chapter / "side.rst").write_text("Oppgave\n=======\n\nIngen notebook.\n")
    app.build(force_all=True)
    assert len(calls) == 1


def test_fullscreen_implies_embed_and_skips_inline_height(tmp_path, monkeypatch):
    src = tmp_path / "src"
    src.mkdir()
    shutil.copyfile(site.EXAMPLES / "01_python.ipynb", src / "øvelse.ipynb")
    (src / "conf.py").write_text(
        "extensions=['munchboka_edutools.directives.notebook']\nmaster_doc='index'\n"
        "project='Notebook test'\n",
        encoding="utf-8",
    )
    (src / "index.rst").write_text(
        "Notebook\n========\n\n.. notebook:: øvelse.ipynb\n   :fullscreen:\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        directive,
        "build_site",
        lambda output, contents, title: output.mkdir(parents=True, exist_ok=True),
    )
    out = tmp_path / "out"
    app = Sphinx(
        str(src),
        str(src),
        str(out),
        str(tmp_path / "cache"),
        "html",
        status=io.StringIO(),
        warning=io.StringIO(),
        freshenv=True,
    )
    app.build(force_all=True)
    soup = BeautifulSoup((out / "index.html").read_text(), "html.parser")
    wrapper = soup.select_one(".munchboka-notebook")
    assert "munchboka-notebook-fullscreen" in wrapper["class"]
    frame = soup.select_one(".munchboka-notebook-frame")
    assert frame is not None  # :fullscreen: implies :embed:
    assert "height" not in (frame.get("style") or "")  # sized by CSS (vh), not inline
    # No page-level link either — the iframe's own toolbar has "Åpne i ny fane".
    assert soup.select_one(".munchboka-notebook-link") is None


def test_default_link_mode_has_no_iframe(tmp_path, monkeypatch):
    src = tmp_path / "src"
    src.mkdir()
    shutil.copyfile(site.EXAMPLES / "01_python.ipynb", src / "øvelse.ipynb")
    (src / "conf.py").write_text(
        "extensions=['munchboka_edutools.directives.notebook']\nmaster_doc='index'\n"
        "project='Notebook test'\n",
        encoding="utf-8",
    )
    (src / "index.rst").write_text(
        "Notebook\n========\n\n.. notebook:: øvelse.ipynb\n   :button-text: Åpne oppgaven\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        directive,
        "build_site",
        lambda output, contents, title: output.mkdir(parents=True, exist_ok=True),
    )
    out = tmp_path / "out"
    app = Sphinx(
        str(src),
        str(src),
        str(out),
        str(tmp_path / "cache"),
        "html",
        status=io.StringIO(),
        warning=io.StringIO(),
        freshenv=True,
    )
    app.build(force_all=True)
    soup = BeautifulSoup((out / "index.html").read_text(), "html.parser")
    assert soup.select_one(".munchboka-notebook-frame") is None
    link = soup.select_one(".munchboka-notebook-link a")
    assert link.text == "Åpne oppgaven"


def test_directive_without_argument_embeds_blank_notebook(tmp_path, monkeypatch):
    src = tmp_path / "src"
    src.mkdir()
    (src / "conf.py").write_text(
        "extensions=['munchboka_edutools.directives.notebook']\nmaster_doc='index'\n"
        "project='Notebook test'\n",
        encoding="utf-8",
    )
    (src / "index.rst").write_text(
        "Notebook\n========\n\n.. notebook::\n   :fullscreen:\n",
        encoding="utf-8",
    )
    calls = []
    monkeypatch.setattr(
        directive,
        "build_site",
        lambda output, contents, title: calls.append(list(contents.rglob("*")))
        or output.mkdir(parents=True, exist_ok=True),
    )
    out = tmp_path / "out"
    app = Sphinx(
        str(src),
        str(src),
        str(out),
        str(tmp_path / "cache"),
        "html",
        status=io.StringIO(),
        warning=io.StringIO(),
        freshenv=True,
    )
    app.build(force_all=True)
    # The site is still built even though no .ipynb was supplied.
    assert calls == [[]]
    soup = BeautifulSoup((out / "index.html").read_text(), "html.parser")
    frame = soup.select_one(".munchboka-notebook-frame")
    assert parse_qs(urlsplit(frame["src"]).query) == {"new": ["1"]}


def test_cli_build_dispatch_and_errors(monkeypatch, tmp_path):
    from munchboka_edutools.cli import notebook as commands
    from munchboka_edutools.cli.build import cli

    captured = []
    monkeypatch.setattr(commands, "build_site", lambda *args: captured.append(args) or tmp_path)
    result = CliRunner().invoke(
        cli, ["notebook", "build", "--output", str(tmp_path), "--title", "R1"]
    )
    assert result.exit_code == 0, result.output
    assert captured == [(tmp_path, None, "R1")]
    assert "Notebook-nettsiden er klar" in result.output


def test_parallel_inventory_merge_and_purge():
    from types import SimpleNamespace

    env = SimpleNamespace(munchboka_notebooks={"old": ["a.ipynb"]})
    other = SimpleNamespace(munchboka_notebooks={"new": ["b.ipynb"], "unrelated": ["c.ipynb"]})
    directive.merge(None, env, ["new"], other)
    directive.purge(None, env, "old")
    assert env.munchboka_notebooks == {"new": ["b.ipynb"]}


@pytest.mark.parametrize("embed", ["", "true"])
def test_myst_yaml_embed(tmp_path, monkeypatch, embed):
    pytest.importorskip("myst_parser")
    (tmp_path / "conf.py").write_text(
        "extensions=['myst_parser','munchboka_edutools.directives.notebook']\n"
        "master_doc='index'\nmyst_enable_extensions=['colon_fence']\n"
    )
    shutil.copyfile(site.EXAMPLES / "01_python.ipynb", tmp_path / "notebook_test.ipynb")
    (tmp_path / "index.md").write_text(
        "# Notebook\n\n:::{notebook} notebook_test.ipynb\n---\n"
        f"embed: {embed}\nheight: 800px\n---\n:::\n"
    )
    monkeypatch.setattr(directive, "build_site", lambda *args: None)
    warnings = io.StringIO()
    app = Sphinx(
        str(tmp_path),
        str(tmp_path),
        str(tmp_path / "out"),
        str(tmp_path / "cache"),
        "html",
        status=io.StringIO(),
        warning=warnings,
        freshenv=True,
    )
    app.build()
    assert app.statuscode == 0, warnings.getvalue()
    assert "ERROR" not in warnings.getvalue()
    frame = BeautifulSoup((tmp_path / "out/index.html").read_text(), "html.parser").select_one(
        ".munchboka-notebook-frame"
    )
    assert frame is not None
    assert "height:800px" in frame["style"]
    assert "border" not in frame["style"]  # Use the host's theme variables in CSS.
