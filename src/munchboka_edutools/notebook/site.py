"""Build a Norwegian notebook site without executing any supplied notebooks."""

import json
import shutil
import subprocess
import sys
import tempfile
from hashlib import sha256
from importlib import metadata
from pathlib import Path

ASSETS = Path(__file__).parent / "assets"
EXAMPLES = Path(__file__).parent / "examples"
MARKER = ".munchboka-notebook.json"


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def dependencies():
    """Only require the large optional dependencies when building a notebook site."""
    try:
        return {
            name: metadata.version(name)
            for name in ("jupyterlite-core", "jupyterlite-pyodide-kernel", "nbformat")
        }
    except metadata.PackageNotFoundError as exc:
        raise ValueError(
            'Notebook-bygging krever: pip install "munchboka-edutools[notebook]"'
        ) from exc


def content_files(root):
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError(f"Oppgavemappen finnes ikke: {root}")
    result = []
    for path in sorted(root.rglob("*")):
        if any(
            part.startswith(".") or part == "__pycache__" for part in path.relative_to(root).parts
        ):
            continue
        if path.is_symlink():
            raise ValueError(f"Symbolske lenker støttes ikke i oppgavemappen: {path}")
        if path.is_file():
            result.append(path)
    return result


def validate_notebook(path):
    import nbformat

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("nbformat") != 4:
            raise ValueError("Bruk notebook-format 4 (.ipynb).")
        nbformat.validate(data)
        notebook_metadata = data.get("metadata", {})
        language = notebook_metadata.get("kernelspec", {}).get("language") or notebook_metadata.get(
            "language_info", {}
        ).get("name", "python")
        if language.lower() != "python":
            raise ValueError("Bare Python-notebooks støttes.")
        return data
    except Exception as exc:
        raise ValueError(f"Ugyldig notebook {path.name}: {exc}") from exc


def build_site(output, contents=None, title="Munchboka · Notebook"):
    """Build once into an owned directory; a failed build leaves the old site intact.

    Content-addressed exercise paths prevent a changed teacher template from
    replacing browser-local student work. The original bytes are never executed
    or rewritten at build time.
    """
    versions = dependencies()
    output = Path(output).resolve()
    root = Path(contents or EXAMPLES).resolve()
    if output == root or root in output.parents or output in root.parents:
        raise ValueError("Oppgavemappen og utdatamappen må være adskilt.")
    files = content_files(root)
    notebooks = {p: validate_notebook(p) for p in files if p.suffix.lower() == ".ipynb"}
    digest = sha256()
    for path in files:
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
    revision = digest.hexdigest()[:16]
    digest.update(json.dumps(versions, sort_keys=True).encode())
    digest.update(title.encode())
    digest.update(Path(__file__).read_bytes())
    for path in sorted(ASSETS.rglob("*")):
        if path.is_file():
            digest.update(path.read_bytes())
    fingerprint = digest.hexdigest()
    if output.exists() and any(output.iterdir()):
        marker = output / MARKER
        if not marker.is_file():
            raise ValueError(f"Utdatamappen er ikke en Munchboka-notebook: {output}")
        if (
            json.loads(marker.read_text()).get("fingerprint") == fingerprint
            and (output / "index.html").exists()
        ):
            return output
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".munch-notebook-", dir=output.parent) as temp:
        temp = Path(temp)
        project = temp / "project"
        project.mkdir()
        staged = temp / "site"
        staged.mkdir()
        supplied = project / "content" / "oppgaver" / revision
        supplied.mkdir(parents=True)
        for path in files:
            target = supplied / path.relative_to(root)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
        write_json(
            project / "jupyter-lite.json",
            {
                "jupyter-lite-schema-version": 0,
                "jupyter-config-data": {
                    "appName": title,
                    "exposeAppInBrowser": True,
                    "defaultKernelName": "python",
                    "disabledExtensions": ["@jupyterlab/apputils-extension:announcements"],
                },
            },
        )
        write_json(
            project / "overrides.json",
            {
                "@jupyterlab/translation-extension:plugin": {"locale": "nb_NO"},
                "@jupyterlab/docmanager-extension:plugin": {"autosaveInterval": 10},
                # JupyterLab 4.6's contentVisibility observer can run after a
                # restored notebook detaches. Student worksheets are small;
                # rendering all cells also keeps navigation predictable.
                "@jupyterlab/notebook-extension:tracker": {"windowingMode": "none"},
            },
        )
        command = [
            sys.executable,
            "-m",
            "jupyterlite_core",
            "build",
            "--lite-dir",
            str(project),
            "--output-dir",
            str(staged / "lite"),
            "--contents",
            str(project / "content"),
            "--apps",
            "lab",
            "--no-sourcemaps",
            "--no-unused-shared-packages",
            "--no-libarchive",
        ]
        result = subprocess.run(command, cwd=project, capture_output=True, text=True, check=False)
        if result.returncode:
            raise RuntimeError("JupyterLite-byggingen feilet:\n" + result.stdout + result.stderr)
        for name in ("index.html", "app.js", "style.css"):
            shutil.copyfile(ASSETS / name, staged / name)
        catalog = []
        for path, data in notebooks.items():
            relative = path.relative_to(root).as_posix()
            catalog.append(
                {
                    "id": relative,
                    "path": f"oppgaver/{revision}/{relative}",
                    "title": data.get("metadata", {}).get("title", path.stem.replace("_", " ")),
                }
            )
        write_json(staged / "catalog.json", {"title": title, "notebooks": catalog})
        # Serve a small, maintained Bokmål catalog using JupyterLite's translation API.
        translations = staged / "lite" / "api" / "translations"
        language_data = json.loads((ASSETS / "nb_NO.json").read_text(encoding="utf-8"))
        messages = {key: [value] for key, value in language_data.items()}
        messages[""] = {
            "domain": "jupyterlab",
            "language": "nb-NO",
            "plural_forms": "nplurals=2; plural=(n != 1);",
        }
        write_json(translations / "nb_NO.json", {"data": {"jupyterlab": messages}, "message": ""})
        all_languages = json.loads((translations / "all.json").read_text())
        all_languages["data"]["nb_NO"] = {
            "displayName": "Norwegian Bokmål",
            "nativeName": "Norsk bokmål",
        }
        write_json(translations / "all.json", all_languages)
        write_json(staged / MARKER, {"fingerprint": fingerprint, "versions": versions})
        # Only replace a site carrying our ownership marker, after successful staging.
        backup = temp / "previous"
        if output.exists():
            output.rename(backup)
        try:
            staged.rename(output)
        except OSError:
            if backup.exists():
                backup.rename(output)
            raise
    return output
